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
    assert len(legacy) == 61
    # The legacy native mode never ran the rows that got a neutral scenario on
    # 23 November 2026 (CT-R0-003, CT-R5-001, CT-R5-004, CT-R7-002): it declared
    # them gaps. The port runs them; everywhere else the two agree.
    executed_now = {v for v, s in legacy.items()
                    if v in SCENARIOS and s == R.ReportingState.IMPLEMENTATION_GAP
                    and ported[v] != R.ReportingState.IMPLEMENTATION_GAP}
    assert executed_now == {"CT-R0-003", "CT-R5-001", "CT-R5-004", "CT-R7-002"}
    assert all(ported[v] == R.ReportingState.PASS for v in executed_now)
    assert {v: s for v, s in ported.items() if v not in executed_now} == \
        {v: s for v, s in legacy.items() if v not in executed_now}


def test_empty_port_passes_nothing():
    adapter = PortAdapter(TemplatePort())
    results = adapter.run_all() + adapter.run_probes() + adapter.run_checks()
    # Nothing passes. The rows no ratified text specifies are NOT_SPECIFIED on
    # every subject (rule of 23 November 2026); everything else needs the port.
    assert {r.status for r in results} == {R.ReportingState.ADAPTER_REQUIRED,
                                           R.ReportingState.NOT_SPECIFIED}
    assert not any(r.status == R.ReportingState.NOT_SPECIFIED for r in adapter.run_probes() + adapter.run_checks())


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


def test_port_cannot_set_aside_a_neutral_scenario_as_not_applicable():
    class Dodger(TemplatePort):
        not_applicable = {"C1": "not for us"}
    with pytest.raises(ValueError):
        PortAdapter(Dodger()).run_vector("C1")


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


def _tenir_gov_version():
    try:
        import tenir_governance
    except ImportError:
        return None
    return tenir_governance.__version__


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


@pytest.mark.skipif(_tenir_gov_version() != "5.7.0",
                    reason="expectations of the pinned 5.7.0; 5.7.6 has its own (test_harness_tenir_gov_576.py)")
def test_tenir_gov_port_on_the_property_checks():
    from harness.ports.tenir_gov import TenirGovPort
    got = {r.vector_id: r.status.value for r in PortAdapter(TenirGovPort()).run_checks()}
    # On 5.7.0 these go forward on a FLAG with no condition: PASS with the reserve.
    assert got["PX-CT-R0-005"] == got["PX-REG-STATE-014"] == got["PX-VEC-6-02"] == "PASS"
    # The default path has no credential to malform: declared outside the perimeter
    # since 23 November 2026 (option A); and no revocation primitive.
    assert got["PX-CT-R3-001"] == "NOT_IN_PERIMETER" and got["PX-CT-R3-003"] == "ADAPTER_REQUIRED"
    # Decision 1: scope is declared outside the runtime's perimeter, neither PASS nor FAIL.
    assert got["PX-CT-R3-007"] == "NOT_IN_PERIMETER"
    # The default path declares no bound: a HOLD it enters carries no tau_k. The
    # credential-expiry check follows its row outside the perimeter (option A).
    assert {got[c] for c in _AT_A_BOUND if c != "PX-CT-R3-006"} == {"ADAPTER_REQUIRED"}
    assert got["PX-CT-R3-006"] == "NOT_IN_PERIMETER"
    # Unreadable evidence is held, and lower confidence widens nothing.
    assert got["PX-REG-STATE-001"] == got["PX-REG-STATE-013"] == got["PX-REG-STATE-015"] == "PASS"
    # Missing evidence: the check runs on every input; its outcome belongs to the version.
    assert got["PX-REG-STATE-010"] in ("PASS", "FAIL")
    # One value per measurement, no age: stale and contradictory cannot be produced.
    assert got["PX-REG-STATE-002"] == got["PX-REG-STATE-004"] == "ADAPTER_REQUIRED"


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


def test_flag_with_a_condition_admits_like_pass_and_is_recorded():
    _, with_pass = _two_phase("PASS")
    adapter, with_flag = _two_phase("FLAG", ("dual control",))
    assert with_pass == with_flag == {"CT-R4-001": "PASS", "CT-R4-002": "PASS"}
    assert adapter.facts["CT-R4-001"] == {"admitted_on": "FLAG",
                                          "flag_conditions": ["dual control"]}


def test_flag_without_a_condition_keeps_its_result_with_the_reserve():
    # Author's decision 3, CLAIMS.md, RN-001 §1: the result stands under the declared
    # mapping, carries the reserve, and the gap is recorded apart.
    from harness.adapter import FLAG_RESERVE
    adapter, statuses = _two_phase("FLAG")
    assert statuses == {"CT-R4-001": "PASS", "CT-R4-002": "PASS"}
    assert adapter.facts["CT-R4-001"]["admitted_on"] == "FLAG"
    assert adapter.facts["CT-R4-001"]["flag_conditions"] == []
    assert "implementation_gap" in adapter.facts["CT-R4-001"]
    r = adapter.run_vector("CT-R4-001")
    assert FLAG_RESERVE in r.gap_note


