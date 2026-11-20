"""Negative controls for snapshot/report/ZIP binding; no provider effects."""
import hashlib
import io
import json
import os
import threading
import unittest
from unittest.mock import patch
import warnings
import zipfile

from proof01_w4 import auditor
from proof01_w4.verifier import verify_snapshot
import test_auditor


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.fx = test_auditor.AuditorKitTest("test_archives_identical_and_non_certifying")
        self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.output = self.fx.base / "snapshot.zip"

    def mutate_after_validation(self, target, replacement):
        validated = threading.Event()
        changed = threading.Event()
        errors = []
        original = auditor._report_snapshot
        first = True

        def writer():
            if not validated.wait(5):
                errors.append("validation signal missing")
                return
            try:
                target.write_bytes(replacement)
            except Exception as exc:
                errors.append(repr(exc))
            finally:
                changed.set()

        def observe(entries, claim=None):
            nonlocal first
            report = original(entries, claim)
            if first:
                first = False
                validated.set()
                if not changed.wait(5):
                    raise AssertionError("writer did not finish")
            return report

        thread = threading.Thread(target=writer)
        thread.start()
        try:
            with patch.object(auditor, "_report_snapshot", observe):
                result = auditor.package(self.fx.bundle, self.output)
        finally:
            validated.set()
            thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result["archive_replay"], "MATCHED_CAPTURED_BYTES")
        return self.output.read_bytes()

    def test_concurrent_receipt_change_keeps_verified_original_bytes(self):
        raw = self.mutate_after_validation(self.fx.bundle / "receipt.bin", b"changed-by-writer")
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(z.read("evidence/receipt.bin"), self.fx.evidence)
        self.assertEqual((self.fx.bundle / "receipt.bin").read_bytes(), b"changed-by-writer")
        self.assertEqual(auditor.verify_archive(raw)["operational_assurance"], "NOT_ESTABLISHED")

    def test_concurrent_manifest_change_keeps_verified_manifest(self):
        original = (self.fx.bundle / auditor.MANIFEST).read_bytes()
        raw = self.mutate_after_validation(self.fx.bundle / auditor.MANIFEST, b'{"changed":true}')
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            self.assertEqual(z.read("evidence/" + auditor.MANIFEST), original)
        auditor.verify_archive(raw)

    def test_mutation_between_manifest_and_artifact_capture_is_rejected(self):
        original = auditor._read_at
        def changed(fd, name):
            if name == "receipt.bin":
                (self.fx.bundle / name).write_bytes(b"changed-before-capture")
            return original(fd, name)
        with patch.object(auditor, "_read_at", changed):
            with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
                auditor.package(self.fx.bundle, self.output)
        self.assertFalse(self.output.exists())

    def test_undeclared_file_is_not_exported(self):
        (self.fx.bundle / "undeclared.txt").write_bytes(b"unlisted marker")
        auditor.package(self.fx.bundle, self.output)
        with zipfile.ZipFile(self.output) as z:
            self.assertNotIn("evidence/undeclared.txt", z.namelist())

    def test_parent_symlink_is_rejected(self):
        outside = self.fx.base / "outside"; outside.mkdir()
        (outside / "receipt.bin").write_bytes(self.fx.evidence)
        (self.fx.bundle / "linked").symlink_to(outside, target_is_directory=True)
        self.fx.manifest["artifacts"][0]["path"] = "linked/receipt.bin"
        self.fx.save()
        with self.assertRaises(ValueError):
            auditor.package(self.fx.bundle, self.output)

    def test_source_fifo_refused_without_blocking(self):
        os.mkfifo(self.fx.bundle / "fifo")
        self.fx.manifest["artifacts"][0]["path"] = "fifo"
        self.fx.save()
        with self.assertRaisesRegex(ValueError, "Non-regular"):
            auditor.package(self.fx.bundle, self.output)

    def test_duplicate_json_keys_are_rejected(self):
        path = self.fx.bundle / auditor.MANIFEST
        path.write_bytes(b'{"artifacts":[],"artifacts":[]}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            auditor.package(self.fx.bundle, self.output)

    def test_path_aliases_are_rejected(self):
        for name in ("./receipt.bin", "dir/../receipt.bin", "/receipt.bin",
                     "C:receipt.bin", "dir//receipt.bin", "dir\\receipt.bin"):
            with self.subTest(path=name):
                self.fx.manifest["artifacts"][0]["path"] = name
                self.fx.save()
                with self.assertRaises(ValueError):
                    auditor.package(self.fx.bundle, self.output)

    def rewritten(self, changes=None, extra=None):
        auditor.package(self.fx.bundle, self.output)
        buf = io.BytesIO()
        with zipfile.ZipFile(self.output) as source, zipfile.ZipFile(buf, "w") as out:
            for info in source.infolist():
                body = source.read(info)
                if changes and info.filename in changes:
                    body = changes[info.filename](body)
                out.writestr(info, body)
            if extra:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    out.writestr(extra[0], extra[1])
        return buf.getvalue()

    def test_final_zip_changed_receipt_is_refuted(self):
        raw = self.rewritten({"evidence/receipt.bin": lambda _: b"changed-in-zip"})
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            auditor.verify_archive(raw)

    def test_final_zip_fabricated_positive_report_is_refuted(self):
        def promote(body):
            report = json.loads(body)
            report["operational_assurance"] = "VERIFIED"
            return json.dumps(report).encode()
        raw = self.rewritten({auditor.REPORT: promote})
        with self.assertRaisesRegex(ValueError, "report does not match"):
            auditor.verify_archive(raw)

    def test_duplicate_zip_members_are_rejected(self):
        raw = self.rewritten(extra=("evidence/receipt.bin", self.fx.evidence))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            auditor.verify_archive(raw)

    def test_extra_zip_evidence_is_rejected(self):
        raw = self.rewritten(extra=("evidence/undeclared.bin", b"marker"))
        with self.assertRaisesRegex(ValueError, "inventory mismatch"):
            auditor.verify_archive(raw)

    def test_zip_escape_is_rejected_without_extraction(self):
        raw = self.rewritten(extra=("evidence/../outside", b"marker"))
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            auditor.verify_archive(raw)
        self.assertFalse((self.fx.base / "outside").exists())

    def test_size_and_count_limits_fail_closed(self):
        with patch.object(auditor, "MAX_FILE_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "Oversized"):
                auditor.package(self.fx.bundle, self.output)
        raw = self.rewritten()
        with patch.object(auditor, "MAX_TOTAL_BYTES", 4):
            with self.assertRaisesRegex(ValueError, "limit"):
                auditor.verify_archive(raw)
        with patch.object(auditor, "MAX_MEMBERS", 1):
            with self.assertRaisesRegex(ValueError, "Too many"):
                auditor.verify_archive(raw)

    def test_missing_report_is_not_self_certifying(self):
        _, entries = auditor._capture(self.fx.bundle)
        raw = auditor._zip(entries, {})
        with self.assertRaisesRegex(ValueError, "report does not match"):
            auditor.verify_archive(raw)

    def test_snapshot_requires_original_digest(self):
        entries = {auditor.MANIFEST: (self.fx.bundle / auditor.MANIFEST).read_bytes(),
                   "receipt.bin": b"changed"}
        self.assertEqual(verify_snapshot(entries)["code"], "HASH_MISMATCH")

    def test_unknown_effect_claim_remains_out_of_scope(self):
        auditor.package(self.fx.bundle, self.output)
        with self.assertRaisesRegex(ValueError, "SCOPE_MISMATCH"):
            auditor.verify_archive(self.output.read_bytes(), "no-unobserved-effects")


if __name__ == "__main__":
    unittest.main()
