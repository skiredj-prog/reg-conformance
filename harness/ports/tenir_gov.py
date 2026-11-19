"""Port over the TENIR-Gov runtime (package `tenir-governance`).

What is under test: `DualKernelGovernor` as shipped, built from the shipped
`ScoringKernelAdapter(TenirKernel())` and `TransitionMembrane`, in process,
with the default composition policy and the default (non Profile S) commit
path. Nothing in TENIR-Gov is patched or mocked. The installed distribution is
the subject: pin it and pass its version and commit on the command line.

What the port adds: one dispatch provider that appends to a journal owned by
the port. It is the only way an effect can occur, and the journal is what
`observed_effects` reads.

Shape of the boundary: two steps. `adjudicate` admits or refuses and claims
the operation; `dispatch_and_execute` crosses the boundary and calls the
provider.

Native verdicts are already the four REG dispositions (PASS, FLAG, HOLD,
HARD_VETO). The port passes them through unchanged. It does not turn a native
FLAG into a PASS.

Intent mapping (PROVISIONAL, written by the harness author from the runtime's
own behaviour; to be confirmed or corrected by the runtime's author):
    ADMISSIBLE      best-case measured inputs, no resource in scope
    INADMISSIBLE    structure outside bounds (S below the tau floor)
    NO_STANDING     authority measured at 0.0
    DENIED          amount above the registered budget (membrane invariant I8)
    NEEDS_APPROVAL  best-case inputs, amount at 90 % of the budget: the
                    composition policy escalates this to HOLD
    INVARIANT_VIOLATED  best-case inputs, amount above the registered budget
                    (membrane invariant I8); the same inputs as DENIED
    OUT_OF_SCOPE    not mapped. Scope is an L1 concern and TENIR-Gov does not
                    read Agent.capabilities; mapping it there gave an appearance
                    of coverage (author's decision 1, 19 November 2026). CT-R3-007
                    is declared outside the perimeter instead (`not_in_perimeter`).

Degraded evidence (DEGRADE), on each of the seven measurements this port
supplies to `adjudicate` (pressure, velocity, capacity, option_space,
authority, context_fit, evidence_quality), same PROVISIONAL caveat:
    MISSING         the measurement is not supplied
    UNKNOWN         the measurement is supplied as a value that is not a
                    number (NaN): it arrives and says nothing of the state
`irreversibility_materiality` is never supplied by this port: the governor
takes its own default for it.

Confidence (CONFIDENCE): `evidence_quality` at 1.0, 0.75, 0.5, 0.25, 0.0, the
other inputs unchanged. `adjudicate` takes one value per measurement, with no
age and no second reading: STALE and CONTRADICTORY are not declared.

Combinations (COMBINE), each on two independent inputs of one adjudication:
    NO_STANDING + NEEDS_APPROVAL    authority at 0.0 and 90 % of the budget
    INADMISSIBLE + NEEDS_APPROVAL   structure outside bounds and 90 % of the budget

Refusal mapping at the boundary (PROVISIONAL, same caveat):
    "payload does not match the payload authorized"        -> BINDING_VIOLATION
    "operation is in state failed|hold|escalated|created"  -> INVALID_DISPOSITION
    duplicate idempotency key at adjudication              -> NONCE_REPLAY
Any other refusal is raised under its own code and satisfies no neutral vector.

Not declared, because the default path of this runtime has no such primitive:
    REVOKE       no revocation of a principal's standing after a verdict
    STALE_GRANT  an admitted operation carries no validity window
    STATE_DRIFT  no policy or state version is bound at verdict and re-checked
    RECEIPTS     ledger entries are hash-chained, not signed
    MALFORMED_CREDENTIAL (intent)  the governor takes no credential: standing
                 arrives as a measured authority score and an agent
                 identifier asserted by the caller
    CLOCK and every bound  `adjudicate` enters a HOLD without a tau_k ("Do not
                 invent a tau_k here", says its source) and takes none from
                 the caller, so the HOLD carries no window that could pass.
                 The default path has no credential lifetime, no request
                 timestamp and no revocation either.

Effect window: zero. The provider is called inside `dispatch_and_execute`,
before it returns.
"""
from __future__ import annotations

import copy
import uuid

from .. import port as P

_BEST = dict(pressure=0.2, velocity=0.2, capacity=0.9, authority=0.9,
             context_fit=1.0, evidence_quality=1.0, option_space=0.9)