def test_flag_condition_reported_by_the_port_is_kept():
    adapter, _ = _two_phase("FLAG", ("dual control",))
    assert adapter.facts["CT-R4-001"]["flag_conditions"] == ["dual control"]


@pytest.mark.parametrize("verdict", ["HOLD", "HARD_VETO"])
def test_a_suspension_or_a_refusal_is_never_an_admission(verdict):
    _, statuses = _two_phase(verdict)
    assert statuses == {"CT-R4-001": "FAIL", "CT-R4-002": "FAIL"}


def _relabel(intent, disposition, conditions=()):
    class F(_Fixture):
        def evaluate(self, asked, **kw):
            d = super().evaluate(asked, **kw)
            if asked == intent:
                d.disposition = disposition
                if conditions:
                    d.conditions = conditions
            return d
    return {r.vector_id: r.status.value for r in PortAdapter(F()).run_probes()}


def test_probes_accept_an_allow_given_as_flag_with_a_condition():
    assert set(_relabel(P.ADMISSIBLE, "FLAG", ("monitoring",)).values()) == {"PASS"}


def test_probes_on_a_flag_without_a_condition_pass_with_the_reserve():
    # Only the probes that go forward on the admitted call (HX-EFFECT-002, 004) carry it.
    from harness.adapter import FLAG_RESERVE

    class F(_Fixture):
        def evaluate(self, asked, **kw):
            d = super().evaluate(asked, **kw)
            if asked == P.ADMISSIBLE:
                d.disposition = "FLAG"
            return d
    adapter = PortAdapter(F())
    probes = {r.vector_id: r for r in adapter.run_probes()}
    assert {r.status.value for r in probes.values()} == {"PASS"}
    reserved = {vid for vid, r in probes.items() if r.gap_note == FLAG_RESERVE}
    assert reserved == {"HX-EFFECT-002", "HX-EFFECT-004"}
    assert all(adapter.facts[vid]["implementation_gap"] for vid in reserved)


def test_a_flag_without_a_condition_is_a_gap_whatever_the_result():
    # The gap is recorded where the adapter sets it, for a FAIL as for a PASS;
    # only a pass carries the reserve. The report reads that one marker.
    from harness.adapter import FLAG_RESERVE
    from harness.scenarios import Scenario
    flagged = {"admitted_on": "FLAG", "flag_conditions": []}
    adapter = PortAdapter(_Fixture())
    failed = adapter._run_scenario("X-FAIL", Scenario("X-FAIL", frozenset(), lambda rt: ("FAIL", "x", dict(flagged))))
    passed = adapter._run_scenario("X-PASS", Scenario("X-PASS", frozenset(), lambda rt: ("PASS", "x", dict(flagged))))
    assert failed.status == R.ReportingState.FAIL and failed.gap_note != FLAG_RESERVE
    assert passed.status == R.ReportingState.PASS and passed.gap_note == FLAG_RESERVE
    assert adapter.facts["X-FAIL"]["implementation_gap"] and adapter.facts["X-PASS"]["implementation_gap"]


def test_a_malformed_perimeter_declaration_is_refused():
    exercised = next(iter(CHECKS.values())).exercises

    class F(_Fixture):
        not_in_perimeter = {exercised: {"declared_by": "", "reason": "x"}}
    with pytest.raises(ValueError, match="not_in_perimeter"):
        PortAdapter(F()).run_checks()


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
    # The fixture declares a scope that matches what it does (CT-R0-003) and
    # claims no native evidence level (CT-R7-002): two passes, nothing else.
    assert {r.vector_id for r in results if r.status == R.ReportingState.PASS} == {"CT-R0-003", "CT-R7-002"}
    # 61 rows: 2 PASS, 28 NOT_SPECIFIED (25 RESERVED, 3 superseded), 31 ADAPTER_REQUIRED.
    assert summary["PASS"] == 2 and summary["ADAPTER_REQUIRED"] == 31 and summary["NOT_SPECIFIED"] == 28
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
    assert verdict["reg_vectors"]["summary"]["PASS"] == 2        # CT-R0-003, CT-R7-002
    assert verdict["property_view"]["summary"]["has_pass"] == 2
    assert verdict["property_view"]["status"] == "candidate"


def test_bundle_verdict_keeps_the_implementation_gaps():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import make_evidence_bundle as B
    adapter, results, probes, view = _view(_Fixture())
    report = R.generate_report(adapter, results)
    report["harness_probes"] = {"results": [R.asdict(r) for r in probes]}
    report["property_view"] = view
    report["admission"] = {"rule": "RFC-0 §4", "checks_admitted_on_flag": ["CT-R4-001"],
                           "flag_condition_observed": {"CT-R4-001": False},
                           "implementation_gaps": ["CT-R4-001"]}
    verdict = B.build_verdict(json.loads(json.dumps(report, default=str)))
    assert verdict["admission"]["implementation_gaps"] == ["CT-R4-001"]


# -- property checks: one indexed property each, never a vector ---------------

