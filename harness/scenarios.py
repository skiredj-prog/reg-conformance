"""Runtime-neutral scenarios, one per executable vector.

A scenario returns (state, details). State is one of the runner's reporting
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
    normative: bool = True      # False = harness probe, outside the REG vector set


def _nonce() -> str:
    return uuid.uuid4().hex


def _principal(tag: str) -> str:
    return f"{tag}-{uuid.uuid4().hex[:8]}"


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
    if d.disposition != "PASS":
        return INCONCLUSIVE, "could not establish the valid-verdict precondition"
    rt.revoke(who)
    try:
        rt.commit(d)
    except P.Refused as e:
        if e.code == P.R_STANDING_REVOKED and e.disposition == "HARD_VETO":
            return PASS, "post-verdict revocation produced HARD_VETO; commit blocked"
        return INCONCLUSIVE, f"commit refused without establishing HARD_VETO: {e}"
    return FAIL, "commit accepted after revocation"


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
    if d.disposition != "PASS":
        return FAIL, f"disposition={d.disposition}"
    rt.commit(d, action_type="wire_transfer")
    return PASS, "valid grant bound and committed"


def r4_002(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if d.disposition != "PASS":
        return FAIL, "no PASS"
    try:
        rt.commit(d, action_type="account_deletion")
    except P.Refused as e:
        return (PASS, "payload binding violation refused") if e.code == P.R_BINDING else (FAIL, str(e))
    return FAIL, "binding violation not detected"


def r4_004(rt):
    d = rt.stale_grant(action_type="wire_transfer")
    try:
        rt.commit(d)
    except P.Refused as e:
        return (PASS, "expired grant refused") if e.code == P.R_EXPIRED else (FAIL, str(e))
    return FAIL, "expired grant accepted"


def r4_005(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="wire_transfer")
    if d.disposition != "PASS":
        return FAIL, "no PASS"
    change = rt.drift_state()
    try:
        rt.commit(d)
    except P.Refused as e:
        if e.code == P.R_STATE_DRIFT and e.disposition == "HARD_VETO":
            return PASS, f"state drift produced HARD_VETO ({change})"
        return FAIL, str(e)
    return FAIL, "state drift not detected"


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
# counted in the 56-vector totals.

def hx_refusal_zero_effects(rt):
    d = rt.evaluate(P.NO_STANDING, principal=_principal("u"), action_type="count")
    if d.disposition not in ("HARD_VETO", "HOLD"):
        return INCONCLUSIVE, f"no refusal to observe (disposition={d.disposition})"
    try:
        rt.commit(d)
    except P.Refused:
        pass
    n = rt.observed_effects(d)
    return (PASS, "refusal matched zero observed effects") if n == 0 \
        else (FAIL, f"refusal matched {n} observed effect(s)")


def hx_allow_exactly_one_effect(rt):
    d = rt.evaluate(P.ADMISSIBLE, principal="a", action_type="count")
    if d.disposition != "PASS":
        return INCONCLUSIVE, f"no allow to observe (disposition={d.disposition})"
    rt.commit(d)
    try:
        rt.commit(d)            # second attempt on the same grant
    except P.Refused:
        pass
    n = rt.observed_effects(d)
    return (PASS, "allow matched exactly one observed effect") if n == 1 \
        else (FAIL, f"allow matched {n} observed effect(s)")


_E, _C = P.EVALUATE, P.COMMIT
SCENARIOS = {s.vector_id: s for s in [
    Scenario("C1", frozenset({_E}), c1),
    Scenario("C2", frozenset({_E}), c2),
    Scenario("C3", frozenset({_E, _C, P.REVOKE}), c3),
    Scenario("C5", frozenset({_E, P.NONCE}), _replay("C5")),
    Scenario("CT-R4-001", frozenset({_E, _C}), r4_001),
    Scenario("CT-R4-002", frozenset({_E, _C}), r4_002),
    Scenario("CT-R4-003", frozenset({_E, P.NONCE}), _replay("CT-R4-003")),
    Scenario("CT-R4-004", frozenset({_C, P.STALE_GRANT}), r4_004),
    Scenario("CT-R4-005", frozenset({_E, _C, P.STATE_DRIFT}), r4_005),
    Scenario("CT-R4-006", frozenset({_E, _C}), r4_006),
    Scenario("CT-R4-007", frozenset({_E, P.RECEIPTS}), r4_007),
    Scenario("CT-R4-008", frozenset({_E, P.MANIFEST}), r4_008),
    Scenario("CT-R2-002", frozenset({P.TENIR_SCORE}), r2_002),
    Scenario("CT-R2-003", frozenset({P.TENIR_SCORE}), r2_003),
]}

PROBES = {s.vector_id: s for s in [
    Scenario("HX-EFFECT-001", frozenset({_E, _C, P.EFFECTS}), hx_refusal_zero_effects, normative=False),
    Scenario("HX-EFFECT-002", frozenset({_E, _C, P.EFFECTS}), hx_allow_exactly_one_effect, normative=False),
]}
