#!/usr/bin/env python3
"""
test_evidence_integrity.py — Tests adversariaux du contrat EvidenceRecord.

Vérifie :
  1. current_hash couvre BIEN chain.previous_hash (faille corrigée)
  2. Toute altération de contenu casse la vérification ; mauvaise clé casse l'authenticité
  3. Continuité de la hash-chain ; genèse à previous_hash=null
  4. Schéma rejette les champs interdits (chain_id, sequence, airep_version)
     et l'ancien placement de previous_hash dans integrity
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ref_impl import sign_record, verify_record, verify_chain, compute_current_hash

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(BASE_DIR, "specs", "evidence-contract-v1.json")) as f:
    SCHEMA = json.load(f)
VALIDATOR = Draft202012Validator(SCHEMA)


def base_record(prev_hash=None, verdict="PASS", commit_result="COMMITTED"):
    rec = {
        "reg_schema_version": "1.0.0",
        "artifact_type": "reg.evidence-record/v1",
        "record_id": "01JAX7K3P0Y8Q2M5N6R7T9V0WX",
        "timestamp": "2026-10-18T12:00:01Z",
        "chain": {"previous_hash": prev_hash},
        "evaluation_context": {
            "catalog_version": "v2.3.1", "profile_id": "agg", "profile_version": "1.4.0",
            "evaluator_version": "ev-0.9.2", "evaluation_time": "2026-10-18T12:00:00Z",
            "signal_ttl_resolution": {"hypothesis.weakened": 30},
        },
        "inputs": {"state_snapshot": {"budget": 5000}, "transition_proposal": {"amount": 1200}},
        "results": {
            "evaluation_verdict": verdict,
            "invariant_details": [{"invariant_id": "commit-binding", "result": "PASS"}],
        },
        "commit_trace": {
            "commit_attempted": commit_result == "COMMITTED",
            "commit_result": commit_result,
        },
        "effective_outcome": "EXECUTED" if commit_result == "COMMITTED" else "VETOED",
    }
    if commit_result == "COMMITTED":
        rec["commit_trace"]["pre_commit_state_hash"] = "sha256:" + "3" * 64
        rec["commit_trace"]["post_commit_state_hash"] = "sha256:" + "4" * 64
    if commit_result == "SKIPPED":
        rec["effective_outcome"] = "VETOED" if verdict == "HARD_VETO" else "HELD"
    return rec


def schema_valid(rec):
    return len(list(VALIDATOR.iter_errors(rec))) == 0


def main():
    failures = []
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    other_pub = Ed25519PrivateKey.generate().public_key()

    # 1. Enregistrement valide se vérifie
    r = sign_record(base_record(prev_hash=None), priv, "k1")
    if not verify_record(r, pub):
        failures.append("1. enregistrement valide non vérifié")
    if not schema_valid(r):
        failures.append("1b. enregistrement valide rejeté par le schéma")

    # 2. ATTAQUE : altérer chain.previous_hash doit casser la vérification
    r2 = json.loads(json.dumps(r))
    r2["chain"]["previous_hash"] = "sha256:" + "f" * 64  # lien de chaîne modifié
    if verify_record(r2, pub):
        failures.append("2. FAILLE : previous_hash modifié passe la vérification")
    # et le hash recalculé doit différer
    if compute_current_hash(r2) == r["integrity"]["current_hash"]:
        failures.append("2b. FAILLE : previous_hash ne change pas current_hash")

    # 3. Altérer le verdict casse la vérification
    r3 = json.loads(json.dumps(r))
    r3["results"]["evaluation_verdict"] = "HARD_VETO"
    if verify_record(r3, pub):
        failures.append("3. verdict altéré passe la vérification")

    # 4. Mauvaise clé publique → authenticité rejetée
    if verify_record(r, other_pub):
        failures.append("4. mauvaise clé publique accepte la signature")

    # 5. Signature altérée → rejetée
    r5 = json.loads(json.dumps(r))
    r5["integrity"]["signature"] = "0" * 128
    if verify_record(r5, pub):
        failures.append("5. signature altérée acceptée")

    # 6. Hash-chain continue sur 3 enregistrements
    chain = []
    prev = None
    for i in range(3):
        rec = base_record(prev_hash=prev)
        rec["record_id"] = f"01JAX7K3P0Y8Q2M5N6R7T9V0W{i}"
        rec = sign_record(rec, priv, "k1")
        chain.append(rec)
        prev = rec["integrity"]["current_hash"]
    if not verify_chain(chain):
        failures.append("6. chaîne continue rejetée")
    # casser le lien du record du milieu
    broken = json.loads(json.dumps(chain))
    broken[2]["chain"]["previous_hash"] = "sha256:" + "a" * 64
    if verify_chain(broken):
        failures.append("6b. lien cassé accepté")

    # 7. Genèse : previous_hash=null OK ; non-genèse à null échoue
    if chain[0]["chain"]["previous_hash"] is not None:
        failures.append("7. genèse n'a pas previous_hash=null")
    bad_genesis = json.loads(json.dumps(chain))
    bad_genesis[1]["chain"]["previous_hash"] = None
    if verify_chain(bad_genesis):
        failures.append("7b. record non-genèse à previous_hash=null accepté")

    # 8. Schéma rejette les champs interdits (dépendance AIREP / blockchain)
    for forbidden in ("chain_id", "sequence", "airep_version"):
        bad = json.loads(json.dumps(r))
        bad[forbidden] = "x"
        if schema_valid(bad):
            failures.append(f"8. champ interdit {forbidden} accepté par le schéma")

    # 9. Schéma rejette l'ancien placement de previous_hash DANS integrity
    bad9 = json.loads(json.dumps(r))
    bad9["integrity"]["previous_hash"] = "sha256:" + "1" * 64
    if schema_valid(bad9):
        failures.append("9. previous_hash dans integrity (faille) accepté par le schéma")

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("OK evidence_integrity : 9 scénarios adversariaux passent "
          "(previous_hash couvert, altérations rejetées, chaîne continue, champs interdits rejetés).")


if __name__ == "__main__":
    main()
