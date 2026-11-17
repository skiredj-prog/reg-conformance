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
from harness.scenarios import CHECKS, PROBES, SCENARIOS

KERNEL = str(Path(__file__).resolve().parents[1] / "kernel" / "tenir_policies.yaml")


def test_reference_port_matches_legacy_native_mode_on_every_vector():
    legacy = {r.vector_id: r.status for r in R.NativeKernelAdapter(KERNEL).run_all()}
    ported = {r.vector_id: r.status for r in PortAdapter(ReferencePort()).run_all()}
    assert len(legacy) == 56
    assert ported == legacy


def test_empty_port_passes_nothing():
    adapter = PortAdapter(TemplatePort())
    results = adapter.run_all() + adapter.run_probes() + adapter.run_checks()
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


@pytest.mark.skipif(not _tenir_gov_installed(), reason="needs a pinned tenir-governance install")
def test_tenir_gov_port_on_the_property_checks():
    from harness.ports.tenir_gov import TenirGovPort
    got = {r.vector_id: r.status.value for r in PortAdapter(TenirGovPort()).run_checks()}
    assert got["PX-CT-R0-005"] == got["PX-REG-STATE-014"] == got["PX-VEC-6-02"] == "PASS"
    # The default path has no credential to malform and no revocation primitive.
    assert got["PX-CT-R3-001"] == got["PX-CT-R3-003"] == "ADAPTER_REQUIRED"
    # The scope check runs: its outcome belongs to the runtime version, not to this test.
    assert got["PX-CT-R3-007"] in ("PASS", "FAIL")


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


# -- property checks: one indexed property each, never a vector ---------------

class _Governed(P.RuntimePort):
    """Two-phase test double with standing, a scope, a hard invariant, keys and
    revocation. `fault` selects the defect."""
    capabilities = frozenset({P.EVALUATE, P.COMMIT, P.REVOKE, P.NONCE, P.COMBINE})
    intents = frozenset({P.ADMISSIBLE, P.NO_STANDING, P.NEEDS_APPROVAL, P.MALFORMED_CREDENTIAL,
                         P.OUT_OF_SCOPE, P.INVARIANT_VIOLATED})
    combinations = frozenset({frozenset({P.NO_STANDING, P.NEEDS_APPROVAL})})
    fault = None
    verdicts = {P.ADMISSIBLE: "PASS", P.NO_STANDING: "HARD_VETO", P.NEEDS_APPROVAL: "HOLD",
                P.MALFORMED_CREDENTIAL: "HARD_VETO", P.OUT_OF_SCOPE: "HARD_VETO",
                P.INVARIANT_VIOLATED: "HARD_VETO"}
    faults = {"admits_malformed": (P.MALFORMED_CREDENTIAL, "PASS"),
              "holds_malformed": (P.MALFORMED_CREDENTIAL, "HOLD"),
              "admits_out_of_scope": (P.OUT_OF_SCOPE, "FLAG"),
              "scores_past_invariant": (P.INVARIANT_VIOLATED, "FLAG"),
              "holds_on_invariant": (P.INVARIANT_VIOLATED, "HOLD")}

    def reset(self):
        self.revoked, self.keys = set(), {}

    def _verdict(self, intent):
        swapped, verdict = self.faults.get(self.fault, (None, None))
        return verdict if intent == swapped else self.verdicts[intent]

    def evaluate(self, intent, *, principal, action_type, nonce=None):
        return self.evaluate_combined((intent,), principal=principal,
                                      action_type=action_type, nonce=nonce)

    def evaluate_combined(self, intents, *, principal, action_type, nonce=None):
        if nonce is not None:
            new_action = nonce in self.keys and self.keys[nonce] != action_type
            if nonce in self.keys and not (new_action and self.fault == "key_reuse_new_action"):
                raise P.Refused(P.R_REPLAY)
            self.keys[nonce] = action_type
        pick = min if self.fault == "least_restrictive_wins" else max
        verdict = pick((self._verdict(i) for i in intents), key=P.RESTRICTIVENESS.index)
        if principal in self.revoked or (self.revoked and self.fault == "revocation_spills"):
            verdict = "HARD_VETO"
        return P.Decision(uuid.uuid4().hex, verdict, action_type, principal, {})

    def commit(self, decision, *, action_type=None):
        if decision.principal in self.revoked or (
                self.revoked and self.fault == "revocation_blocks_grants"):
            raise P.Refused(P.R_STANDING_REVOKED, "HARD_VETO")
        return P.Committed(decision.decision_id)

    def revoke(self, principal):
        if self.fault != "revocation_inert":
            self.revoked.add(principal)


