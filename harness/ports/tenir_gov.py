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

Degraded evidence (DEGRADE), on each of the eight measurements this port
supplies to `adjudicate` (pressure, velocity, capacity, option_space,
authority, context_fit, evidence_quality, irreversibility_materiality), same
PROVISIONAL caveat:
    MISSING         the measurement is not supplied
    UNKNOWN         the measurement is supplied as a value that is not a
                    number (NaN): it arrives and says nothing of the state
`irreversibility_materiality` is the eighth measurement since the 5.7.7
candidate work (runtime author's decision C, 23 November 2026): the port
declares it per intent, like the seven others, instead of leaving it to the
governor's default. 5.7.0 and 5.7.6 default an omitted axis to 0.0 and admit on
it, so on those runtimes REG-STATE-010 now reads FAIL on this measurement: a
declared change of a recorded result, not a reinterpretation of it. The 5.7.7
candidate treats the omitted axis as UNKNOWN (HOLD). The values are the port's
provisional declarations: 0.1 for an attempt with no irreversible pathway, 0.6
for the attempt that needs approval (90 % of the budget), 0.8 for the attempts
that exceed the budget. None of them crosses the reference geometry's
irreversibility-authority boundary (materiality - authority <= 0.25) on its own.

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
             context_fit=1.0, evidence_quality=1.0, option_space=0.9,
             irreversibility_materiality=0.1)
_BUDGET = "reg-harness-budget"
_CAPACITY = 100.0
# intent -> (overrides of _BEST, amount charged to the budget or None)
_INPUTS = {
    P.ADMISSIBLE:     ({}, None),
    P.INADMISSIBLE:   (dict(pressure=0.95, velocity=0.90, capacity=0.10), None),
    P.NO_STANDING:    (dict(authority=0.0), None),
    P.DENIED:         (dict(irreversibility_materiality=0.8), _CAPACITY * 5),
    P.NEEDS_APPROVAL: (dict(irreversibility_materiality=0.6), _CAPACITY * 0.9),
    P.INVARIANT_VIOLATED: (dict(irreversibility_materiality=0.8), _CAPACITY * 5),
}
# Levels of confidence in the evidence, from full down.
_QUALITY = (1.0, 0.75, 0.5, 0.25, 0.0)
_NOT_ADMITTED = ("failed", "hold", "escalated", "created")


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
        try:
            result = self._gov.adjudicate(passage, payload={"action_type": action_type},
                                          **measured, **budget)
        except ValueError as exc:
            # Since the 5.7.7 candidate a malformed request raises
            # `InvalidArgumentError` (code INVALID_ARGUMENT) at the API boundary
            # instead of returning a HARD_VETO: an API-level refusal, never a
            # governance decision. Matched by code so that this port still loads
            # on 5.7.0 and 5.7.6, which have no such class.
            if getattr(exc, "code", None) == "INVALID_ARGUMENT":
                raise P.Refused("NATIVE:invalid_argument", None, str(exc)) from exc
            raise
        if str(result.get("composed_rationale", "")).startswith("Duplicate operation blocked"):
            raise P.Refused(P.R_REPLAY, result.get("composed_decision"),
                            result["composed_rationale"])
        return P.Decision(key, result["composed_decision"], action_type, principal,
                          {"result": result, "amount": amount})

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
