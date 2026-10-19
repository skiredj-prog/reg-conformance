#!/usr/bin/env python3
"""
verify_effective_guarantees.py — Vérification build-time de la garantie EFFECTIVE.

L'admissibilité STRUCTURELLE (compatibility-rules) prouve seulement que la
configuration est cohérente. Ce script vérifie que chaque capacité RÉCLAMÉE par
la config d'un profil est attestée par une preuve RÉELLE :

  - evidence_type et capability_ids couverts ;
  - verified == true ;
  - evidence_ref : chemin relatif, sans '..', sans chemin absolu, pointant vers
    un fichier existant dans le dépôt ;
  - evidence_sha256 présent et égal au SHA-256 du fichier.

Politique par défaut : fail-closed.

Limites (documentées, non résolues ici) :
  - `verified` reste une assertion déclarée dans le profil : ce script ne vérifie
    pas l'identité du vérificateur ni une signature sur l'attestation.
  - Le hash garantit que le fichier n'a pas changé depuis l'attestation ; il ne
    garantit pas que son contenu est vrai.

Usage : python3 tools/verify_effective_guarantees.py  (exit 0 si tout est attesté)
"""

import glob
import hashlib
import os
import re
import sys

import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAPABILITIES = os.path.join(BASE_DIR, "catalog", "capabilities-v1.yaml")
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
AXES = ("HOST_SCOPE", "DEDUP_LAYER", "CONCURRENCY", "UNCERTAINTY")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def load_capabilities(path=CAPABILITIES):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def required_evidence(config: dict, caps: dict):
    """Retourne (ensemble des pairs (capability_id, evidence_type), capability_ids connus)."""
    required = set()
    known_cap_ids = set()
    for axis in AXES:
        value = config.get(axis)
        cap_entry = caps["capabilities"].get(axis, {}).get(value)
        if cap_entry is None:
            continue  # valeur inconnue → géré par la validation structurelle
        cid = cap_entry["capability_id"]
        known_cap_ids.add(cid)
        for ev in cap_entry["required_evidence"]:
            required.add((cid, ev))
    return required, known_cap_ids


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_evidence(base_dir: str, ref: str):
    """Retourne (chemin absolu, None) ou (None, message d'erreur)."""
    if os.path.isabs(ref):
        return None, "evidence_ref absolu interdit"
    norm = os.path.normpath(ref)
    if norm.startswith("..") or os.path.isabs(norm):
        return None, "evidence_ref hors du dépôt interdit"
    full = os.path.join(base_dir, norm)
    if not os.path.isfile(full):
        return None, "fichier de preuve absent"
    return full, None


def check_profile(path, caps, base_dir=BASE_DIR) -> tuple:
    """Retourne (erreurs: list, avertissements: list)."""
    name = os.path.basename(path)
    errors, warnings = [], []
    with open(path, encoding="utf-8") as f:
        profile = yaml.safe_load(f)

    config = profile.get("config", {})
    required, known_cap_ids = required_evidence(config, caps)

    covered = set()
    for i, att in enumerate(profile.get("attestations", []) or []):
        label = f"attestation #{i+1}"
        cids = att.get("capability_ids", [])
        ev_type = att.get("evidence_type")
        ev_ref = att.get("evidence_ref")
        ev_sha = att.get("evidence_sha256")

        for cid in cids:
            if cid not in known_cap_ids and cid not in {c for c, _ in required}:
                warnings.append(f"{name} {label} : capability_id inconnu '{cid}'")

        if not att.get("verified", False):
            errors.append(f"{name} {label} ({ev_type}) : verified=false")
            continue
        if not ev_ref:
            errors.append(f"{name} {label} ({ev_type}) : evidence_ref vide")
            continue
        full, err = resolve_evidence(base_dir, ev_ref)
        if err:
            errors.append(f"{name} {label} ({ev_type}) : {err} ({ev_ref})")
            continue
        if not ev_sha or not SHA256_RE.match(str(ev_sha)):
            errors.append(f"{name} {label} ({ev_type}) : evidence_sha256 absent ou invalide")
            continue
        actual = sha256_file(full)
        if actual != ev_sha:
            errors.append(f"{name} {label} ({ev_type}) : hash ne correspond pas "
                          f"(attendu {ev_sha[:12]}…, obtenu {actual[:12]}…)")
            continue
        for cid in cids:
            covered.add((cid, ev_type))

    for cid, ev in sorted(required - covered):
        errors.append(f"{name} : capacité {cid} réclamée, preuve {ev} manquante")

    for cid, ev in sorted(covered - required):
        warnings.append(f"{name} : attestation {cid}/{ev} non réclamée par la config")

    return errors, warnings


def main():
    caps = load_capabilities()
    profiles = sorted(glob.glob(os.path.join(PROFILES_DIR, "*.yaml")))
    if not profiles:
        print("Aucun profil trouvé (rien à vérifier).")
        return 0

    all_errors, all_warnings = [], []
    for p in profiles:
        errs, warns = check_profile(p, caps)
        all_errors.extend(errs)
        all_warnings.extend(warns)
        status = "ÉCHEC" if errs else "OK"
        print(f"{status} {os.path.basename(p)}" + (f"  ({len(warns)} avertissement(s))" if warns else ""))

    for w in all_warnings:
        print("  !", w)
    if all_errors:
        print("\nÉCHEC de garantie effective :")
        for e in all_errors:
            print("  -", e)
        return 1
    print(f"\n{len(profiles)} profil(s) : toutes les capacités réclamées sont attestées.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
