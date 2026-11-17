"""Runtime-neutral scenarios: one per executable vector, then the effect
probes and the property checks, which are not vectors.

A scenario returns (state, details), or (state, details, facts) when it has
something to record beside the result. State is one of the runner's reporting
states. A scenario never names a runtime and never reads runtime internals.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Callable

from . import port as P

PASS, FAIL, INCONCLUSIVE = "PASS", "FAIL", "INCONCLUSIVE"


@dataclass(frozen=True)
class Scenario:
    vector_id: str
    requires: frozenset
    run: Callable
    intents: frozenset = frozenset()
    normative: bool = True      # False = probe or property check, outside the REG vector set
    exercises: str = ""         # property check only: the VECTORS.md row it exercises
    bounds: frozenset = frozenset()   # bounds the subject must declare for the scenario to run
    degradations: frozenset = frozenset()   # epistemic states the port must be able to produce
    at: str = ""                # where it observes, in the terms of RFC-0 §5
    not_observed: tuple = ()    # what a result of this scenario does not establish


# Where a scenario observes. The four phases are those of RFC-0 §5. MODEL is
# for the scenarios that call the structural model directly, outside any attempt.
PRE = "pre-execution"
AUTH = "conditional authorization"
EXEC = "supervised execution"
PROOF = "closure and proof"
MODEL = "structural model alone, outside the lifecycle"
PHASES = (PRE, AUTH, EXEC, PROOF, MODEL)


def _nonce() -> str:
    return uuid.uuid4().hex


def _principal(tag: str) -> str:
    return f"{tag}-{uuid.uuid4().hex[:8]}"


# -- admission ---------------------------------------------------------------
# RFC-0 §4 gives each disposition an execution instruction. PASS is ALLOW and
# FLAG is ALLOW_WITH_MONITORING: both let execution proceed, FLAG only under an
# explicit condition or supervision. A scenario that needs "an admitted action"
# therefore accepts either, and records which one it went forward on.

def _admitted(d) -> bool:
    return d.disposition in P.ADMISSION_DISPOSITIONS


def _admission(d) -> dict:
    """Facts kept beside a result when the check went forward on this decision."""
    return {"admitted_on": d.disposition,
            "flag_conditions": [str(c) for c in (getattr(d, "conditions", ()) or ())]}


def _via(d) -> str:
    return " (admitted on FLAG)" if d.disposition == "FLAG" else ""


def c1(rt):
    d = rt.evaluate(P.NO_STANDING, principal=_principal("u"), action_type="wire_transfer")
    return (PASS, "HARD_VETO on standing failure") if d.disposition == "HARD_VETO" \
        else (FAIL, f"disposition={d.disposition}")


def c2(rt):
    d = rt.evaluate(P.INADMISSIBLE, principal=_principal("a"), action_type="wire_transfer")
    return (PASS, f"{d.disposition} on inadmissible structure") \
        if d.disposition in ("FLAG", "HARD_VETO") else (FAIL, f"disposition={d.disposition}")


def c3(rt):
    who = _principal("race")
    d = rt.evaluate(P.ADMISSIBLE, principal=who, action_type="wire_transfer")
    if not _admitted(d):
        return INCONCLUSIVE, "could not establish the valid-verdict precondition"
    rt.revoke(who)
    try:
        rt.commit(d)
    except P.Refused as e:
        if e.code == P.R_STANDING_REVOKED and e.disposition == "HARD_VETO":
            return (PASS, "post-verdict revocation produced HARD_VETO; commit blocked" + _via(d),
                    _admission(d))
        return INCONCLUSIVE, f"commit refused without establishing HARD_VETO: {e}", _admission(d)
    return FAIL, "commit accepted after revocation", _admission(d)


def _replay(vector_id):
    def run(rt):
        n = _nonce()
        rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer", nonce=n)
        try:
            rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer", nonce=n)
        except P.Refused as e:
            return (PASS, "nonce replay refused") if e.code == P.R_REPLAY else (FAIL, str(e))
        return FAIL, "nonce replay accepted"
    return run


def r4_001(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if not _admitted(d):
        return FAIL, f"no admission (disposition={d.disposition})"
    rt.commit(d, action_type="wire_transfer")
    return PASS, "valid grant bound and committed" + _via(d), _admission(d)


def r4_002(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if not _admitted(d):
        return FAIL, f"no admission (disposition={d.disposition})"
    try:
        rt.commit(d, action_type="account_deletion")
    except P.Refused as e:
        if e.code == P.R_BINDING:
            return PASS, "payload binding violation refused" + _via(d), _admission(d)
        return FAIL, str(e), _admission(d)
    return FAIL, "binding violation not detected", _admission(d)


def r4_004(rt):
    d = rt.stale_grant(action_type="wire_transfer")
    try:
        rt.commit(d)
    except P.Refused as e:
        return (PASS, "expired grant refused") if e.code == P.R_EXPIRED else (FAIL, str(e))
    return FAIL, "expired grant accepted"


def r4_005(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if not _admitted(d):
        return FAIL, f"no admission (disposition={d.disposition})"
    change = rt.drift_state()
    try:
        rt.commit(d)
    except P.Refused as e:
        if e.code == P.R_STATE_DRIFT and e.disposition == "HARD_VETO":
            return PASS, f"state drift produced HARD_VETO ({change})" + _via(d), _admission(d)
        return FAIL, str(e), _admission(d)
    return FAIL, "state drift not detected", _admission(d)


def r4_006(rt):
    d = rt.evaluate(P.NO_STANDING, principal=_principal("u"), action_type="wire_transfer")
    if d.disposition != "HARD_VETO":
        return FAIL, "no HARD_VETO"
    try:
        rt.commit(d)
    except P.Refused as e:
        return (PASS, "HARD_VETO blocked at commit gate") \
            if e.code == P.R_INVALID_DISPOSITION else (FAIL, str(e))
    return FAIL, "HARD_VETO committed"


def r4_007(rt):
    d = rt.evaluate(P.NO_STANDING, principal=_principal("u"), action_type="wire_transfer")
    if not rt.receipt_verifies(d):
        return FAIL, "receipt missing or signature invalid"
    if rt.tampered_receipt_verifies(d):
        return FAIL, "changed receipt field still verified"
    return PASS, "signature binds receipt fields"


def r4_008(rt):
    rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if rt.tampered_manifest_intact():
        return FAIL, "tampering in a copied manifest was not detected"
    if not rt.manifest_intact():
        return FAIL, "original manifest does not verify"
    return PASS, "tampering in a copied manifest was detected"


def r2_002(rt):
    Pv, V, K = 0.4, (0.4 * 0.5) ** 0.5, 0.75
    a, b = rt.tenir_score(Pv, V, K), rt.tenir_score(Pv, V, K)
    if abs(a["s_score"] - b["s_score"]) < 1e-9 and a["decision"] == b["decision"]:
        return PASS, f"S={a['s_score']:.6f}, deterministic"
    return FAIL, "non-deterministic results"


def r2_003(rt):
    try:
        r = rt.tenir_score(0.0, 0.0, 0.85)
    except Exception as e:      # a crash here is the failure being tested
        return FAIL, f"divide-by-zero not handled: {e}"
    return (PASS, f"epsilon guard active; S={r['s_score']}") \
        if r["decision"] in ("PASS", "FLAG", "HARD_VETO") else (FAIL, f"unexpected result: {r}")


# -- harness probes: observe the effect, not only the verdict -----------------
# These are NOT REG vectors. They are reported under their own ids and never
# counted in the 56-vector totals. The property view (properties.py) counts
# them, as probes, under the candidate family they exercise.
#
# Some runtimes decide and dispatch in one step. For those, `evaluate` IS the
# boundary crossing and there is no separate commit: the probes only call
# `commit` when the port declares it.

def _cross(rt, d):
    if P.COMMIT in rt.capabilities:
        try:
            rt.commit(d)
        except P.Refused:
            pass


def _effects(rt, d) -> int:
    """Effects observed for a decision, read once the declared effect window
    has passed. Without that wait, "no effect" would only mean "none yet"."""
    if rt.effect_window:
        rt.elapse_past(P.EFFECT_WINDOW)
    return rt.observed_effects(d)


def hx_refusal_zero_effects(rt):
    d = rt.evaluate(P.DENIED, principal=_principal("a"), action_type="count")
    if d.disposition not in ("HARD_VETO", "HOLD"):
        return INCONCLUSIVE, f"no refusal to observe (disposition={d.disposition})"
    _cross(rt, d)
    n = _effects(rt, d)
    return (PASS, "refusal matched zero observed effects") if n == 0 \
        else (FAIL, f"refusal matched {n} observed effect(s)")


def hx_allow_exactly_one_effect(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="count")
    if not _admitted(d):
        return INCONCLUSIVE, f"no allow to observe (disposition={d.disposition})"
    _cross(rt, d)
    _cross(rt, d)               # a second attempt on the same grant, where one exists
    n = _effects(rt, d)
    if n == 1:
        return PASS, "allow matched exactly one observed effect" + _via(d), _admission(d)
    return FAIL, f"allow matched {n} observed effect(s)", _admission(d)


def hx_unanswered_approval_zero_effects(rt):
    d = rt.evaluate(P.NEEDS_APPROVAL, principal="a", action_type="count")
    if d.disposition == "PASS":
        return FAIL, "call needing approval was allowed without one"
    _cross(rt, d)
    n = _effects(rt, d)
    return (PASS, f"unanswered approval gave {d.disposition} and zero observed effects") if n == 0 \
        else (FAIL, f"unanswered approval matched {n} observed effect(s)")


def hx_allow_after_refusal(rt):
    refused = rt.evaluate(P.DENIED, principal="a", action_type="count")
    allowed = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="count")
    if not _admitted(allowed):
        return INCONCLUSIVE, f"no allow after the refusal (disposition={allowed.disposition})"
    _cross(rt, allowed)
    a, b = _effects(rt, refused), _effects(rt, allowed)
    if (a, b) == (0, 1):
        return (PASS, "a refusal left the next allowed call intact: 0 then 1 effect" + _via(allowed),
                _admission(allowed))
    return FAIL, f"effects after refusal then allow: {a}, {b}", _admission(allowed)


# -- property checks: one indexed property each, outside the vector set -------
# A property check exercises a property that VECTORS.md indexes and that has
# no executable vector. It is NOT a REG vector. It is reported under its own
# id (PX-<index id>), never counted in the 56-vector totals, and counted by
# the property view under the family of the row it exercises. Registering one
# as a vector is a ratification decision, not a harness change.
#
# A check states an outcome, never a mechanism: what must not be admitted and
# what must stay admitted. Where a rejection is expected, an outright refusal
# and a HARD_VETO both count. A HOLD suspends without rejecting: the check is
# then not concluded.

def _attempt(call, *args, **kw):
    """(decision, refusal): exactly one of the two is set."""
    try:
        return call(*args, **kw), None
    except P.Refused as e:
        return None, e


def _control(rt):
    """The same request with nothing wrong. Expecting a rejection only means
    something on a runtime that admits this one."""
    return rt.evaluate(P.ADMISSIBLE, principal=_principal("ok"), action_type="wire_transfer")


def _rejected(d, refusal, what):
    if refusal is not None:
        return PASS, f"{what} was refused outright ({refusal.code})"
    if d.disposition == "HARD_VETO":
        return PASS, f"{what} got HARD_VETO"
    if _admitted(d):
        return FAIL, f"{what} was admitted ({d.disposition})"
    return INCONCLUSIVE, f"{what} got {d.disposition}: suspended, not rejected"


def _must_reject(intent, what):
    def run(rt):
        ok = _control(rt)
        if not _admitted(ok):
            return INCONCLUSIVE, f"the control request was not admitted (disposition={ok.disposition})"
        d, refusal = _attempt(rt.evaluate, intent, principal=_principal("x"),
                              action_type="wire_transfer")
        return (*_rejected(d, refusal, what), _admission(ok))
    return run


# CT-R3-001. "Malformed credentials rejected before evaluation." The index
# anchors it on RFC-3; the clauses read here are §2.2 and §2.3. The check
# observes the rejection. It cannot observe that it came before evaluation.
px_malformed_credential = _must_reject(
    P.MALFORMED_CREDENTIAL, "a request with a malformed credential")

# CT-R3-007. "Standing valid only within declared organizational scope." The
# index anchors it on RFC-3; the clause read here is §1, where Standing is the
# possession of a given Authority Scope.
px_out_of_scope = _must_reject(
    P.OUT_OF_SCOPE, "a request outside the scope its caller holds")


def px_hard_invariant(rt):
    """REG-STATE-014. RFC-2 §3.3 and §4.1: a hard invariant violation gives
    HARD_VETO whatever the scoring says. The check uses the measurements the
    control request is admitted on, so no score can explain the refusal."""
    ok = _control(rt)
    if not _admitted(ok):
        return INCONCLUSIVE, f"the control request was not admitted (disposition={ok.disposition})"
    d, refusal = _attempt(rt.evaluate, P.INVARIANT_VIOLATED, principal=_principal("x"),
                          action_type="wire_transfer")
    got = refusal.disposition if refusal is not None else d.disposition
    if got == "HARD_VETO":
        return (PASS, "a hard invariant violation got HARD_VETO on measurements that are "
                      "admitted without it", _admission(ok))
    if refusal is not None:
        return (INCONCLUSIVE, f"refused without a recorded disposition ({refusal.code}); "
                              "RFC-2 §3.3 asks for HARD_VETO", _admission(ok))
    return FAIL, f"a hard invariant violation got {got}, not HARD_VETO", _admission(ok)


def px_key_reuse_modified_action(rt):
    """VEC-6-02. RFC-6 §3.1: a key already used, presented again with a
    different payload, must be rejected."""
    key = _nonce()
    first = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer", nonce=key)
    if not _admitted(first):
        return INCONCLUSIVE, f"the first use of the key was not admitted (disposition={first.disposition})"
    d, refusal = _attempt(rt.evaluate, P.ADMISSIBLE, principal="a",
                          action_type="account_deletion", nonce=key)
    return (*_rejected(d, refusal, "a used key presented again with a modified action"),
            _admission(first))


def px_revocation_isolated(rt):
    """CT-R3-003, an unspecified proposal: revoking one principal leaves
    another principal's standing as it was."""
    revoked, other = _principal("revoked"), _principal("other")
    earlier = rt.evaluate(P.ADMISSIBLE, principal=other, action_type="wire_transfer")
    if not _admitted(earlier):
        return INCONCLUSIVE, f"the control request was not admitted (disposition={earlier.disposition})"
    facts = _admission(earlier)
    rt.revoke(revoked)
    if P.B_REVOCATION in rt.bounds and P.CLOCK in rt.capabilities:
        rt.elapse_past(P.B_REVOCATION)      # a revocation need only hold beyond the declared bound
    d, refusal = _attempt(rt.evaluate, P.ADMISSIBLE, principal=revoked, action_type="wire_transfer")
    if refusal is None and _admitted(d):
        return INCONCLUSIVE, "the revoked principal was still admitted: nothing to isolate", facts
    d, refusal = _attempt(rt.evaluate, P.ADMISSIBLE, principal=other, action_type="wire_transfer")
    if refusal is not None or not _admitted(d):
        how = refusal.code if refusal is not None else d.disposition
        return FAIL, f"revoking one principal stopped another principal's new request ({how})", facts
    if P.COMMIT not in rt.capabilities:
        return PASS, "revoking one principal left another principal's new request admitted", facts
    try:
        rt.commit(earlier)
    except P.Refused as e:
        return FAIL, f"revoking one principal blocked another principal's earlier grant ({e.code})", facts
    return (PASS, "revoking one principal left another principal's new request admitted "
                  "and its earlier grant committable", facts)


