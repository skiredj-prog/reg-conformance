"""TENIR-Gov 5.7.6 port: what it adds over the v0.7.0 port, and what it gives on 5.7.6.

Runs only against an installed tenir-governance 5.7.6 (the distributed wheel,
pinned by hash in `pins/tenir-governance-5.7.6.txt`). The expectations below are
the ones observed on that distribution in the qualification run of 22 November
2026; they describe this subject, not a conformance claim, and a change in any of
them is a change of the subject or of the instrument that has to be looked at.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from harness import port as P
from harness.adapter import PortAdapter


def _installed_version():
    try:
        import tenir_governance
    except ImportError:
        return None
    return tenir_governance.__version__


needs_576 = pytest.mark.skipif(_installed_version() != "5.7.6",
                               reason="needs tenir-governance 5.7.6 installed from the pinned wheel")


@needs_576
def test_v070_port_admits_nothing_on_576():
    """The caller contract of 5.7.6: with no declared condition, every FLAG is held."""
    from harness.ports.tenir_gov import TenirGovPort
    port = TenirGovPort()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    assert d.disposition == "HOLD"
    assert d.raw["result"]["composed_decision"] == "HOLD"


@needs_576
def test_576_port_declares_one_condition_and_reports_it_on_every_flag():
    from harness.ports.tenir_gov_576 import FLAG_CONDITION, TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    # The native verdict passes through unchanged: a FLAG stays a FLAG.
    assert d.disposition == "FLAG" == d.raw["result"]["composed_decision"]
    # The condition is read from the runtime's result, not added by the port.
    assert tuple(d.raw["result"]["flag_conditions"]) == (FLAG_CONDITION,)
    assert d.conditions == (FLAG_CONDITION,)


@needs_576
def test_576_port_acknowledges_at_dispatch_and_one_effect_follows():
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    committed = port.commit(d, action_type="wire_transfer")
    assert committed.raw.get("dispatched") is True
    assert port.observed_effects(d) == 1


@needs_576
def test_576_port_refusals_keep_the_v070_mapping():
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    with pytest.raises(P.Refused) as e:
        port.commit(d, action_type="other_action")
    assert e.value.code == P.R_BINDING
    assert port.observed_effects(d) == 0
    vetoed = port.evaluate(P.NO_STANDING, principal="a", action_type="wire_transfer")
    assert vetoed.disposition == "HARD_VETO"
    with pytest.raises(P.Refused) as e:
        port.commit(vetoed)
    assert e.value.code == P.R_INVALID_DISPOSITION
    assert port.observed_effects(vetoed) == 0


@needs_576
def test_576_port_on_vectors_probes_and_checks():
    from harness.ports.tenir_gov_576 import TenirGov576Port
    adapter = PortAdapter(TenirGov576Port())
    vectors = {r.vector_id: r.status.value for r in adapter.run_all()}
    assert len(vectors) == 61
    assert "FAIL" not in vectors.values() and "INCONCLUSIVE" not in vectors.values()
    assert vectors["CT-R4-001"] == vectors["CT-R4-002"] == "PASS"
    # Three adapters since the runtime author's decision of 23 November 2026 (11:22):
    # revocation at dispatch, state drift at dispatch, tau_k on a held attempt.
    assert {vectors[v] for v in ("C3", "CT-R4-004b", "CT-R4-005")} == {"PASS"}
    # Primitives the default path does not have: the port declares the gap and the
    # scenario cannot run, so the declaration is what the report carries
    # (IMPLEMENTATION_GAP with the port's note): exit code 2, not a PASS.
    assert {vectors[v] for v in ("CT-R4-004a", "CT-R4-007")} == {"IMPLEMENTATION_GAP"}
    # Eight neutral scenarios of 23 November 2026 on primitives the runtime has:
    # declared scope, pinned thresholds, verification from the ledger (hard facet
    # or S under the thresholds, FLAG-condition rule), UNKNOWN outcome kept open,
    # manifest retrievable and deletion detected, adapter evidence level.
    assert {vectors[v] for v in ("CT-R0-003", "CT-R2-001", "CT-R4-009", "CT-R4-010",
                                 "CT-R5-001", "CT-R5-002", "CT-R5-004", "CT-R7-002")} == {"PASS"}
    assert {vectors[v] for v in ("C4", "CT-R1-003", "CT-R1-005")} == {"NOT_APPLICABLE"}
    # Rule of 23 November 2026 (standard author's option A, 15:07 UTC): the rows no
    # ratified text specifies are listed NOT_SPECIFIED; three credential rows are
    # declared outside the perimeter with CT-R3-007; CT-R3-002 (revocation latency
    # window) is a declared gap, counted; no row is left ADAPTER_REQUIRED.
    from collections import Counter
    tally = Counter(vectors.values())
    assert tally["NOT_SPECIFIED"] == 29
    # Before the checks run, CT-R0-005 (no scenario, exercised by PX-CT-R0-005) is the
    # one row left ADAPTER_REQUIRED; `fold_checks` reports it by its check.
    assert tally["ADAPTER_REQUIRED"] == 1 and vectors["CT-R0-005"] == "ADAPTER_REQUIRED"
    assert {vectors[v] for v in ("CT-R3-001", "CT-R3-006", "CT-R3-007", "CT-R3-008")} == {"NOT_IN_PERIMETER"}
    assert vectors["CT-R3-002"] == "IMPLEMENTATION_GAP"
    # CT-R4-004 is superseded by 004a/004b: its declared gap is no longer counted
    # twice with 004a (internal review of 23 November 2026); three gaps counted.
    assert vectors["CT-R4-004"] == "NOT_SPECIFIED" and vectors["CT-R4-004a"] == "IMPLEMENTATION_GAP"
    assert tally["IMPLEMENTATION_GAP"] == 3 and tally["PASS"] == 21 and tally["NOT_APPLICABLE"] == 3
    probes = {r.vector_id: r.status.value for r in adapter.run_probes()}
    assert set(probes.values()) == {"PASS"}
    results = {r.vector_id: r for r in adapter.run_checks()}
    checks = {k: r.status.value for k, r in results.items()}
    # Declared domain [0, 1] on every measure (REG-STATE-025, RESERVED): a value
    # outside it is held as an invalid measure, never admitted, but not rejected
    # explicitly before a disposition. The check does not conclude on that; the
    # question (HOLD as unknown, or explicit error) is the runtime author's.
    assert checks["PX-REG-STATE-025"] == "INCONCLUSIVE"
    assert "closed by a disposition" in results["PX-REG-STATE-025"].details
    assert "capacity=1.5 (HOLD)" in results["PX-REG-STATE-025"].details
    # Revocation on this runtime acts at dispatch only (mandate re-validation); a new
    # request from the revoked principal is still adjudicated on its measured
    # authority, so the isolation check (RESERVED row) has nothing to isolate.
    assert checks["PX-CT-R3-003"] == "INCONCLUSIVE"
    assert {k for k, v in checks.items() if v == "INCONCLUSIVE"} == {"PX-REG-STATE-025", "PX-CT-R3-003"}
    assert checks["PX-REG-STATE-024"] == "PASS"
    assert checks["PX-CT-R3-002"] == "ADAPTER_REQUIRED"   # no revocation bound declared
    assert "gap declared by the implementer on CT-R3-002" in results["PX-CT-R3-002"].gap_note
    # The credential rows declared outside the perimeter carry their checks with them.
    assert {checks[c] for c in ("PX-CT-R3-001", "PX-CT-R3-006", "PX-CT-R3-007")} == {"NOT_IN_PERIMETER"}
    # Folded: CT-R0-005 is reported by its passing check; nothing stays ADAPTER_REQUIRED.
    folded = {r.vector_id: r.status.value for r in PortAdapter.fold_checks(adapter.run_all(), list(results.values()))}
    assert folded["CT-R0-005"] == "EXERCISED_BY_CHECK" and "ADAPTER_REQUIRED" not in folded.values()
    # Missing evidence: 5.7.6 holds seven missing measurements and admits on the
    # eighth, `irreversibility_materiality`, which it defaults to 0.0. The port
    # declares that measurement since the runtime author's decision C of 23
    # November 2026, so the check reads it: FAIL on 5.7.6, on that one input. It
    # read PASS on the seven while the port left the eighth to the default.
    assert checks["PX-REG-STATE-010"] == "FAIL"
    assert "irreversibility_materiality (FLAG)" in results["PX-REG-STATE-010"].details
    assert "pressure" not in results["PX-REG-STATE-010"].details.split("; not admitted on:")[0]
    assert {k for k, v in checks.items() if v == "FAIL"} == {"PX-REG-STATE-010"}
    assert checks["PX-CT-R3-007"] == "NOT_IN_PERIMETER"
    # Every admission on a FLAG carries the declared condition (RFC-0 §4).
    on_flag = {c: f for c, f in adapter.facts.items() if f.get("admitted_on") == "FLAG"}
    assert on_flag and all(f.get("flag_conditions") for f in on_flag.values())
    assert not any(f.get("implementation_gap") for f in adapter.facts.values())


@needs_576
def test_576_flag_without_acknowledgement_is_not_dispatched():
    """The acknowledgement is what lets a FLAG through on 5.7.6. Without it the
    shipped governor refuses the dispatch, the refusal falls outside the v0.7.0
    mapping (`NATIVE:`, no neutral vector satisfied) and nothing is executed; the
    operation stays reserved and dispatches once acknowledged."""
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    wrapper, port._gov = port._gov, port._gov._governor
    with pytest.raises(P.Refused) as e:
        port.commit(d, action_type="wire_transfer")
    assert e.value.code == "NATIVE:reserved"
    assert port.observed_effects(d) == 0
    port._gov = wrapper
    assert port.commit(d, action_type="wire_transfer").raw.get("dispatched") is True
    assert port.observed_effects(d) == 1


@needs_576
def test_576_acknowledgement_is_recorded_even_when_the_dispatch_is_refused():
    """Observed on 5.7.6, for the review of the mapping: the port acknowledges on
    every commit, and the runtime persists and ledgers the acknowledgement before
    the payload binding check. An acknowledgement in the ledger therefore does not
    mean a dispatch. This describes the subject; it is not a defect claim."""
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    with pytest.raises(P.Refused) as e:
        port.commit(d, action_type="other_action")
    assert e.value.code == P.R_BINDING
    record = port._gov.registry.get(d.decision_id)
    assert record.state.value == "reserved" and record.flag_conditions_met
    acknowledged = [x for x in port._gov.ledger.entries if x.idempotency_key == d.decision_id
                    and "acknowledged at dispatch" in (x.rationale or "")]
    assert len(acknowledged) == 1
    assert port.observed_effects(d) == 0


# -- R8 (review of 2026-11-23): an API refusal is not a governance veto ---------

def test_port_maps_invalid_argument_to_a_native_refusal_not_a_decision():
    """From the 5.7.7 candidate on, a malformed request raises an error carrying
    `code == "INVALID_ARGUMENT"` instead of returning a HARD_VETO dict. The port
    surfaces it as a `Refused` outside the neutral mapping (`NATIVE:invalid_argument`,
    no disposition), never as a `Decision`: an API-level rejection is kept apart from
    a governance-level veto. Matched by code, so the test needs no 5.7.7 install."""
    from harness.ports.tenir_gov import TenirGovPort

    class _InvalidArgument(ValueError):
        code = "INVALID_ARGUMENT"

    class _Gov:
        def adjudicate(self, passage, **kw):
            raise _InvalidArgument("INVALID_ARGUMENT (amount): Amount is invalid.")

    port = TenirGovPort.__new__(TenirGovPort)
    port._gov = _Gov()
    with pytest.raises(P.Refused) as exc:
        port._adjudicate({"pressure": 0.2}, 10.0, principal="a", action_type="wire_transfer")
    assert exc.value.code == "NATIVE:invalid_argument"
    assert exc.value.disposition is None
    assert "HARD_VETO" not in str(exc.value)


def test_port_lets_other_value_errors_through():
    from harness.ports.tenir_gov import TenirGovPort

    class _Gov:
        def adjudicate(self, passage, **kw):
            raise ValueError("something else")

    port = TenirGovPort.__new__(TenirGovPort)
    port._gov = _Gov()
    with pytest.raises(ValueError, match="something else"):
        port._adjudicate({"pressure": 0.2}, 10.0, principal="a", action_type="wire_transfer")


def test_port_declares_irreversibility_materiality_per_intent():
    """Decision C (23 November 2026): the port measures `irreversibility_materiality`
    per intent as its eighth declared measurement, degraded like the seven others,
    instead of leaving it to the governor's default (0.0 on 5.7.0 and 5.7.6, UNKNOWN
    on the 5.7.7 candidate). The declared values stay inside the reference
    geometry's irreversibility-authority boundary (materiality - authority <= 0.25)
    for the authority they are declared with, so none of them vetoes on its own."""
    from harness.ports.tenir_gov import _BEST, _INPUTS, TenirGovPort

    assert _BEST["irreversibility_materiality"] == 0.1
    for state in (P.E_MISSING, P.E_UNKNOWN):
        assert "irreversibility_materiality" in TenirGovPort.degradations[state]
        assert len(TenirGovPort.degradations[state]) == 8
    declared = {intent: {**_BEST, **overrides}["irreversibility_materiality"]
                for intent, (overrides, _) in _INPUTS.items()}
    assert declared[P.NEEDS_APPROVAL] == 0.6
    assert declared[P.DENIED] == declared[P.INVARIANT_VIOLATED] == 0.8
    assert declared[P.ADMISSIBLE] == declared[P.INADMISSIBLE] == declared[P.NO_STANDING] == 0.1
    for intent, (overrides, _) in _INPUTS.items():
        measured = {**_BEST, **overrides}
        assert measured["irreversibility_materiality"] - measured["authority"] <= 0.25, intent


@needs_576
def test_576_port_revocation_after_verdict_is_refused_at_commit():
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="r", action_type="wire_transfer")
    assert d.disposition == "FLAG"
    port.revoke("r")
    with pytest.raises(P.Refused) as e:
        port.commit(d, action_type="wire_transfer")
    assert e.value.code == P.R_STANDING_REVOKED and e.value.disposition == "HARD_VETO"
    assert port.observed_effects(d) == 0
    assert port._inner.registry.get(d.decision_id).state.value == "failed"
    # Standing is a measured score on this runtime: a new request from the revoked
    # principal is adjudicated on its measured authority (declared partial gap).
    again = port.evaluate(P.ADMISSIBLE, principal="r", action_type="wire_transfer")
    assert again.disposition == "FLAG"


@needs_576
def test_576_port_state_drift_is_refused_at_commit():
    from harness.ports.tenir_gov_576 import TenirGov576Port
    port = TenirGov576Port()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    change = port.drift_state()
    assert "composition policy version" in change
    with pytest.raises(P.Refused) as e:
        port.commit(d, action_type="wire_transfer")
    assert e.value.code == P.R_STATE_DRIFT and e.value.disposition == "HARD_VETO"
    assert port.observed_effects(d) == 0


@needs_576
def test_576_port_tau_k_is_a_declared_fixture_and_expiry_is_terminal():
    from harness.ports.tenir_gov_576 import TAU_K, TAU_K_SOURCE, TenirGov576Port
    assert "fixture" in TAU_K_SOURCE and "not derived from an SLA" in TAU_K_SOURCE
    port = TenirGov576Port()
    assert port.bounds == {P.B_TAU_K: TAU_K} and port.clock_mode == "simulated"
    assert port.exhaustion_policy == "fail-closed"
    held = port.evaluate(P.NEEDS_APPROVAL, principal="h", action_type="wire_transfer")
    assert held.disposition == "HOLD"
    # Before the bound: the hold is open and cannot be committed, not terminal.
    with pytest.raises(P.Refused) as e:
        port.commit(held, action_type="wire_transfer")
    assert e.value.code == P.R_INVALID_DISPOSITION
    assert port.elapse_past(P.B_TAU_K) > TAU_K
    record = port._inner.registry.get(held.decision_id)
    assert record.state.value == "failed" and record.hold_record.exit_reason == "expired"
    with pytest.raises(P.Refused) as e:
        port.commit(held, action_type="wire_transfer")
    assert e.value.code == P.R_EXPIRED and e.value.disposition == "HARD_VETO"
    assert port.observed_effects(held) == 0