class _Governed(P.RuntimePort):
    """Two-phase test double with standing, a scope, a hard invariant, keys,
    revocation, a clock and declared bounds. `fault` selects the defect."""
    capabilities = frozenset({P.EVALUATE, P.COMMIT, P.REVOKE, P.NONCE, P.COMBINE, P.CLOCK,
                              P.DEGRADE, P.CONFIDENCE})
    degradations = {P.E_UNKNOWN: ("load",), P.E_STALE: ("load",),
                    P.E_MISSING: ("load", "limit"), P.E_CONTRADICTORY: ("load",)}
    degraded = {P.E_UNKNOWN: "HOLD", P.E_STALE: "HARD_VETO", P.E_MISSING: "HARD_VETO",
                P.E_CONTRADICTORY: "HOLD"}
    domains = {"load": (0.0, 1.0)}
    confidence_steps = 4
    intents = frozenset({P.ADMISSIBLE, P.NO_STANDING, P.NEEDS_APPROVAL, P.MALFORMED_CREDENTIAL,
                         P.OUT_OF_SCOPE, P.INVARIANT_VIOLATED, P.EXPIRING_CREDENTIAL,
                         P.STALE_REQUEST, P.REVOKED_KEY})
    combinations = frozenset({frozenset({P.NO_STANDING, P.NEEDS_APPROVAL})})
    bounds = {P.B_REVOCATION: 5.0, P.B_CREDENTIAL: 60.0, P.B_FRESHNESS: 300.0, P.B_TAU_K: 120.0}
    clock_mode = "simulated"
    fault = None
    verdicts = {P.ADMISSIBLE: "PASS", P.NO_STANDING: "HARD_VETO", P.NEEDS_APPROVAL: "HOLD",
                P.MALFORMED_CREDENTIAL: "HARD_VETO", P.OUT_OF_SCOPE: "HARD_VETO",
                P.INVARIANT_VIOLATED: "HARD_VETO", P.EXPIRING_CREDENTIAL: "PASS",
                P.STALE_REQUEST: "HARD_VETO", P.REVOKED_KEY: "HARD_VETO"}
    faults = {"admits_malformed": (P.MALFORMED_CREDENTIAL, "PASS"),
              "holds_malformed": (P.MALFORMED_CREDENTIAL, "HOLD"),
              "admits_out_of_scope": (P.OUT_OF_SCOPE, "FLAG"),
              "scores_past_invariant": (P.INVARIANT_VIOLATED, "FLAG"),
              "holds_on_invariant": (P.INVARIANT_VIOLATED, "HOLD"),
              "accepts_stale_request": (P.STALE_REQUEST, "PASS"),
              "accepts_revoked_key": (P.REVOKED_KEY, "PASS")}

    def reset(self):
        self.now, self.revoked, self.keys, self.issued, self.made = 0.0, {}, {}, {}, {}

    def elapse_past(self, bound):
        step = self.bounds[bound] + 0.001
        self.now += step
        return step

    def _landed(self):
        """Principals whose revocation has taken effect: after the declared
        bound, or twice that when the revocation is late."""
        lag = self.bounds.get(P.B_REVOCATION, 0.0) * (2 if self.fault == "revocation_late" else 1)
        return {who for who, at in self.revoked.items() if self.now - at >= lag}

    def _verdict(self, intent, principal):
        swapped, verdict = self.faults.get(self.fault, (None, None))
        if intent == swapped:
            return verdict
        if intent == P.EXPIRING_CREDENTIAL and self.fault != "credential_never_expires":
            issued = self.issued.setdefault(principal, self.now)
            if self.now - issued >= self.bounds.get(P.B_CREDENTIAL, 0.0):
                return "HARD_VETO"
        return self.verdicts[intent]

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
        verdict = pick((self._verdict(i, principal) for i in intents),
                       key=P.RESTRICTIVENESS.index)
        landed = self._landed()
        if principal in landed or (landed and self.fault == "revocation_spills"):
            verdict = "HARD_VETO"
        return self._decide(verdict, principal, action_type)

    def _decide(self, verdict, principal, action_type):
        decision = P.Decision(uuid.uuid4().hex, verdict, action_type, principal, {})
        self.made[decision.decision_id] = (verdict, self.now)
        return decision

    def evaluate_at_value(self, measurement, value, *, principal, action_type):
        low, high = self.domains[measurement]
        if not low <= value <= high:
            if self.fault == "admits_out_of_domain":
                return P.Decision(uuid.uuid4().hex, "PASS", action_type, principal, {})
            if self.fault == "holds_out_of_domain":
                return P.Decision(uuid.uuid4().hex, "HOLD", action_type, principal, {})
            raise P.Refused("OUT_OF_DOMAIN", None, f"{measurement}={value} outside [{low}, {high}]")
        if self.fault == "refuses_the_edge" and value in (low, high):
            raise P.Refused("OUT_OF_DOMAIN", None, "edge rejected")
        return P.Decision(uuid.uuid4().hex, "PASS", action_type, principal, {})

    def evaluate_degraded(self, state, measurement, *, principal, action_type):
        verdict = self.degraded[state]
        if (self.fault, state) in (("admits_unknown", P.E_UNKNOWN), ("admits_stale", P.E_STALE),
                                   ("admits_contradiction", P.E_CONTRADICTORY)):
            verdict = "FLAG"
        if self.fault == "vetoes_contradiction" and state == P.E_CONTRADICTORY:
            verdict = "HARD_VETO"
        if self.fault == "defaults_a_missing_limit" and (state, measurement) == (P.E_MISSING, "limit"):
            verdict = "PASS"            # a default stood in for the measurement
        return self._decide(verdict, principal, action_type)

    def evaluate_at_confidence(self, intent, step, *, principal, action_type):
        base = self._verdict(intent, principal)
        ladder = ("PASS", "PASS", "FLAG", "HOLD") if base == "PASS" else (base,) * 4
        if self.fault == "confidence_widens" and intent == P.ADMISSIBLE:
            ladder = ("PASS", "FLAG", "PASS", "PASS")
        if self.fault == "low_confidence_rescues" and intent == P.NEEDS_APPROVAL:
            ladder = ("HOLD", "HOLD", "FLAG", "FLAG")
        return self._decide(ladder[step], principal, action_type)

    def commit(self, decision, *, action_type=None):
        verdict, born = self.made[decision.decision_id]
        if verdict == "HOLD":
            over = self.now - born >= self.bounds.get(P.B_TAU_K, float("inf"))
            if over and self.fault == "hold_executes_after_window":
                return P.Committed(decision.decision_id)
            ended = over and self.fault != "hold_never_ends"
            raise P.Refused(P.R_INVALID_DISPOSITION, "HARD_VETO" if ended else "HOLD")
        if verdict == "HARD_VETO":
            raise P.Refused(P.R_INVALID_DISPOSITION, "HARD_VETO")
        landed = self._landed()
        gone = decision.principal in landed and self.fault != "revocation_spares_grants"
        if gone or (landed and self.fault == "revocation_blocks_grants"):
            raise P.Refused(P.R_STANDING_REVOKED, "HARD_VETO")
        return P.Committed(decision.decision_id)

    def revoke(self, principal):
        if self.fault != "revocation_inert":
            self.revoked[principal] = self.now


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
    ("revocation_spares_grants", "PX-CT-R3-002"),
    ("credential_never_expires", "PX-CT-R3-006"),
    ("accepts_stale_request", "PX-VEC-6-03"),
    ("accepts_revoked_key", "PX-VEC-6-04"),
    ("hold_executes_after_window", "PX-REG-STATE-024"),
    ("admits_unknown", "PX-REG-STATE-001"),
    ("admits_stale", "PX-REG-STATE-002"),
    ("admits_contradiction", "PX-REG-STATE-004"),
    ("defaults_a_missing_limit", "PX-REG-STATE-010"),
    ("confidence_widens", "PX-REG-STATE-013"),
    ("low_confidence_rescues", "PX-REG-STATE-015"),
    ("admits_out_of_domain", "PX-REG-STATE-025"),
    ("refuses_the_edge", "PX-REG-STATE-025"),            # the declared domain is not the one enforced
])
def test_each_property_check_detects_its_fault_and_only_that_one(fault, check):
    got = _checks(fault)
    assert [c for c, state in got.items() if state != "PASS"] == [check]
    assert got[check] == "FAIL"