_RANK = {d: i for i, d in enumerate(P.RESTRICTIVENESS)}


def px_most_restrictive_governs(rt):
    """CT-R0-005. RFC-0 §4: when controls produce incompatible dispositions,
    the most restrictive one governs. For each pair of conditions the port can
    produce together, the check reads the disposition of each condition alone,
    then of both at once, in both orders. A result less restrictive than the
    stricter of the two is a failure. A stricter one is not: another control
    may apply to the combination."""
    seen = []
    for pair in sorted(tuple(sorted(c)) for c in rt.combinations if len(c) == 2):
        try:
            alone = []
            for intent in pair:
                rt.reset()
                alone.append(rt.evaluate(intent, principal=_principal("c"),
                                         action_type="wire_transfer").disposition)
            if alone[0] == alone[1]:
                continue                    # these two conditions do not conflict
            need = max(alone, key=_RANK.__getitem__)
            together = []
            for order in (pair, pair[::-1]):
                rt.reset()
                got = rt.evaluate_combined(order, principal=_principal("c"),
                                           action_type="wire_transfer").disposition
                if _RANK[got] < _RANK[need]:
                    return FAIL, (f"{pair[0]} ({alone[0]}) and {pair[1]} ({alone[1]}) together "
                                  f"gave {got}, submitted as {' + '.join(order)}: the less "
                                  "restrictive disposition prevailed")
                together.append(got)
        except P.Refused as e:
            return INCONCLUSIVE, f"a condition was refused without a disposition ({e.code})"
        seen.append(f"{pair[0]} ({alone[0]}) with {pair[1]} ({alone[1]}) gave "
                    + " and ".join(sorted(set(together))))
    if not seen:
        return INCONCLUSIVE, "no two conditions the port can combine produced different dispositions"
    return PASS, "the more restrictive disposition governed: " + "; ".join(seen)


