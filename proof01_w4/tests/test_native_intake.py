"""Native intake negative controls. Fixtures are not the original B3/RC-01 kits."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from proof01_w4.native_intake import REQUIRED, inspect_native_snapshot, inspect_native_bundle


class NativeIntakeTests(unittest.TestCase):
    def setUp(self):
        self.entries = {name: json.dumps({"fixture_only": name}).encode() for name in REQUIRED}
        self.pins = b'{"fixture_only": "unvalidated external pin document"}'
        self.rehash()

    def rehash(self):
        self.entries["proof-manifest-v1.json"] = json.dumps({
            "schema_version": "proof01-w4/1",
            "scope": {"system": "intake-fixture-only", "deployment": "local-test",
                      "time_window": "fixture-only", "fault_model": "input-mutation"},
            "claims": ["lab-repair-consistency"],
            "artifacts": [{"path": n, "sha256": hashlib.sha256(b).hexdigest()}
                          for n, b in self.entries.items() if n != "proof-manifest-v1.json"]
        }).encode()

    def subject(self):
        deployment = b'{"fixture_only": true, "quarantine_enforced": true}'
        self.entries["deployment-manifest.json"] = deployment
        value = {"integration_sha": "a" * 40,
                 "deployment_manifest_sha256": hashlib.sha256(deployment).hexdigest(),
                 "topology_id": "fixture-topology"}
        self.entries["convergence.json"] = json.dumps(value).encode()
        self.rehash()
        return value

    def test_documentary_intake_never_substitutes_for_native_readers(self):
        r = inspect_native_snapshot(self.entries, self.pins)
        self.assertEqual(r["documentary_intake"], "READY_FOR_NATIVE_READERS")
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["native_semantics"], "NOT_EVALUATED")
        self.assertEqual(r["integration_lock"], "HOLD")
        for name in REQUIRED:
            self.assertEqual(r["native_artifact_sha256"][name],
                             hashlib.sha256(self.entries[name]).hexdigest())

    def test_changed_original_bytes_are_refuted(self):
        self.entries["provider-bundle.json"] = b'{"changed":true}'
        self.assertEqual(inspect_native_snapshot(self.entries, self.pins)["code"], "HASH_MISMATCH")

    def test_rehashed_inventory_does_not_establish_authenticity(self):
        self.entries["provider-bundle.json"] = b'{"forged":true}'
        self.rehash()
        r = inspect_native_snapshot(self.entries, self.pins)
        self.assertEqual(r["outcome"], "INDETERMINATE")
        self.assertEqual(r["pins_status"], "PRESENT_NOT_AUTHENTICATED")

    def test_missing_required_native_file_is_indeterminate(self):
        self.entries.pop("local-state.json"); self.rehash()
        self.assertEqual(inspect_native_snapshot(self.entries, self.pins)["code"], "NATIVE_ARTIFACTS_MISSING")

    def test_unlisted_native_file_is_not_accepted(self):
        self.entries.pop("witness-events.json"); self.rehash()
        self.entries["witness-events.json"] = b'{"unlisted":true}'
        self.assertEqual(inspect_native_snapshot(self.entries, self.pins)["code"],
                         "NATIVE_ARTIFACT_NOT_INVENTORIED")

    def test_duplicate_native_json_keys_are_refuted(self):
        self.entries["local-state.json"] = b'{"version":1,"version":2}'
        self.rehash()
        self.assertEqual(inspect_native_snapshot(self.entries, self.pins)["code"], "NATIVE_JSON_INVALID")

    def test_missing_or_invalid_pins_do_not_promote(self):
        self.assertEqual(inspect_native_snapshot(self.entries)["code"], "EXTERNAL_PINS_REQUIRED")
        self.assertEqual(inspect_native_snapshot(self.entries, b"{}")["code"], "EXTERNAL_PINS_INVALID")

    def test_matching_subject_is_only_a_match_to_caller_input(self):
        expected = self.subject()
        r = inspect_native_snapshot(self.entries, self.pins, expected)
        self.assertEqual(r["subject_check"], "MATCHES_CALLER_REFERENCE_ONLY")
        self.assertEqual(r["integration_lock"], "HOLD")

    def test_rebound_configuration_invalidates_old_reference(self):
        expected = self.subject()
        changed = b'{"fixture_only": true, "quarantine_enforced": false}'
        self.entries["deployment-manifest.json"] = changed
        subject = {**expected, "deployment_manifest_sha256": hashlib.sha256(changed).hexdigest()}
        self.entries["convergence.json"] = json.dumps(subject).encode()
        self.rehash()
        r = inspect_native_snapshot(self.entries, self.pins, expected)
        self.assertEqual(r["code"], "SUBJECT_BINDING_STALE")
        self.assertEqual(r["evidence_status"], "STALE")
        self.assertEqual(r["affected_guarantees"], "NOT_COMPUTED")

    def test_deployment_bytes_must_match_subject_digest(self):
        expected = self.subject()
        self.entries["deployment-manifest.json"] = b'{"fixture_only": "changed"}'; self.rehash()
        r = inspect_native_snapshot(self.entries, self.pins, expected)
        self.assertIn("deployment_manifest_bytes", r["mismatches"])

    def test_subject_evidence_must_be_inventoried(self):
        expected = self.subject()
        convergence = self.entries.pop("convergence.json"); self.rehash()
        self.entries["convergence.json"] = convergence
        self.assertEqual(inspect_native_snapshot(self.entries, self.pins, expected)["code"],
                         "SUBJECT_EVIDENCE_MISSING")

    def test_undeclared_real_world_claim_is_out_of_scope(self):
        r = inspect_native_snapshot(self.entries, self.pins, claim="real-banking-effect")
        self.assertEqual(r["outcome"], "OUT_OF_SCOPE")

    def test_pins_inside_bundle_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for path, body in self.entries.items():
                (root / path).write_bytes(body)
            pins = root / "pins.json"; pins.write_bytes(self.pins)
            r = inspect_native_bundle(root, pins)
            self.assertEqual(r["code"], "CAPTURE_OR_REFERENCE_INVALID")

    def test_cli_cannot_exit_success_for_partial_native_assurance(self):
        with tempfile.TemporaryDirectory() as name:
            parent = Path(name); root = parent / "bundle"; root.mkdir()
            for path, body in self.entries.items():
                (root / path).write_bytes(body)
            pins = parent / "pins.json"; pins.write_bytes(self.pins)
            run = subprocess.run([sys.executable, "-B", "-m", "proof01_w4.native_intake",
                                  str(root), "--pins", str(pins)], capture_output=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["code"], "NATIVE_READERS_REQUIRED")


if __name__ == "__main__":
    unittest.main()
