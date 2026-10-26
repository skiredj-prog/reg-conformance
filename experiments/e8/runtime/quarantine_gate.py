"""E8-NEG-Q6 experimental local-quarantine integrity gate.

This gate returns only ELIGIBLE_FOR_FURTHER_CHECKS, NEVER a real execution
authorization. There is NO actual G1/G4-A admission or effect dispatch here.
"""
import hashlib
import json
from pathlib import Path

QUARANTINE_DOMAIN = b"REG-E8-LAB-QUARANTINE-v1\x00"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def quarantine_digest(state):
    if not isinstance(state, dict) or set(state) != {
        "realm_id", "store_id", "generation", "active",
    }:
        raise ValueError("invalid quarantine snapshot")
    if (type(state["generation"]) is not int or state["generation"] < 0
            or type(state["active"]) is not bool
            or not all(isinstance(state[x], str) and state[x]
                       for x in ("realm_id", "store_id"))):
        raise ValueError("invalid quarantine fields")
    return "sha256:" + hashlib.sha256(
        QUARANTINE_DOMAIN + canonical(state)
    ).hexdigest()


def check_quarantine_before_admission(client, local_path):
    try:
        # Runtime-controllable local evidence is NEVER its own authority.
        state = json.loads(Path(local_path).read_text(encoding="utf-8"))
        local_digest = quarantine_digest(state)
        witness_head = client.get_head()  # nonce-bound signed, pinned read
        if witness_head is None:
            return {"decision": "HOLD_GLOBAL", "reason": "E8_HEAD_MISSING"}
        if (state["realm_id"] != witness_head["realm_id"]
                or state["store_id"] != witness_head["store_id"]):
            return {"decision": "HOLD_GLOBAL", "reason": "E8_SCOPE_MISMATCH"}
        if local_digest != witness_head["quarantine_digest"]:
            return {"decision": "HOLD_GLOBAL", "reason": "E8_Q6_ROLLBACK_DETECTED"}
        if state["active"]:
            return {"decision": "HOLD_GLOBAL", "reason": "QUARANTINE_ACTIVE"}
        # This is not permission to dispatch. G1's authenticated single-use
        # grant, CAS and atomically guarded commit remain missing.
        return {
            "decision": "ELIGIBLE_FOR_FURTHER_CHECKS",
            "reason": "QUARANTINE_SNAPSHOT_MATCHES_ANCHOR",
        }
    except (OSError, ValueError, KeyError, TypeError, UnicodeError):
        return {"decision": "HOLD_GLOBAL", "reason": "E8_LOCAL_QUARANTINE_UNTRUSTED"}
    except Exception:
        # Real witness client raises typed witness errors on failed signature,
        # read staleness and network failure. Never silently continue.
        return {"decision": "HOLD_GLOBAL", "reason": "E8_WITNESS_UNAVAILABLE_OR_UNTRUSTED"}