# -- property checks at a declared bound --------------------------------------
# The harness sets no duration. Each check below needs a bound the port
# declares for the subject and asks the port to let that bound pass. No
# declared bound, no check.
#
# CT-R3-008 ("Rotated credentials invalidate prior grants") has no check. The
# index anchors it on RFC-3, and no clause of the frozen RFC-3 mentions
# rotation. RFC-6 §4.1 covers the rotation of keys and asks that old keys stay
# usable for an overlap period. The row needs an anchor before it gets a check.

def px_revocation_at_bound(rt):
    """CT-R3-002. RFC-3 §4.2: a revoked authority is not executable beyond the
    declared revocation bound. Nothing is asked of the time before it."""
    who = _principal("revoked")
    earlier = rt.evaluate(P.ADMISSIBLE, principal=who, action_type="wire_transfer")
    if not _admitted(earlier):
        return INCONCLUSIVE, f"the control request was not admitted (disposition={earlier.disposition})"
    facts = _admission(earlier)
    rt.revoke(who)
    rt.elapse_past(P.B_REVOCATION)
    bound = f"declared bound {rt.bounds[P.B_REVOCATION]:g} s"
    d, refusal = _attempt(rt.evaluate, P.ADMISSIBLE, principal=who, action_type="wire_transfer")
    state, details = _rejected(d, refusal, "past the bound, a new request from the revoked principal")
    if state != PASS or P.COMMIT not in rt.capabilities:
        return state, f"{details} ({bound})", facts
    try:
        rt.commit(earlier)
    except P.Refused:
        return PASS, f"{details}, and its earlier grant could not be committed ({bound})", facts
    return FAIL, f"past the bound, an earlier grant of the revoked principal was committed ({bound})", facts


