"""
reg_common.py — REG Conformance Suite v0.3.1
Shared primitives used by shim.py (HTTP adapter) and NativeKernelAdapter.
"""
import base64, hashlib, json
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption)


# ── Hash-chain manifest (RFC-4 §4) ───────────────────────────────────────────

class HashChainManifest:
    """
    Minimal append-only hash chain.
    Each entry: sha256(prev_hash || canonical_json(entry)).
    Satisfies RFC-4 §4 "equivalent append-only ledger" clause.
    """
    GENESIS = "0" * 64

    def __init__(self):
        self.entries: list[dict] = []
        self._head: str = self.GENESIS

    def append(self, entry: dict) -> str:
        canonical = json.dumps(entry, sort_keys=True, default=str)
        h = hashlib.sha256((self._head + canonical).encode()).hexdigest()
        self.entries.append({
            "index": len(self.entries),
            "prev":  self._head,
            "hash":  h,
            "entry": entry,
        })
        self._head = h
        return h

    def verify(self) -> dict:
        prev = self.GENESIS
        for item in self.entries:
            canonical = json.dumps(item["entry"], sort_keys=True, default=str)
            expected = hashlib.sha256((prev + canonical).encode()).hexdigest()
            if expected != item["hash"]:
                return {"integrity_ok": False, "first_fault": item["index"],
                        "expected": expected, "got": item["hash"]}
            if item["prev"] != prev:
                return {"integrity_ok": False, "first_fault": item["index"],
                        "detail": "prev pointer mismatch"}
            prev = item["hash"]
        return {"integrity_ok": True, "length": len(self.entries),
                "head": self._head}

    def find(self, evaluation_id: str) -> dict | None:
        for item in self.entries:
            if item["entry"].get("evaluation_id") == evaluation_id:
                return item
        return None

    @property
    def head(self) -> str:
        return self._head


# ── Ed25519 receipt signing (RFC-4 §3) ───────────────────────────────────────

def generate_keypair() -> tuple[Ed25519PrivateKey, bytes]:
    """Return (private_key, raw_32_byte_public_key)."""
    priv = Ed25519PrivateKey.generate()
    pub  = priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return priv, pub


def sign_receipt(private_key: Ed25519PrivateKey, receipt: dict) -> dict:
    """
    Sign the canonical receipt payload (excl. signature fields).
    Adds: signed=True, signed_payload (str), signature (base64url).
    """
    payload_fields = {
        k: receipt[k] for k in
        ("receipt_id", "receipt_type", "evaluation_id",
         "final_disposition", "policy_version", "issued_at")
        if k in receipt
    }
    payload_str  = json.dumps(payload_fields, sort_keys=True)
    sig_bytes    = private_key.sign(payload_str.encode())

    return {
        **receipt,
        "signed":         True,
        "signed_payload": payload_str,
        "signature":      base64.urlsafe_b64encode(sig_bytes).rstrip(b"=").decode(),
    }


def verify_receipt_signature(pub_key_bytes: bytes, receipt: dict) -> bool:
    """
    Verify an Ed25519-signed receipt.
    pub_key_bytes: raw 32-byte public key.
    Returns True if valid, raises on failure.
    """
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    pub  = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    sig  = base64.urlsafe_b64decode(receipt["signature"] + "==")
    pub.verify(sig, receipt["signed_payload"].encode())
    return True


def pubkey_to_jwks(pub_bytes: bytes) -> dict:
    """Return a minimal JWK Set for the given raw Ed25519 public key bytes."""
    x = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
    return {"keys": [{"kty": "OKP", "crv": "Ed25519", "use": "sig", "x": x}]}
