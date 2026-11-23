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
confidence ladder, combinations, refusal mapping, capabilities, bounds. No other
5.7.6 feature is declared: no tau_k, no attestation verifier, no state drift.
"""
from __future__ import annotations

import dataclasses

from .tenir_gov import TenirGovPort

FLAG_CONDITION = ("supervised execution: the operation runs only through the REG harness "
                  "journal executor, which records every call")
ACKNOWLEDGEMENT = "met by construction: the journal executor is the port's only provider"


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
        policy = CompositionPolicy(flag_conditions=(FLAG_CONDITION,))
        self._gov = _AcknowledgingGovernor(DualKernelGovernor(
            self._scoring, TransitionMembrane(state), policy=policy, provider=self._provider))

    def _adjudicate(self, measured, amount, *, principal, action_type, nonce=None):
        d = super()._adjudicate(measured, amount, principal=principal,
                                action_type=action_type, nonce=nonce)
        if d.disposition == "FLAG":
            conditions = tuple(str(c) for c in (d.raw["result"].get("flag_conditions") or ()))
            d = dataclasses.replace(d, conditions=conditions)
        return d