def px_credential_expires(rt):
    """CT-R3-006. RFC-3 §2.2 and §2.3: a time-limited credential is honoured
    while valid and no longer once its declared lifetime has passed."""
    who = _principal("limited")
    first = rt.evaluate(P.EXPIRING_CREDENTIAL, principal=who, action_type="wire_transfer")
    if not _admitted(first):
        return INCONCLUSIVE, f"the credential was not admitted while valid (disposition={first.disposition})"
    rt.elapse_past(P.B_CREDENTIAL)
    d, refusal = _attempt(rt.evaluate, P.EXPIRING_CREDENTIAL, principal=who,
                          action_type="wire_transfer")
    state, details = _rejected(d, refusal, "the same credential, past its declared lifetime,")
    return state, f"{details} (declared lifetime {rt.bounds[P.B_CREDENTIAL]:g} s)", _admission(first)


# VEC-6-03. RFC-6 §3.2: a request whose timestamp falls outside the declared
# freshness window is rejected. The port builds the stale request.
px_stale_request = _must_reject(
    P.STALE_REQUEST, "a request submitted outside the declared freshness window")

# VEC-6-04. RFC-6 §4.2: a credential signed with a revoked key and presented
# after the revocation bound produces no executable authorization.
px_revoked_key = _must_reject(
    P.REVOKED_KEY, "a credential signed by a key revoked for longer than the declared bound")


