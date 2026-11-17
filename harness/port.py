"""RuntimePort: the only surface a runtime has to implement.

A port declares its capabilities explicitly. A scenario that needs a
capability the port does not declare is never executed.

The port author owns the mapping from native verdicts to REG dispositions
(`PASS`, `FLAG`, `HOLD`, `HARD_VETO`) and from native refusals to REG reason
codes. The harness does not infer either.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Capability names. A port lists the ones it implements in `capabilities`.
EVALUATE = "evaluate"            # submit an intent, get a disposition
COMMIT = "commit"                # cross the execution boundary with a grant
REVOKE = "revoke"                # revoke a principal's standing after a verdict
STATE_DRIFT = "state_drift"      # change governing state between verdict and commit
STALE_GRANT = "stale_grant"      # obtain a grant that is already expired
NONCE = "nonce"                  # caller-supplied nonce, replay must be refused
RECEIPTS = "receipts"            # signed decision receipts, verifiable
MANIFEST = "manifest"            # append-only evidence ledger, tamper-evident
TENIR_SCORE = "tenir_score"      # exposes the TENIR S = K/(P*V+eps) computation
EFFECTS = "effects"              # effects observable independently of the runtime

ALL_CAPABILITIES = frozenset({
    EVALUATE, COMMIT, REVOKE, STATE_DRIFT, STALE_GRANT, NONCE,
    RECEIPTS, MANIFEST, TENIR_SCORE, EFFECTS,
})

# Intents the harness asks for. The port maps each one to its own inputs.
ADMISSIBLE = "admissible"            # standing valid, structure comfortably inside bounds
INADMISSIBLE = "inadmissible"        # standing valid, structure outside bounds
NO_STANDING = "no_standing"          # caller has no valid standing
NEEDS_APPROVAL = "needs_approval"    # the runtime must obtain a human approval first
# Refused by the runtime's own policy, for whatever reason it has. Deliberately
# distinct from INADMISSIBLE: a policy refusal is not evidence of REG structural
# admissibility, and must never satisfy a vector about it.
DENIED = "denied"

ALL_INTENTS = frozenset({ADMISSIBLE, INADMISSIBLE, NO_STANDING, NEEDS_APPROVAL, DENIED})

# Normalised refusal codes.
R_STANDING_REVOKED = "STANDING_REVOKED"
R_STATE_DRIFT = "STATE_DRIFT"
R_EXPIRED = "EXPIRED"
R_BINDING = "BINDING_VIOLATION"
R_INVALID_DISPOSITION = "INVALID_DISPOSITION"
R_REPLAY = "NONCE_REPLAY"

# Dispositions that let execution proceed (RFC-0 §4). PASS is ALLOW. FLAG is
# ALLOW_WITH_MONITORING: "execution may proceed only under an explicitly
# defined additional condition or supervision" and is "never a bare ALLOW".
# A port reports the condition it observes in `Decision.conditions`.
# HOLD (SUSPEND) and HARD_VETO (BLOCK) never admit.
ADMISSION_DISPOSITIONS = frozenset({"PASS", "FLAG"})


class Refused(Exception):
    """The runtime refused an operation.

    `disposition` is the disposition the runtime recorded for the refusal
    (for example HARD_VETO), or None if it recorded none.
    """

    def __init__(self, code: str, disposition: Optional[str] = None, detail: str = ""):
        super().__init__(f"{code}{':' + disposition if disposition else ''} {detail}".strip())
        self.code = code
        self.disposition = disposition
        self.detail = detail


@dataclass
class Decision:
    """A verdict returned by the runtime for one submitted action."""
    decision_id: str
    disposition: str                 # PASS | FLAG | HOLD | HARD_VETO
    action_type: str
    principal: str
    raw: dict = field(default_factory=dict)   # opaque to scenarios
    # For a FLAG: the additional condition or supervision the runtime attaches,
    # as the port observes it. Empty when the port observes none.
    conditions: tuple = ()


@dataclass
class Committed:
    decision_id: str
    raw: dict = field(default_factory=dict)


class RuntimePort:
    """Base class. Override only what the runtime supports and list it."""

    name: str = "unnamed"
    interface_mode: str = "port"
    # 1 = semantic mapping, 2 = adapter-tested. A port can never claim 3.
    evidence_level: int = 2
    capabilities: frozenset = frozenset()
    # Intents the port can produce on demand. A scenario needing another one is not run.
    intents: frozenset = frozenset()
    # vector_id -> reason. Vectors that cannot apply to this runtime by construction.
    not_applicable: dict = {}
    # vector_id -> note. Gaps the implementer declares about its own runtime.
    declared_gaps: dict = {}

    def reset(self) -> None:
        """Return the runtime to a clean state. Called before every scenario."""

    # -- primitives ---------------------------------------------------------
    def evaluate(self, intent: str, *, principal: str, action_type: str,
                 nonce: Optional[str] = None) -> Decision:
        raise NotImplementedError

    def commit(self, decision: Decision, *, action_type: Optional[str] = None) -> Committed:
        raise NotImplementedError

    def revoke(self, principal: str) -> None:
        raise NotImplementedError

    def drift_state(self) -> str:
        """Change governing state; return a short description of the change."""
        raise NotImplementedError

    def stale_grant(self, *, action_type: str) -> Decision:
        raise NotImplementedError

    def receipt_verifies(self, decision: Decision) -> bool:
        raise NotImplementedError

    def tampered_receipt_verifies(self, decision: Decision) -> bool:
        raise NotImplementedError

    def manifest_intact(self) -> bool:
        raise NotImplementedError

    def tampered_manifest_intact(self) -> bool:
        raise NotImplementedError

    def tenir_score(self, P: float, V: float, K: float) -> dict:
        raise NotImplementedError

    def observed_effects(self, decision: Decision) -> int:
        """Number of downstream effects observed for this decision, read from a
        journal the runtime does not control."""
        raise NotImplementedError

    # -- escape hatch -------------------------------------------------------
    def run_custom(self, vector_id: str) -> Optional[Any]:
        """Return a ConformanceResult for a vector the port handles itself,
        or None. Used for runtime-specific probes; never for a neutral vector."""
        return None
