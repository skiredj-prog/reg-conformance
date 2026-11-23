"""Port over TENIR-Gov 5.7.6 (package `tenir-governance` 5.7.6, as distributed on
PyPI): the v0.7.0 `TenirGovPort`, plus the one thing the 5.7.6 caller contract
requires before a FLAG can admit anything.

CANDIDATE, not part of any released revision of reg-conformance. Mapping
PROVISIONAL, like the v0.7.0 port's: it must be reviewed independently and
confirmed or corrected by the runtime's author before any result obtained with it
is cited (author's decision of 22 November 2026, condition 1 of the HOLD on the
REG qualification of 5.7.6).

Why a port of its own. Since 5.7.6 a FLAG admits only when the deployment's
composition policy declares at least one condition (`CompositionPolicy.
flag_conditions`), and a FLAG-admitted operation is dispatched only when the
caller acknowledges those conditions (`flag_conditions_met`). With the default
policy every FLAG is held (HOLD). The v0.7.0 port declares nothing, so on 5.7.6
nothing it submits is admitted and CT-R4-001 / CT-R4-002 fail with "no admission"
(qualification run of 22 November 2026, exit code 1). This port keeps the v0.7.0
port unchanged for 5.7.0 and adds the declaration here.

What changes, and only this:
- The deployment under test declares one FLAG condition, `FLAG_CONDITION`, in its
  composition policy.
- The port reports, as `Decision.conditions`, the conditions the runtime copies
  onto a FLAG result (`flag_conditions`). It reads them; it does not invent them.
- At commit, the port acknowledges the declared condition (`flag_conditions_met`),
  which 5.7.6 requires before dispatching a FLAG-admitted operation; a PASS
  admission ignores it. The acknowledgement is added by `_AcknowledgingGovernor`,
  which wraps the shipped governor and changes nothing else, so the refusal
  mapping of `TenirGovPort.commit` applies unchanged.

The condition is met by construction in this harness: the port's journal provider
is the only executor, it records every call, and the journal is what
`observed_effects` reads. That is a property of the harness, not an observation of
any deployment.

Everything else is the v0.7.0 port's: intents, measurements, degradations,
confidence ladder, combinations, refusal mapping, capabilities, bounds.

Three more declarations since the 5.7.7 candidate work (runtime author's decision
of 23 November 2026, 11:22 UTC, option B: write the missing adapters). Each one
reads a primitive 5.7.6 has on its default path; none invents one. PROVISIONAL,
to be confirmed by the runtime's author like the rest of the mapping:

- CLOCK, with the bound `tau_k` (TAU_K seconds, a HARNESS FIXTURE, not an SLA):
  the deployment under test declares `hold_tau_k_seconds` and its source, as
  every deployment must since 5.7.7 (R11, option C). `elapse_past(tau_k)` is
  simulated: the port moves the recorded start of every open HOLD back past the
  bound and then runs the expiry sweep the runtime offers (`expire_hold`), which
  the deployment would run on a schedule. The runtime records the exhaustion as
  FAILED, exhaustion_disposition "fail-closed", CONFIRMED_NONEXECUTION. The
  commit of such an attempt is refused; the port reports it as
  `Refused(EXPIRED, "HARD_VETO")`: the runtime's "fail-closed, terminal" is read
  as the REG terminal refusal disposition. `exhaustion_policy` is "fail-closed".
- REVOKE: the runtime re-validates the admitting mandate before dispatch (5.7.6):
  an acting agent that was registered at admission and is no longer registered
  refuses the dispatch, FAILED, CONFIRMED_NONEXECUTION, HARD_VETO in the ledger.
  So the port registers every principal as an Agent when it first adjudicates
  for it, and `revoke(principal)` removes that registration. This is revocation
  after verdict and before commit (C3, RFC-4 §2.2), nothing more: a NEW request
  from the revoked principal is still adjudicated on its measured authority,
  because standing on this runtime is a measured score, not a registry entry
  (declared partial gap on NO_STANDING, P4). No revocation bound is declared, so
  the checks that read a new request after revocation stay ADAPTER_REQUIRED.
- STATE_DRIFT: the same re-validation refuses when the composition policy
  version differs from the one that admitted. `drift_state()` replaces the
  governor's policy by the same policy under another version. The commit is
  refused: `Refused(STATE_DRIFT, "HARD_VETO")`.

Refusal mapping added, on the dispatch reason the runtime returns:
    "MANDATE_REVALIDATION_FAILED" + "no longer registered"       -> STANDING_REVOKED
    "MANDATE_REVALIDATION_FAILED" + policy version / budget limit -> STATE_DRIFT
    state failed with hold exit_reason "expired"                  -> EXPIRED

Declared gaps (the primitive is absent on the default path; nothing is adapted):
    CT-R4-004, CT-R4-004a (stale_grant): an admission carries no validity bound
        of its own; only a held attempt is bounded (tau_k). An authorization
        bound is a candidate feature for 5.8.0, runtime author's decision pending.
    CT-R4-007 (receipts): signed receipts exist only on the Profile S commit
        path (Ed25519 authorization and consumption receipts); a disposition on
        the default path is a hash-chained ledger entry, not a signed receipt.
Not applicable (no transport: the runtime is driven in process, like C4):
    CT-R1-003, CT-R1-005.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta, timezone

from .. import port as P
from .tenir_gov import TenirGovPort

FLAG_CONDITION = ("supervised execution: the operation runs only through the REG harness "
                  "journal executor, which records every call")
ACKNOWLEDGEMENT = "met by construction: the journal executor is the port's only provider"
# tau_k of the deployment under test: a harness fixture, not an SLA. The runtime
# refuses a policy whose tau_k has no source (5.7.7), so the source says what it is.
TAU_K = 600.0
TAU_K_SOURCE = "REG harness fixture: ten minutes, not derived from an SLA"
DRIFTED_VERSION_SUFFIX = "+reg-harness-drift"


class _AcknowledgingGovernor:
    """The shipped governor, unchanged; only adds `flag_conditions_met` at dispatch."""

    def __init__(self, governor):
        self._governor = governor

    def __getattr__(self, name):
        return getattr(self._governor, name)

    def dispatch_and_execute(self, *args, **kwargs):
        kwargs.setdefault("flag_conditions_met", {FLAG_CONDITION: ACKNOWLEDGEMENT})
        return self._governor.dispatch_and_execute(*args, **kwargs)


class TenirGov576Port(TenirGovPort):
    name = "tenir-governance (5.7.6, FLAG condition declared)"
    interface_mode = "port:tenir-governance+flag_conditions"
    capabilities = TenirGovPort.capabilities | {P.CLOCK, P.REVOKE, P.STATE_DRIFT}
    bounds = {P.B_TAU_K: TAU_K}
    clock_mode = "simulated"
    exhaustion_policy = "fail-closed"
    not_applicable = dict(TenirGovPort.not_applicable, **{
        "CT-R1-003": "No transport layer: the runtime is driven in process (HTTP status semantics).",
        "CT-R1-005": "No transport layer: the runtime is driven in process (TLS)."})
    declared_gaps = {
        # Not a credential row on this runtime (standard author's option A of
        # 23 November 2026 named five credential rows; this one, measured, is
        # about a revocation latency window): revocation of a principal's
        # standing exists and acts at dispatch (C3, REVOKE declared), but the
        # runtime declares no revocation latency bound, so the window the row
        # asks for cannot be read. Declared as a gap, counted in the exit code,
        # not set outside the perimeter.
        "CT-R3-002": ("revocation acts at dispatch (mandate re-validation, C3) but the runtime "
                      "declares no revocation latency bound; the declared window the row asks "
                      "for does not exist on the default path"),
        "CT-R4-004": ("the default path binds no validity window to an admission; only a held "
                      "attempt is bounded (tau_k). An authorization bound is a 5.8.0 candidate "
                      "feature, runtime author's decision pending"),
        "CT-R4-004a": ("same as CT-R4-004: no authorization bound on the default path"),
        "CT-R4-007": ("signed receipts exist only on the Profile S commit path (Ed25519 "
                      "authorization and consumption receipts); a disposition on the default "
                      "path is a hash-chained ledger entry, not an independently verifiable "
                      "signed receipt")}

    def __init__(self):
        from tenir_governance.composition import CompositionPolicy
        if "flag_conditions" not in getattr(CompositionPolicy, "__dataclass_fields__", {}):
            raise RuntimeError("this port needs CompositionPolicy.flag_conditions "
                               "(tenir-governance 5.7.6 or later); use TenirGovPort for 5.7.0")
        super().__init__()

    def reset(self):
        from tenir_governance.composition import (CompositionPolicy, DualKernelGovernor,
                                                  ScoringKernelAdapter)
        from tenir_governance.membrane import MembraneState, TransitionMembrane
        from tenir_governance.objects import Resource
        from tenir_kernel.kernel import TenirKernel
        from . import tenir_gov as base

        state = self._state = MembraneState()
        state.register_resource(Resource(resource_id=base._BUDGET, capacity=base._CAPACITY))
        self._provider = base._JournalProvider()
        self._scoring = ScoringKernelAdapter(TenirKernel())
        policy_kw = dict(flag_conditions=(FLAG_CONDITION,))
        if "hold_tau_k_seconds" in CompositionPolicy.__dataclass_fields__:
            policy_kw.update(hold_tau_k_seconds=TAU_K, hold_tau_k_source=TAU_K_SOURCE)
        policy = CompositionPolicy(**policy_kw)
        self._inner = DualKernelGovernor(self._scoring, TransitionMembrane(state),
                                         policy=policy, provider=self._provider)
        self._gov = _AcknowledgingGovernor(self._inner)
        self._registered = set()

    # -- standing as the runtime holds it: a registered agent ----------------
    def _adjudicate(self, measured, amount, *, principal, action_type, nonce=None):
        if principal not in self._registered:
            from tenir_governance.objects import Agent
            # Registered so that the runtime's mandate re-validation reads this
            # principal at dispatch (5.7.6). The authority the decision reads is
            # the measured `authority` input, not this score.
            self._state.register_agent(Agent(agent_id=principal, authority_score=1.0))
            self._registered.add(principal)
        return self._adjudicate_576(measured, amount, principal=principal,
                                    action_type=action_type, nonce=nonce)

    def revoke(self, principal):
        """Withdraw the principal's registration: the runtime refuses, at
        dispatch, every admitted operation whose acting agent is no longer
        registered (mandate re-validation, 5.7.6)."""
        self._state.agents.pop(principal, None)
        self._registered.discard(principal)

    def drift_state(self):
        """Change the governing state the runtime binds at admission: the
        composition policy version. Everything else in the policy is unchanged."""
        before = self._inner.policy.version
        self._inner.policy = dataclasses.replace(self._inner.policy,
                                                 version=before + DRIFTED_VERSION_SUFFIX)
        return f"composition policy version {before} -> {self._inner.policy.version}"

    def elapse_past(self, bound):
        """Simulated clock. For tau_k: every open HOLD is dated back past the
        bound, then the runtime's own expiry (`expire_hold`) is run for each,
        as a deployment's expiry sweep would. Returns the seconds let pass."""
        if bound == P.EFFECT_WINDOW:
            return 0.0
        if bound != P.B_TAU_K:
            raise NotImplementedError(f"no declared bound: {bound}")
        seconds = TAU_K + 1.0
        past = (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()
        for record in self._inner.find_holds():
            if record.hold_record is not None:
                record.hold_record.hold_start = past
            self._inner.expire_hold(record.idempotency_key)
        return seconds

    def commit(self, decision, *, action_type=None):
        amount = decision.raw.get("amount")
        args = (self._budget_name(), amount) if amount else ()
        result = self._gov.dispatch_and_execute(
            decision.decision_id, *args,
            payload={"action_type": action_type or decision.action_type})
        if result.get("dispatched"):
            return P.Committed(decision.decision_id, result)
        reason = str(result.get("reason", ""))
        if reason.startswith("MANDATE_REVALIDATION_FAILED"):
            # The runtime records the attempt FAILED, CONFIRMED_NONEXECUTION, and
            # ledgers a HARD_VETO: terminal for this attempt identity.
            if "no longer registered" in reason:
                raise P.Refused(P.R_STANDING_REVOKED, "HARD_VETO", reason)
            raise P.Refused(P.R_STATE_DRIFT, "HARD_VETO", reason)
        record = self._inner.registry.get(decision.decision_id)
        if (record is not None and record.state.value == "failed" and record.hold_record is not None
                and getattr(record.hold_record, "exit_reason", "") == "expired"):
            # tau_k exhausted: FAILED, exhaustion_disposition fail-closed,
            # CONFIRMED_NONEXECUTION. Read as the terminal refusal disposition.
            raise P.Refused(P.R_EXPIRED, "HARD_VETO", reason)
        return super().commit(decision, action_type=action_type)

    @staticmethod
    def _budget_name():
        from . import tenir_gov as base
        return base._BUDGET

    def _adjudicate_576(self, measured, amount, *, principal, action_type, nonce=None):
        d = TenirGovPort._adjudicate(self, measured, amount, principal=principal,
                                     action_type=action_type, nonce=nonce)
        if d.disposition == "FLAG":
            conditions = tuple(str(c) for c in (d.raw["result"].get("flag_conditions") or ()))
            d = dataclasses.replace(d, conditions=conditions)
        return d
