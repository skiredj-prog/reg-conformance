"""The harness is an instrument: these tests check that it can fail.

Fixture runtimes below are deliberately broken test doubles. They exist only
to show that each effect probe detects the fault it is meant to detect. They
are not runtimes under qualification and produce no conformance evidence.
"""
import json
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import runner as R
from harness import port as P
from harness import properties
from harness.adapter import PortAdapter
from harness.ports.reference import ReferencePort
from harness.ports.template import TemplatePort
from harness.scenarios import PROBES, SCENARIOS

KERNEL = str(Path(__file__).resolve().parents[1] / "kernel" / "tenir_policies.yaml")


def test_reference_port_matches_legacy_native_mode_on_every_vector():
    legacy = {r.vector_id: r.status for r in R.NativeKernelAdapter(KERNEL).run_all()}
    ported = {r.vector_id: r.status for r in PortAdapter(ReferencePort()).run_all()}
    assert len(legacy) == 56
    assert ported == legacy


def test_empty_port_passes_nothing():
    adapter = PortAdapter(TemplatePort())
    results = adapter.run_all() + adapter.run_probes()
    assert {r.status for r in results} == {R.ReportingState.ADAPTER_REQUIRED}


def test_port_cannot_claim_native_conformance():
    class Boastful(TemplatePort):
        evidence_level = 3
    assert PortAdapter(Boastful()).evidence_level == R.EvidenceLevel.ADAPTER_TESTED


def test_unknown_capability_and_intent_are_rejected():
    class BadCap(TemplatePort):
        capabilities = frozenset({"telepathy"})
    class BadIntent(TemplatePort):
        intents = frozenset({"whatever"})
    for bad in (BadCap, BadIntent):
        with pytest.raises(ValueError):
            PortAdapter(bad())


def test_port_cannot_override_a_neutral_scenario():
    class Cheater(TemplatePort):
        def run_custom(self, vector_id):
            return R.ConformanceResult(vector_id, R.ReportingState.PASS, "x", 2)
    with pytest.raises(ValueError):
        PortAdapter(Cheater()).run_vector("C1")


def test_declared_but_unimplemented_capability_is_not_a_pass():
    class Hollow(TemplatePort):
        capabilities = frozenset({P.EVALUATE})
        intents = frozenset({P.NO_STANDING})
    assert PortAdapter(Hollow()).run_vector("C1").status == R.ReportingState.INCONCLUSIVE


def test_policy_denial_cannot_satisfy_a_structural_vector():
    assert P.DENIED not in SCENARIOS["C2"].intents
    assert SCENARIOS["C2"].intents == frozenset({P.INADMISSIBLE})


class _Fixture(P.RuntimePort):
    """Single-phase test double with a journal. `fault` selects the defect."""
    capabilities = frozenset({P.EVALUATE, P.EFFECTS})
    intents = frozenset({P.ADMISSIBLE, P.DENIED, P.NEEDS_APPROVAL})
    fault = None

    def reset(self):
        self.journal = []

    def evaluate(self, intent, *, principal, action_type, nonce=None):
        token = uuid.uuid4().hex
        disposition = {P.ADMISSIBLE: "PASS", P.DENIED: "HARD_VETO", P.NEEDS_APPROVAL: "HOLD"}[intent]
        runs = 1 if intent == P.ADMISSIBLE else 0
        if self.fault == "executes_on_refusal" and intent == P.DENIED: runs = 1
        if self.fault == "executes_twice" and intent == P.ADMISSIBLE: runs = 2
        if self.fault == "executes_unapproved" and intent == P.NEEDS_APPROVAL: runs = 1
        if self.fault == "refusal_poisons_next" and intent == P.ADMISSIBLE and getattr(self, "_refused", False):
            runs = 0
        if intent == P.DENIED: self._refused = True
        self.journal += [token] * runs
        return P.Decision(token, disposition, action_type, principal, {})

    def observed_effects(self, decision):
        return self.journal.count(decision.decision_id)


def _probe(fault):
    class F(_Fixture): pass
    F.fault = fault
    return {r.vector_id: r.status.value for r in PortAdapter(F()).run_probes()}


def test_probes_pass_on_a_correct_runtime():
    assert set(_probe(None).values()) == {"PASS"}


@pytest.mark.parametrize("fault,probe", [
    ("executes_on_refusal", "HX-EFFECT-001"),
    ("executes_twice", "HX-EFFECT-002"),
    ("executes_unapproved", "HX-EFFECT-003"),
    ("refusal_poisons_next", "HX-EFFECT-004"),
])
def test_each_probe_detects_its_fault(fault, probe):
    assert _probe(fault)[probe] == "FAIL"


def test_probes_are_not_reg_vectors():
    assert not set(PROBES) & set(R.VECTORS)
    assert all(not s.normative for s in PROBES.values())


def _tenir_gov_installed():
    try:
        import tenir_governance  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _tenir_gov_installed(), reason="needs a pinned tenir-governance install")
def test_tenir_gov_port_reports_native_dispositions_unchanged():
    from harness.ports.tenir_gov import TenirGovPort
    port = TenirGovPort()
    adapter = PortAdapter(port)
    # The port must not turn the runtime's FLAG into a PASS.
    port.reset()
    d = port.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    assert d.disposition == d.raw["result"]["composed_decision"]
    # Nothing may pass on a capability the port does not declare.
    undeclared = {"C3", "CT-R4-004", "CT-R4-005", "CT-R4-007"}
    results = {r.vector_id: r.status for r in adapter.run_all()}
    assert {results[v] for v in undeclared} == {R.ReportingState.ADAPTER_REQUIRED}
    # A refusal and an unanswered approval leave the port's journal empty.
    probes = {r.vector_id: r.status.value for r in adapter.run_probes()}
    assert probes["HX-EFFECT-001"] == "PASS" and probes["HX-EFFECT-003"] == "PASS"


