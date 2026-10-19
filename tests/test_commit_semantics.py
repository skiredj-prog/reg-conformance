#!/usr/bin/env python3
"""
test_commit_semantics.py — Tests adversariaux de la sémantique de commit.

Vérifie la distinction evaluation_verdict (pur) vs effective_outcome (opérationnel)
et la stricte conditionnalité de commit_trace :
  1. PASS + FAILED_RACE → COMMIT_FAILED (jamais EXECUTED) — scénario clé
  2. HARD_VETO → SKIPPED + VETOED ; HOLD → HELD
  3. COMMITTED exige pre+post hash ; FAILED_* exige post_failure_state + commit_error
  4. SKIPPED impose commit_attempted=false
  5. Incohérence commit_result ↔ effective_outcome rejetée par le schéma
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _ref_impl import commit_outcome

from jsonschema import Draft202012Validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(BASE_DIR, "specs", "evidence-contract-v1.json")) as f:
    SCHEMA = json.load(f)
VALIDATOR = Draft202012Validator(SCHEMA)


def base(verdict="PASS", commit_attempted=True, commit_result="COMMITTED", outcome="EXECUTED"):
    rec = {
        "reg_schema_version": "1.0.0",
        "artifact_type": "reg.evidence-record/v1",
        "record_id": "01JAX7K3P0Y8Q2M5N6R7T9V0WX",
        "timestamp": "2026-10-18T12:00:01Z",
        "chain": {"previous_hash": None},
        "evaluation_context": {
            "catalog_version": "v2.3.1", "profile_id": "agg", "profile_version": "1.4.0",
            "evaluator_version": "ev-0.9.2", "evaluation_time": "2026-10-18T12:00:00Z",
        },
        "inputs": {"state_snapshot": {}, "transition_proposal": {}},
        "results": {"evaluation_verdict": verdict,
                    "invariant_details": [{"invariant_id": "i1", "result": "PASS"}]},
        "commit_trace": {"commit_attempted": commit_attempted, "commit_result": commit_result},
        "effective_outcome": outcome,
        "integrity": {"current_hash": "sha256:" + "1" * 64, "signature": "b" * 128,
                      "producer_key_id": "k1"},
    }
    if commit_result == "COMMITTED":
        rec["commit_trace"]["pre_commit_state_hash"] = "sha256:" + "3" * 64
        rec["commit_trace"]["post_commit_state_hash"] = "sha256:" + "4" * 64
    if commit_result in ("FAILED_RACE", "FAILED_CONSTRAINT", "ERROR"):
        rec["commit_trace"]["pre_commit_state_hash"] = "sha256:" + "3" * 64
        rec["commit_trace"]["commit_error"] = "détail"
        rec["commit_trace"]["post_failure_state"] = "ROLLED_BACK_ATOMIC"
    return rec


def schema_valid(rec):
    return len(list(VALIDATOR.iter_errors(rec))) == 0


def main():
    failures = []

    # 1. Machine à états : PASS + FAILED_RACE → COMMIT_FAILED
    if commit_outcome("PASS", True, "FAILED_RACE") != "COMMIT_FAILED":
        failures.append("1. PASS+FAILED_RACE ne donne pas COMMIT_FAILED")
    # et jamais EXECUTED
    if commit_outcome("PASS", True, "FAILED_RACE") == "EXECUTED":
        failures.append("1b. PASS+FAILED_RACE donne EXECUTED (fatal)")
    # PASS + COMMITTED → EXECUTED
    if commit_outcome("PASS", True, "COMMITTED") != "EXECUTED":
        failures.append("1c. PASS+COMMITTED ne donne pas EXECUTED")

    # 2. HARD_VETO → VETOED ; HOLD sans commit → HELD
    if commit_outcome("HARD_VETO", False, "SKIPPED") != "VETOED":
        failures.append("2a. HARD_VETO ne donne pas VETOED")
    if commit_outcome("HOLD", False, "SKIPPED") != "HELD":
        failures.append("2b. HOLD sans commit ne donne pas HELD")

    # 3. Schéma : COMMITTED sans post_commit_state_hash → invalide
    bad3 = base()
    del bad3["commit_trace"]["post_commit_state_hash"]
    if schema_valid(bad3):
        failures.append("3. COMMITTED sans post hash accepté")

    # 4. Schéma : FAILED_RACE sans post_failure_state → invalide
    bad4 = base(commit_result="FAILED_RACE", outcome="COMMIT_FAILED")
    del bad4["commit_trace"]["post_failure_state"]
    if schema_valid(bad4):
        failures.append("4. FAILED_RACE sans post_failure_state accepté")

    # 5. Schéma : FAILED_RACE sans commit_error → invalide
    bad5 = base(commit_result="FAILED_RACE", outcome="COMMIT_FAILED")
    del bad5["commit_trace"]["commit_error"]
    if schema_valid(bad5):
        failures.append("5. FAILED_RACE sans commit_error accepté")

    # 6. Schéma : SKIPPED avec commit_attempted=true → invalide
    bad6 = base(verdict="HARD_VETO", commit_attempted=True, commit_result="SKIPPED", outcome="VETOED")
    if schema_valid(bad6):
        failures.append("6. SKIPPED avec commit_attempted=true accepté")

    # 7. Schéma : FAILED_RACE + effective_outcome=EXECUTED (incohérent) → invalide
    bad7 = base(commit_result="FAILED_RACE", outcome="EXECUTED")
    if schema_valid(bad7):
        failures.append("7. FAILED_RACE + EXECUTED (incohérent) accepté")

    # 8. Schéma : HARD_VETO + commit tenté (commit_result=COMMITTED) → incohérent → invalide
    bad8 = base(verdict="HARD_VETO", commit_attempted=True, commit_result="COMMITTED", outcome="EXECUTED")
    if schema_valid(bad8):
        failures.append("8. HARD_VETO + COMMITTED accepté (incohérent)")

    # 9. Cas valides passent
    if not schema_valid(base()):
        failures.append("9a. cas PASS+COMMITTED valide rejeté")
    if not schema_valid(base(verdict="HARD_VETO", commit_attempted=False, commit_result="SKIPPED", outcome="VETOED")):
        failures.append("9b. cas HARD_VETO+SKIPPED valide rejeté")
    if not schema_valid(base(commit_result="FAILED_RACE", outcome="COMMIT_FAILED")):
        failures.append("9c. cas FAILED_RACE+COMMIT_FAILED valide rejeté")

    if failures:
        print("ÉCHECS :")
        for f_ in failures:
            print("  -", f_)
        sys.exit(1)
    print("OK commit_semantics : 9 scénarios passent "
          "(PASS+FAILED_RACE≠EXECUTED, HARD_VETO→VETOED, post_failure_state obligatoire, incohérences rejetées).")


if __name__ == "__main__":
    main()
