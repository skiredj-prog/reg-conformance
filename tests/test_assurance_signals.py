#!/usr/bin/env python3
"""
test_assurance_signals.py — Tests adversariaux du contrat Assure.

Vérifie :
  1. Anti-injection : non signé / mal signé / émetteur inconnu → rejet au stade A
  2. Anti-rejeu : même signal_id accepté une seule fois
  3. Fraîcheur calculée sur t_eval EXPLICITE (déterminisme), pas l'horloge système
  4. correlation_id hors périmètre → rejet
  5. Signal critique expiré → EXPIRED_CRITICAL + défaut fail-closed (HOLD), jamais PASS
  6. Absence de signal ≠ état favorable
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ref_impl import (
    InjectionValidator, critical_signal_state, sign_signal, signal_fresh, verify_signal,
)

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

TTL = {"hypothesis.weakened": 30, "hypothesis.verified": 30}


def t(ts):
    return time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))


def base_signal(sid, sig_type="hypothesis.weakened", severity="critical",
                issued="2026-10-18T12:00:00Z", expires="2026-10-18T12:00:30Z",
                cid="run_abc"):
    return {
        "signal_id": sid,
        "signal_type": sig_type,
        "severity": severity,
        "issued_at": issued,
        "expires_at": expires,
        "assure_instance_id": "assure-01",
        "correlation_id": cid,
        "observed_value": 150,
        "threshold": 100,
    }


def main():
    failures = []
    priv = Ed25519PrivateKey.generate()
    other_priv = Ed25519PrivateKey.generate()
    key_registry = {"assure-01": priv.public_key(), "assure-02": other_priv.public_key()}

    iv = InjectionValidator(key_registry, TTL)
    now = t("2026-10-18T12:00:10Z")
    in_scope = {"run_abc"}

    # 1. Signal non signé → rejeté
    unsigned = base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A1")
    ok, reason = iv.accept(unsigned, now, in_scope)
    if ok:
        failures.append("1. signal non signé accepté")

    # 2. Payload altéré après signature → signature invalide → rejet
    s2 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A2"), priv)
    s2["severity"] = "info"  # altération
    if verify_signal(s2, priv.public_key()):
        failures.append("2. payload altéré passe la vérification de signature")

    # 3. Émetteur inconnu → rejet
    s3 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A3"), other_priv)
    s3["assure_instance_id"] = "assure-inconnu"
    ok, reason = iv.accept(s3, now, in_scope)
    if ok or reason != "emetteur_inconnu":
        failures.append(f"3. émetteur inconnu accepté (raison={reason})")

    # 4. Anti-rejeu : accepté une fois, rejeté la deuxième
    s4 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A4"), priv)
    ok1, _ = iv.accept(s4, now, in_scope)
    ok2, reason = iv.accept(s4, now, in_scope)  # rejeu
    if not ok1 or ok2 or reason != "rejeu":
        failures.append(f"4. anti-rejeu défaillant (ok1={ok1}, ok2={ok2}, raison={reason})")

    # 5. Fraîcheur sur t_eval explicite, déterministe
    s5 = base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A5", expires="2026-10-18T12:00:30Z")
    t_in = t("2026-10-18T12:00:15Z")
    t_out = t("2026-10-18T12:00:45Z")
    if not signal_fresh(s5, t_in, TTL):
        failures.append("5a. signal frais jugé non frais")
    if signal_fresh(s5, t_out, TTL):
        failures.append("5b. signal expiré jugé frais")
    # déterminisme : même t_eval → même résultat, indépendamment de l'heure réelle
    if signal_fresh(s5, t_in, TTL) != signal_fresh(s5, t_in, TTL):
        failures.append("5c. fraîcheur non déterministe")

    # 6. correlation_id hors périmètre → rejet
    s6 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A6", cid="run_xyz"), priv)
    ok, reason = iv.accept(s6, now, in_scope)
    if ok or reason != "correlation_hors_perimetre":
        failures.append(f"6. correlation hors périmètre acceptée (raison={reason})")

    # 7. Signal critique expiré → EXPIRED_CRITICAL + défaut fail-closed (HOLD)
    s7 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A7",
                                 issued="2026-10-18T11:59:00Z",
                                 expires="2026-10-18T11:59:30Z"), priv)
    state, verdict = critical_signal_state([s7], "hypothesis.weakened", t_out, TTL, {})
    if state != "EXPIRED_CRITICAL" or verdict != "HOLD":
        failures.append(f"7. critique expiré → {state}/{verdict}, attendu EXPIRED_CRITICAL/HOLD")

    # 8. Absence de signal ≠ favorable (défaut HOLD)
    state, verdict = critical_signal_state([], "hypothesis.weakened", t_in, TTL, {})
    if verdict == "PASS":
        failures.append(f"8. absence de signal jugée PASS (attendu ≠ favorable)")

    # 9. Signal favorable valide → VALID_FAVORABLE
    s9 = sign_signal(base_signal("01JAX7K3P0Y8Q2M5N6R7T9V0A9",
                                 sig_type="hypothesis.verified", severity="info"), priv)
    state, verdict = critical_signal_state([s9], "hypothesis.verified", t_in, TTL, {})
    if state != "VALID_FAVORABLE":
        failures.append(f"9. signal favorable valide → {state}, attendu VALID_FAVORABLE")

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("OK assurance_signals : 9 scénarios adversariaux passent "
          "(anti-injection, anti-rejeu, fraîcheur déterministe, critique expiré fail-closed).")


if __name__ == "__main__":
    main()
