"""Local assertion suite for the RFC-3 §6 reference simulator.

Run from the repository root with:
    python -m unittest composition.tests -v
"""
import contextlib
import io
import unittest

from composition.simulator import CompositionEngine, ConflictType, Strategy, TAU


def tau_pair(p1=1, n1=60.0, l1=106.0, p2=2, n2=50.0, l2=107.0):
    return (
        TAU("hedge-alpha-01", p1, n1, l1),
        TAU("hedge-beta-01", p2, n2, l2),
    )


class CompositionSimulatorTests(unittest.TestCase):
    def setUp(self):
        self.engine = CompositionEngine(
            composition_id="liquidity-control-group",
            lcr_group_threshold=110.0,
            shared_notional_limit=100.0,
            tau_k_seconds=1200.0,
            max_hold_minutes=30.0,
        )

    def evaluate(self, *args, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return self.engine.evaluate_scenario(*args, **kwargs)

    def test_c1_default_priority_enforce(self):
        self.assertEqual(
            self.evaluate(list(tau_pair()), ConflictType.C1_VERTICAL, 300.0)["decision"],
            "PARTIAL_PASS",
        )

    def test_c2_default_serialize(self):
        self.assertEqual(
            self.evaluate(list(tau_pair()), ConflictType.C2_HORIZONTAL, 150.0)["decision"],
            "SERIALIZED",
        )

    def test_c3_default_escalate(self):
        self.assertEqual(
            self.evaluate(list(tau_pair()), ConflictType.C3_TEMPOREL, 200.0)["decision"],
            "ESCALATED_HOLD",
        )

    def test_c4_fail_closed_collectif(self):
        taus = list(tau_pair())
        result = self.evaluate(taus, ConflictType.C4_NO_PRIORITY, 400.0)
        self.assertEqual(result["decision"], "FAIL_CLOSED_COLLECTIF")
        self.assertTrue(all(tau.status == "FAIL_CLOSED" for tau in taus))

    def test_tau_k_expiry_has_absolute_precedence(self):
        result = self.evaluate(list(tau_pair()), ConflictType.C1_VERTICAL, 1300.0)
        self.assertEqual(result["decision"], "FAIL_CLOSED_COLLECTIF")
        self.assertEqual(result["reason"], "Expiration de τ_K de composition")

    def test_equal_priority_fails_closed(self):
        result = self.evaluate(
            list(tau_pair(p1=1, p2=1)), ConflictType.C2_HORIZONTAL, 100.0
        )
        self.assertEqual(result["decision"], "FAIL_CLOSED_COLLECTIF")
        self.assertIn("Égalité de priorités", result["reason"])

    def test_no_measured_c1_violation_is_nominal(self):
        result = self.evaluate(
            list(tau_pair(l1=112.0, l2=111.0)),
            ConflictType.C1_VERTICAL,
            100.0,
        )
        self.assertEqual(result["decision"], "NOMINAL_PASS")

    def test_pareto_restore_holds_lower_priority_tau(self):
        taus = [
            TAU("hedge-alpha-01", 1, 60.0, 113.0),
            TAU("hedge-beta-01", 2, 50.0, 105.0),
        ]
        result = self.evaluate(
            taus, ConflictType.C1_VERTICAL, 300.0,
            custom_strategy=Strategy.PARETO_RESTORE,
        )
        self.assertEqual(result["decision"], "PARETO_RESTORED")
        self.assertEqual(result["passed"], ["hedge-alpha-01"])
        self.assertEqual(result["held"], ["hedge-beta-01"])
        self.assertEqual(result["restored_lcr_pct"], 113.0)

    def test_invalid_strategy_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.evaluate(
                list(tau_pair()),
                ConflictType.C3_TEMPOREL,
                100.0,
                custom_strategy=Strategy.FAIL_CLOSED_COLLECTIF,
            )

    def test_empty_composition_rejected(self):
        with self.assertRaises(ValueError):
            self.evaluate([], ConflictType.NONE, 0.0)


    def test_tau_k_exact_boundary_fails_closed(self):
        taus = list(tau_pair())
        result = self.evaluate(taus, ConflictType.NONE, 1200.0)
        self.assertEqual(result["decision"], "FAIL_CLOSED_COLLECTIF")
        self.assertTrue(all(tau.status == "FAIL_CLOSED" for tau in taus))

    def test_c1_exact_threshold_is_nominal(self):
        result = self.evaluate(
            list(tau_pair(l1=110.0, l2=110.0)),
            ConflictType.C1_VERTICAL,
            100.0,
        )
        self.assertEqual(result["decision"], "NOMINAL_PASS")

    def test_c2_exact_shared_limit_is_nominal(self):
        result = self.evaluate(
            list(tau_pair(n1=60.0, n2=40.0)),
            ConflictType.C2_HORIZONTAL,
            100.0,
        )
        self.assertEqual(result["decision"], "NOMINAL_PASS")

    def test_serialize_is_independent_of_input_order(self):
        first = list(tau_pair())
        second = list(reversed(tau_pair()))
        result_first = self.evaluate(first, ConflictType.C2_HORIZONTAL, 100.0)
        result_second = self.evaluate(second, ConflictType.C2_HORIZONTAL, 100.0)
        self.assertEqual(result_first["decision"], "SERIALIZED")
        self.assertEqual(result_second["decision"], "SERIALIZED")
        self.assertEqual(
            {tau.agent_id: tau.status for tau in first},
            {tau.agent_id: tau.status for tau in second},
        )
        self.assertEqual(
            {tau.agent_id: tau.status for tau in first},
            {"hedge-alpha-01": "PASS", "hedge-beta-01": "HOLD"},
        )

    def test_pareto_restore_escalates_when_no_subset_can_meet_threshold(self):
        taus = [
            TAU("hedge-alpha-01", 1, 60.0, 90.0),
            TAU("hedge-beta-01", 2, 50.0, 95.0),
        ]
        result = self.evaluate(
            taus,
            ConflictType.C1_VERTICAL,
            300.0,
            custom_strategy=Strategy.PARETO_RESTORE,
        )
        self.assertEqual(result["decision"], "ESCALATED_HOLD")
        self.assertTrue(all(tau.status == "HOLD" for tau in taus))

    def test_status_is_reset_between_scenario_evaluations(self):
        taus = list(tau_pair())
        self.evaluate(taus, ConflictType.C2_HORIZONTAL, 100.0)
        self.assertEqual(
            [tau.status for tau in taus],
            ["PASS", "HOLD"],
        )
        result = self.evaluate(taus, ConflictType.NONE, 100.0)
        self.assertEqual(result["decision"], "NOMINAL_PASS")
        self.assertTrue(all(tau.status == "PASS" for tau in taus))

    def test_strategy_not_applicable_to_c1_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.evaluate(
                list(tau_pair()),
                ConflictType.C1_VERTICAL,
                100.0,
                custom_strategy=Strategy.ESCALATE,
            )


if __name__ == "__main__":
    unittest.main()
