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
        for index, item in enumerate(self.entries):
            canonical = json.dumps(item["entry"], sort_keys=True, default=str)
            expected = hashlib.sha256((prev + canonical).encode()).hexdigest()
            if item.get("index") != index:
                return {"integrity_ok": False, "first_fault": index,
                        "detail": "index mismatch"}
            if expected != item.get("hash"):
                return {"integrity_ok": False, "first_fault": index,
                        "expected": expected, "got": item.get("hash")}
            if item.get("prev") != prev:
                return {"integrity_ok": False, "first_fault": index,
                        "detail": "prev pointer mismatch"}
            prev = item["hash"]
        if prev != self._head:
            return {"integrity_ok": False, "first_fault": len(self.entries),
                    "detail": "head pointer mismatch", "expected": prev,
                    "got": self._head}
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
    payload_fields = _receipt_payload(receipt)
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
    payload = _receipt_payload(receipt)
    canonical = json.dumps(payload, sort_keys=True)
    if receipt.get("signed_payload") != canonical:
        raise ValueError("signed payload does not match receipt fields")
    pub  = Ed25519PublicKey.from_public_bytes(pub_key_bytes)
    sig  = base64.urlsafe_b64decode(receipt["signature"] + "==")
    pub.verify(sig, canonical.encode())
    return True


def pubkey_to_jwks(pub_bytes: bytes) -> dict:
    """Return a minimal JWK Set for the given raw Ed25519 public key bytes."""
    x = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()
    return {"keys": [{"kty": "OKP", "crv": "Ed25519", "use": "sig", "x": x}]}


def _receipt_payload(receipt: dict) -> dict:
    required = ("receipt_id", "receipt_type", "evaluation_id", "action_id",
                "final_disposition", "reason_codes", "policy_version",
                "threshold_version", "reproducibility_class", "issued_at")
    missing = [key for key in required if key not in receipt]
    if missing:
        raise ValueError(f"receipt missing signed fields: {', '.join(missing)}")
    return {key: receipt[key] for key in required}
