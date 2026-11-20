import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from proof01_w4.verifier import verify


class W4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        data = b"synthetic-receipt-no-real-effect"
        (self.root / "receipt.bin").write_bytes(data)
        self.m = {
            "schema_version": "proof01-w4/1",
            "scope": {
                "system": "fixture-only", "deployment": "local-simulation",
                "time_window": "2026-10-26T00:00:00Z/2026-10-26T00:01:00Z",
                "fault_model": "synthetic"
            },
            "claims": ["fixture-receipt-integrity"],
            "artifacts": [{"path": "receipt.bin", "sha256": hashlib.sha256(data).hexdigest()}]
        }
        self.save()

    def save(self):
        (self.root / "proof-manifest-v1.json").write_text(json.dumps(self.m), encoding="utf-8")

    def test_valid_hash_is_not_effect_proof(self):
        r = verify(self.root, "fixture-receipt-integrity")
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["code"], "SEMANTIC_PROOF_NOT_ESTABLISHED")

    def test_tamper_refuted(self):
        (self.root / "receipt.bin").write_bytes(b"tampered")
        self.assertEqual(verify(self.root)["code"], "HASH_MISMATCH")

    def test_missing_indeterminate(self):
        (self.root / "receipt.bin").unlink()
        self.assertEqual(verify(self.root)["outcome"], "INDETERMINATE")

    def test_undeclared_claim_out_of_scope(self):
        self.assertEqual(verify(self.root, "exactly-once")["outcome"], "OUT_OF_SCOPE")

    def test_escape_refuted(self):
        self.m["artifacts"][0]["path"] = "../elsewhere"
        self.save()
        self.assertEqual(verify(self.root)["code"], "PATH_ESCAPE")

    def test_symlink_not_followed(self):
        (self.root / "link.bin").symlink_to(self.root / "receipt.bin")
        self.m["artifacts"][0]["path"] = "link.bin"
        self.save()
        self.assertEqual(verify(self.root)["code"], "EVIDENCE_MISSING")

    def test_missing_scope_rejected(self):
        self.m["scope"].pop("fault_model")
        self.save()
        self.assertEqual(verify(self.root)["code"], "SCOPE")

    def test_manifest_self_reference_refuted(self):
        self.m["artifacts"][0]["path"] = "proof-manifest-v1.json"
        self.save()
        self.assertEqual(verify(self.root)["code"], "DUPLICATE")


if __name__ == "__main__":
    unittest.main()