@pytest.mark.parametrize("fault,check", [
    ("holds_malformed", "PX-CT-R3-001"),                 # suspended is not rejected
    ("revocation_inert", "PX-CT-R3-003"),                # nothing to isolate
    ("hold_never_ends", "PX-REG-STATE-024"),             # not executable is not rejected
    ("vetoes_contradiction", "PX-REG-STATE-004"),        # RFC-2 §2.5 names HOLD, not a veto
    ("holds_out_of_domain", "PX-REG-STATE-025"),         # closed, but not rejected explicitly
])
def test_a_property_check_does_not_conclude_on_a_half_observation(fault, check):
    assert _checks(fault)[check] == "INCONCLUSIVE"


def test_the_domain_check_needs_a_declared_domain_and_reads_only_consistency():
    """REG-STATE-025 prescribes no domain. A port that declares none gets
    ADAPTER_REQUIRED; a port that declares another domain is read against that one."""
    class NoDomain(_Governed):
        domains = {}
    got = {r.vector_id: r for r in PortAdapter(NoDomain()).run_checks()}["PX-REG-STATE-025"]
    assert got.status.value == "ADAPTER_REQUIRED" and "no admissible domain" in got.gap_note

    class Wider(_Governed):
        domains = {"load": (-1.0, 2.0)}
    got = {r.vector_id: r for r in PortAdapter(Wider()).run_checks()}["PX-REG-STATE-025"]
    assert got.status.value == "PASS" and "load in [-1, 2]" in got.details
    assert "load=3.5" in got.details and "load=-2.5" in got.details


@pytest.mark.parametrize("domains", [{"": (0, 1)}, {"load": (0, 1, 2)}, {"load": (1.0, 0.0)},
                                     {"load": (0.0, float("inf"))}, {"load": (False, 1)}])
def test_a_port_declares_its_domains_well_formed(domains):
    class Bad(_Governed): pass
    Bad.domains = domains
    with pytest.raises(ValueError):
        PortAdapter(Bad())


