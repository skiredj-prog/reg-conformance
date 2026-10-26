"""Canonical, domain-separated Ed25519 E8 laboratory protocol.

Not a finalized REG wire format. Neither TLS nor independent root pinning is
provided by this module; a separate G1 trust domain is still necessary.
"""
import base64
import binascii
import hashlib
import json
import re

from cryptography.exceptions import InvalidSignature

HEAD_CONTEXT = b"REG-E8-LAB-HEAD-v1\x00"
READ_CONTEXT = b"REG-E8-LAB-READ-v1\x00"
ADVANCE_CONTEXT = b"REG-E8-LAB-ADVANCE-v1\x00"
ADVANCE_RESULT_CONTEXT = b'REG-E8-LAB-ADVANCE-RESULT-v1\x00'
GENESIS_DIGEST = "sha256:" + "0" * 64
HEAD_KEYS = frozenset({
    "realm_id", "store_id", "epoch", "sequence", "state_digest",
    "key_digest", "quarantine_digest", "previous_head_digest", "recorded_at",
})
ADVANCE_KEYS = frozenset({
    "protocol", "request_id", "realm_id", "store_id", "epoch",
    "expected_prev_sequence", "expected_prev_digest", "state_digest",
    "key_digest", "quarantine_digest",
})
SHA256 = re.compile(r"^sha256:[a-f0-9]{64}$")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(context, value):
    return "sha256:" + hashlib.sha256(context + canonical(value)).hexdigest()


def head_digest(head):
    if set(head) != HEAD_KEYS:
        raise ValueError("invalid head fields")
    return digest(HEAD_CONTEXT, head)


def sign(private_key, context, value):
    return "ed25519:" + base64.b64encode(
        private_key.sign(context + canonical(value))
    ).decode("ascii")


def verify(public_key, context, value, signature):
    if not isinstance(signature, str) or not signature.startswith("ed25519:"):
        raise ValueError("missing signature")
    try:
        raw = base64.b64decode(signature[8:], validate=True)
        if len(raw) != 64:
            raise ValueError("invalid signature length")
        public_key.verify(raw, context + canonical(value))
    except (InvalidSignature, ValueError, binascii.Error) as exc:
        raise ValueError("invalid Ed25519 signature") from exc


def validate_sha256(value):
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise ValueError("invalid SHA-256 digest")
    return value


def validate_advance(body):
    if not isinstance(body, dict) or set(body) != ADVANCE_KEYS:
        raise ValueError("invalid request fields")
    if body["protocol"] != "reg-e8-advance-lab-v0.1":
        raise ValueError("invalid protocol")
    for name in ("realm_id", "store_id", "request_id"):
        if (not isinstance(body[name], str) or not body[name]
                or len(body[name]) > 128):
            raise ValueError("invalid identifier: " + name)
    for name in ("epoch", "expected_prev_sequence"):
        if type(body[name]) is not int or body[name] < 0:
            raise ValueError("invalid integer: " + name)
    for name in ("expected_prev_digest", "state_digest",
                 "key_digest", "quarantine_digest"):
        validate_sha256(body[name])
    return body