def px_hold_expiry_fail_closed(rt):
    """REG-STATE-024. RFC-5 §2: a HOLD nobody answers within tau_k is rejected
    (HARD_VETO) unless a fail-degraded policy was pre-declared. A suspension
    that merely goes on is not a rejection: the check then does not conclude."""
    if rt.exhaustion_policy == "fail-degraded":
        return INCONCLUSIVE, "the deployment pre-declares a fail-degraded policy: the default does not apply"
    d = rt.evaluate(P.NEEDS_APPROVAL, principal=_principal("held"), action_type="wire_transfer")
    if d.disposition != "HOLD":
        return INCONCLUSIVE, f"no suspension to observe (disposition={d.disposition})"
    rt.elapse_past(P.B_TAU_K)
    window = f"declared window {rt.bounds[P.B_TAU_K]:g} s"
    rejected = None
    if P.COMMIT in rt.capabilities:
        try:
            rt.commit(d)
        except P.Refused as e:
            rejected = e.disposition == "HARD_VETO"
        else:
            return FAIL, f"a HOLD left unanswered past its window was committed ({window})"
    if P.EFFECTS in rt.capabilities:
        n = _effects(rt, d)
        if n:
            return FAIL, f"a HOLD left unanswered past its window matched {n} effect(s) ({window})"
    elif rejected is None:
        return INCONCLUSIVE, "the port can neither attempt the crossing nor observe effects"
    if rejected:
        return PASS, f"a HOLD left unanswered past its window was rejected with HARD_VETO ({window})"
    return (INCONCLUSIVE, "past its window the HOLD was not executable, and no rejection was "
                          f"recorded ({window})")


# -- property checks on degraded evidence -------------------------------------
# RFC-2 §4.2 asks for "specific tests for UNKNOWN, STALE, and CONTRADICTORY
# states to prove the implementation correctly defaults to HOLD/HARD_VETO
# rather than silently passing". Each check below submits the admissible
# attempt with one measurement degraded, for every measurement the port lists,
# and reads the disposition. How the runtime reaches it is not looked at.
#
# Rows of the index with no check of their own, and why:
#   REG-STATE-003  what a boundary can show of it (missing evidence is not
#                  handled like low confidence) is what REG-STATE-001 and -010
#                  read; the rest is how the runtime labels its evidence.
#   REG-STATE-005  the same law as REG-STATE-013 and -015, stated as the
#   REG-STATE-012  mechanism that produces it (Conservative Admissibility,
#                  worst-case plausible bounds). A disposition cannot show
#                  which mechanism produced it.

