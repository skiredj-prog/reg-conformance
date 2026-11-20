"""Independent W4.3 event-state oracle.

Separate from proof01_w4.semantic: does not import its replay engine.
This oracle computes the expected *trace-internal* bookkeeping only.
It is NOT a proof of real provider effects or complete capture.
"""
from collections import defaultdict

class OracleReject(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def reconstruct(events):
    """Replay already-authenticated payloads; signature checks belong to verifier."""
    states = {}
    attempts = {}
    budgets = defaultdict(lambda: {"reserved": 0, "committed": 0})
    capacities = {}
    provider_effect_ids = set()
    legal = {
        "RESERVED": {None},
        "DISPATCHING": {"RESERVED"},
        "PROVIDER_EXECUTED": {"DISPATCHING"},
        "REPAIR": {"PROVIDER_EXECUTED"},
        "COMMITTED": {"PROVIDER_EXECUTED", "REPAIR"},
    }
    for sequence, ev in enumerate(events, start=1):
        if ev.get("seq") != sequence:
            raise OracleReject("SEQUENCE")
        kind = ev.get("kind")
        aid = ev.get("attempt_id")
        resource = ev.get("resource_id")
        quantity = ev.get("amount")
        ceiling = ev.get("capacity")
        if kind not in legal or not isinstance(aid, str) or not aid or not isinstance(resource, str) or not resource:
            raise OracleReject("FIELDS")
        if type(quantity) is not int or quantity <= 0 or type(ceiling) is not int or ceiling < 0:
            raise OracleReject("FIELDS")
        current = states.get(aid)
        if current not in legal[kind]:
            raise OracleReject("TRANSITION")
        binding = (resource, quantity, ceiling)
        if aid in attempts and attempts[aid] != binding:
            raise OracleReject("BINDING")
        attempts[aid] = binding
        if resource in capacities and capacities[resource] != ceiling:
            raise OracleReject("CAPACITY")
        capacities[resource] = ceiling
        if kind == "RESERVED":
            budgets[resource]["reserved"] += quantity
        elif kind == "COMMITTED":
            budgets[resource]["reserved"] -= quantity
            budgets[resource]["committed"] += quantity
        if any(x < 0 for x in budgets[resource].values()) or sum(budgets[resource].values()) > ceiling:
            raise OracleReject("I8")
        if kind == "PROVIDER_EXECUTED":
            receipt = ev.get("effect_id")
            if not isinstance(receipt, str) or not receipt or receipt in provider_effect_ids:
                raise OracleReject("DUPLICATE_RECEIPT")
            provider_effect_ids.add(receipt)
        states[aid] = kind
    return {"final_states": states, "balances": dict(budgets), "event_count": len(events)}


def compare_report(report, authenticated_events):
    """Fail on verifier/oracle disagreement. Only for synthetic wire v1."""
    if report.get("outcome") != "VERIFIED" or report.get("code") != "SIGNED_TRACE_VALID":
        return {"outcome": "INDETERMINATE", "reason": "VERIFIER_NOT_POSITIVE"}
    try:
        expected = reconstruct(authenticated_events)
    except OracleReject as exc:
        return {"outcome": "REFUTED", "reason": "ORACLE_" + exc.code}
    for key, value in (("final_states", expected["final_states"]), ("balances", expected["balances"]),
                       ("events", expected["event_count"])):
        if report.get(key) != value:
            return {"outcome": "REFUTED", "reason": "DIFFERENTIAL_MISMATCH_" + key.upper()}
    return {"outcome": "VERIFIED", "reason": "TRACE_INTERNAL_DIFFERENTIAL_AGREEMENT",
            "limits": "Only the supplied synthetic authenticated event trace; no independent effect completeness"}
