#!/usr/bin/env python3
"""
REG Conformance Suite v0.3.1 — RFC-0 through RFC-7
==================================================
Registers 18 core/commit vectors (incl. T6–T8 lifecycle) and 38 extended integration vectors.
Results separate vector coverage, observed conformance status, and evidence level.
Extended vectors without an executable adapter report IMPLEMENTATION_GAP.

NOTE: Full adapter body was truncated by a bad push. This bootstrap restores
CORE_VECTORS (incl. CT-R4-011..013) and minimal handlers. Re-merge full adapters
from git history (commit 039774bef7369011089c33e55e937a157ce9e775 / pre-truncation).
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ReportingState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    ADAPTER_REQUIRED = "ADAPTER_REQUIRED"
    IMPLEMENTATION_GAP = "IMPLEMENTATION_GAP"


class EvidenceLevel(int, Enum):
    SEMANTIC_MAPPING = 1
    ADAPTER_TESTED = 2
    NATIVE_CONFORMANT = 3


@dataclass
class TestVector:
    vector_id: str
    rfc: str
    normative_property: str
    abstract_description: str


@dataclass
class ConformanceResult:
    vector_id: str
    status: ReportingState
    interface_mode: str
    evidence_level: int
    details: str = ""
    gap_note: str = ""


CORE_VECTORS: dict[str, TestVector] = {
    "C1": TestVector("C1", "RFC-3", "Standing Gate",
                     "Invalid credential → HARD_VETO regardless of structural state."),
    "C2": TestVector("C2", "RFC-2", "Structure Gate",
                     "P≥0.9, V≥0.9, K≤0.15 → FLAG or HARD_VETO, never PASS."),
    "C3": TestVector("C3", "RFC-3 §4.2; RFC-4 §2.2", "Commit-State Binding — Standing Revocation",
                     "Revocation after verdict and before/during commit must produce HARD_VETO."),
    "C4": TestVector("C4", "RFC-1", "Fail-Closed Transport Safety",
                     "Transport fault → no execution."),
    "C5": TestVector("C5", "RFC-1/4", "Replay Soundness — Idempotency",
                     "Duplicate nonce → REJECT/NONCE_REPLAY."),
    "CT-R4-001": TestVector("CT-R4-001", "RFC-4 §1", "Valid Grant Binding",
                            "Matching evaluation_id/action/nonce within window → GRANT/COMMITTED."),
    "CT-R4-002": TestVector("CT-R4-002", "RFC-4 §1.3", "Action/Payload Binding Violation",
                            "Grant for action_A; commit attempts action_B → REJECT/BINDING_VIOLATION."),
    "CT-R4-003": TestVector("CT-R4-003", "RFC-4 §2.1", "Replay Rejection",
                            "Consumed nonce reused → REJECT/REPLAY_DETECTED."),
    "CT-R4-004": TestVector("CT-R4-004", "RFC-4 §2", "Expired Grant Rejection",
                            "valid_until passed before commit → REJECT/EVALUATION_EXPIRED."),
    "CT-R4-005": TestVector("CT-R4-005", "RFC-4 §2.2", "Commit-State Binding / Race Detection",
                            "State (policy_epoch) changed between verdict and commit → REJECT/STATE_DRIFT."),
    "CT-R4-006": TestVector("CT-R4-006", "RFC-4 §1", "Non-PASS Cannot Cross Commit",
                            "HOLD or HARD_VETO → commit attempt → REJECT/INVALID_DISPOSITION."),
    "CT-R4-007": TestVector("CT-R4-007", "RFC-4 §3", "Decision Receipt Generation",
                            "Every disposition → cryptographically signed Receipt."),
    "CT-R4-008": TestVector("CT-R4-008", "RFC-4 §4", "Evidence Manifest Integrity",
                            "Append-only hash-chain manifest."),
    "CT-R4-009": TestVector("CT-R4-009", "RFC-4 §4", "Independent Evidence Verification",
                            "Third-party verifier reproduces decision from manifest."),
    "CT-R4-010": TestVector("CT-R4-010", "RFC-4 §1.1", "External-Effect Claim Boundary",
                            "external_effect_atomic=false; post_commit_evidence_required=true."),
    "CT-R4-011": TestVector("CT-R4-011", "RFC-4 lifecycle T6", "UNKNOWN → RESOLVED (qualified)",
                            "Qualified evidence within τ_K or explicit resolve transitions UNKNOWN/AWAITING to RESOLVED."),
    "CT-R4-012": TestVector("CT-R4-012", "RFC-4 lifecycle T7", "UNKNOWN → FAILED (evidence guard)",
                            "FAILED requires evidence_qualified=true; timeout alone must not auto-FAILED."),
    "CT-R4-013": TestVector("CT-R4-013", "RFC-4 lifecycle T8", "FAILED + retry_eligible → new attempt",
                            "retry_eligible=true allows a new attempt_id on same LEI; false keeps LEI locked."),
}

EXTENDED_VECTORS: dict[str, TestVector] = {}
VECTORS = {**CORE_VECTORS, **EXTENDED_VECTORS}


class BaseAdapter(ABC):
    interface_mode: str = "base"
    evidence_level: EvidenceLevel = EvidenceLevel.ADAPTER_TESTED

    def run_all(self, ids=None):
        return [self.run_vector(v) for v in (ids or list(VECTORS))]

    @abstractmethod
    def run_vector(self, vid: str) -> ConformanceResult: ...

    def _r(self, vid, status, details="", gap_note=""):
        return ConformanceResult(vid, status, self.interface_mode, int(self.evidence_level), details, gap_note)

    def _pass(self, v, d=""):
        return self._r(v, ReportingState.PASS, d)

    def _fail(self, v, d=""):
        return self._r(v, ReportingState.FAIL, d)

    def _gap(self, v, n=""):
        return self._r(v, ReportingState.IMPLEMENTATION_GAP, gap_note=n)


class HTTPAdapter(BaseAdapter):
    interface_mode = "adapter"
    evidence_level = EvidenceLevel.ADAPTER_TESTED

    def __init__(self, endpoint="", **kwargs):
        self.endpoint = endpoint

    def run_vector(self, vid: str) -> ConformanceResult:
        fn = getattr(self, "_v_" + vid.lower().replace("-", "_"), None)
        if fn:
            return fn()
        return self._gap(vid, "Handler not restored — re-merge full runner from history")

    def _v_ct_r4_011(self):
        return self._gap("CT-R4-011", "T6 lab-validated in tenir-conformance-s1-g1; HTTP adapter gap.")

    def _v_ct_r4_012(self):
        return self._gap("CT-R4-012", "T7 lab-validated in tenir-conformance-s1-g1; HTTP adapter gap.")

    def _v_ct_r4_013(self):
        return self._gap("CT-R4-013", "T8 lab-validated in tenir-conformance-s1-g1; HTTP adapter gap.")


class NativeKernelAdapter(BaseAdapter):
    interface_mode = "native"
    evidence_level = EvidenceLevel.NATIVE_CONFORMANT

    def run_vector(self, vid: str) -> ConformanceResult:
        fn = getattr(self, "_v_" + vid.lower().replace("-", "_"), None)
        if fn:
            return fn()
        return self._gap(vid, "Handler not restored — re-merge full runner from history")

    def _v_ct_r4_011(self):
        return self._gap("CT-R4-011", "T6 lab-validated in tenir-conformance-s1-g1; native gap.")

    def _v_ct_r4_012(self):
        return self._gap("CT-R4-012", "T7 lab-validated in tenir-conformance-s1-g1; native gap.")

    def _v_ct_r4_013(self):
        return self._gap("CT-R4-013", "T8 lab-validated in tenir-conformance-s1-g1; native gap.")


def main():
    print("REG Conformance Suite — bootstrap runner (lifecycle vectors registered).")
    print(f"Core vectors: {len(CORE_VECTORS)}")
    for vid in ("CT-R4-011", "CT-R4-012", "CT-R4-013"):
        tv = CORE_VECTORS[vid]
        print(f"  {vid}: {tv.normative_property}")
    print("WARNING: Full HTTP/Native adapter body must be re-merged from git history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
