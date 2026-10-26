"""Experimental E8 witness; NOT production REG/CB-05 qualification.

The witness signs a durable monotone head and only accepts CAS advances signed
by an independently provisioned ENGINE key. The runtime container has no
engine signing key. An authenticated engine can still lie about its state;
this is NOT a verified G4-A pre-authorization or real append-only hardware.
"""
import argparse
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from witness.protocol import (
    ADVANCE_CONTEXT, ADVANCE_RESULT_CONTEXT, GENESIS_DIGEST, HEAD_CONTEXT, READ_CONTEXT,
    canonical, digest, head_digest, sign, validate_advance, verify,
)

ADVANCE_RESULT_CONTEXT = b"REG-E8-LAB-ADVANCE-RESULT-v1\x00"
NONCE = re.compile(r"^[0-9a-f]{32}$")


class SignedAdvance(BaseModel):
    body: dict
    signature: str


def load_private(path):
    key = serialization.load_pem_private_key(Path(path).read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise TypeError("expected an Ed25519 private key")
    return key


def load_public(path):
    key = serialization.load_pem_public_key(Path(path).read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise TypeError("expected an Ed25519 public key")
    return key


class WitnessStore:
    def __init__(self, db_path, private_key, engine_public_key, realm_id, store_id, epoch=0):
        self.db_path = str(db_path)
        self.key, self.engine_public = private_key, engine_public_key
        self.realm_id, self.store_id, self.epoch = realm_id, store_id, epoch
        if not realm_id or not store_id or type(epoch) is not int or epoch < 0:
            raise ValueError("invalid trusted witness identity")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._conn()) as con:
            con.executescript(Path(__file__).with_name("schema.sql").read_text())
            con.execute("BEGIN IMMEDIATE")
            previous = con.execute(
                "SELECT realm_id,store_id,epoch FROM witness_meta WHERE id=1"
            ).fetchone()
            identity = (realm_id, store_id, epoch)
            if previous and tuple(previous) != identity:
                con.rollback()
                raise ValueError("existing witness identity does not match configuration")
            if not previous:
                con.execute(
                    "INSERT INTO witness_meta VALUES (1,?,?,?)", identity
                )
            con.commit()

    def _conn(self):
        con = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        con.execute("PRAGMA synchronous=FULL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=10000")
        return con

    @staticmethod
    def _get_head(con, sequence=None):
        if sequence is None:
            row = con.execute(
                "SELECT payload_json,signature FROM witness_head "
                "ORDER BY sequence DESC LIMIT 1"
            ).fetchone()
        else:
            row = con.execute(
                "SELECT payload_json,signature FROM witness_head WHERE sequence=?",
                (sequence,),
            ).fetchone()
        if row is None:
            return None
        import json
        head = json.loads(row[0])
        return dict(head, signature=row[1])

    def fresh_read(self, nonce):
        if NONCE.fullmatch(nonce) is None:
            raise ValueError("invalid freshness nonce")
        with closing(self._conn()) as con:
            con.execute("BEGIN")
            head = self._get_head(con)
            con.commit()
        body = {
            "nonce": nonce, "realm_id": self.realm_id,
            "store_id": self.store_id, "head": head,
        }
        return {"body": body, "signature": sign(self.key, READ_CONTEXT, body)}

    def historical(self, sequence):
        with closing(self._conn()) as con:
            return self._get_head(con, sequence)

    def _signed_result(self, decision, reason, *, head=None):
        body = {"decision": decision, "reason": reason, "head": head}
        return {
            "body": body,
            "signature": sign(self.key, ADVANCE_RESULT_CONTEXT, body),
        }

    def advance(self, envelope):
        body = validate_advance(envelope.body)
        verify(self.engine_public, ADVANCE_CONTEXT, body, envelope.signature)
        if (body["realm_id"] != self.realm_id
                or body["store_id"] != self.store_id
                or body["epoch"] != self.epoch):
            return self._signed_result("REJECTED", "E8_SCOPE_MISMATCH")
        request_digest = digest(ADVANCE_CONTEXT, body)
        with closing(self._conn()) as con:
            con.execute("BEGIN IMMEDIATE")
            previous_request = con.execute(
                "SELECT request_digest,assigned_sequence FROM advance_requests "
                "WHERE request_id=?", (body["request_id"],)
            ).fetchone()
            if previous_request:
                if previous_request[0] != request_digest:
                    con.rollback()
                    return self._signed_result("REJECTED", "E8_REQUEST_CONFLICT")
                head = self._get_head(con, previous_request[1])
                con.commit()
                return self._signed_result("ALREADY_ADVANCED", "REPLAY", head=head)

            current = self._get_head(con)
            current_seq = current["sequence"] if current else 0
            current_hash = head_digest({k: v for k, v in current.items() if k != "signature"}) if current else GENESIS_DIGEST
            if (body["expected_prev_sequence"] != current_seq
                    or body["expected_prev_digest"] != current_hash):
                con.rollback()
                return self._signed_result("CONFLICT", "E8_HEAD_DIVERGENCE", head=current)

            now = datetime.now(timezone.utc).isoformat()
            next_head = {
                "realm_id": self.realm_id, "store_id": self.store_id,
                "epoch": self.epoch, "sequence": current_seq + 1,
                "state_digest": body["state_digest"],
                "key_digest": body["key_digest"],
                "quarantine_digest": body["quarantine_digest"],
                "previous_head_digest": current_hash,
                "recorded_at": now,
            }
            signature = sign(self.key, HEAD_CONTEXT, next_head)
            con.execute(
                "INSERT INTO witness_head(sequence,payload_json,signature) VALUES(?,?,?)",
                (current_seq + 1, canonical(next_head).decode("utf-8"), signature),
            )
            con.execute(
                "INSERT INTO advance_requests(request_id,request_digest,assigned_sequence) "
                "VALUES(?,?,?)",
                (body["request_id"], request_digest, current_seq + 1),
            )
            con.commit()
            # Commit is durable before the CMT-like signed result is returned.
            return self._signed_result(
                "ADVANCED", "OK", head=dict(next_head, signature=signature)
            )


def create_app(db_path, signing_key_path, engine_public_key_path, *, realm_id, store_id, epoch=0):
    store = WitnessStore(
        db_path, load_private(signing_key_path),
        load_public(engine_public_key_path), realm_id, store_id, epoch
    )
    app = FastAPI(title="TENIR E8 LAB — NOT PRODUCTION")
    app.state.witness = store

    @app.get("/health")
    def health():
        # Health does not imply current trust or authentication.
        return {"status": "ok", "security_assurance": "LAB_ONLY"}

    @app.get("/head")
    def head(nonce: str = Query(...)):
        try:
            return store.fresh_read(nonce)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/head/at/{sequence}")
    def head_at(sequence: int):
        if sequence < 1:
            raise HTTPException(404, "head absent")
        h = store.historical(sequence)
        if h is None:
            raise HTTPException(404, "head absent")
        return {"head": h}

    @app.post("/advance")
    def advance(envelope: SignedAdvance):
        # The runtime container has no engine private key. A plain HTTP POST
        # from runtime cannot advance the witness's authoritative head.
        try:
            return store.advance(envelope)
        except (ValueError, TypeError) as exc:
            raise HTTPException(403, "unauthorized or malformed advance") from exc
    return app


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8443)
    p.add_argument("--db", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--engine-public-key", required=True)
    p.add_argument("--realm", required=True)
    p.add_argument("--store", required=True)
    p.add_argument("--epoch", type=int, default=0)
    a = p.parse_args()
    import uvicorn
    uvicorn.run(create_app(a.db, a.key, a.engine_public_key,
                          realm_id=a.realm, store_id=a.store, epoch=a.epoch),
                host=a.host, port=a.port)


if __name__ == "__main__":
    main()