_BUDGET = "reg-harness-budget"
_CAPACITY = 100.0
# intent -> (overrides of _BEST, amount charged to the budget or None)
_INPUTS = {
    P.ADMISSIBLE:     ({}, None),
    P.INADMISSIBLE:   (dict(pressure=0.95, velocity=0.90, capacity=0.10), None),
    P.NO_STANDING:    (dict(authority=0.0), None),
    P.DENIED:         ({}, _CAPACITY * 5),
    P.NEEDS_APPROVAL: ({}, _CAPACITY * 0.9),
    P.INVARIANT_VIOLATED: ({}, _CAPACITY * 5),
}
# Levels of confidence in the evidence, from full down.
_QUALITY = (1.0, 0.75, 0.5, 0.25, 0.0)
_NOT_ADMITTED = ("failed", "hold", "escalated", "created")



def _flag_conditions(result) -> tuple:
    """The conditions a FLAG states, as the runtime reports them.

    tenir-governance 5.7.5 copies the conditions its policy declares into
    ``flag_conditions`` (empty by default); 5.7.0 has no such field. The port
    reports what it observes and adds nothing.
    """
    if result.get("composed_decision") != "FLAG":
        return ()
    return tuple(str(c) for c in (result.get("flag_conditions") or ()))

class _JournalProvider:
    """The only executor. One journal line per call the runtime makes."""

    def __init__(self):
        self.journal = []

    def execute(self, idempotency_key, action_type, amount, agent_id, metadata=None):
        from tenir_governance.operations.provider import DispatchResult, ProviderOutcome
        self.journal.append(idempotency_key)
        return DispatchResult(outcome=ProviderOutcome.CONFIRMED,
                              provider_reference=f"journal-{len(self.journal)}")

    def reconcile(self, idempotency_key, provider_reference=""):
        from tenir_governance.operations.provider import ReconciliationResult
        return ReconciliationResult(resolved=False)


