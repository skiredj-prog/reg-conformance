"""Regression controls for current REG E8 API — not a production witness.

All tests are same-process or mocked. No external host, G1/G4-A grant,
real provider effect, or independently provisioned floor is exercised.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from fastapi.testclient import TestClient

from runtime.quarantine_gate import check_quarantine_before_admission
from witness.checkpoint import LocalCheckpoint, load_checkpoint, save_checkpoint
from witness.client import (
    PinnedWitnessClient, WitnessChainBroken, WitnessIntegrityError,
    WitnessUnavailable,
)
from witness.protocol import HEAD_KEYS, head_digest
from witness.service import create_app

from test_witness_protocol import lab as lab_fixture  # noqa: F401
from test_witness_protocol import make_request


def _mock_client(lab, *, code, body, controller=False):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            code, text=body, headers={"content-type": "text/html"}
        )
    )
    session = httpx.Client(transport=transport)
    return PinnedWitnessClient(
        "http://witness.invalid", lab["public"],
        "lab-realm", "lab-store", http_client=session,
        engine_private_key=lab["engine"] if controller else None,
    )


def test_advance_http_500_html_returns_typed_unavailable_not_json_crash(lab_fixture):
    """Current API raises WitnessUnavailable; it does NOT return AdvanceResult."""
    lab = lab_fixture
    client = _mock_client(
        lab, code=500, body="<html>server failure</html>", controller=True
    )
    req = make_request(lab, "http-500", "sha256:"+"1"*64, "sha256:"+"2"*64)
    with pytest.raises(WitnessUnavailable, match="UNKNOWN"):
        client.advance(req)


def test_advance_http_200_non_json_is_untrusted_and_fails_closed(lab_fixture):
    lab = lab_fixture
    client = _mock_client(
        lab, code=200, body="<html>not JSON</html>", controller=True
    )
    req = make_request(lab, "bad-json", "sha256:"+"1"*64, "sha256:"+"2"*64)
    with pytest.raises(WitnessIntegrityError, match="untrusted"):
        client.advance(req)


def test_signed_read_http_500_html_is_unavailable(lab_fixture):
    client = _mock_client(lab_fixture, code=500, body="<html>failure</html>")
    with pytest.raises(WitnessUnavailable, match="read unavailable"):
        client.get_head()


def test_history_404_identifies_missing_sequence(lab_fixture):
    with pytest.raises(WitnessChainBroken, match=r"seq 17"):
        lab_fixture["reader"].get_head_at(17)


def test_q6d_empty_witness_db_is_rejected_against_explicit_floor(lab_fixture, tmp_path):
    """Witness reset is detectable ONLY against an externally retained floor.

    The test fixture stores its floor locally; that is NOT independent trust.
    A deployment must pin the floor outside the compromised witness domain.
    """
    lab = lab_fixture
    req = make_request(
        lab, "before-wipe", "sha256:"+"1"*64, "sha256:"+"2"*64
    )
    assert lab["controller"].advance(req)["decision"] == "ADVANCED"
    prior = lab["reader"].get_head()
    checkpoint_path = tmp_path / "outside-witness-checkpoint.json"
    save_checkpoint(
        checkpoint_path,
        LocalCheckpoint(
            sequence=prior["sequence"],
            head_digest=head_digest({k: prior[k] for k in HEAD_KEYS}),
        ),
    )
    floor = load_checkpoint(checkpoint_path)
    assert floor.sequence == 1

    # Reinitialize an entirely empty DB under the SAME witness identity
    # and SAME signing key. This is a stronger continuity attack than
    # rolling the witness back to a previously signed nonempty history.
    old_store = lab["app"].state.witness
    witness_key_path = tmp_path / "old-witness.key"
    witness_key_path.write_bytes(old_store.key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    engine_public_path = tmp_path / "old-engine.pub"
    engine_public_path.write_bytes(lab["engine"].public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ))
    empty_app = create_app(
        str(tmp_path / "wiped-witness.db"),
        witness_key_path, engine_public_path,
        realm_id="lab-realm", store_id="lab-store", epoch=0,
    )
    empty_client = PinnedWitnessClient(
        "http://testserver", lab["public"], "lab-realm", "lab-store",
        http_client=TestClient(empty_app),
    )
    assert empty_client.get_head() is None
    with pytest.raises(WitnessChainBroken, match="missing despite pinned floor"):
        empty_client.walk_back(minimum=floor)

    # The Q6 gate also refuses to admit if the witness head is missing,
    # even when the local quarantine is a syntactically valid snapshot.
    local_quarantine = tmp_path / "quarantine.json"
    local_quarantine.write_text(
        '{"realm_id":"lab-realm","store_id":"lab-store",'
        '"generation":0,"active":false}', encoding="utf-8",
    )
    assert check_quarantine_before_admission(empty_client, local_quarantine) == {
        "decision": "HOLD_GLOBAL", "reason": "E8_HEAD_MISSING",
    }


def test_no_floor_cannot_establish_witness_history_after_wipe(lab_fixture, tmp_path):
    """Document the limitation: no external floor => no continuity proof."""
    lab = lab_fixture
    old_store = lab["app"].state.witness
    witness_key_path = tmp_path / "key"
    witness_key_path.write_bytes(old_store.key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    engine_pub = tmp_path / "engine.pub"
    engine_pub.write_bytes(lab["engine"].public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    empty = create_app(
        str(tmp_path / "empty.db"), witness_key_path, engine_pub,
        realm_id="lab-realm", store_id="lab-store", epoch=0,
    )
    client = PinnedWitnessClient(
        "http://testserver", lab["public"], "lab-realm", "lab-store",
        http_client=TestClient(empty),
    )
    # walk_back without a minimum verifies only an empty current chain.
    # It MUST NOT be represented as a proof of no prior witness history.
    assert client.walk_back() == 0