# -- degraded evidence: read the disposition, not how it was reached -----------

_ON_EVIDENCE = {"PX-REG-STATE-001", "PX-REG-STATE-002", "PX-REG-STATE-004", "PX-REG-STATE-010"}


def test_the_missing_check_reports_each_measurement():
    class F(_Governed): pass
    F.fault = "defaults_a_missing_limit"
    got = {r.vector_id: r for r in PortAdapter(F()).run_checks()}["PX-REG-STATE-010"]
    # One measurement defaulted is enough to fail, and the result says which.
    assert got.status.value == "FAIL"
    assert "limit (PASS)" in got.details and "load (HARD_VETO)" in got.details


def test_a_declared_resolution_lifts_the_hold_on_contradiction():
    class Resolved(_Governed):
        contradiction_resolution = True
    assert _checks(base=Resolved)["PX-REG-STATE-004"] == "INCONCLUSIVE"


def test_a_check_on_evidence_does_not_run_when_the_port_cannot_degrade_it():
    class Partial(_Governed):
        degradations = {P.E_MISSING: ("load",)}
    got = {r.vector_id: r for r in PortAdapter(Partial()).run_checks()}
    assert {c for c in _ON_EVIDENCE if got[c].status.value == "ADAPTER_REQUIRED"} \
        == _ON_EVIDENCE - {"PX-REG-STATE-010"}
    assert "port cannot make evidence: stale" in got["PX-REG-STATE-002"].gap_note


def test_an_unchanged_disposition_passes_the_ladder_and_says_so():
    class Deaf(_Governed):
        def evaluate_at_confidence(self, intent, step, **kw):
            return self._decide(self._verdict(intent, kw["principal"]), kw["principal"],
                                kw["action_type"])
    got = {r.vector_id: r for r in PortAdapter(Deaf()).run_checks()}["PX-REG-STATE-013"]
    assert got.status.value == "PASS" and "it did not change" in got.details


@pytest.mark.parametrize("change", [
    dict(degradations={"rumour": ("load",)}),             # not an epistemic state of RFC-2 §2.5
    dict(degradations={P.E_STALE: ()}),                   # no measurement named
    dict(confidence_steps=1),                             # one level is not a ladder
])
def test_a_port_says_precisely_what_evidence_it_can_degrade(change):
    Bad = type("Bad", (_Governed,), change)
    with pytest.raises(ValueError):
        PortAdapter(Bad())


# -- declared bounds: the harness sets no duration -----------------------------

_AT_A_BOUND = {"PX-CT-R3-002", "PX-CT-R3-006", "PX-VEC-6-03", "PX-VEC-6-04", "PX-REG-STATE-024"}


def test_a_revocation_that_lands_after_the_declared_bound_fails():
    got = _checks("revocation_late")
    # Still executable just past the bound the subject declares.
    assert got["PX-CT-R3-002"] == "FAIL"
    # And nothing to isolate yet for the isolation check.
    assert got["PX-CT-R3-003"] == "INCONCLUSIVE"


def test_a_revocation_that_does_nothing_fails_at_the_bound():
    assert _checks("revocation_inert")["PX-CT-R3-002"] == "FAIL"


def test_without_a_declared_bound_the_check_does_not_run():
    class Undeclared(_Governed):
        bounds = {}
    adapter = PortAdapter(Undeclared())
    got = {r.vector_id: r for r in adapter.run_checks()}
    assert {c for c, r in got.items() if r.status.value == "ADAPTER_REQUIRED"} == _AT_A_BOUND
    assert all("no bound declared for" in got[c].gap_note for c in _AT_A_BOUND)
    # The checks that need no bound are untouched.
    assert {r.status.value for c, r in got.items() if c not in _AT_A_BOUND} == {"PASS"}


def test_each_check_at_a_bound_names_a_bound_the_port_can_declare():
    assert {c for c, s in CHECKS.items() if s.bounds} == _AT_A_BOUND
    assert all(s.bounds <= P.ALL_BOUNDS for s in CHECKS.values())


def test_a_fail_degraded_deployment_is_not_judged_on_the_default():
    class Degraded(_Governed):
        exhaustion_policy = "fail-degraded"
    assert _checks(base=Degraded)["PX-REG-STATE-024"] == "INCONCLUSIVE"


@pytest.mark.parametrize("change", [
    dict(bounds={"patience": 3.0}),                       # not a bound the harness knows
    dict(bounds={P.B_TAU_K: -1.0}),
    dict(bounds={P.B_TAU_K: float("inf")}),
    dict(clock_mode=""),                                  # clock declared, mode not said
    dict(exhaustion_policy="whatever"),
])
def test_a_port_states_its_bounds_and_its_clock_precisely(change):
    Bad = type("Bad", (_Governed,), change)
    with pytest.raises(ValueError):
        PortAdapter(Bad())