class TenirGovPort(P.RuntimePort):
    name = "tenir-governance"
    interface_mode = "port:tenir-governance"
    evidence_level = 2
    capabilities = frozenset({P.EVALUATE, P.COMMIT, P.NONCE, P.MANIFEST,
                              P.TENIR_SCORE, P.EFFECTS, P.COMBINE, P.DEGRADE, P.CONFIDENCE})
    intents = frozenset(_INPUTS)
    degradations = {P.E_MISSING: tuple(_BEST), P.E_UNKNOWN: tuple(_BEST)}
    confidence_steps = len(_QUALITY)
    combinations = frozenset({frozenset({P.NO_STANDING, P.NEEDS_APPROVAL}),
                              frozenset({P.INADMISSIBLE, P.NEEDS_APPROVAL})})
    not_applicable = {"C4": "No transport layer: the runtime is driven in process."}
    not_in_perimeter = {"CT-R3-007": {
        "declared_by": "the author of tenir_governance (decision 1, 19 November 2026)",
        "reason": ("scope is an L1 concern; TENIR-Gov does not read Agent.capabilities")}}

    def __init__(self):
        import tenir_governance
        self.subject_version = tenir_governance.__version__
        self.reset()

    def reset(self):
        from tenir_governance.composition import DualKernelGovernor, ScoringKernelAdapter
        from tenir_governance.membrane import MembraneState, TransitionMembrane
        from tenir_governance.objects import Resource
        from tenir_kernel.kernel import TenirKernel

        state = self._state = MembraneState()
        state.register_resource(Resource(resource_id=_BUDGET, capacity=_CAPACITY))
        self._provider = _JournalProvider()
        self._scoring = ScoringKernelAdapter(TenirKernel())
        self._gov = DualKernelGovernor(self._scoring, TransitionMembrane(state),
                                       provider=self._provider)

    # -- primitives ---------------------------------------------------------
    def evaluate(self, intent, *, principal, action_type, nonce=None):
        return self.evaluate_combined((intent,), principal=principal,
                                      action_type=action_type, nonce=nonce)

    def evaluate_combined(self, intents, *, principal, action_type, nonce=None):

        overrides, amounts = {}, []
        for intent in intents:
            changed, amount = _INPUTS[intent]
            overrides.update(changed)
            if amount:
                amounts.append(amount)
        if len(amounts) > 1:
            raise ValueError("one adjudication carries one amount")
        amount = amounts[0] if amounts else None
        return self._adjudicate({**_BEST, **overrides}, amount, principal=principal,
                                action_type=action_type, nonce=nonce)

    def evaluate_degraded(self, state, measurement, *, principal, action_type):
        measured = dict(_BEST)
        if state == P.E_MISSING:
            del measured[measurement]
        else:
            measured[measurement] = float("nan")
        return self._adjudicate(measured, None, principal=principal, action_type=action_type)

    def evaluate_at_confidence(self, intent, step, *, principal, action_type):
        overrides, amount = _INPUTS[intent]
        measured = {**_BEST, **overrides, "evidence_quality": _QUALITY[step]}
        return self._adjudicate(measured, amount, principal=principal, action_type=action_type)

    def _adjudicate(self, measured, amount, *, principal, action_type, nonce=None):
        from tenir_governance.objects import Passage

        key = nonce or f"op-{uuid.uuid4().hex}"
        passage = Passage(agent_id=principal, action_type=action_type,
                          amount=amount or 0.0, idempotency_key=key)
        budget = dict(resource_id=_BUDGET, amount=amount) if amount else {}
        result = self._gov.adjudicate(passage, payload={"action_type": action_type},
                                      **measured, **budget)
        if str(result.get("composed_rationale", "")).startswith("Duplicate operation blocked"):
            raise P.Refused(P.R_REPLAY, result.get("composed_decision"),
                            result["composed_rationale"])
        return P.Decision(key, result["composed_decision"], action_type, principal,
                          {"result": result, "amount": amount},
                          conditions=_flag_conditions(result))

    def commit(self, decision, *, action_type=None):
        amount = decision.raw.get("amount")
        args = (_BUDGET, amount) if amount else ()
        result = self._gov.dispatch_and_execute(
            decision.decision_id, *args,
            payload={"action_type": action_type or decision.action_type})
        if result.get("dispatched"):
            return P.Committed(decision.decision_id, result)
        reason = str(result.get("reason", ""))
        state = str(result.get("operation_state", ""))
        if result.get("tau_k_expired"):
            raise P.Refused(P.R_EXPIRED, result.get("composed_decision"), reason)
        if reason.startswith("QUARANTINE_LOCK is active"):
            raise P.Refused(P.R_STATE_DRIFT, None, reason)
        if "does not match the payload authorized" in reason:
            raise P.Refused(P.R_BINDING, None, reason)
        if reason.startswith("Cannot dispatch") and state in _NOT_ADMITTED:
            raise P.Refused(P.R_INVALID_DISPOSITION, decision.disposition, reason)
        raise P.Refused(f"NATIVE:{state or 'unknown'}", None, reason)

    def manifest_intact(self):
        return bool(self._gov.ledger.verify_chain())

    def tampered_manifest_intact(self):
        probe = copy.deepcopy(self._gov.ledger)
        probe.entries[0].decision = "TAMPERED"
        return bool(probe.verify_chain())

    def tenir_score(self, Pv, V, K):
        best = {k: v for k, v in _BEST.items() if k not in ("pressure", "velocity", "capacity")}
        r = self._scoring.adjudicate(pressure=Pv, velocity=V, capacity=K, **best)
        return {"s_score": r["s_score"], "decision": r["decision"]}

    def observed_effects(self, decision):
        return self._provider.journal.count(decision.decision_id)


# The bound this deployment declares for a HOLD's human resolution, and its
# source. It is the deployment's declaration, written here because the port
# builds the deployment; TENIR-Gov invents none.
_TAU_K = 1.0
_TAU_K_SOURCE = "REG harness deployment: declared for the run, not derived from an SLA"


