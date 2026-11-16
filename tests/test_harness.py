"""The harness is an instrument: these tests check that it can fail.

Fixture runtimes below are deliberately broken test doubles. They exist only
to show that each effect probe detects the fault it is meant to detect. They
are not runtimes under qualification and produce no conformance evidence.
"""
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import runner as R
from harness import port as P
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