class _OneStepHolding(_Fixture):
    """One-step double that suspends, with a clock and a declared tau_k.
    Fault `approves_on_timeout`: the suspended call runs once the window ends."""
    capabilities = _Fixture.capabilities | {P.CLOCK}
    bounds = {P.B_TAU_K: 30.0}
    clock_mode = "simulated"

    def reset(self):
        super().reset()
        self.held = []

    def evaluate(self, intent, **kw):
        d = super().evaluate(intent, **kw)
        if intent == P.NEEDS_APPROVAL:
            self.held.append(d.decision_id)
        return d

    def elapse_past(self, bound):
        if bound == P.B_TAU_K and self.fault == "approves_on_timeout":
            self.journal += self.held
        return self.bounds[bound] + 0.001


def test_a_hold_that_runs_when_its_window_ends_is_caught_by_its_effect():
    class F(_OneStepHolding): pass
    F.fault = "approves_on_timeout"
    got = {r.vector_id: r.status.value for r in PortAdapter(F()).run_checks()}
    assert got["PX-REG-STATE-024"] == "FAIL"


def test_with_no_separate_commit_no_effect_alone_does_not_prove_a_rejection():
    got = {r.vector_id: r.status.value for r in PortAdapter(_OneStepHolding()).run_checks()}
    assert got["PX-REG-STATE-024"] == "INCONCLUSIVE"


# -- "no effect" is read after the declared effect window ----------------------

class _Lagging(_Fixture):
    """One-step double whose effects land `effect_window` seconds after the call."""
    capabilities = _Fixture.capabilities | {P.CLOCK}
    effect_window = 2.0
    clock_mode = "simulated"

    def reset(self):
        super().reset()
        self.now, self.pending = 0.0, []

    def evaluate(self, intent, **kw):
        before = len(self.journal)
        d = super().evaluate(intent, **kw)
        self.pending += [(self.now + self.effect_window, token) for token in self.journal[before:]]
        del self.journal[before:]
        return d

    def elapse_past(self, bound):
        assert bound == P.EFFECT_WINDOW
        self.now += self.effect_window + 0.001
        self.journal += [token for due, token in self.pending if due <= self.now]
        self.pending = [(due, token) for due, token in self.pending if due > self.now]
        return self.effect_window + 0.001


def _lagging(fault):
    class F(_Lagging): pass
    F.fault = fault
    return {r.vector_id: r.status.value for r in PortAdapter(F()).run_probes()}


def test_an_effect_that_lands_late_is_still_counted():
    # Read at once, the journal would be empty and the allowed call would show no effect.
    assert set(_lagging(None).values()) == {"PASS"}


def test_a_late_effect_after_a_refusal_is_caught():
    # Read at once, the journal would be empty and the refusal would look clean.
    assert _lagging("executes_on_refusal")["HX-EFFECT-001"] == "FAIL"


def test_a_port_with_an_effect_window_must_be_able_to_let_it_pass():
    class NoClock(_Fixture):
        effect_window = 2.0
    with pytest.raises(ValueError):
        PortAdapter(NoClock())


# -- every result says where it observed and what it does not establish --------

def test_every_scenario_says_where_it_observes_and_what_it_does_not_establish():
    from harness.scenarios import PHASES
    for vid, scenario in {**SCENARIOS, **PROBES, **CHECKS}.items():
        assert scenario.at in PHASES, vid
        assert scenario.not_observed and all(scenario.not_observed), vid
    # No probe may claim more than its journal and its window let it see.
    assert all("journal" in s.not_observed[0] and "effect window" in s.not_observed[1]
               for s in PROBES.values())


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
    # Two proposals the frozen RFCs do not state: CT-R3-003, and REG-STATE-025
    # (declared admissible domain, draft RFC-2 v0.2 §1.4 of 2026-11-23, not ratified).
    assert sorted(r for r, state in status.items() if state == "RESERVED") == ["CT-R3-003", "REG-STATE-025"]


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
    ran = {k: r.status.value for k, r in got.items() if r.status.value != "ADAPTER_REQUIRED"}
    assert ran == {"PX-CT-R3-001": "FAIL", "PX-CT-R3-003": "PASS", "PX-VEC-6-02": "PASS",
                   "PX-REG-STATE-001": "PASS", "PX-REG-STATE-010": "PASS"}
    # Since the finiteness guard, a measurement that is not a number is held, not admitted.
    # The kernel declares no bound: none of the checks at a bound runs on it.
    assert _AT_A_BOUND <= set(got) - set(ran)
    assert "Revocation propagation latency not declared" in got["PX-CT-R3-002"].gap_note
    # The kernel admits a blank credential. Its own gap register says so.
    assert "CT-R3-001" in got["PX-CT-R3-001"].gap_note
    # A failing check marks the family, whatever else passes in it.
    assert view["families"]["EGP-01"]["PASS"] == 1
    assert view["families"]["EGP-01"]["state"] == "has_fail"
    # 19 before 23 November 2026; CT-R0-003, CT-R5-001, CT-R5-004 and CT-R7-002
    # got a neutral scenario the reference kernel passes.
    assert (view["index"]["PASS"], view["index"]["FAIL"]) == (23, 1)


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