# -- admission class (RFC-0 §4: PASS is ALLOW, FLAG is ALLOW_WITH_MONITORING) --

class _TwoPhase(P.RuntimePort):
    """Two-phase test double: a verdict, then a commit bound to its action type."""
    capabilities = frozenset({P.EVALUATE, P.COMMIT})
    intents = frozenset({P.ADMISSIBLE})
    verdict = "PASS"
    conditions = ()

    def evaluate(self, intent, *, principal, action_type, nonce=None):
        return P.Decision(uuid.uuid4().hex, self.verdict, action_type, principal, {},
                          self.conditions)

    def commit(self, decision, *, action_type=None):
        if action_type and action_type != decision.action_type:
            raise P.Refused(P.R_BINDING)
        return P.Committed(decision.decision_id)


def _two_phase(verdict, conditions=()):
    class T(_TwoPhase): pass
    T.verdict, T.conditions = verdict, conditions
    adapter = PortAdapter(T())
    return adapter, {v: adapter.run_vector(v).status.value for v in ("CT-R4-001", "CT-R4-002")}


def test_flag_admits_like_pass_and_is_recorded():
    _, with_pass = _two_phase("PASS")
    adapter, with_flag = _two_phase("FLAG")
    assert with_pass == with_flag == {"CT-R4-001": "PASS", "CT-R4-002": "PASS"}
    assert adapter.facts["CT-R4-001"] == {"admitted_on": "FLAG", "flag_conditions": []}


def test_flag_condition_reported_by_the_port_is_kept():
    adapter, _ = _two_phase("FLAG", ("dual control",))
    assert adapter.facts["CT-R4-001"]["flag_conditions"] == ["dual control"]


@pytest.mark.parametrize("verdict", ["HOLD", "HARD_VETO"])
def test_a_suspension_or_a_refusal_is_never_an_admission(verdict):
    _, statuses = _two_phase(verdict)
    assert statuses == {"CT-R4-001": "FAIL", "CT-R4-002": "FAIL"}


def _relabel(intent, disposition):
    class F(_Fixture):
        def evaluate(self, asked, **kw):
            d = super().evaluate(asked, **kw)
            if asked == intent:
                d.disposition = disposition
            return d
    return {r.vector_id: r.status.value for r in PortAdapter(F()).run_probes()}


def test_probes_accept_an_allow_given_as_flag():
    assert set(_relabel(P.ADMISSIBLE, "FLAG").values()) == {"PASS"}


def test_a_call_needing_approval_must_not_get_a_plain_pass():
    assert _relabel(P.NEEDS_APPROVAL, "PASS")["HX-EFFECT-003"] == "FAIL"


# -- property view: a second reading, never a second tally --------------------

_RUNNABLE = set(SCENARIOS) | set(PROBES)


def _index_ids():
    text = (Path(__file__).resolve().parents[1] / "VECTORS.md").read_text(encoding="utf-8")
    return {line.split("|")[1].strip() for line in text.splitlines()
            if line.startswith("|") and not line.startswith(("|---", "| vector_id"))}


def _view(port, with_probes=True):
    adapter = PortAdapter(port)
    results = adapter.run_all()
    probes = adapter.run_probes() if with_probes else []
    return adapter, results, probes, properties.view(
        results, probes, registered=R.VECTORS, executable=_RUNNABLE)


def test_every_indexed_check_and_every_probe_has_exactly_one_family():
    data = properties.load()
    assert set(data["checks"]) == _index_ids() | set(PROBES)
    assert set(R.VECTORS) <= set(data["checks"])
    assert len(data["families"]) == 14 and data["status"] == "candidate"


def test_property_view_counts_probes_and_leaves_the_vector_tally_alone():
    adapter, results, _, view = _view(_Fixture())
    summary = R.generate_report(adapter, results)["summary"]
    assert summary["PASS"] == 0 and summary["ADAPTER_REQUIRED"] == 56
    assert view["families"]["EGP-06"]["PASS"] == 2 and view["families"]["EGP-12"]["PASS"] == 2
    assert view["summary"] == {"families": 14, "has_pass": 2, "has_fail": 0,
                               "inconclusive": 0, "not_exercised": 12}
    assert view["unattached"] == []


def test_property_view_shows_a_failing_family():
    class F(_Fixture):
        fault = "executes_on_refusal"
    _, _, _, view = _view(F())
    assert view["families"]["EGP-06"]["state"] == "has_fail"
    assert view["summary"]["has_fail"] >= 1


def test_property_view_without_probes_reports_them_as_not_run():
    _, _, _, view = _view(_Fixture(), with_probes=False)
    assert view["summary"]["has_pass"] == 0
    assert view["families"]["EGP-06"]["not_run"] == 3      # CT-R4-006 and two probes


def test_bundle_verdict_carries_the_property_summary_and_never_certifies():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import make_evidence_bundle as B
    adapter, results, probes, view = _view(_Fixture())
    report = R.generate_report(adapter, results)
    report["harness_probes"] = {"results": [R.asdict(r) for r in probes]}
    report["property_view"] = view
    verdict = B.build_verdict(json.loads(json.dumps(report, default=str)))
    assert verdict["certifying"] is False
    assert verdict["reg_vectors"]["summary"]["PASS"] == 0
    assert verdict["property_view"]["summary"]["has_pass"] == 2
    assert verdict["property_view"]["status"] == "candidate"
