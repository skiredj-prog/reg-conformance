"""
_ref_impl.py — Implémentation de référence MINIMALE des mécanismes REG+,
utilisée UNIQUEMENT par les tests adversariaux. Une implémentation de production
doit utiliser une bibliothèque RFC 8785 complète (la canonicalisation ici est
une approximation suffisante pour des fixtures contrôlées : clés ASCII, entiers).

Couvre : canonicalisation JCS (approximation fixtures), calcul current_hash,
signature/vérification Ed25519, continuité hash-chain, injection-validator
stateful (anti-rejeu, fraîcheur, portée correlation_id), machine à états commit.
"""

import hashlib
import json
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


# ---------- Canonicalisation et hash ----------

def canonicalize(obj) -> bytes:
    """JCS approximation : clés triées, pas d'espace, ensure_ascii=False."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(obj) -> str:
    return "sha256:" + hashlib.sha256(canonicalize(obj)).hexdigest()


def pre_image(record: dict) -> dict:
    """Pré-image de current_hash : tout l'enregistrement SAUF integrity."""
    return {k: v for k, v in record.items() if k != "integrity"}


def compute_current_hash(record: dict) -> str:
    return sha256_hex(pre_image(record))


def sign_record(record: dict, priv: Ed25519PrivateKey, producer_key_id: str) -> dict:
    """Renseigne integrity.current_hash + integrity.signature. Retourne l'enregistrement."""
    h = compute_current_hash(record)
    sig = priv.sign(h.encode("utf-8")).hex()
    record["integrity"] = {
        "current_hash": h,
        "signature": sig,
        "producer_key_id": producer_key_id,
    }
    return record


def verify_record(record: dict, pub) -> bool:
    """Vérifie current_hash ET signature. Retourne False si altération ou origine invalide."""
    integrity = record.get("integrity", {})
    h_stored = integrity.get("current_hash")
    sig = integrity.get("signature")
    if not h_stored or not sig:
        return False
    if compute_current_hash(record) != h_stored:
        return False  # altération du contenu (inclut chain.previous_hash)
    try:
        pub.verify(bytes.fromhex(sig), h_stored.encode("utf-8"))
        return True
    except (InvalidSignature, ValueError):
        return False


def verify_chain(records: list) -> bool:
    """Continuité : records[i].chain.previous_hash == records[i-1].integrity.current_hash.
    Le premier (genèse) doit avoir previous_hash=None."""
    for i, rec in enumerate(records):
        prev = rec["chain"]["previous_hash"]
        if i == 0:
            if prev is not None:
                return False
        else:
            if prev != records[i - 1]["integrity"]["current_hash"]:
                return False
    return True


# ---------- AssuranceSignal ----------

def signal_payload(signal: dict) -> dict:
    return {k: v for k, v in signal.items() if k != "signature"}


def sign_signal(signal: dict, priv: Ed25519PrivateKey) -> dict:
    sig = priv.sign(canonicalize(signal_payload(signal))).hex()
    signal["signature"] = sig
    return signal


def verify_signal(signal: dict, pub) -> bool:
    sig = signal.get("signature")
    if not sig:
        return False
    try:
        pub.verify(bytes.fromhex(sig), canonicalize(signal_payload(signal)))
        return True
    except (InvalidSignature, ValueError):
        return False


def signal_fresh(signal: dict, t_eval: float, ttl_resolution: dict) -> bool:
    """Fraîcheur calculée sur t_eval (explicite), jamais sur l'horloge système."""
    issued = time.mktime(time.strptime(signal["issued_at"], "%Y-%m-%dT%H:%M:%SZ"))
    if "expires_at" in signal:
        expires = time.mktime(time.strptime(signal["expires_at"], "%Y-%m-%dT%H:%M:%SZ"))
    else:
        ttl = ttl_resolution.get(signal["signal_type"], 30)
        expires = issued + ttl
    return issued <= t_eval <= expires


class InjectionValidator:
    """Stade A (stateful) : valide avant Evaluate. Registre anti-rejeu borné."""

    def __init__(self, key_registry: dict, ttl_resolution: dict):
        self.key_registry = key_registry  # assure_instance_id -> public key
        self.ttl_resolution = ttl_resolution
        self.consumed = set()  # signal_id déjà consommés (borné en prod par TTL)

    def accept(self, signal: dict, now: float, in_scope_correlation_ids: set) -> tuple:
        """Retourne (accepte: bool, raison: str|None)."""
        # 1. signature + identité émetteur
        inst = signal.get("assure_instance_id")
        pub = self.key_registry.get(inst)
        if pub is None:
            return False, "emetteur_inconnu"
        if not verify_signal(signal, pub):
            return False, "signature_invalide"
        # 2. fraîcheur initiale (sur now, injection)
        if not signal_fresh(signal, now, self.ttl_resolution):
            return False, "signal_non_frais"
        # 3. anti-rejeu
        sid = signal["signal_id"]
        if sid in self.consumed:
            return False, "rejeu"
        # 4. portée correlation_id
        cid = signal.get("correlation_id")
        if cid is not None and cid not in in_scope_correlation_ids:
            return False, "correlation_hors_perimetre"
        self.consumed.add(sid)
        return True, None


def critical_signal_state(signals: list, signal_type: str, t_eval: float, ttl_resolution: dict, profile_mapping: dict) -> str:
    """4 états §5. profile_mapping peut être {} (non déclaré → défaut fail-closed).
    Retourne (etat, verdict_minimal)."""
    of_type = [s for s in signals if s["signal_type"] == signal_type]
    if not of_type:
        return "ABSENT", "HOLD"  # absence ≠ favorable
    latest = max(of_type, key=lambda s: s["issued_at"])
    fresh = signal_fresh(latest, t_eval, ttl_resolution)
    if fresh:
        if latest["severity"] == "critical":
            return "VALID_DEGRADATION", profile_mapping.get(signal_type, "HARD_VETO")
        return "VALID_FAVORABLE", profile_mapping.get(signal_type, "PASS")
    # expiré
    if latest["severity"] == "critical":
        return "EXPIRED_CRITICAL", profile_mapping.get(signal_type, "HOLD")  # défaut fail-closed
    return "EXPIRED_NON_CRITICAL", profile_mapping.get(signal_type, "PASS")


# ---------- Machine à états commit ----------

def commit_outcome(evaluation_verdict: str, commit_attempted: bool, commit_result: str) -> str:
    """Dérive effective_outcome. Reflet des règles du schéma."""
    if evaluation_verdict == "HARD_VETO":
        return "VETOED"
    if evaluation_verdict == "HOLD" and not commit_attempted:
        return "HELD"
    if commit_attempted and commit_result == "COMMITTED":
        return "EXECUTED"
    if commit_attempted and commit_result in ("FAILED_RACE", "FAILED_CONSTRAINT", "ERROR"):
        return "COMMIT_FAILED"
    return "INCOHERENT"
