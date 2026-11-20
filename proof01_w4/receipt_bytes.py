"""Verify an exact signed B3 receipt message, without assuming a bundle codec.

This primitive authenticates bytes and supplied request bindings. Merkle,
witness, RC-01/I8 and authorization checks are separate. Never emits VERIFIED.
"""
from pathlib import Path
import hashlib
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jsonschema import Draft202012Validator, ValidationError

from .verifier import parse_json

SCHEMA_PATH = Path(__file__).with_name("contracts") / "native-receipt-candidate-v0.1.schema.json"
BINDINGS = ("provider_id", "key_id", "operation_id", "idempotency_key", "request_hash", "scope", "action_type")
MAX_RECEIPT_BYTES = 1024 * 1024


def _result(outcome, code, **details):
    return {"outcome": outcome, "code": code,
            "native_bundle_verification": "NOT_ESTABLISHED",
            "provider_effect_truth": "NOT_ESTABLISHED",
            "integration_lock": "HOLD", **details}


def verify_receipt_bytes(message, signature, public_key, expected):
    """message is exactly the message covered by the Ed25519 signature.

    expected supplies ALL BINDINGS from the caller's separately held request/key
    reference, not from the receipt itself. No canonicalization or signing occurs.
    Valid results remain INDETERMINATE for full native-bundle assurance.
    """
    if not isinstance(expected, dict) or set(expected) != set(BINDINGS):
        return _result("INDETERMINATE", "EXPECTED_BINDINGS_REQUIRED")
    if (not isinstance(message, bytes) or len(message) > MAX_RECEIPT_BYTES
            or not isinstance(signature, bytes) or len(signature) != 64
            or not isinstance(public_key, bytes) or len(public_key) != 32):
        return _result("REFUTED", "RECEIPT_ENCODING")
    try:
        schema = json.loads(SCHEMA_PATH.read_text("utf-8"))
        reference_schema = {"type": "object", "required": list(BINDINGS),
                            "additionalProperties": False,
                            "properties": {k: schema["properties"][k] for k in BINDINGS}}
        Draft202012Validator(reference_schema).validate(expected)
        if type(expected["scope"]["amount_minor"]) is not int:
            raise ValueError("Integer minor units required")
    except (ValidationError, ValueError):
        return _result("INDETERMINATE", "EXPECTED_BINDINGS_INVALID")
    # A separate reference must authorize this key/provider. Passing a public key
    # is not itself evidence of independent custody or of a trustworthy provider.
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except (InvalidSignature, ValueError):
        return _result("REFUTED", "RECEIPT_SIGNATURE_INVALID")
    try:
        body = parse_json(message)
        Draft202012Validator(schema).validate(body)
        if type(body["sequence"]) is not int or type(body["scope"]["amount_minor"]) is not int:
            raise ValueError("Integer fields cannot be floats or bools")
    except (ValidationError, ValueError, UnicodeError):
        return _result("REFUTED", "RECEIPT_BODY_INVALID")
    for key in BINDINGS:
        if body[key] != expected[key]:
            return _result("REFUTED", "RECEIPT_BINDING_MISMATCH", field=key)
    return _result(
        "INDETERMINATE", "RECEIPT_SIGNATURE_AND_BINDINGS_VALID",
        signature_check="VALID_FOR_SUPPLIED_KEY",
        message_sha256=hashlib.sha256(message).hexdigest(),
        request_binding="MATCHES_CALLER_REFERENCE",
        signed_provider_assertion=body["effect_status"],
        remaining_checks=["native codec/envelope interoperability", "Merkle inclusion and checkpoint",
                          "witness chain and custody", "RC-01/I8 replay", "grant authority",
                          "issued_at format/freshness/revocation", "observation completeness"],
        schema_scope="structural Draft 2020-12 checks; format is annotation-only")
