"""Negative consumer boundary tests, not execution or authorization of W2."""
import copy
import hashlib
import json
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from proof01_w4.receipt_bytes import BINDINGS, verify_receipt_bytes
from proof01_w4.rc01_i8_oracle import PROFILE, replay_projection


class NativeBindingBoundaryTests(unittest.TestCase):
    def setUp(self):
        # Generated test keys and signed fixture bytes are not native evidence.
        self.key = Ed25519PrivateKey.generate()
        self.public = self.key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw)
        self.body = {
            "schema": "proof-provider-receipt/candidate-v0.1",
            "provider_id": "fixture-provider", "key_id": "a" * 64,
            "sequence": 1, "operation_id": "fixture-op",
            "idempotency_key": "fixture-idem", "request_hash": "b" * 64,
            "scope": {"account": "fixture-account", "amount_minor": 3, "currency": "EUR"},
            "action_type": "transfer", "effect_status": "EXECUTED",
            "effect_digest": "c" * 64, "finality": "PROVIDER_LEDGER_TERMINAL",
            "issued_at": "2026-10-28T14:00:00Z", "reason": "fixture only"}
        self.expected = {k: copy.deepcopy(self.body[k]) for k in BINDINGS}

    def verify(self, expected=None, body=None):
        message = json.dumps(self.body if body is None else body, indent=2).encode()
        return verify_receipt_bytes(message, self.key.sign(message), self.public,
                                    self.expected if expected is None else expected)

    def mismatch(self, field, value):
        expected = copy.deepcopy(self.expected); expected[field] = value
        result = self.verify(expected=expected)
        self.assertEqual(result["code"], "RECEIPT_BINDING_MISMATCH")
        self.assertEqual(result["field"], field)
        self.assertEqual(result["integration_lock"], "HOLD")

    def test_valid_signature_cannot_be_reused_for_another_operation_reference(self):
        self.mismatch("operation_id", "other-op")

    def test_valid_signature_cannot_be_reused_for_another_idempotency_reference(self):
        self.mismatch("idempotency_key", "other-idem")

    def test_valid_signature_cannot_be_reused_for_another_request_hash_reference(self):
        self.mismatch("request_hash", "d" * 64)

    def test_missing_request_bindings_are_not_recovered_from_signed_body(self):
        for field in ("operation_id", "idempotency_key", "request_hash"):
            with self.subTest(field=field):
                expected = copy.deepcopy(self.expected); expected.pop(field)
                self.assertEqual(self.verify(expected=expected)["code"], "EXPECTED_BINDINGS_REQUIRED")

    def test_evaluation_and_grant_references_cannot_be_silently_ignored(self):
        for field in ("evaluation_id", "grant_id"):
            with self.subTest(field=field):
                expected = copy.deepcopy(self.expected); expected[field] = "external-reference"
                self.assertEqual(self.verify(expected=expected)["code"], "EXPECTED_BINDINGS_REQUIRED")

    def test_current_receipt_schema_cannot_be_extended_even_with_a_valid_signature(self):
        for field in ("evaluation_id", "grant_id"):
            with self.subTest(field=field):
                body = copy.deepcopy(self.body); body[field] = "unreviewed-wire-extension"
                self.assertEqual(self.verify(body=body)["code"], "RECEIPT_BODY_INVALID")

    def test_unsigned_context_changes_do_not_establish_authorization(self):
        # Both envelopes point to the very same signed bytes. The primitive
        # sees no evidence linking either evaluation/grant pair to the receipt.
        message = json.dumps(self.body, indent=2).encode()
        signature = self.key.sign(message)
        reports = []
        for evaluation, grant in (("eval-A", "grant-A"), ("eval-B", "grant-B")):
            outer = {"evaluation_id": evaluation, "grant_id": grant,
                     "message": message, "signature": signature}
            reports.append(verify_receipt_bytes(outer["message"], outer["signature"],
                                                self.public, self.expected))
        self.assertEqual(reports[0], reports[1])
        self.assertEqual(reports[0]["outcome"], "INDETERMINATE")
        self.assertIn("grant authority", reports[0]["remaining_checks"])

    def test_operation_only_projection_does_not_accept_unreviewed_context_mapping(self):
        projection = {"profile": PROFILE, "operation_id": "fixture-op", "resource_id": "account",
                      "amount_minor": 3, "baseline": {"capacity": 3, "reserved": 0, "committed": 0},
                      "initial_view": "INIT", "initial_settlement": "NONE", "records": []}
        # Even a consistent empty prefix says nothing about a real grant.
        self.assertEqual(replay_projection(projection)["grant_and_witness"], "NOT_EVALUATED")
        for field in ("evaluation_id", "grant_id", "idempotency_key", "request_hash"):
            with self.subTest(field=field):
                extended = copy.deepcopy(projection); extended[field] = "not-a-reviewed-mapping"
                self.assertEqual(replay_projection(extended)["outcome"], "INDETERMINATE")

    def test_request_codec_difference_is_not_normalized_into_a_match(self):
        payload = {"beneficiary": "caf\u00e9", "amount_minor": 3}
        source_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        alternate = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=False).encode()
        self.assertNotEqual(source_bytes, alternate)
        self.body["request_hash"] = hashlib.sha256(source_bytes).hexdigest()
        expected = copy.deepcopy(self.expected)
        expected["request_hash"] = hashlib.sha256(alternate).hexdigest()
        self.assertEqual(self.verify(expected=expected)["field"], "request_hash")


if __name__ == "__main__":
    unittest.main()
