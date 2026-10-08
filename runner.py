#!/usr/bin/env python3
"""
REG Conformance Suite v0.3.1 — RFC-0 through RFC-7
==================================================
Registers 18 core/commit vectors (incl. T6–T8 lifecycle) and 38 extended integration vectors.
Results separate vector coverage, observed conformance status, and evidence level.
Extended vectors without an executable adapter report IMPLEMENTATION_GAP.
"""

import argparse, base64, hashlib, importlib.metadata, json, subprocess, sys, time, uuid
import platform, re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

import requests


# ── Enums & dataclasses ───────────────────────────────────────────────────────

class ReportingState(str, Enum):
    PASS               = "PASS"
    FAIL               = "FAIL"
    INCONCLUSIVE       = "INCONCLUSIVE"
    NOT_APPLICABLE     = "NOT_APPLICABLE"
    ADAPTER_REQUIRED   = "ADAPTER_REQUIRED"
    IMPLEMENTATION_GAP = "IMPLEMENTATION_GAP"

class EvidenceLevel(int, Enum):
    SEMANTIC_MAPPING  = 1
    ADAPTER_TESTED    = 2
    NATIVE_CONFORMANT = 3

@dataclass
class TestVector:
    vector_id:            str
    rfc:                  str
    normative_property:   str
    abstract_description: str

@dataclass
class ConformanceResult:
    vector_id:      str
    status:         ReportingState
    interface_mode: str
    evidence_level: int
    details:        str = ""
    gap_note:       str = ""


# ── Core vectors — 18 (RFC-4 §5 + C-series + T6–T8 lifecycle) ─────────────────

CORE_VECTORS: dict[str, TestVector] = {
    "C1":       TestVector("C1","RFC-3","Standing Gate",
                    "Invalid credential → HARD_VETO regardless of structural state."),
    "C2":       TestVector("C2","RFC-2","Structure Gate",
                    "P≥0.9, V≥0.9, K≤0.15 → FLAG or HARD_VETO, never PASS."),
    "C3":       TestVector("C3","RFC-3 §4.2; RFC-4 §2.2","Commit-State Binding — Standing Revocation",
                    "Revocation after verdict and before/during commit must produce HARD_VETO and prevent the governed effect."),
    "C4":       TestVector("C4","RFC-1","Fail-Closed Transport Safety",
                    "Transport fault → no execution. NOT_APPLICABLE for in-process kernels."),
    "C5":       TestVector("C5","RFC-1/4","Replay Soundness — Idempotency",
                    "Duplicate nonce → REJECT/NONCE_REPLAY."),
    "CT-R4-001":TestVector("CT-R4-001","RFC-4 §1","Valid Grant Binding",
                    "Matching evaluation_id/action/nonce within window → GRANT/COMMITTED."),
    "CT-R4-002":TestVector("CT-R4-002","RFC-4 §1.3","Action/Payload Binding Violation",
                    "Grant for action_A; commit attempts action_B → REJECT/BINDING_VIOLATION."),
    "CT-R4-003":TestVector("CT-R4-003","RFC-4 §2.1","Replay Rejection",
                    "Consumed nonce reused → REJECT/REPLAY_DETECTED."),
    "CT-R4-004":TestVector("CT-R4-004","RFC-4 §2","Expired Grant Rejection",
                    "valid_until passed before commit → REJECT/EVALUATION_EXPIRED."),
    "CT-R4-005":TestVector("CT-R4-005","RFC-4 §2.2","Commit-State Binding / Race Detection",
                    "State (policy_epoch) changed between verdict and commit → REJECT/STATE_DRIFT."),
    "CT-R4-006":TestVector("CT-R4-006","RFC-4 §1","Non-PASS Cannot Cross Commit",
                    "HOLD or HARD_VETO → commit attempt → REJECT/INVALID_DISPOSITION."),
    "CT-R4-007":TestVector("CT-R4-007","RFC-4 §3","Decision Receipt Generation",
                    "Every disposition → cryptographically signed Receipt, independently verifiable."),
    "CT-R4-008":TestVector("CT-R4-008","RFC-4 §4","Evidence Manifest Integrity",
                    "Append-only hash-chain manifest; integrity verifiable at any time."),
    "CT-R4-009":TestVector("CT-R4-009","RFC-4 §4","Independent Evidence Verification",
                    "Third-party verifier reproduces decision from manifest without mutable state."),
    "CT-R4-010":TestVector("CT-R4-010","RFC-4 §1.1","External-Effect Claim Boundary",
                    "external_effect_atomic=false; post_commit_evidence_required=true."),
    "CT-R4-011":TestVector("CT-R4-011","RFC-4 lifecycle T6","UNKNOWN → RESOLVED (qualified)",
                    "Qualified evidence within τ_K or explicit resolve transitions UNKNOWN/AWAITING to RESOLVED; client may leave HOLD."),
    "CT-R4-012":TestVector("CT-R4-012","RFC-4 lifecycle T7","UNKNOWN → FAILED (evidence guard)",
                    "FAILED requires evidence_qualified=true; timeout alone must not auto-FAILED."),
    "CT-R4-013":TestVector("CT-R4-013","RFC-4 lifecycle T8","FAILED + retry_eligible → new attempt",
                    "retry_eligible=true allows a new attempt_id on same LEI; retry_eligible=false keeps LEI locked."),
}