class TenirGovTauKPort(TenirGovPort):
    """TENIR-Gov with a policy that declares τ_K (needs 5.7.1 or later).

    What is under test: the same governor as TenirGovPort, built with
    `CompositionPolicy(hold_tau_k_seconds=1.0, hold_tau_k_source=...)`. That
    policy field is the only difference. On a subject that has no such field
    (5.7.0 and earlier) the port refuses to start: there is then no public
    path by which a policy declares τ_K (issue #140, case C2a).

    Additional mapping (PROVISIONAL, same caveat as TenirGovPort):
        NEEDS_APPROVAL  best-case inputs with `evidence_quality` unknown (NaN):
                        the scoring kernel returns no decision and the
                        governor holds, fail-closed, pending evidence. The
                        budget-driven HOLD of TenirGovPort is not used: on
                        5.7.x no answer can lead it to admission (its
                        re-adjudication holds again, or is vetoed by its own
                        reservation, issue #141), so it cannot serve as the
                        control a late answer is compared with.
        approve         `resolve_hold` with the original passage and the
                        evidence supplied (`evidence_quality` = 1.0): the
                        runtime's own "fresh evidence" answer to a HOLD.
        STATE_DRIFT     `lock_quarantine` between verdict and commit. It is
                        the governing-state change this runtime re-checks at
                        dispatch. It is not a policy epoch, which the runtime
                        does not have; a refusal under it is mapped to
                        STATE_DRIFT with no disposition, since the operation
                        stays RESERVED until the quarantine is released.
    Clock: real. `elapse_past` waits the bound and 50 ms more. Nothing runs
    on a schedule: the bound applies when the operation tries to advance.
    Exhaustion policy: TENIR-Gov fails closed on an exhausted τ_K; the
    deployment declares nothing else.
    """
    name = "tenir-governance (policy declares tau_k)"
    interface_mode = "port:tenir-governance+tau_k"
    capabilities = TenirGovPort.capabilities | {P.CLOCK, P.APPROVE, P.STATE_DRIFT}
    bounds = {P.B_TAU_K: _TAU_K}
    clock_mode = "real"
    exhaustion_policy = "fail-closed"

    def reset(self):
        from tenir_governance.composition import (
            CompositionPolicy, DualKernelGovernor, ScoringKernelAdapter)
        from tenir_governance.membrane import MembraneState, TransitionMembrane
        from tenir_governance.objects import Resource
        from tenir_kernel.kernel import TenirKernel

        try:
            policy = CompositionPolicy(hold_tau_k_seconds=_TAU_K, hold_tau_k_source=_TAU_K_SOURCE)
        except TypeError as e:
            raise RuntimeError(
                f"tenir-governance {self.subject_version}: the composition policy has no "
                f"hold_tau_k_seconds field, so no deployment can declare tau_k ({e})") from e
        state = self._state = MembraneState()
        state.register_resource(Resource(resource_id=_BUDGET, capacity=_CAPACITY))
        self._provider = _JournalProvider()
        self._scoring = ScoringKernelAdapter(TenirKernel())
        self._gov = DualKernelGovernor(self._scoring, TransitionMembrane(state),
                                       policy=policy, provider=self._provider)
        self._passages = {}

    def evaluate_combined(self, intents, *, principal, action_type, nonce=None):
        if P.NEEDS_APPROVAL not in intents:
            return super().evaluate_combined(intents, principal=principal,
                                             action_type=action_type, nonce=nonce)
        # On this port NEEDS_APPROVAL is the evidence input alone (evidence_quality
        # unknown). The other intents of `combinations` act on other inputs
        # (authority, or pressure/velocity/capacity), so they combine without
        # undoing it. They carry no amount.
        overrides = {}
        for intent in intents:
            if intent == P.NEEDS_APPROVAL:
                continue
            changed, amount = _INPUTS[intent]
            if amount or "evidence_quality" in changed:
                raise ValueError(f"{intent} cannot be combined with NEEDS_APPROVAL on this port")
            overrides.update(changed)
        measured = {**_BEST, **overrides, "evidence_quality": float("nan")}
        return self._adjudicate(measured, None, principal=principal,
                                action_type=action_type, nonce=nonce)

    def _adjudicate(self, measured, amount, *, principal, action_type, nonce=None):
        d = super()._adjudicate(measured, amount, principal=principal,
                                action_type=action_type, nonce=nonce)
        self._passages[d.decision_id] = d
        return d

    def approve(self, decision):
        from tenir_governance.objects import Passage

        record = self._gov.registry.get(decision.decision_id)
        if record is None:
            raise P.Refused("NATIVE:not_found", None, decision.decision_id)
        passage = Passage(agent_id=record.agent_id, action_type=record.action_type,
                          amount=record.amount, idempotency_key=decision.decision_id,
                          passage_id=record.passage_id)
        result = self._gov.resolve_hold(decision.decision_id, passage=passage,
                                        payload={"action_type": decision.action_type},
                                        **_BEST)
        if result.get("tau_k_expired"):
            raise P.Refused(P.R_EXPIRED, result.get("composed_decision"), str(result.get("reason")))
        disposition = result.get("composed_decision")
        if disposition is None:
            raise P.Refused(f"NATIVE:{result.get('operation_state') or 'unknown'}", None,
                            str(result.get("reason")))
        return P.Decision(decision.decision_id, disposition, decision.action_type,
                          decision.principal, {"result": result, "amount": decision.raw.get("amount")},
                          conditions=_flag_conditions(result))

    def drift_state(self):
        self._gov.lock_quarantine("reg-harness", incident_id=f"drift-{uuid.uuid4().hex[:8]}")
        return "quarantine lock set"

    def elapse_past(self, bound):
        import time

        seconds = self.bounds[bound] if bound in self.bounds else self.effect_window
        time.sleep(seconds + 0.05)
        return seconds + 0.05
