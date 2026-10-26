"""E8-NEG-Q6 **model**: restore LOCAL quarantine, not the witness database.

The witness is on another SQLite store, but here runs in the same test process.
This proves a bounded signed-head comparison, NOT production Q6 closure:
there is no actual G1/G4-A dispatch, host/UID separation, or external pinning.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from runtime.quarantine_gate import (
    check_quarantine_before_admission, quarantine_digest,
)
from witness.protocol import HEAD_KEYS, head_digest, GENESIS_DIGEST

from test_witness_protocol import lab as lab_fixture  # noqa: F401
from test_witness_protocol import make_request


def local_state(generation, active):
    return {
        "realm_id": "lab-realm", "store_id": "lab-store",
        "generation": generation, "active": active,
    }


def anchor_quarantine(lab, request_id, state):
    head = lab["reader"].get_head()
    req = make_request(
        lab, request_id, "sha256:"+"b"*64,
        quarantine_digest(state), prior=head
    )
    out = lab["controller"].advance(req)
    assert out["decision"] == "ADVANCED"
    assert lab["reader"].get_head()["quarantine_digest"] == quarantine_digest(state)


def test_e8_neg_q6_old_inactive_quarantine_snapshot_restored(lab_fixture, tmp_path):
    """Restored VALID inactive local state must fail against newer witness head."""
    lab = lab_fixture
    path = tmp_path / "quarantine.json"
    q0 = local_state(0, False)
    q1 = local_state(1, True)

    # Historical legal inactive snapshot.
    path.write_text(json.dumps(q0))
    anchor_quarantine(lab, "q0", q0)
    assert check_quarantine_before_admission(lab["reader"], path)["decision"] == (
        "ELIGIBLE_FOR_FURTHER_CHECKS"
    )

    # Authorized security transition: witness now anchors active quarantine.
    path.write_text(json.dumps(q1))
    anchor_quarantine(lab, "q1", q1)
    assert check_quarantine_before_admission(lab["reader"], path) == {
        "decision": "HOLD_GLOBAL", "reason": "QUARANTINE_ACTIVE",
    }
    trusted_head = lab["reader"].get_head()
    assert trusted_head["sequence"] == 2

    # T2 adversary swaps local file back to a formerly valid inactive copy.
    path.write_text(json.dumps(q0))
    out = check_quarantine_before_admission(lab["reader"], path)
    assert out == {
        "decision": "HOLD_GLOBAL", "reason": "E8_Q6_ROLLBACK_DETECTED",
    }
    assert lab["reader"].get_head() == trusted_head
    # No business commit/dispatch path exists in this model.


def test_e8_neg_q1_deleted_local_quarantine_fails_closed(lab_fixture, tmp_path):
    lab = lab_fixture
    path = tmp_path / "quarantine.json"
    q0 = local_state(0, False)
    path.write_text(json.dumps(q0))
    anchor_quarantine(lab, "q0", q0)
    path.unlink()
    out = check_quarantine_before_admission(lab["reader"], path)
    assert out == {
        "decision": "HOLD_GLOBAL", "reason": "E8_LOCAL_QUARANTINE_UNTRUSTED",
    }


def test_quarantine_forged_equal_generation_is_rejected(lab_fixture, tmp_path):
    lab = lab_fixture
    path = tmp_path / "quarantine.json"
    q0 = local_state(0, False)
    anchor_quarantine(lab, "q0", q0)
    forged = dict(q0, active=True)
    path.write_text(json.dumps(forged))
    assert check_quarantine_before_admission(lab["reader"], path)["reason"] == (
        "E8_Q6_ROLLBACK_DETECTED"
    )
