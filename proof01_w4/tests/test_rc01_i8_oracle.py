"""Preparation tests for an independent projection oracle, not W2 execution."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from proof01_w4.rc01_i8_oracle import PROFILE, replay_projection, compare_projection


class ProjectionOracleTests(unittest.TestCase):
    def projection(self):
        return {"profile": PROFILE, "operation_id": "fixture-op", "resource_id": "fixture-resource",
                "amount_minor": 100, "baseline": {"capacity": 1000, "reserved": 0, "committed": 0},
                "initial_view": "INIT", "initial_settlement": "NONE", "records": []}

    def add(self, p, kind, **fields):
        row = {"sequence": len(p["records"]) + 1, "kind": kind, "operation_id": p["operation_id"]}
        if kind in ("I8", "PROVIDER"):
            row.update(resource_id=p["resource_id"], amount_minor=p["amount_minor"])
        row.update(fields); p["records"].append(row)
        return row

    def pending(self):
        p = self.projection()
        self.add(p, "I8", action="RESERVE_APPLIED")
        self.add(p, "STATE", **{"from": "INIT", "to": "RESERVED"})
        self.add(p, "STATE", **{"from": "RESERVED", "to": "DISPATCHING"})
        self.add(p, "STATE", **{"from": "DISPATCHING", "to": "UNKNOWN"})
        return p

    def fact(self, p, status="EXECUTED"):
        return self.add(p, "PROVIDER", effect_status=status, receipt_sha256="a" * 64,
                        finality="PROVIDER_LEDGER_TERMINAL")

    def repaired(self):
        p = self.pending(); self.fact(p)
        self.add(p, "I8", action="SETTLE_FAILED")
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "REPAIR"})
        self.add(p, "I8", action="COMMIT_APPLIED")
        self.add(p, "STATE", **{"from": "REPAIR", "to": "RECONCILED_CONFIRMED"})
        return p

    def report_fixture(self):
        # A manually specified expected report, not an executed second verifier.
        return {"outcome": "VERIFIED", "assurance_scope": PROFILE,
                "final_view": "RECONCILED_CONFIRMED", "settlement": "COMMITTED",
                "observed_provider_outcome": "EXECUTED", "review_required": False, "terminal": True,
                "balances": {"capacity": 1000, "reserved": 0, "committed": 100,
                             "released_minor": 0, "available": 900},
                "counters": {"reserve_applied": 1, "commit_applied": 1, "release_applied": 0,
                             "failed_settlement_observed": 1, "replays": 0}}

    def test_repair_projection_conserves_budget_and_stays_scoped(self):
        r = replay_projection(self.repaired())
        self.assertEqual(r["outcome"], "VERIFIED")
        self.assertEqual(r["balances"], self.report_fixture()["balances"])
        self.assertEqual(r["counters"]["commit_applied"], 1)
        self.assertEqual(r["capture_completeness"], "NOT_ESTABLISHED")
        self.assertEqual(r["integration_lock"], "HOLD")

    def test_unknown_retains_capacity_without_inventing_failure(self):
        r = replay_projection(self.pending())
        self.assertEqual(r["outcome"], "VERIFIED")
        self.assertEqual(r["final_view"], "UNKNOWN")
        self.assertEqual(r["balances"]["reserved"], 100)
        self.assertFalse(r["terminal"])

    def test_repair_can_follow_local_commit_while_anchor_unverified(self):
        p = self.pending(); self.fact(p)
        self.add(p, "I8", action="COMMIT_APPLIED")
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "REPAIR"})
        r = replay_projection(p)
        self.assertEqual(r["outcome"], "VERIFIED")
        self.assertEqual(r["settlement"], "COMMITTED")
        self.assertEqual(r["grant_and_witness"], "NOT_EVALUATED")

    def test_review_required_is_nonterminal_and_does_not_release_budget(self):
        p = self.pending()
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "REVIEW_REQUIRED"})
        r = replay_projection(p)
        self.assertTrue(r["review_required"])
        self.assertFalse(r["terminal"])
        self.assertEqual(r["balances"]["reserved"], 100)
        self.add(p, "STATE", **{"from": "REVIEW_REQUIRED", "to": "UNKNOWN"})
        self.assertFalse(replay_projection(p)["review_required"])

    def test_terminal_before_local_settlement_is_refuted(self):
        p = self.pending(); self.fact(p)
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "RECONCILED_CONFIRMED"})
        self.assertEqual(replay_projection(p)["code"], "POSITIVE_TERMINAL_WITHOUT_MATCHING_SETTLEMENT")

    def test_double_applied_settlement_is_refuted(self):
        p = self.repaired(); self.add(p, "I8", action="COMMIT_APPLIED")
        self.assertEqual(replay_projection(p)["code"], "DOUBLE_SETTLEMENT")

    def test_idempotent_observation_is_not_another_applied_settlement(self):
        p = self.repaired()
        for _ in range(3):
            self.add(p, "I8", action="COMMIT_REPLAY")
        r = replay_projection(p)
        self.assertEqual(r["outcome"], "VERIFIED")
        self.assertEqual(r["counters"]["commit_applied"], 1)
        self.assertEqual(r["counters"]["replays"], 3)
        self.assertEqual(r["balances"]["committed"], 100)

    def test_release_from_unresolved_repair_is_refuted(self):
        p = self.pending(); self.fact(p)
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "REPAIR"})
        self.add(p, "I8", action="RELEASE_APPLIED")
        self.assertEqual(replay_projection(p)["code"], "RELEASE_WITHOUT_NEGATIVE_FINAL")

    def test_negative_final_can_release_once(self):
        p = self.pending(); self.fact(p, "NOT_EXECUTED_FINAL")
        self.add(p, "I8", action="RELEASE_APPLIED")
        self.add(p, "STATE", **{"from": "UNKNOWN", "to": "RECONCILED_NOT_EXECUTED"})
        r = replay_projection(p)
        self.assertEqual(r["outcome"], "VERIFIED")
        self.assertEqual(r["balances"]["released_minor"], 100)
        self.assertEqual(r["balances"]["available"], 1000)

    def test_absent_provider_response_never_qualifies_negative_final(self):
        p = self.pending()
        self.add(p, "PROVIDER", effect_status="UNKNOWN")
        self.add(p, "I8", action="RELEASE_APPLIED")
        self.assertEqual(replay_projection(p)["code"], "RELEASE_WITHOUT_NEGATIVE_FINAL")

    def test_negative_finality_and_receipt_reference_must_be_explicit(self):
        p = self.pending(); row = self.fact(p, "NOT_EXECUTED_FINAL")
        row["finality"] = "NOT_FOUND"
        self.assertEqual(replay_projection(p)["outcome"], "INDETERMINATE")
        row["finality"] = "PROVIDER_LEDGER_TERMINAL"; row.pop("receipt_sha256")
        self.assertEqual(replay_projection(p)["outcome"], "INDETERMINATE")

    def test_conflicting_provider_final_assertions_are_refuted(self):
        p = self.pending(); self.fact(p); self.fact(p, "NOT_EXECUTED_FINAL")
        self.assertEqual(replay_projection(p)["code"], "PROVIDER_OUTCOME_CONTRADICTION")

    def test_capacity_and_baseline_are_not_projected_away(self):
        p = self.pending(); p["baseline"]["capacity"] = 99
        self.assertEqual(replay_projection(p)["code"], "I8_CAPACITY_OR_CONSERVATION_VIOLATION")

    def test_missing_i8_amount_or_operation_is_not_inferred(self):
        for field in ("amount_minor", "operation_id"):
            with self.subTest(field=field):
                p = self.repaired(); p["records"][5].pop(field)
                self.assertEqual(replay_projection(p)["outcome"], "INDETERMINATE")

    def test_wrong_operation_amount_and_boolean_fields_are_refuted(self):
        for field, value in (("operation_id", "other-op"), ("amount_minor", True),
                             ("resource_id", "other-resource")):
            with self.subTest(field=field):
                p = self.pending(); p["records"][0][field] = value
                self.assertEqual(replay_projection(p)["outcome"], "REFUTED")

    def test_sequence_gaps_are_missing_evidence_not_runtime_failure(self):
        p = self.repaired(); p["records"][4]["sequence"] = 10
        self.assertEqual(replay_projection(p)["code"], "SEQUENCE_INCOMPLETE_OR_UNORDERED")
        self.assertEqual(replay_projection(p)["outcome"], "INDETERMINATE")

    def test_duplicate_sequence_is_refuted(self):
        p = self.pending(); p["records"][1]["sequence"] = 1
        self.assertEqual(replay_projection(p)["code"], "SEQUENCE_REUSED")

    def test_unknown_record_extensions_are_not_silently_discarded(self):
        for kind, fields in (("STATE", {"from": "INIT", "to": "INIT"}),
                             ("I8", {"action": "RESERVE_APPLIED"}),
                             ("PROVIDER", {"effect_status": "UNKNOWN"})):
            with self.subTest(kind=kind):
                p = self.projection()
                self.add(p, kind, **fields, unreviewed_semantics=True)
                self.assertEqual(replay_projection(p)["code"], "OBSERVATION_EXTENSION_UNSUPPORTED")

    def test_malformed_record_types_produce_explicit_verdicts(self):
        mutations = (("kind", []), ("action", {}), ("sequence", True))
        for field, value in mutations:
            with self.subTest(field=field):
                p = self.pending(); p["records"][0][field] = value
                self.assertIn(replay_projection(p)["outcome"], {"INDETERMINATE", "REFUTED"})
        p = self.pending(); self.add(p, "STATE", **{"from": [], "to": {}})
        self.assertEqual(replay_projection(p)["code"], "STATE_FIELDS_INVALID")
        p = self.pending(); self.fact(p)["effect_status"] = []
        self.assertEqual(replay_projection(p)["code"], "PROVIDER_OUTCOME_UNSUPPORTED")

    def test_native_summary_and_unknown_initial_boundary_are_not_replayed(self):
        self.assertEqual(replay_projection({"final_state": "RECONCILED_CONFIRMED",
                                            "settlement_count": 1})["outcome"], "INDETERMINATE")
        p = self.pending(); p["initial_settlement"] = "ASSUMED"
        self.assertEqual(replay_projection(p)["outcome"], "INDETERMINATE")

    def test_wrong_predecessor_cannot_be_hidden_by_correct_terminal_label(self):
        p = self.repaired(); p["records"][-1]["from"] = "DISPATCHING"
        self.assertEqual(replay_projection(p)["code"], "STATE_PREDECESSOR_MISMATCH")

    def test_differential_report_fixture_matches_and_detects_changed_capacity(self):
        p, report = self.repaired(), self.report_fixture()
        self.assertEqual(compare_projection(report, p)["code"], "PROJECTED_DIFFERENTIAL_AGREEMENT")
        report["balances"]["capacity"] += 1
        self.assertEqual(compare_projection(report, p)["code"], "DIFFERENTIAL_PROJECTION_MISMATCH")

    def test_missing_verifier_projection_is_not_differential_agreement(self):
        self.assertEqual(compare_projection({"outcome": "INDETERMINATE"}, self.repaired())["outcome"],
                         "INDETERMINATE")

    def test_boolean_counters_cannot_equal_integer_counts(self):
        report = self.report_fixture(); report["counters"]["commit_applied"] = True
        self.assertEqual(compare_projection(report, self.repaired())["code"],
                         "DIFFERENTIAL_PROJECTION_MISMATCH")

    def test_cli_rejects_duplicate_json_and_keeps_partial_scope_explicit(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / "projection.json"
            path.write_text(json.dumps(self.repaired()))
            command = [sys.executable, "-B", "-m", "proof01_w4.rc01_i8_oracle", str(path)]
            run = subprocess.run(command, capture_output=True)
            self.assertEqual(run.returncode, 0)
            self.assertEqual(json.loads(run.stdout)["integration_lock"], "HOLD")
            path.write_bytes(b'{"profile":"old","profile":"new"}')
            run = subprocess.run(command, capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["code"], "PROJECTION_INPUT_INVALID")


if __name__ == "__main__":
    unittest.main()
