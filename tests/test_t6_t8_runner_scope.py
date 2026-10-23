"""Scope guards for RFC-4 lifecycle vectors in the REG runner.

Lab membrane observations must not become HTTP/native conformance claims.
These tests require no external provider and do not demonstrate T6-T8 behavior.
"""
import unittest
from unittest.mock import patch

from runner import (
    HTTPAdapter,
    NativeKernelAdapter,
    ReportingState,
)

IDS = ("CT-R4-011", "CT-R4-012", "CT-R4-013")


class LifecycleRunnerScopeTests(unittest.TestCase):
    def setUp(self):
        self.http = HTTPAdapter("http://127.0.0.1:1")
        # The targeted lifecycle handlers do not require an initialized kernel.
        # This avoids claiming that a real native subject was exercised.
        self.native = NativeKernelAdapter.__new__(NativeKernelAdapter)

    def test_t6_and_t8_have_explicit_implementation_gaps(self):
        for adapter in (self.http, self.native):
            for vector_id in ("CT-R4-011", "CT-R4-013"):
                with self.subTest(mode=adapter.interface_mode, vector=vector_id):
                    result = adapter.run_vector(vector_id)
                    self.assertEqual(result.status, ReportingState.IMPLEMENTATION_GAP)
                    self.assertEqual(result.interface_mode, adapter.interface_mode)
                    self.assertTrue(result.gap_note)

    def test_t7_lab_pass_is_not_native_or_http_pass(self):
        for adapter in (self.http, self.native):
            with self.subTest(mode=adapter.interface_mode):
                with patch("lifecycle.t7_membrane_probe.run_t7_probe",
                           return_value=("PASS", "qualified UNKNOWN to FAILED in lab")):
                    result = adapter.run_vector("CT-R4-012")
                self.assertEqual(result.status, ReportingState.IMPLEMENTATION_GAP)
                self.assertIn("Laboratory", result.gap_note)
                self.assertIn(adapter.interface_mode, result.gap_note)

    def test_t7_lab_failure_is_not_swallowed(self):
        for adapter in (self.http, self.native):
            with self.subTest(mode=adapter.interface_mode):
                with patch("lifecycle.t7_membrane_probe.run_t7_probe",
                           return_value=("FAIL", "evidence guard violated")):
                    result = adapter.run_vector("CT-R4-012")
                self.assertEqual(result.status, ReportingState.FAIL)

    def test_t7_missing_lab_is_explicit_gap(self):
        for adapter in (self.http, self.native):
            with self.subTest(mode=adapter.interface_mode):
                with patch("lifecycle.t7_membrane_probe.run_t7_probe",
                           return_value=("GAP", "lab package absent")):
                    result = adapter.run_vector("CT-R4-012")
                self.assertEqual(result.status, ReportingState.IMPLEMENTATION_GAP)

    def test_all_lifecycle_vectors_are_registered(self):
        from runner import CORE_VECTORS
        self.assertTrue(set(IDS).issubset(CORE_VECTORS))


if __name__ == "__main__":
    unittest.main()