def test_bundle_verdict_carries_the_residue_of_each_observed_result():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import make_evidence_bundle as B
    adapter, results, checks, view = _view_with_checks(_Governed())
    report = R.generate_report(adapter, results)
    report["property_checks"] = {"exercises": _EXERCISES, "results": [R.asdict(r) for r in checks]}
    every = {**SCENARIOS, **PROBES, **CHECKS}
    report["observation"] = {
        "conditions": {"effect_window_s": 0.0, "clock_mode": "simulated",
                       "declared_bounds_s": dict(_Governed.bounds), "exhaustion_policy": None},
        "checks": {vid: {"at": s.at, "not_observed": list(s.not_observed)}
                   for vid, s in every.items()}}
    verdict = B.build_verdict(json.loads(json.dumps(report, default=str)))
    kept = verdict["observation"]["checks"]
    observed = {r.vector_id for r in results + checks
                if r.status.value in ("PASS", "FAIL", "INCONCLUSIVE")}
    assert set(kept) == observed and set(CHECKS) <= observed
    assert kept["PX-CT-R3-001"]["not_observed"][0] == "that the rejection comes before evaluation"
    assert verdict["observation"]["conditions"]["declared_bounds_s"][P.B_TAU_K] == 120.0


# -- P1 / P2 (review of 2026-11-23): what the report says about FLAG conditions --

def test_report_states_flag_conditions_are_port_declared_and_what_an_ack_proves(tmp_path, capsys):
    """P1: a recorded FLAG condition is the port's own declaration, acknowledged by the
    port; P2: a recorded acknowledgement proves neither effective dispatch outside the
    process nor external supervision. Both statements travel with every report, and
    with the bundle verdict, whether or not a check went forward on a FLAG."""
    from harness.__main__ import main
    out = tmp_path / "report.json"
    code = main(["--port", "harness.ports.reference:ReferencePort", "--output", str(out)])
    report = json.loads(out.read_text())
    adm = report["admission"]
    assert adm["flag_conditions_provenance"].startswith("port-declared and port-acknowledged")
    assert "not conditions of any supervised deployment" in adm["flag_conditions_provenance"]
    ack = adm["what_an_acknowledgement_establishes"]
    assert "does not establish that the dispatch took effect outside this process" in ack
    assert "external production supervision" in ack
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import make_evidence_bundle as B
    verdict = B.build_verdict(json.loads(json.dumps(report, default=str)))
    assert verdict["admission"]["flag_conditions_provenance"] == adm["flag_conditions_provenance"]
    assert verdict["admission"]["what_an_acknowledgement_establishes"] == ack
    assert code in (0, 2, 3)


# -- rule of 23 November 2026: rows no port can adapt -------------------------
# Standard author's decision (15:07 UTC, option A): a row no ratified text
# specifies, a row the implementer declares outside the perimeter with a signed
# reason, and a row a passing property check exercised are listed, with their
# reason, and stay out of the exit code. The rule is dated; it reinterprets no
# earlier report. The two missing primitives stay IMPLEMENTATION_GAP until 5.8.0.

from harness.adapter import HARNESS_GAP, OUT_OF_EXIT_CODE, SUPERSEDED, reserved_rows


def test_reserved_and_superseded_rows_are_not_specified_on_every_subject():
    got = {r.vector_id: r for r in PortAdapter(TemplatePort()).run_all()}
    reserved = set(reserved_rows()) & set(R.VECTORS)
    assert len(reserved) == 25 and len(SUPERSEDED) == 3 and not reserved & set(SUPERSEDED)
    assert {got[v].status.value for v in reserved | set(SUPERSEDED)} == {"NOT_SPECIFIED"}
    assert all("RESERVED in VECTORS.md" in got[v].gap_note and "nothing to test" in got[v].gap_note
               for v in reserved)
    for v, successor in SUPERSEDED.items():
        assert f"superseded by {successor}" in got[v].gap_note and "RFC-4 v0.3" in got[v].gap_note
    # A row the RFCs specify and no scenario covers keeps the harness gap, counted.
    assert got["CT-R3-001"].status.value == "ADAPTER_REQUIRED" and got["CT-R3-001"].gap_note == HARNESS_GAP
    # A reserved row with a neutral scenario is run, not set aside (none today).
    assert not (reserved | set(SUPERSEDED)) & set(SCENARIOS)


def test_a_port_may_declare_a_registered_row_outside_its_perimeter():
    decl = {"declared_by": "the author of the runtime (test fixture)", "reason": "no credential object"}

    class F(TemplatePort):
        not_in_perimeter = {"CT-R3-001": decl}
    adapter = PortAdapter(F())
    got = {r.vector_id: r for r in adapter.run_all()}
    assert got["CT-R3-001"].status.value == "NOT_IN_PERIMETER"
    assert got["CT-R3-001"].gap_note.startswith("not_in_perimeter on CT-R3-001, declared by the author")
    # The check that exercises the same row carries the same declaration.
    checks = {r.vector_id: r.status.value for r in adapter.run_checks()}
    assert checks["PX-CT-R3-001"] == "NOT_IN_PERIMETER"

    class Neutral(TemplatePort):
        not_in_perimeter = {"CT-R0-003": decl}
    with pytest.raises(ValueError, match="neutral scenario"):
        PortAdapter(Neutral()).run_all()

    class Unsigned(TemplatePort):
        not_in_perimeter = {"CT-R3-001": {"declared_by": "x", "reason": " "}}
    with pytest.raises(ValueError, match="not_in_perimeter"):
        PortAdapter(Unsigned()).run_all()


