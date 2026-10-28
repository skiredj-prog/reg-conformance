"""Receipt-byte security tests; generated keys are ephemeral test material."""
import copy
import hashlib
import json
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

from proof01_w4.receipt_bytes import BINDINGS, verify_receipt_bytes


class ReceiptBytesTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.body = {
            "schema": "proof-provider-receipt/candidate-v0.1", "provider_id": "fixture-provider",
            "key_id": "a" * 64, "sequence": 1, "operation_id": "fixture-op",
            "idempotency_key": "fixture-idem", "request_hash": "b" * 64,
            "scope": {"account": "fixture-account", "amount_minor": 3, "currency": "EUR"},
            "action_type": "fixture-transfer", "effect_status": "EXECUTED",
            "effect_digest": "c" * 64, "finality": "PROVIDER_LEDGER_TERMINAL",
            "issued_at": "2026-10-28T14:00:00Z", "reason": "test fixture only"}
        self.expected = {k: copy.deepcopy(self.body[k]) for k in BINDINGS}

    def check(self, body=None, expected=None):
        message = json.dumps(body or self.body, indent=2).encode()
        return verify_receipt_bytes(message, self.key.sign(message), self.public,
                                    self.expected if expected is None else expected)

    def test_exact_signed_bytes_and_bindings_are_checked_without_global_promotion(self):
        message = json.dumps(self.body, indent=2).encode()
        r = self.check()
        self.assertEqual(r["code"], "RECEIPT_SIGNATURE_AND_BINDINGS_VALID")
        self.assertEqual(r["message_sha256"], hashlib.sha256(message).hexdigest())
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["native_bundle_verification"], "NOT_ESTABLISHED")
        self.assertEqual(r["integration_lock"], "HOLD")

    def test_message_is_not_canonicalized_before_verifying(self):
        message = json.dumps(self.body, indent=2).encode()
        reformatted = json.dumps(self.body, separators=(",", ":")).encode()
        r = verify_receipt_bytes(reformatted, self.key.sign(message), self.public, self.expected)
        self.assertEqual(r["code"], "RECEIPT_SIGNATURE_INVALID")

    def test_modified_body_with_original_signature_is_refuted(self):
        message = json.dumps(self.body).encode()
        self.body["scope"]["amount_minor"] += 1
        changed = json.dumps(self.body).encode()
        r = verify_receipt_bytes(changed, self.key.sign(message), self.public, self.expected)
        self.assertEqual(r["code"], "RECEIPT_SIGNATURE_INVALID")

    def test_wrong_verification_key_is_refuted(self):
        message = json.dumps(self.body).encode()
        other = Ed25519PrivateKey.generate().public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.assertEqual(verify_receipt_bytes(message, self.key.sign(message), other,
                                             self.expected)["code"], "RECEIPT_SIGNATURE_INVALID")

    def test_valid_signature_for_a_different_request_is_refuted(self):
        self.body["operation_id"] = "other-op"
        self.assertEqual(self.check()["code"], "RECEIPT_BINDING_MISMATCH")

    def test_scope_amount_change_with_valid_signature_is_refuted(self):
        self.body["scope"]["amount_minor"] = 4
        self.assertEqual(self.check()["field"], "scope")

    def test_provider_and_key_id_mismatches_are_refuted(self):
        for field in ("provider_id", "key_id"):
            with self.subTest(field=field):
                body = copy.deepcopy(self.body)
                body[field] = "d" * 64
                self.assertEqual(self.check(body)["field"], field)

    def test_expected_request_reference_is_required(self):
        self.assertEqual(self.check(expected={})["code"], "EXPECTED_BINDINGS_REQUIRED")

    def test_wrong_typed_expected_amount_cannot_equal_one(self):
        self.body["scope"]["amount_minor"] = 1
        self.expected["scope"]["amount_minor"] = True
        self.assertEqual(self.check()["code"], "EXPECTED_BINDINGS_INVALID")

    def test_signed_boolean_or_float_integer_fields_are_refuted(self):
        for field in ("amount_minor", "sequence"):
            for value in (True, 1.0):
                with self.subTest(field=field, value=value):
                    body = copy.deepcopy(self.body)
                    if field == "sequence":
                        body[field] = value
                    else:
                        body["scope"][field] = value
                    self.assertEqual(self.check(body)["code"], "RECEIPT_BODY_INVALID")

    def test_additional_body_fields_and_unknown_schema_are_refuted(self):
        for field, value in (("extra", "unclaimed"), ("schema", "future/unknown")):
            with self.subTest(field=field):
                body = copy.deepcopy(self.body); body[field] = value
                self.assertEqual(self.check(body)["code"], "RECEIPT_BODY_INVALID")

    def test_duplicate_json_keys_are_not_authenticated_as_unambiguous_body(self):
        message = b'{"schema":"old","schema":"new"}'
        r = verify_receipt_bytes(message, self.key.sign(message), self.public, self.expected)
        self.assertEqual(r["code"], "RECEIPT_BODY_INVALID")

    def test_old_signed_time_does_not_infer_freshness(self):
        self.body["issued_at"] = "2000-01-01T00:00:00Z"
        r = self.check()
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertIn("issued_at format/freshness/revocation", r["remaining_checks"])

    def test_negative_final_is_only_an_authenticated_assertion(self):
        self.body.update(effect_status="NOT_EXECUTED_FINAL", effect_digest=None)
        r = self.check()
        self.assertEqual(r["signed_provider_assertion"], "NOT_EXECUTED_FINAL")
        self.assertEqual(r["provider_effect_truth"], "NOT_ESTABLISHED")

    def test_malformed_signature_encoding_is_rejected(self):
        message = json.dumps(self.body).encode()
        self.assertEqual(verify_receipt_bytes(message, b"short", self.public,
                                             self.expected)["code"], "RECEIPT_ENCODING")


if __name__ == "__main__":
    unittest.main()
