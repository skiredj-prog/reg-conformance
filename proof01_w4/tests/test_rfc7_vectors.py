"""RFC-7 candidate adversarial vector harness (W4.3).

Fixture keys are GENERATED ONLY IN MEMORY; no private keys committed.
No production claim or independent institutional witness.
"""
import json
import unittest
from pathlib import Path

from proof01_w4.oracle import reconstruct, compare_report, OracleReject
from proof01_w4.semantic import check, auth, trusted
import test_semantic


class RFC7CandidateVectors(unittest.TestCase):
    def setUp(self):
        self.fx = test_semantic.TestW42("test_bounded_verified")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)

    def authenticated(self):
        store = trusted(self.fx.trust)
        result = []
        for envelope in self.fx.events:
            kind = envelope["kind"]
            role = "provider" if kind == "PROVIDER_EXECUTED" else "runtime"
            result.append(auth(envelope, store, role))
        return result

    def test_rfc7_positive_trace_internal_only(self):
        report = check(self.fx.root, self.fx.trust)
        self.assertEqual(compare_report(report, self.authenticated())["outcome"], "VERIFIED")

    def test_rfc7_differential_mismatch_detected(self):
        report = check(self.fx.root, self.fx.trust)
        report["balances"]["r1"]["committed"] = 0
        self.assertEqual(compare_report(report, self.authenticated())["reason"],
                         "DIFFERENTIAL_MISMATCH_BALANCES")

    def test_rfc7_capacity_mismatch_is_not_hidden_by_balance_projection(self):
        for mutation in ("changed", "missing"):
            with self.subTest(mutation=mutation):
                report = check(self.fx.root, self.fx.trust)
                if mutation == "changed":
                    report["balances"]["r1"]["capacity"] += 1
                else:
                    report["balances"]["r1"].pop("capacity")
                self.assertEqual(compare_report(report, self.authenticated())["reason"],
                                 "DIFFERENTIAL_MISMATCH_BALANCES")

    def test_rfc7_final_state_mismatch_still_refuted(self):
        report = check(self.fx.root, self.fx.trust)
        report["final_states"]["a1"] = "REPAIR"
        self.assertEqual(compare_report(report, self.authenticated())["reason"],
                         "DIFFERENTIAL_MISMATCH_FINAL_STATES")

    def test_rfc7_event_count_mismatch_still_refuted(self):
        report = check(self.fx.root, self.fx.trust)
        report["events"] -= 1
        self.assertEqual(compare_report(report, self.authenticated())["reason"],
                         "DIFFERENTIAL_MISMATCH_EVENTS")

    def test_rfc7_rollback_witness_checkpoint(self):
        # Earlier checkpoint signed by same witness, but no longer matches event tip.
        old = json.loads((self.fx.root / "checkpoint.json").read_text())
        self.fx.make(amount=3)
        # Replacing old checkpoint invalidates manifest digest, which is fail-closed.
        (self.fx.root / "checkpoint.json").write_text(json.dumps(old))
        self.assertNotEqual(check(self.fx.root, self.fx.trust)["outcome"], "VERIFIED")

    def test_rfc7_unobserved_second_effect_is_indeterminate(self):
        # No signed external source guarantees completeness of provider side effects.
        report = check(self.fx.root, self.fx.trust, "no-unobserved-effects")
        self.assertEqual(report["outcome"], "INDETERMINATE")

    def test_rfc7_two_reservations_exceed_capacity(self):
        events = [
            {"seq": 1, "attempt_id": "a", "resource_id": "r", "amount": 3, "capacity": 5, "kind": "RESERVED"},
            {"seq": 2, "attempt_id": "b", "resource_id": "r", "amount": 3, "capacity": 5, "kind": "RESERVED"},
        ]
        with self.assertRaises(OracleReject) as ctx:
            reconstruct(events)
        self.assertEqual(ctx.exception.code, "I8")

    def test_rfc7_duplicate_provider_receipt(self):
        events = [
            {"seq": 1, "attempt_id": "a", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "RESERVED"},
            {"seq": 2, "attempt_id": "a", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "DISPATCHING"},
            {"seq": 3, "attempt_id": "a", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "PROVIDER_EXECUTED", "effect_id": "same"},
            {"seq": 4, "attempt_id": "b", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "RESERVED"},
            {"seq": 5, "attempt_id": "b", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "DISPATCHING"},
            {"seq": 6, "attempt_id": "b", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "PROVIDER_EXECUTED", "effect_id": "same"},
        ]
        with self.assertRaises(OracleReject) as ctx:
            reconstruct(events)
        self.assertEqual(ctx.exception.code, "DUPLICATE_RECEIPT")

    def test_rfc7_release_not_implicitly_accepted(self):
        events = [{"seq": 1, "attempt_id": "a", "resource_id": "r", "amount": 1, "capacity": 5, "kind": "RELEASED"}]
        with self.assertRaises(OracleReject) as ctx:
            reconstruct(events)
        self.assertEqual(ctx.exception.code, "FIELDS")

    def test_rfc7_unsigned_claim_not_a_proof(self):
        report = {"outcome": "VERIFIED", "code": "SIGNED_TRACE_VALID",
                  "final_states": {}, "balances": {}, "events": 0}
        self.assertEqual(compare_report(report, self.authenticated())["outcome"], "REFUTED")


if __name__ == "__main__":
    unittest.main()