def _never_admitted(state, label, named=("HOLD", "HARD_VETO")):
    """The admissible attempt, with each listed measurement in `state` in
    turn, is never admitted. `named` are the dispositions the RFC names."""
    def run(rt):
        ok = _control(rt)
        if not _admitted(ok):
            return INCONCLUSIVE, f"the control request was not admitted (disposition={ok.disposition})"
        facts = _admission(ok)
        if state == P.E_CONTRADICTORY and rt.contradiction_resolution:
            return (INCONCLUSIVE, "the deployment pre-declares a resolution for contradictory "
                                  "measurements: the HOLD is not required", facts)
        admitted, as_named, otherwise = [], [], []
        for measurement in rt.degradations[state]:
            rt.reset()
            d, refusal = _attempt(rt.evaluate_degraded, state, measurement,
                                  principal=_principal("e"), action_type="wire_transfer")
            if refusal is not None:
                # No disposition at all. Where the RFC names several, a refusal
                # is as closed as any of them. Where it names one, it is not it.
                (as_named if len(named) > 1 else otherwise).append(f"{measurement} (refused)")
            elif _admitted(d):
                admitted.append(f"{measurement} ({d.disposition})")
            elif d.disposition in named:
                as_named.append(f"{measurement} ({d.disposition})")
            else:
                otherwise.append(f"{measurement} ({d.disposition})")
        if admitted:
            rest = as_named + otherwise
            return (FAIL, f"admitted with {label} evidence on: {', '.join(admitted)}"
                          + (f"; not admitted on: {', '.join(rest)}" if rest else ""), facts)
        if otherwise:
            return (INCONCLUSIVE, f"not admitted with {label} evidence, by another way than "
                                  f"{' or '.join(named)}: {', '.join(otherwise)}", facts)
        return PASS, f"never admitted with {label} evidence: {', '.join(as_named)}", facts
    return run


# REG-STATE-001. RFC-2 §2.5: "UNKNOWN defaults to HOLD or HARD_VETO, never PASS."
px_unknown_evidence = _never_admitted(P.E_UNKNOWN, "unknown")
# REG-STATE-002. RFC-2 §2.5: a stale measurement critical to an invariant gives
# HOLD or HARD_VETO.
px_stale_evidence = _never_admitted(P.E_STALE, "stale")
# REG-STATE-004. RFC-2 §2.5: contradictory measurements "MUST trigger a HOLD",
# unless a deterministic resolution is pre-declared.
px_contradictory_evidence = _never_admitted(P.E_CONTRADICTORY, "contradictory", named=("HOLD",))
# REG-STATE-010. RFC-2 §2.6: no guessed or interpolated value stands in for a
# missing measurement "to produce a best estimate for execution authorization".
px_missing_evidence = _never_admitted(P.E_MISSING, "missing")


def _ladder(rt, intent):
    """Dispositions of one attempt from full confidence down, one clean run each."""
    out = []
    for step in range(rt.confidence_steps):
        rt.reset()
        out.append(rt.evaluate_at_confidence(intent, step, principal=_principal("q"),
                                             action_type="wire_transfer").disposition)
    return out


def _widening(ladder):
    """First step whose disposition is less restrictive than an earlier one."""
    for step in range(1, len(ladder)):
        if _RANK[ladder[step]] < max(_RANK[d] for d in ladder[:step]):
            return step
    return None


def px_uncertainty_never_widens(rt):
    """REG-STATE-013. RFC-2 §2.8 and §4.1: as uncertainty increases, the
    admissible region shrinks or stays as it is. It never expands. Read on the
    admissible attempt, at each level of confidence the port can submit."""
    try:
        ladder = _ladder(rt, P.ADMISSIBLE)
    except P.Refused as e:
        return INCONCLUSIVE, f"a level of confidence was refused without a disposition ({e.code})"
    if ladder[0] not in P.ADMISSION_DISPOSITIONS:
        return INCONCLUSIVE, f"the attempt was not admitted at full confidence ({ladder[0]})"
    path = " > ".join(ladder)
    step = _widening(ladder)
    if step is not None:
        return FAIL, f"at step {step} of decreasing confidence the disposition widened: {path}"
    changed = "" if len(set(ladder)) > 1 else " (it did not change)"
    return PASS, (f"over {len(ladder)} levels of decreasing confidence the disposition never "
                  f"widened: {path}{changed}")


def px_confidence_never_upgrades(rt):
    """REG-STATE-015. RFC-2 §3.4: the modulator can only degrade a disposition,
    never upgrade it. Read on attempts that are restricted at full confidence:
    no lower level of confidence may give them a less restrictive disposition."""
    ok = _control(rt)
    if not _admitted(ok):
        return INCONCLUSIVE, f"the control request was not admitted (disposition={ok.disposition})"
    seen = []
    for intent in (P.INADMISSIBLE, P.NEEDS_APPROVAL):
        if intent not in rt.intents:
            continue
        try:
            ladder = _ladder(rt, intent)
        except P.Refused as e:
            return INCONCLUSIVE, f"a level of confidence was refused without a disposition ({e.code})"
        if ladder[0] in P.ADMISSION_DISPOSITIONS:
            continue                        # admitted at full confidence: not a restricted attempt
        step = _widening(ladder)
        if step is not None:
            return FAIL, (f"{intent}: {ladder[0]} at full confidence became {ladder[step]} at "
                          f"step {step}: {' > '.join(ladder)}")
        seen.append(f"{intent} {' > '.join(ladder)}")
    if not seen:
        return INCONCLUSIVE, "no attempt restricted at full confidence could be submitted at lower confidence"
    return PASS, "lower confidence never upgraded a restricted attempt: " + "; ".join(seen)