def _checks(fault=None, base=_Governed):
    class F(base): pass
    F.fault = fault
    return {r.vector_id: r.status.value for r in PortAdapter(F()).run_checks()}


def test_property_checks_pass_on_a_correct_runtime():
    assert _checks() == {c: "PASS" for c in CHECKS}


@pytest.mark.parametrize("fault,check", [
    ("admits_malformed", "PX-CT-R3-001"),
    ("admits_out_of_scope", "PX-CT-R3-007"),
    ("scores_past_invariant", "PX-REG-STATE-014"),
    ("holds_on_invariant", "PX-REG-STATE-014"),          # RFC-2 §3.3 names HARD_VETO
    ("key_reuse_new_action", "PX-VEC-6-02"),
    ("revocation_spills", "PX-CT-R3-003"),
    ("revocation_blocks_grants", "PX-CT-R3-003"),
    ("least_restrictive_wins", "PX-CT-R0-005"),
])
def test_each_property_check_detects_its_fault_and_only_that_one(fault, check):
    got = _checks(fault)
    assert [c for c, state in got.items() if state != "PASS"] == [check]
    assert got[check] == "FAIL"


@pytest.mark.parametrize("fault,check", [
    ("holds_malformed", "PX-CT-R3-001"),                 # suspended is not rejected
    ("revocation_inert", "PX-CT-R3-003"),                # nothing to isolate
])
def test_a_property_check_does_not_conclude_on_a_half_observation(fault, check):
    assert _checks(fault)[check] == "INCONCLUSIVE"


def test_a_runtime_that_refuses_everything_passes_no_property_check():
    class Closed(_Governed):
        verdicts = dict.fromkeys(_Governed.verdicts, "HARD_VETO")
    assert set(_checks(base=Closed).values()) == {"INCONCLUSIVE"}


def test_most_restrictive_check_needs_two_conditions_that_conflict():
    class Flat(_Governed):
        combinations = frozenset({frozenset({P.NO_STANDING, P.INVARIANT_VIOLATED})})
    assert _checks(base=Flat)["PX-CT-R0-005"] == "INCONCLUSIVE"


def test_property_checks_are_not_reg_vectors_and_never_double_one():
    assert not set(CHECKS) & (set(R.VECTORS) | set(SCENARIOS) | set(PROBES))
    assert all(not s.normative for s in CHECKS.values())
    rows = [s.exercises for s in CHECKS.values()]
    assert set(rows) <= _index_ids() and len(set(rows)) == len(rows)
    assert not set(rows) & set(SCENARIOS)        # a row with an executable vector needs no check
    assert all(vid == f"PX-{s.exercises}" for vid, s in CHECKS.items())


def test_each_property_check_names_a_row_and_says_whether_the_rfcs_specify_it():
    rows = properties.index_rows()
    assert set(rows) == _index_ids()
    status = {s.exercises: rows[s.exercises]["status"] for s in CHECKS.values()}
    # None of the six rows has a behavioural test in the runner.
    assert "IMPLEMENTED" not in status.values()
    # CT-R3-003 is a proposal: the frozen RFCs do not state it.
    assert [r for r, state in status.items() if state == "RESERVED"] == ["CT-R3-003"]


