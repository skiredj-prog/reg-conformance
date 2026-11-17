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


def hx_refusal_zero_effects(rt):
    d = rt.evaluate(P.DENIED, principal=_principal("a"), action_type="count")
    if d.disposition not in ("HARD_VETO", "HOLD"):
        return INCONCLUSIVE, f"no refusal to observe (disposition={d.disposition})"
    _cross(rt, d)
    n = rt.observed_effects(d)
    return (PASS, "refusal matched zero observed effects") if n == 0 \
        else (FAIL, f"refusal matched {n} observed effect(s)")


def hx_allow_exactly_one_effect(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="count")
    if not _admitted(d):
        return INCONCLUSIVE, f"no allow to observe (disposition={d.disposition})"
    _cross(rt, d)
    _cross(rt, d)               # a second attempt on the same grant, where one exists
    n = rt.observed_effects(d)
    if n == 1:
        return PASS, "allow matched exactly one observed effect" + _via(d), _admission(d)
    return FAIL, f"allow matched {n} observed effect(s)", _admission(d)


def hx_unanswered_approval_zero_effects(rt):
    d = rt.evaluate(P.NEEDS_APPROVAL, principal="a", action_type="count")
    if d.disposition == "PASS":
        return FAIL, "call needing approval was allowed without one"
    _cross(rt, d)
    n = rt.observed_effects(d)
    return (PASS, f"unanswered approval gave {d.disposition} and zero observed effects") if n == 0 \
        else (FAIL, f"unanswered approval matched {n} observed effect(s)")


def hx_allow_after_refusal(rt):
    refused = rt.evaluate(P.DENIED, principal="a", action_type="count")
    allowed = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="count")
    if not _admitted(allowed):
        return INCONCLUSIVE, f"no allow after the refusal (disposition={allowed.disposition})"
    _cross(rt, allowed)
    a, b = rt.observed_effects(refused), rt.observed_effects(allowed)
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


_E, _C = P.EVALUATE, P.COMMIT
_A, _I, _N, _H, _D = (frozenset({x}) for x in (P.ADMISSIBLE, P.INADMISSIBLE, P.NO_STANDING,
                                               P.NEEDS_APPROVAL, P.DENIED))
_none = frozenset()
SCENARIOS = {s.vector_id: s for s in [
    Scenario("C1", frozenset({_E}), c1, _N),
    Scenario("C2", frozenset({_E}), c2, _I),
    Scenario("C3", frozenset({_E, _C, P.REVOKE}), c3, _A),
    Scenario("C5", frozenset({_E, P.NONCE}), _replay("C5"), _A),
    Scenario("CT-R4-001", frozenset({_E, _C}), r4_001, _A),
    Scenario("CT-R4-002", frozenset({_E, _C}), r4_002, _A),
    Scenario("CT-R4-003", frozenset({_E, P.NONCE}), _replay("CT-R4-003"), _A),
    Scenario("CT-R4-004", frozenset({_C, P.STALE_GRANT}), r4_004, _none),
    Scenario("CT-R4-005", frozenset({_E, _C, P.STATE_DRIFT}), r4_005, _A),
    Scenario("CT-R4-006", frozenset({_E, _C}), r4_006, _N),
    Scenario("CT-R4-007", frozenset({_E, P.RECEIPTS}), r4_007, _N),
    Scenario("CT-R4-008", frozenset({_E, P.MANIFEST}), r4_008, _A),
    Scenario("CT-R2-002", frozenset({P.TENIR_SCORE}), r2_002, _none),
    Scenario("CT-R2-003", frozenset({P.TENIR_SCORE}), r2_003, _none),
]}

_EF = frozenset({_E, P.EFFECTS})
PROBES = {s.vector_id: s for s in [
    Scenario("HX-EFFECT-001", _EF, hx_refusal_zero_effects, _D, normative=False),
    Scenario("HX-EFFECT-002", _EF, hx_allow_exactly_one_effect, _A, normative=False),
    Scenario("HX-EFFECT-003", _EF, hx_unanswered_approval_zero_effects, _H, normative=False),
    Scenario("HX-EFFECT-004", _EF, hx_allow_after_refusal, _A | _D, normative=False),
]}

_M, _O, _V = (frozenset({P.ADMISSIBLE, x}) for x in (P.MALFORMED_CREDENTIAL, P.OUT_OF_SCOPE,
                                                     P.INVARIANT_VIOLATED))


def _check(exercises, requires, run, intents):
    return Scenario(f"PX-{exercises}", frozenset(requires), run, intents,
                    normative=False, exercises=exercises)


# In the order of VECTORS.md.
CHECKS = {s.vector_id: s for s in [
    _check("CT-R0-005", {_E, P.COMBINE}, px_most_restrictive_governs, _none),
    _check("CT-R3-001", {_E}, px_malformed_credential, _M),
    _check("CT-R3-003", {_E, P.REVOKE}, px_revocation_isolated, _A),
    _check("CT-R3-007", {_E}, px_out_of_scope, _O),
    _check("VEC-6-02", {_E, P.NONCE}, px_key_reuse_modified_action, _A),
    _check("REG-STATE-014", {_E}, px_hard_invariant, _V),
]}