def _folded(status, details="d"):
    port = TemplatePort()
    adapter = PortAdapter(port)
    results = adapter.run_all()
    check = R.ConformanceResult("PX-CT-R0-005", R.ReportingState(status), port.interface_mode, 2, details=details)
    return {r.vector_id: r for r in PortAdapter.fold_checks(results, [check])}, {r.vector_id: r for r in results}


def test_a_row_exercised_by_a_passing_check_is_reported_by_it():
    folded, before = _folded("PASS", "the more restrictive disposition governed")
    assert before["CT-R0-005"].status.value == "ADAPTER_REQUIRED"
    r = folded["CT-R0-005"]
    assert r.status.value == "EXERCISED_BY_CHECK"
    assert r.details.startswith("exercised by PX-CT-R0-005 PASS: the more restrictive")
    # Every other row is the same object, untouched.
    assert all(folded[v] is before[v] for v in before if v != "CT-R0-005")


def test_a_row_whose_check_fails_fails_and_an_unrun_check_leaves_the_gap():
    folded, _ = _folded("FAIL", "a weaker disposition governed")
    assert folded["CT-R0-005"].status.value == "FAIL"
    assert "PX-CT-R0-005 FAIL" in folded["CT-R0-005"].details
    folded, _ = _folded("ADAPTER_REQUIRED")
    r = folded["CT-R0-005"]
    assert r.status.value == "ADAPTER_REQUIRED" and r.gap_note.startswith(HARNESS_GAP)
    assert "PX-CT-R0-005 ADAPTER_REQUIRED" in r.gap_note


def test_fold_touches_only_a_harness_gap():
    # A declared gap, a pass, a not-applicable row: the check does not replace them.
    port = ReferencePort()
    adapter = PortAdapter(port)
    results = adapter.run_all()
    check = R.ConformanceResult("PX-CT-R0-005", R.ReportingState.PASS, port.interface_mode, 2, details="x")
    folded = {r.vector_id: r for r in PortAdapter.fold_checks(results, [check])}
    before = {r.vector_id: r for r in results}
    assert before["CT-R0-005"].status.value == "IMPLEMENTATION_GAP"     # the reference kernel declares it
    assert all(folded[v] is before[v] for v in before)


def test_the_exit_code_counts_only_what_can_be_tested(tmp_path):
    """The rows out of the exit code are listed in the report, each with its
    reason; the code and conformance_status count FAIL, INCONCLUSIVE,
    IMPLEMENTATION_GAP and ADAPTER_REQUIRED, as before."""
    from harness.__main__ import main
    out = tmp_path / "report.json"
    code = main(["--port", "harness.ports.template:TemplatePort", "--checks", "--output", str(out)])
    report = json.loads(out.read_text())
    rule = report["exit_code_rule"]
    assert rule["date"] == "2026-11-23" and rule["statuses_out_of_exit_code"] == list(OUT_OF_EXIT_CODE)
    rows = rule["rows_out_of_exit_code"]
    assert len(rows) == 28 and {v["status"] for v in rows.values()} == {"NOT_SPECIFIED"}
    assert all(v["reason"] for v in rows.values())
    # An empty port still has 33 rows it cannot run: code 2, INCOMPLETE, nothing hidden.
    assert code == 2 and report["conformance_status"] == "INCOMPLETE"
    assert report["summary"]["ADAPTER_REQUIRED"] == 33 and rule["counted_in_exit_code"]["ADAPTER_REQUIRED"] == 33
    # The row set is whole: every registered vector is in the results.
    assert {r["vector_id"] for r in report["results"]} == set(R.VECTORS)


def test_exit_code_zero_needs_every_counted_row_passed():
    """Fixture, not a runtime: a port whose every counted row passes. The rule
    gives 0 only then; a single gap on a specified row gives 2."""
    from harness.__main__ import main
    results_all = {r.vector_id: r for r in PortAdapter(TemplatePort()).run_all()}
    counted = [v for v, r in results_all.items() if r.status.value in ("ADAPTER_REQUIRED", "IMPLEMENTATION_GAP")]
    assert len(counted) == 33 and len(results_all) == 61
    summary = {s.value: 0 for s in R.ReportingState}
    for v, r in results_all.items():
        summary[r.status.value] += 1
    def code(s):
        return 1 if s["FAIL"] else 3 if s["INCONCLUSIVE"] else 2 if s["IMPLEMENTATION_GAP"] or s["ADAPTER_REQUIRED"] else 0
    assert code(summary) == 2
    summary["ADAPTER_REQUIRED"] = 0
    assert code(summary) == 0                 # NOT_SPECIFIED rows alone do not hold the code at 2
    summary["IMPLEMENTATION_GAP"] = 1
    assert code(summary) == 2                 # one declared gap on a specified row does
