"""Explicit-clock policy tests. Test keys/policies are not independent authorities."""
import base64
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from proof01_w4.receipt_bytes import BINDINGS
from proof01_w4.receipt_policy import POLICY_SCHEMA, _read, verify_with_policy


class ReceiptPolicyTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        public = self.key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.body = {"schema": "proof-provider-receipt/candidate-v0.1",
                     "provider_id": "fixture", "key_id": "a" * 64, "sequence": 1,
                     "operation_id": "op", "idempotency_key": "idem", "request_hash": "b" * 64,
                     "scope": {"account": "test", "amount_minor": 3, "currency": "EUR"},
                     "action_type": "test-transfer", "effect_status": "EXECUTED",
                     "effect_digest": "c" * 64, "finality": "PROVIDER_LEDGER_TERMINAL",
                     "issued_at": "2026-10-28T16:00:00Z", "reason": "test-only"}
        self.expected = {k: copy.deepcopy(self.body[k]) for k in BINDINGS}
        self.policy = {"schema": POLICY_SCHEMA, "policy_id": "fixture-policy",
                       "provider_id": "fixture", "key_id": "a" * 64,
                       "public_key_b64": base64.b64encode(public).decode(),
                       "valid_from": "2026-10-28T15:00:00Z", "valid_until": "2026-10-28T17:00:00Z",
                       "revoked_at": None, "status_as_of": "2026-10-28T16:00:30Z",
                       "max_status_age_seconds": 60, "max_receipt_age_seconds": 120,
                       "clock_skew_seconds": 2, "revocation_rule": "reject_at_or_after"}
        self.now = "2026-10-28T16:01:00Z"

    def evaluate(self, now=None):
        message = json.dumps(self.body, indent=2).encode()
        return verify_with_policy(message, self.key.sign(message), self.expected,
                                  self.policy, self.now if now is None else now)

    def test_positive_policy_is_scoped_and_still_indeterminate(self):
        r = self.evaluate()
        self.assertEqual(r["code"], "RECEIPT_POLICY_CHECKS_VALID")
        self.assertEqual(r["receipt_age_microseconds"], 60_000_000)
        self.assertEqual(r["status_age_microseconds"], 30_000_000)
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["policy_provenance"], "NOT_AUTHENTICATED")
        self.assertEqual(r["integration_lock"], "HOLD")

    def test_expired_receipt_is_refuted(self):
        self.body["issued_at"] = "2026-10-28T15:58:59Z"
        r = self.evaluate()
        self.assertEqual(r["code"], "RECEIPT_TOO_OLD")
        self.assertEqual(r["evidence_status"], "STALE")

    def test_receipt_age_boundary_is_exact_to_microseconds(self):
        self.policy["max_receipt_age_seconds"] = 60
        self.assertEqual(self.evaluate()["code"], "RECEIPT_POLICY_CHECKS_VALID")
        self.body["issued_at"] = "2026-10-28T15:59:59.999999Z"
        self.assertEqual(self.evaluate()["code"], "RECEIPT_TOO_OLD")

    def test_future_timestamp_beyond_skew_is_refuted(self):
        self.body["issued_at"] = "2026-10-28T16:01:02.000001Z"
        self.assertEqual(self.evaluate()["code"], "RECEIPT_FROM_FUTURE")

    def test_declared_future_skew_boundary_is_accepted(self):
        self.body["issued_at"] = "2026-10-28T16:01:02Z"
        r = self.evaluate()
        self.assertEqual(r["code"], "RECEIPT_POLICY_CHECKS_VALID")
        self.assertEqual(r["receipt_age_microseconds"], -2_000_000)

    def test_key_expiry_excludes_upper_boundary(self):
        self.policy["status_as_of"] = "2026-10-28T17:00:00Z"
        self.body["issued_at"] = "2026-10-28T16:59:30Z"
        self.assertEqual(self.evaluate("2026-10-28T17:00:00Z")["code"], "KEY_NOT_VALID_AT_EVALUATION")

    def test_key_validity_includes_lower_boundary(self):
        self.policy["status_as_of"] = self.policy["valid_from"]
        self.body["issued_at"] = self.policy["valid_from"]
        self.assertEqual(self.evaluate(self.policy["valid_from"])["code"], "RECEIPT_POLICY_CHECKS_VALID")

    def test_signature_time_must_be_in_key_window(self):
        for issued in ("2026-10-28T14:59:59Z", "2026-10-28T17:00:00Z"):
            with self.subTest(issued=issued):
                self.body["issued_at"] = issued
                self.assertEqual(self.evaluate()["code"], "KEY_NOT_VALID_AT_ISSUANCE")

    def test_revocation_at_evaluation_rejects_earlier_signature(self):
        self.policy["revoked_at"] = self.now
        self.assertEqual(self.evaluate()["code"], "KEY_REVOKED_UNDER_POLICY")

    def test_future_effective_revocation_does_not_revoke_earlier_case(self):
        self.policy["revoked_at"] = "2026-10-28T16:02:00Z"
        self.assertEqual(self.evaluate()["code"], "RECEIPT_POLICY_CHECKS_VALID")

    def test_future_signature_cannot_cross_scheduled_revocation_within_skew(self):
        self.policy["revoked_at"] = "2026-10-28T16:01:01Z"
        self.body["issued_at"] = "2026-10-28T16:01:01Z"
        self.assertEqual(self.evaluate()["code"], "KEY_REVOKED_UNDER_POLICY")

    def test_stale_revocation_status_is_indeterminate(self):
        self.policy["status_as_of"] = "2026-10-28T15:59:59Z"
        r = self.evaluate()
        self.assertEqual(r["code"], "POLICY_STATUS_STALE")
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["evidence_status"], "STALE")

    def test_status_age_boundary_is_exact(self):
        self.policy["max_status_age_seconds"] = 30
        self.assertEqual(self.evaluate()["code"], "RECEIPT_POLICY_CHECKS_VALID")
        self.policy["status_as_of"] = "2026-10-28T16:00:29.999999Z"
        self.assertEqual(self.evaluate()["code"], "POLICY_STATUS_STALE")

    def test_status_from_future_is_not_current_knowledge(self):
        self.policy["status_as_of"] = "2026-10-28T16:01:03Z"
        self.assertEqual(self.evaluate()["code"], "POLICY_STATUS_FROM_FUTURE")

    def test_explicit_verification_time_is_required(self):
        message = json.dumps(self.body).encode()
        for at in (None, "2026-10-28T16:01:00", "today"):
            with self.subTest(at=at):
                self.assertEqual(verify_with_policy(message, self.key.sign(message), self.expected,
                                                    self.policy, at)["code"], "VERIFICATION_TIME_INVALID")

    def test_invalid_calendar_and_unqualified_receipt_time_are_refuted(self):
        for issued in ("2026-02-30T16:00:00Z", "2026-10-28T16:00:00", "not-a-time"):
            with self.subTest(issued=issued):
                self.body["issued_at"] = issued
                self.assertEqual(self.evaluate()["code"], "RECEIPT_ISSUED_AT_INVALID")

    def test_supported_timezones_compare_the_same_instant(self):
        self.body["issued_at"] = "2026-10-28T17:00:00+01:00"
        self.assertEqual(self.evaluate()["receipt_age_microseconds"], 60_000_000)
        self.body["issued_at"] = "2026-10-28t16:00:00z"
        self.assertEqual(self.evaluate()["code"], "RECEIPT_POLICY_CHECKS_VALID")

    def test_unsupported_encodings_are_not_silently_rounded(self):
        for issued in ("2026-10-28T16:00:00.1234567Z", "2026-10-28T16:00:00-00:00",
                       "2016-12-31T23:59:60Z"):
            with self.subTest(issued=issued):
                self.body["issued_at"] = issued
                self.assertEqual(self.evaluate()["code"], "RECEIPT_TIME_ENCODING_UNSUPPORTED")

    def test_policy_bindings_must_authorize_the_same_provider_and_key(self):
        for field in ("provider_id", "key_id"):
            with self.subTest(field=field):
                value = self.policy[field]
                self.policy[field] = "d" * 64
                self.assertEqual(self.evaluate()["code"], "TRUST_POLICY_BINDING_MISMATCH")
                self.policy[field] = value

    def test_missing_explicit_revocation_state_is_not_assumed_clear(self):
        self.policy.pop("revoked_at")
        self.assertEqual(self.evaluate()["code"], "TRUST_POLICY_INVALID")

    def test_unknown_options_and_invalid_durations_are_refused(self):
        original = dict(self.policy)
        for field, value in (("extra", "ignore-revocation"), ("clock_skew_seconds", True),
                             ("max_receipt_age_seconds", -1), ("max_status_age_seconds", 2**40)):
            with self.subTest(field=field):
                self.policy = {**original, field: value}
                self.assertEqual(self.evaluate()["code"], "TRUST_POLICY_INVALID")

    def test_invalid_key_and_empty_validity_window_are_refused(self):
        original = dict(self.policy)
        for update in ({"public_key_b64": "not base64"}, {"valid_until": original["valid_from"]},
                       {"schema": "future/2"}, {"revocation_rule": "ignore"}):
            with self.subTest(update=update):
                self.policy = {**original, **update}
                self.assertEqual(self.evaluate()["code"], "TRUST_POLICY_INVALID")

    def test_invalid_signature_remains_refuted(self):
        message = json.dumps(self.body).encode()
        self.assertEqual(verify_with_policy(message, b"x" * 64, self.expected,
                                            self.policy, self.now)["code"], "RECEIPT_SIGNATURE_INVALID")

    def cli(self, parent, inside=False):
        evidence = parent / "receipt"; evidence.mkdir()
        trust = parent / "reference"; trust.mkdir()
        message = json.dumps(self.body).encode()
        (evidence / "body.json").write_bytes(message)
        (evidence / "signature.bin").write_bytes(self.key.sign(message))
        policy_path = (evidence if inside else trust) / "policy.json"
        policy_path.write_text(json.dumps(self.policy))
        (trust / "expected.json").write_text(json.dumps(self.expected))
        return subprocess.run(
            [sys.executable, "-B", "-m", "proof01_w4.receipt_policy",
             str(evidence / "body.json"), "--signature", str(evidence / "signature.bin"),
             "--expected", str(trust / "expected.json"), "--policy", str(policy_path), "--at", self.now],
            capture_output=True)

    def test_cli_keeps_policy_success_indeterminate_and_records_reference_hashes(self):
        with tempfile.TemporaryDirectory() as name:
            run = self.cli(Path(name))
            r = json.loads(run.stdout)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(r["code"], "RECEIPT_POLICY_CHECKS_VALID")
            self.assertEqual(len(r["policy_file_sha256"]), 64)
            self.assertEqual(len(r["expected_file_sha256"]), 64)

    def test_cli_revoked_key_fails_and_embedded_policy_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            self.policy["revoked_at"] = self.now
            run = self.cli(Path(name))
            self.assertEqual(run.returncode, 1)
            self.assertEqual(json.loads(run.stdout)["code"], "KEY_REVOKED_UNDER_POLICY")
        with tempfile.TemporaryDirectory() as name:
            run = self.cli(Path(name), inside=True)
            self.assertEqual(json.loads(run.stdout)["code"], "REFERENCE_OR_INPUT_INVALID")

    def test_special_input_file_does_not_block_reader(self):
        with tempfile.TemporaryDirectory() as name:
            fifo = Path(name) / "fifo"; os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError, "Regular input"):
                _read(fifo, 100)


if __name__ == "__main__":
    unittest.main()
