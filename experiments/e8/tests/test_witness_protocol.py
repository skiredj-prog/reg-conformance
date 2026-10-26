"""Bounded E8 witness protocol tests; in-process ASGI, NOT independent proof."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient

from witness.client import (
    PinnedWitnessClient, WitnessIntegrityError, WitnessKeySubstitution,
)
from witness.protocol import (
    ADVANCE_CONTEXT, GENESIS_DIGEST, HEAD_KEYS, head_digest, sign,
)
from witness.service import create_app


def write_keys(root):
    root.mkdir(parents=True, exist_ok=True)
    witness = Ed25519PrivateKey.generate()
    engine = Ed25519PrivateKey.generate()
    private = root / "witness_signing.key"
    public = root / "witness_pub.pem"
    engine_pub = root / "engine_pub.pem"
    for target, key in ((private, witness),):
        target.write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ))
    for target, key in ((public, witness.public_key()),
                        (engine_pub, engine.public_key())):
        target.write_bytes(key.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    return private, public, engine_pub, engine


@pytest.fixture
def lab(tmp_path):
    private, public, engine_pub, engine = write_keys(tmp_path / "keys")
    app = create_app(
        str(tmp_path / "witness.db"), private, engine_pub,
        realm_id="lab-realm", store_id="lab-store", epoch=0
    )
    session = TestClient(app)
    reader = PinnedWitnessClient(
        "http://testserver", public, "lab-realm", "lab-store",
        http_client=session
    )
    controller = PinnedWitnessClient(
        "http://testserver", public, "lab-realm", "lab-store",
        http_client=session, engine_private_key=engine
    )
    return {
        "app": app, "http": session, "public": public,
        "engine": engine, "reader": reader, "controller": controller,
    }


def make_request(lab, request_id, state, quarantine, *, prior=None):
    prior = lab["reader"].get_head() if prior is None else prior
    predecessor = (
        GENESIS_DIGEST if prior is None else head_digest({
            k: prior[k] for k in HEAD_KEYS
        })
    )
    return {
        "protocol": "reg-e8-advance-lab-v0.1",
        "request_id": request_id, "realm_id": "lab-realm",
        "store_id": "lab-store", "epoch": 0,
        "expected_prev_sequence": 0 if prior is None else prior["sequence"],
        "expected_prev_digest": predecessor,
        "state_digest": state, "key_digest": "sha256:" + "a" * 64,
        "quarantine_digest": quarantine,
    }


def test_signed_monotone_advance_and_fresh_read(lab):
    assert lab["reader"].get_head() is None
    req = make_request(lab, "req-1", "sha256:"+"1"*64, "sha256:"+"2"*64)
    res = lab["controller"].advance(req)
    assert res["decision"] == "ADVANCED"
    head = lab["reader"].get_head()
    assert head["sequence"] == 1
    assert head["state_digest"] == req["state_digest"]
    assert head["previous_head_digest"] == GENESIS_DIGEST
    assert lab["reader"].walk_back() == 1
    req2 = make_request(lab, "req-2", "sha256:"+"3"*64, "sha256:"+"4"*64)
    assert lab["controller"].advance(req2)["decision"] == "ADVANCED"
    assert lab["reader"].get_head()["sequence"] == 2
    assert lab["reader"].walk_back() == 2


def test_unsigned_runtime_cannot_advance_witness(lab):
    body = make_request(lab, "unauthorized", "sha256:"+"1"*64, "sha256:"+"2"*64)
    res = lab["http"].post("/advance", json={"body": body, "signature": "forged"})
    assert res.status_code == 403
    assert lab["reader"].get_head() is None
    with pytest.raises(WitnessIntegrityError):
        lab["reader"].advance(body)  # runtime has no engine signing key


def test_cas_conflict_and_request_replay(lab):
    first = make_request(lab, "first", "sha256:"+"1"*64, "sha256:"+"2"*64)
    other = make_request(lab, "other", "sha256:"+"3"*64, "sha256:"+"2"*64)
    assert lab["controller"].advance(first)["decision"] == "ADVANCED"
    assert lab["controller"].advance(other)["decision"] == "CONFLICT"
    again = lab["controller"].advance(first)
    assert again["decision"] == "ALREADY_ADVANCED"
    changed = dict(first, state_digest="sha256:"+"4"*64)
    assert lab["controller"].advance(changed)["reason"] == "E8_REQUEST_CONFLICT"
    assert lab["reader"].get_head()["sequence"] == 1


def test_wrong_key_fails_signature_verification(lab, tmp_path):
    alien = Ed25519PrivateKey.generate().public_key()
    path = tmp_path / "wrong.pub"
    path.write_bytes(alien.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ))
    reader = PinnedWitnessClient(
        "http://testserver", path, "lab-realm", "lab-store",
        http_client=lab["http"]
    )
    with pytest.raises(WitnessIntegrityError):
        reader.get_head()


def test_nonce_read_prevents_replay_of_earlier_signed_head(lab):
    from unittest.mock import Mock
    import json
    import secrets
    # An attacker who replays a formerly signed response cannot satisfy
    # the client's newly chosen random nonce.
    old_nonce = secrets.token_hex(16)
    frozen = lab["http"].get("/head", params={"nonce": old_nonce}).json()
    transport = Mock()
    response = Mock()
    response.status_code = 200
    response.raise_for_status.return_value = None
    response.json.return_value = frozen
    transport.get.return_value = response
    reader = PinnedWitnessClient(
        "http://testserver", lab["public"], "lab-realm", "lab-store",
        http_client=transport
    )
    with pytest.raises(WitnessIntegrityError, match="stale"):
        reader.get_head()


def test_untrusted_head_update_or_delete_rejected_by_triggers(lab):
    import sqlite3
    db = lab["app"].state.witness.db_path
    req = make_request(lab, "first", "sha256:"+"1"*64, "sha256:"+"2"*64)
    lab["controller"].advance(req)
    with sqlite3.connect(db) as con:
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("DELETE FROM witness_head")
        with pytest.raises(sqlite3.IntegrityError):
            con.execute("UPDATE witness_head SET signature='evil'")
    assert lab["reader"].get_head()["sequence"] == 1


def test_store_identity_cannot_be_silently_reprovisioned(lab, tmp_path):
    from witness.service import WitnessStore, load_private, load_public
    # Even with the same signing material the stored scope is fixed.
    engine = lab["engine"]
    witness = lab["app"].state.witness
    with pytest.raises(ValueError, match="identity"):
        WitnessStore(witness.db_path, witness.key, engine.public_key(),
                     "other-realm", "lab-store", epoch=0)


def test_witness_db_rollback_detected_only_against_retained_external_floor(lab, tmp_path):
    """Distinct from Q6: a rewound WITNESS database needs an independent floor."""
    import sqlite3
    from witness.checkpoint import LocalCheckpoint
    from witness.client import PinnedWitnessClient, WitnessChainBroken
    from witness.protocol import HEAD_KEYS, head_digest
    from witness.service import create_app
    from fastapi.testclient import TestClient

    first = make_request(lab, "before-backup", "sha256:"+"1"*64,
                         "sha256:"+"2"*64)
    assert lab["controller"].advance(first)["decision"] == "ADVANCED"

    # SQLite backup API handles WAL snapshots coherently. This archive is
    # held by the test attacker, NOT a trustworthy continuity source.
    backup = tmp_path / "rewound-witness.db"
    with sqlite3.connect(lab["app"].state.witness.db_path) as source:
        with sqlite3.connect(backup) as target:
            source.backup(target)

    second = make_request(lab, "after-backup", "sha256:"+"3"*64,
                          "sha256:"+"4"*64)
    assert lab["controller"].advance(second)["decision"] == "ADVANCED"
    trusted = lab["reader"].get_head()
    trusted_floor = LocalCheckpoint(
        trusted["sequence"],
        head_digest({k: trusted[k] for k in HEAD_KEYS}),
    )
    assert trusted_floor.sequence == 2

    # An actor who rolled the witness DB back to sequence 1 would still
    # serve VALID signatures from the legitimate private key. Only an
    # independently retained floor distinguishes that history.
    original = lab["app"].state.witness
    from cryptography.hazmat.primitives import serialization
    pinned_pub = lab["public"]
    engine_pub = tmp_path / "backup-engine.pub"
    engine_pub.write_bytes(lab["engine"].public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    witness_priv = tmp_path / "backup-witness.key"
    witness_priv.write_bytes(original.key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    rewound_app = create_app(
        str(backup), witness_priv, engine_pub,
        realm_id="lab-realm", store_id="lab-store", epoch=0,
    )
    rewound_client = PinnedWitnessClient(
        "http://testserver", pinned_pub, "lab-realm", "lab-store",
        http_client=TestClient(rewound_app),
    )
    assert rewound_client.get_head()["sequence"] == 1
    with pytest.raises(WitnessChainBroken, match="regression"):
        rewound_client.walk_back(minimum=trusted_floor)