_E, _C = P.EVALUATE, P.COMMIT
_A, _I, _N, _H, _D = (frozenset({x}) for x in (P.ADMISSIBLE, P.INADMISSIBLE, P.NO_STANDING,
                                               P.NEEDS_APPROVAL, P.DENIED))
_none = frozenset()


def _vector(vector_id, requires, run, intents, at, *not_observed):
    return Scenario(vector_id, frozenset(requires), run, intents, at=at, not_observed=not_observed)


# Each entry ends with where the scenario observes and with what its result
# does not establish. A PASS is a PASS on the case submitted, no further.
_ONE_REPLAY = ("a replay presented at commit", "replays sent concurrently")
SCENARIOS = {s.vector_id: s for s in [
    _vector("C1", {_E}, c1, _N, AUTH,
            "structural states other than the one submitted"),
    _vector("C2", {_E}, c2, _I, AUTH,
            "points of the region other than the one submitted",
            "the thresholds themselves"),
    _vector("C3", {_E, _C, P.REVOKE}, c3, _A, EXEC,
            "a revocation during the commit or the execution: it lands between verdict and commit",
            "a propagation delay: the port applies the revocation at once"),
    _vector("C5", {_E, P.NONCE}, _replay("C5"), _A, PRE, *_ONE_REPLAY),
    _vector("CT-R4-001", {_E, _C}, r4_001, _A, EXEC,
            "each bound field taken alone: only the matching case is submitted",
            "the effect itself"),
    _vector("CT-R4-002", {_E, _C}, r4_002, _A, EXEC,
            "bound fields other than the action type"),
    _vector("CT-R4-003", {_E, P.NONCE}, _replay("CT-R4-003"), _A, PRE,
            "a reuse after a commit consumed the nonce: the replay comes before any commit",
            *_ONE_REPLAY),
    _vector("CT-R4-004", {_C, P.STALE_GRANT}, r4_004, _none, EXEC,
            "the passage of time across the bound: the grant is created already expired"),
    _vector("CT-R4-005", {_E, _C, P.STATE_DRIFT}, r4_005, _A, EXEC,
            "which state changes count as relevant: the port picks one",
            "a change during the execution"),
    _vector("CT-R4-006", {_E, _C}, r4_006, _N, EXEC,
            "a commit attempt on a HOLD: only a HARD_VETO is submitted"),
    _vector("CT-R4-007", {_E, P.RECEIPTS}, r4_007, _N, PROOF,
            "receipts for PASS, FLAG and HOLD: the receipt of a refusal is checked",
            "verification by a third party holding public material only: the port verifies",
            "fields other than the one altered"),
    _vector("CT-R4-008", {_E, P.MANIFEST}, r4_008, _A, PROOF,
            "deletion or truncation: one entry is altered in a copy",
            "anchoring outside the runtime"),
    _vector("CT-R2-002", {P.TENIR_SCORE}, r2_002, _none, MODEL,
            "inputs other than the one submitted",
            "determinism across processes or versions"),
    _vector("CT-R2-003", {P.TENIR_SCORE}, r2_003, _none, MODEL,
            "denominators near zero other than exactly zero"),
]}

_EF = frozenset({_E, P.EFFECTS})
_JOURNAL = ("an effect outside the journal the port reads",
            "an effect that appears after the declared effect window")


def _probe(vector_id, run, intents, *not_observed):
    return Scenario(vector_id, _EF, run, intents, normative=False, at=EXEC,
                    not_observed=_JOURNAL + not_observed)


PROBES = {s.vector_id: s for s in [
    _probe("HX-EFFECT-001", hx_refusal_zero_effects, _D),
    _probe("HX-EFFECT-002", hx_allow_exactly_one_effect, _A,
           "more than two crossing attempts", "attempts made concurrently"),
    _probe("HX-EFFECT-003", hx_unanswered_approval_zero_effects, _H,
           "what follows a late approval or the end of the approval window"),
    _probe("HX-EFFECT-004", hx_allow_after_refusal, _A | _D,
           "sequences longer than one refusal then one allowed call"),
]}

_M, _O, _V, _S, _K = (frozenset({P.ADMISSIBLE, x}) for x in (
    P.MALFORMED_CREDENTIAL, P.OUT_OF_SCOPE, P.INVARIANT_VIOLATED, P.STALE_REQUEST, P.REVOKED_KEY))