def test_a_port_cannot_declare_a_combination_it_cannot_produce():
    class Bad(TemplatePort):
        capabilities = frozenset({P.EVALUATE, P.COMBINE})
        intents = frozenset({P.ADMISSIBLE})
        combinations = frozenset({frozenset({P.ADMISSIBLE, P.DENIED})})
    with pytest.raises(ValueError):
        PortAdapter(Bad())


_EXERCISES = {vid: s.exercises for vid, s in CHECKS.items()}


def _view_with_checks(port, run=True):
    adapter = PortAdapter(port)
    results = adapter.run_all()
    checks = adapter.run_checks() if run else []
    return adapter, results, checks, properties.view(
        results, (), checks, registered=R.VECTORS,
        executable=_RUNNABLE | set(CHECKS), exercises=_EXERCISES)


def test_property_view_counts_a_check_under_the_row_it_exercises():
    adapter, results, checks, view = _view_with_checks(_Governed())
    # The vector tally does not move when the checks run.
    assert [r.status for r in PortAdapter(_Governed()).run_all()] == [r.status for r in results]
    assert view["families"]["EGP-01"]["checks"]["PX-CT-R3-001"] == "PASS"
    assert view["families"]["EGP-01"]["checks"]["PX-CT-R3-007"] == "PASS"
    assert view["families"]["EGP-14"]["checks"]["PX-REG-STATE-014"] == "PASS"
    assert view["unattached"] == []
    assert view["index"]["indexed"] == len(_index_ids())
    assert view["index"]["with_check"] == len(SCENARIOS) + len(CHECKS)


def test_a_row_with_a_check_that_did_not_run_is_counted_once():
    # CT-R0-005 is a registered vector and has a check: one row, not two.
    # REG-STATE-014 has no vector: it stops being "no check" once a check exists.
    for run in (True, False):
        _, _, _, view = _view_with_checks(TemplatePort(), run=run)
        family = view["families"]["EGP-14"]
        assert (family["not_run"], family["no_check"], family["unregistered"]) == (3, 0, 1)
        assert view["index"]["observed"] == 0


def test_reference_kernel_on_the_property_checks():
    adapter, _, checks, view = _view_with_checks(ReferencePort())
    got = {r.vector_id: r for r in checks}
    assert {k: r.status.value for k, r in got.items()} == {
        "PX-CT-R0-005": "ADAPTER_REQUIRED", "PX-CT-R3-001": "FAIL", "PX-CT-R3-003": "PASS",
        "PX-CT-R3-007": "ADAPTER_REQUIRED", "PX-VEC-6-02": "PASS",
        "PX-REG-STATE-014": "ADAPTER_REQUIRED"}
    # The kernel admits a blank credential. Its own gap register says so.
    assert "CT-R3-001" in got["PX-CT-R3-001"].gap_note
    # A failing check marks the family, whatever else passes in it.
    assert view["families"]["EGP-01"]["PASS"] == 1
    assert view["families"]["EGP-01"]["state"] == "has_fail"
    assert (view["index"]["PASS"], view["index"]["FAIL"]) == (16, 1)


def test_bundle_verdict_lists_property_checks_apart_from_the_vectors():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import make_evidence_bundle as B
    adapter, results, checks, view = _view_with_checks(_Governed())
    report = R.generate_report(adapter, results)
    report["property_checks"] = {"exercises": _EXERCISES, "results": [R.asdict(r) for r in checks]}
    report["property_view"] = view
    verdict = B.build_verdict(json.loads(json.dumps(report, default=str)))
    assert verdict["property_checks"]["results"] == {c: "PASS" for c in CHECKS}
    assert not set(verdict["property_checks"]["results"]) & set(verdict["reg_vectors"]["passed"])
    assert verdict["property_view"]["index"]["with_check"] == len(SCENARIOS) + len(CHECKS)
    assert verdict["certifying"] is False
