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
    # Capabilities the port does not declare stay ADAPTER_REQUIRED: exit code 2, not a PASS.
    assert {vectors[v] for v in ("C3", "CT-R4-004", "CT-R4-005", "CT-R4-007")} == {"ADAPTER_REQUIRED"}
    probes = {r.vector_id: r.status.value for r in adapter.run_probes()}
    assert set(probes.values()) == {"PASS"}
    checks = {r.vector_id: r.status.value for r in adapter.run_checks()}
    assert "FAIL" not in checks.values() and "INCONCLUSIVE" not in checks.values()
    # Missing evidence is never admitted on 5.7.6 (it was on 5.7.0).
    assert checks["PX-REG-STATE-010"] == "PASS"
    assert checks["PX-CT-R3-007"] == "NOT_IN_PERIMETER"
    # Every admission on a FLAG carries the declared condition (RFC-0 §4).
    on_flag = {c: f for c, f in adapter.facts.items() if f.get("admitted_on") == "FLAG"}
    assert on_flag and all(f.get("flag_conditions") for f in on_flag.values())
    assert not any(f.get("implementation_gap") for f in adapter.facts.values())