_T = frozenset({P.EXPIRING_CREDENTIAL})
_STATED = "that the bound is declared, versioned and signed: the port states it"
_SIMULATED = "under a simulated clock, timers and background expiry in real time"


_LISTED = ("measurements other than those the port lists",)


def _check(exercises, requires, run, intents, at, *not_observed, bounds=(), degradations=()):
    return Scenario(f"PX-{exercises}", frozenset(requires), run, intents, normative=False,
                    exercises=exercises, bounds=frozenset(bounds),
                    degradations=frozenset(degradations), at=at, not_observed=not_observed)


# In the order of VECTORS.md.
CHECKS = {s.vector_id: s for s in [
    _check("CT-R0-005", {_E, P.COMBINE}, px_most_restrictive_governs, _none, AUTH,
           "the disposition of each control inside the combined attempt: each condition is "
           "read alone, then both together",
           "more than two conditions at once",
           "combinations the port does not declare"),
    _check("CT-R3-001", {_E}, px_malformed_credential, _M, PRE,
           "that the rejection comes before evaluation",
           "malformations other than the one the port submits"),
    _check("CT-R3-002", {_E, P.REVOKE, P.CLOCK}, px_revocation_at_bound, _A, EXEC,
           "what the runtime does before the bound has passed",
           _STATED, _SIMULATED, bounds={P.B_REVOCATION}),
    _check("CT-R3-003", {_E, P.REVOKE}, px_revocation_isolated, _A, AUTH,
           "principals linked by a delegation",
           "revocations made concurrently"),
    _check("CT-R3-006", {_E, P.CLOCK}, px_credential_expires, _T, AUTH,
           "the start of validity (not_before)",
           "that the expiry is the one written in the credential: the port states the lifetime",
           _SIMULATED, bounds={P.B_CREDENTIAL}),
    _check("CT-R3-007", {_E}, px_out_of_scope, _O, AUTH,
           "scope dimensions other than the one the port submits (targets, value limits, time)"),
    _check("VEC-6-02", {_E, P.NONCE}, px_key_reuse_modified_action, _A, PRE,
           "a replay with an identical payload",
           "that the key is unique or random"),
    _check("VEC-6-03", {_E}, px_stale_request, _S, PRE,
           "a timestamp in the future",
           "the exact edges of the window", _STATED, bounds={P.B_FRESHNESS}),
    _check("VEC-6-04", {_E}, px_revoked_key, _K, PRE,
           "a key revoked for less than the bound",
           "how the revocation reached the runtime", _STATED, bounds={P.B_REVOCATION}),
    _check("REG-STATE-001", {_E, P.DEGRADE}, px_unknown_evidence, _A, AUTH,
           *_LISTED, "unknown evidence on an attempt that is not otherwise admissible",
           degradations={P.E_UNKNOWN}),
    _check("REG-STATE-002", {_E, P.DEGRADE}, px_stale_evidence, _A, AUTH,
           "that the stale measurement is left out of the interpretation: only the "
           "disposition is read",
           "the edge of the freshness window", *_LISTED, degradations={P.E_STALE}),
    _check("REG-STATE-004", {_E, P.DEGRADE}, px_contradictory_evidence, _A, AUTH,
           "a pre-declared resolution policy",
           "more than two measurements that disagree", *_LISTED,
           degradations={P.E_CONTRADICTORY}),
    _check("REG-STATE-010", {_E, P.DEGRADE}, px_missing_evidence, _A, AUTH,
           "the other inferences RFC-2 §2.6 prohibits: intent guessed, a state assumed "
           "unchanged without a new measurement, an invariant check skipped for its cost",
           "that the refusal is deliberate: an error raised before any disposition counts as one",
           *_LISTED, degradations={P.E_MISSING}),
    _check("REG-STATE-013", {_E, P.CONFIDENCE}, px_uncertainty_never_widens, _A, AUTH,
           "that lower confidence shrinks the region at all: an unchanged disposition passes",
           "that worst-case plausible bounds were used: only the disposition is read",
           "points of the admissible region other than the one submitted"),
    _check("REG-STATE-014", {_E}, px_hard_invariant, _V, AUTH,
           "that the scoring was bypassed: only the disposition is read",
           "invariants other than the one the port submits"),
    _check("REG-STATE-015", {_E, P.CONFIDENCE}, px_confidence_never_upgrades, _none, AUTH,
           "restricted attempts other than those the port submits",
           "a change of confidence upward"),
    _check("REG-STATE-024", {_E, P.CLOCK}, px_hold_expiry_fail_closed, _H, EXEC,
           "that tau_k was derived from an organizational constraint",
           "a pre-declared fail-degraded policy",
           "the review capacity Shadow Mode requires",
           "on a runtime with no separate commit, a rejection as opposed to a suspension "
           "that never ends",
           _SIMULATED, bounds={P.B_TAU_K}),
]}
