"""Receipt time/key policy evaluated against explicit caller-held references.

No host-clock default, native codec guessing, signing or operational authority.
"""
import argparse
import base64
import binascii
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat

from .receipt_bytes import MAX_RECEIPT_BYTES, verify_receipt_bytes
from .verifier import parse_json

POLICY_SCHEMA = "proof01-receipt-trust-policy/0.1"
FIELDS = {"schema", "policy_id", "provider_id", "key_id", "public_key_b64",
          "valid_from", "valid_until", "revoked_at", "status_as_of",
          "max_status_age_seconds", "max_receipt_age_seconds", "clock_skew_seconds",
          "revocation_rule"}
TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:(?P<sec>[0-9]{2})"
    r"(?P<fraction>\.[0-9]+)?(?P<offset>Z|[+-][0-9]{2}:[0-9]{2})", re.IGNORECASE)


class UnsupportedTime(ValueError):
    pass


def _time(value):
    match = TIMESTAMP.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError("Qualified date/time with seconds and explicit offset required")
    fraction = match["fraction"]
    if match["offset"] == "-00:00" or match["sec"] == "60" or (fraction and len(fraction) > 7):
        raise UnsupportedTime("Unknown offset, leap seconds or submicrosecond precision not evaluated")
    try:
        return datetime.fromisoformat(value.upper().replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ValueError("Invalid or out-of-range timestamp") from exc


def _result(outcome, code, **details):
    return {"policy_schema": POLICY_SCHEMA, "outcome": outcome, "code": code,
            "native_bundle_verification": "NOT_ESTABLISHED",
            "policy_provenance": "NOT_AUTHENTICATED", "integration_lock": "HOLD",
            "production": "HOLD", **details}


def _policy(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("Explicit policy fields required; unknown options refused")
    value = dict(value)
    if value["schema"] != POLICY_SCHEMA or value["revocation_rule"] != "reject_at_or_after":
        raise ValueError("Unsupported policy version or revocation rule")
    for field in ("policy_id", "provider_id", "key_id"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError("Missing policy binding")
    for field in ("max_status_age_seconds", "max_receipt_age_seconds", "clock_skew_seconds"):
        if type(value[field]) is not int or not 0 <= value[field] <= 2**31 - 1:
            raise ValueError("Bounded nonnegative integer duration required")
    if not isinstance(value["public_key_b64"], str):
        raise ValueError("Public key encoding")
    key = base64.b64decode(value["public_key_b64"], validate=True)
    if len(key) != 32:
        raise ValueError("Ed25519 public key length")
    times = {name: _time(value[name]) for name in ("valid_from", "valid_until", "status_as_of")}
    times["revoked_at"] = _time(value["revoked_at"]) if value["revoked_at"] is not None else None
    if times["valid_from"] >= times["valid_until"]:
        raise ValueError("Empty/reversed validity window")
    return value, key, times


def _micros(delta):
    return (delta.days * 86400 + delta.seconds) * 1000000 + delta.microseconds


def verify_with_policy(message, signature, expected, policy, verification_time):
    """Policy and evaluation time are explicit caller references, not trusted by assertion.

    Validity windows are [from, until). Effective revocation rejects both signing
    and evaluation at/after the cutoff. Stale status knowledge is indeterminate.
    """
    try:
        policy, key, times = _policy(policy)
    except (ValueError, binascii.Error):
        return _result("INDETERMINATE", "TRUST_POLICY_INVALID")
    try:
        now = _time(verification_time)
    except ValueError:
        return _result("INDETERMINATE", "VERIFICATION_TIME_INVALID")
    receipt = verify_receipt_bytes(message, signature, key, expected)
    if receipt["code"] != "RECEIPT_SIGNATURE_AND_BINDINGS_VALID":
        return {**receipt, "policy_id": policy["policy_id"],
                "policy_provenance": "NOT_AUTHENTICATED", "production": "HOLD"}
    if any(policy[k] != expected[k] for k in ("provider_id", "key_id")):
        return _result("REFUTED", "TRUST_POLICY_BINDING_MISMATCH")
    try:
        issued = _time(parse_json(message)["issued_at"])
    except UnsupportedTime:
        return _result("INDETERMINATE", "RECEIPT_TIME_ENCODING_UNSUPPORTED")
    except ValueError:
        return _result("REFUTED", "RECEIPT_ISSUED_AT_INVALID")
    skew = timedelta(seconds=policy["clock_skew_seconds"])
    status_age = now - times["status_as_of"]
    if status_age < -skew:
        return _result("INDETERMINATE", "POLICY_STATUS_FROM_FUTURE")
    if status_age > timedelta(seconds=policy["max_status_age_seconds"]):
        return _result("INDETERMINATE", "POLICY_STATUS_STALE", evidence_status="STALE")
    if times["revoked_at"] is not None and max(now, issued) >= times["revoked_at"]:
        return _result("REFUTED", "KEY_REVOKED_UNDER_POLICY")
    if not times["valid_from"] <= now < times["valid_until"]:
        return _result("REFUTED", "KEY_NOT_VALID_AT_EVALUATION")
    if not times["valid_from"] <= issued < times["valid_until"]:
        return _result("REFUTED", "KEY_NOT_VALID_AT_ISSUANCE")
    age = now - issued
    if age < -skew:
        return _result("REFUTED", "RECEIPT_FROM_FUTURE")
    if age > timedelta(seconds=policy["max_receipt_age_seconds"]):
        return _result("REFUTED", "RECEIPT_TOO_OLD", evidence_status="STALE")
    remaining = [x for x in receipt["remaining_checks"] if x != "issued_at format/freshness/revocation"]
    remaining.append("policy provenance, clock trust and completeness of key-status observation")
    return _result(
        "INDETERMINATE", "RECEIPT_POLICY_CHECKS_VALID",
        policy_id=policy["policy_id"], signature_check=receipt["signature_check"],
        message_sha256=receipt["message_sha256"], request_binding=receipt["request_binding"],
        signed_provider_assertion=receipt["signed_provider_assertion"],
        verification_time=now.isoformat(), issued_at=issued.isoformat(),
        receipt_age_microseconds=_micros(age), status_age_microseconds=_micros(status_age),
        temporal_policy="MATCHES_SUPPLIED_REFERENCE",
        remaining_checks=remaining)


def _read(path, limit):
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as source:
        if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
            raise ValueError("Regular input file required")
        body = source.read(limit + 1)
    if len(body) > limit:
        raise ValueError("Input exceeds size limit")
    return body


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("message", type=Path)
    p.add_argument("--signature", required=True, type=Path, help="Raw 64-byte Ed25519 signature")
    p.add_argument("--expected", required=True, type=Path)
    p.add_argument("--policy", required=True, type=Path)
    p.add_argument("--at", required=True, help="Explicit evaluation time; never defaults to host clock")
    args = p.parse_args()
    try:
        root = args.message.resolve(strict=True).parent
        if any(path.resolve(strict=True).is_relative_to(root) for path in (args.expected, args.policy)):
            raise ValueError("Policy/request references must be outside receipt directory")
        message, signature = _read(args.message, MAX_RECEIPT_BYTES), _read(args.signature, 64)
        policy_bytes = _read(args.policy, MAX_RECEIPT_BYTES)
        expected_bytes = _read(args.expected, MAX_RECEIPT_BYTES)
        result = verify_with_policy(message, signature, parse_json(expected_bytes),
                                    parse_json(policy_bytes), args.at)
        result.update(policy_file_sha256=hashlib.sha256(policy_bytes).hexdigest(),
                      expected_file_sha256=hashlib.sha256(expected_bytes).hexdigest())
    except (OSError, ValueError) as exc:
        result = _result("INDETERMINATE", "REFERENCE_OR_INPUT_INVALID", detail=str(exc))
    print(json.dumps(result, indent=2))
    return 1 if result["outcome"] == "REFUTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
