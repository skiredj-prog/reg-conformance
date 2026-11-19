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
COMBINE = "combine"              # one attempt that meets several conditions at once
CLOCK = "clock"                  # let a declared bound pass for the runtime
DEGRADE = "degrade"              # submit the admissible attempt with one measurement degraded
CONFIDENCE = "confidence"        # submit an attempt at several levels of confidence in its evidence

ALL_CAPABILITIES = frozenset({
    EVALUATE, COMMIT, REVOKE, STATE_DRIFT, STALE_GRANT, NONCE,
    RECEIPTS, MANIFEST, TENIR_SCORE, EFFECTS, COMBINE, CLOCK, DEGRADE, CONFIDENCE,
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
# The three below describe one departure from ADMISSIBLE each. A port declares
# one only if the runtime has the notion: a credential that can be malformed, a
# scope a caller can hold, a hard invariant that can be declared.
MALFORMED_CREDENTIAL = "malformed_credential"   # the credential presented is not well-formed
OUT_OF_SCOPE = "out_of_scope"                   # valid standing for a declared scope; the request lies outside it
INVARIANT_VIOLATED = "invariant_violated"       # measurements as ADMISSIBLE; a declared hard invariant is violated
# The three below involve a bound the subject declares (see `bounds`).
# Standing under a time-limited credential. The first use for a principal
# issues it; every later use for that principal presents the same one.
EXPIRING_CREDENTIAL = "expiring_credential"
STALE_REQUEST = "stale_request"                 # submitted outside the declared freshness window
REVOKED_KEY = "revoked_key"                     # credential signed by a key revoked for longer than the declared bound

ALL_INTENTS = frozenset({ADMISSIBLE, INADMISSIBLE, NO_STANDING, NEEDS_APPROVAL, DENIED,
                         MALFORMED_CREDENTIAL, OUT_OF_SCOPE, INVARIANT_VIOLATED,
                         EXPIRING_CREDENTIAL, STALE_REQUEST, REVOKED_KEY})

# Bounds a subject may declare, in seconds. The harness never sets a duration:
# a check that depends on time reads the bound the port declares and asks the
# port to let it pass. No declared bound, no check.
B_REVOCATION = "revocation"              # RFC-3 §4.2: a revoked authority is not executable beyond it
B_CREDENTIAL = "credential_validity"     # RFC-3 §2.2: lifetime of the time-limited credential the port presents
B_FRESHNESS = "freshness"                # RFC-6 §3.2: a request older than this is rejected
B_TAU_K = "tau_k"                        # RFC-5 §1: how long a HOLD may wait for a human
ALL_BOUNDS = frozenset({B_REVOCATION, B_CREDENTIAL, B_FRESHNESS, B_TAU_K})
# Not a policy bound but a condition of observation: how long after a call an
# effect may still appear. "No effect" is read once it has passed.
EFFECT_WINDOW = "effect_window"

# Epistemic states a measurement can be put in (RFC-2 §2.5). LOW CONFIDENCE is
# not here: it is a matter of degree, submitted through CONFIDENCE.
E_UNKNOWN = "unknown"                # it arrives and establishes nothing
E_STALE = "stale"                    # older than its freshness window
E_MISSING = "missing"                # absent from the request
E_CONTRADICTORY = "contradictory"    # two valid measurements of it disagree
ALL_EPISTEMIC = frozenset({E_UNKNOWN, E_STALE, E_MISSING, E_CONTRADICTORY})

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

# From least to most restrictive. RFC-0 §4: "When multiple applicable controls
# produce incompatible dispositions, the most restrictive applicable
# disposition governs", with the example PASS, FLAG and HOLD giving HOLD, and
# HARD_VETO prevailing over all.
RESTRICTIVENESS = ("PASS", "FLAG", "HOLD", "HARD_VETO")


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
    # Sets of intents the port can produce together in one attempt (COMBINE).
    # Declare a set only when each condition comes from its own input, so that
    # asking for one does not undo another.
    combinations: frozenset = frozenset()
    # bound name (B_*) -> seconds, as the subject declares it. The port states
    # what the deployment under test declares. It does not invent a value.
    bounds: dict = {}
    # How long after a call an effect may still appear, in seconds. Zero for a
    # runtime that executes synchronously. Above zero, the port needs CLOCK.
    effect_window: float = 0.0
    # How the port lets time pass: "real" (it waits) or "simulated" (it moves
    # the clock the runtime reads). Required with CLOCK.
    clock_mode: str = ""
    # epistemic state (E_*) -> the measurements the port can put in that state
    # on the admissible attempt, under the runtime's own names. List every
    # measurement the decision reads: a port that lists only the safe ones
    # hides what the check is for.
    degradations: dict = {}
    # Levels of confidence the port can submit an attempt at: step 0 is full
    # confidence, each next step is lower. Two or more with CONFIDENCE.
    confidence_steps: int = 0
    # True when the deployment pre-declares a deterministic resolution for
    # contradictory measurements. RFC-2 §2.5 then does not require a HOLD.
    contradiction_resolution: bool = False
    # What the deployment pre-declares for a HOLD nobody answers within tau_k:
    # "fail-closed", "fail-degraded", or None when it declares nothing, in
    # which case the default of RFC-5 §2.1 applies: fail-closed.
    exhaustion_policy: Optional[str] = None

    def reset(self) -> None:
        """Return the runtime to a clean state. Called before every scenario,
        and by a scenario between two observations that must not share state."""

    # -- primitives ---------------------------------------------------------
    def evaluate(self, intent: str, *, principal: str, action_type: str,
                 nonce: Optional[str] = None) -> Decision:
        """Submit one attempt. `nonce` is the caller-supplied key the runtime
        uses against replay, whatever it calls it (nonce, idempotency key)."""
        raise NotImplementedError

    def evaluate_combined(self, intents: tuple, *, principal: str, action_type: str,
                          nonce: Optional[str] = None) -> Decision:
        """Submit one attempt that meets every listed condition at once, in
        the order given where the runtime's input has an order."""
        raise NotImplementedError

    def evaluate_degraded(self, state: str, measurement: str, *, principal: str,
                          action_type: str) -> Decision:
        """Submit the admissible attempt with one measurement put in the given
        epistemic state. Everything else is as for ADMISSIBLE."""
        raise NotImplementedError

    def evaluate_at_confidence(self, intent: str, step: int, *, principal: str,
                               action_type: str) -> Decision:
        """Submit the attempt for `intent` at confidence level `step`."""
        raise NotImplementedError

    def elapse_past(self, bound: str) -> float:
        """Let the named bound pass for the runtime, and just more than it.
        `bound` is a declared bound or EFFECT_WINDOW. Returns the seconds let
        pass. The port knows its own clock: the harness supplies no margin.
        Letting time pass includes whatever the deployment runs on a schedule
        once it has passed, an expiry sweep for example."""
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
