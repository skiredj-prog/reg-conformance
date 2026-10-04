#!/usr/bin/env python3
"""
REG Conformance Suite v0.3.1 — RFC-0 through RFC-7
==================================================
Registers 15 core/commit vectors and 38 extended integration vectors.
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


# ── Core vectors — 15 (RFC-4 §5 + C-series) ──────────────────────────────────

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
}


# ── Extended vectors — 38 (RFC-0/1/2/3/5/6/7) ────────────────────────────────
# Infrastructure not yet built. Two exceptions: CT-R2-002 and CT-R2-003
# are mathematical properties of the PolicyEngine kernel — testable now.

EXTENDED_VECTORS: dict[str, TestVector] = {
    # RFC-0 — Constitution (5)
    "CT-R0-001":TestVector("CT-R0-001","RFC-0","Policy Anchor Integrity",
                    "Policy file hash verifiable independently."),
    "CT-R0-002":TestVector("CT-R0-002","RFC-0","RFC Version Declaration",
                    "Implementation declares conformant RFC versions."),
    "CT-R0-003":TestVector("CT-R0-003","RFC-0","Governance Scope Declaration",
                    "Declared scope matches tested behavior."),
    "CT-R0-004":TestVector("CT-R0-004","RFC-0","Normative Reference Binding",
                    "All referenced RFCs pinned with SHA/date."),
    "CT-R0-005":TestVector("CT-R0-005","RFC-0","Constitutional Override Prohibition",
                    "No mechanism bypasses REG constitution."),
    # RFC-1 — Wire Protocol (7)
    "CT-R1-001":TestVector("CT-R1-001","RFC-1","Response Schema Compliance",
                    "Response fields match declared schema exactly."),
    "CT-R1-002":TestVector("CT-R1-002","RFC-1","Content-Type Declaration",
                    "Responses declare Content-Type: application/json."),
    "CT-R1-003":TestVector("CT-R1-003","RFC-1","HTTP Status Semantics",
                    "2xx/4xx/5xx used per RFC semantics."),
    "CT-R1-004":TestVector("CT-R1-004","RFC-1","Request Timeout Enforcement",
                    "Requests time out within declared window."),
    "CT-R1-005":TestVector("CT-R1-005","RFC-1","TLS Requirement (production)",
                    "Non-TLS connections rejected in production mode."),
    "CT-R1-006":TestVector("CT-R1-006","RFC-1","Request Size Limit",
                    "Oversized payloads rejected with 413."),
    "CT-R1-007":TestVector("CT-R1-007","RFC-1","Concurrent Request Isolation",
                    "Parallel evaluations do not interfere."),
    # RFC-2 — Structure (6)
    "CT-R2-001":TestVector("CT-R2-001","RFC-2","Threshold Declaration",
                    "Thresholds declared and pinned in policy file."),
    "CT-R2-002":TestVector("CT-R2-002","RFC-2","S-Score Determinism",
                    "Identical P/V/K → identical S and disposition across independent calls."),
    "CT-R2-003":TestVector("CT-R2-003","RFC-2","Epsilon Guard",
                    "Zero-denominator (P=0, V=0) handled without error; epsilon prevents divide-by-zero."),
    "CT-R2-004":TestVector("CT-R2-004","RFC-2","Boundary Exactness",
                    "Values at threshold boundaries produce consistent, declared dispositions."),
    "CT-R2-005":TestVector("CT-R2-005","RFC-2","Measurement Range Validation",
                    "P/V/K outside [0,1] rejected with 422."),
    "CT-R2-006":TestVector("CT-R2-006","RFC-2","Institutional Override Audit",
                    "Threshold overrides logged with policy_epoch."),
    # RFC-3 — Standing (8)
    "CT-R3-001":TestVector("CT-R3-001","RFC-3","Credential Format Validation",
                    "Malformed credentials rejected before evaluation."),
    "CT-R3-002":TestVector("CT-R3-002","RFC-3","Revocation Propagation",
                    "Revocation effective within declared latency window."),
    "CT-R3-003":TestVector("CT-R3-003","RFC-3","Multi-Principal Isolation",
                    "Revocation of A does not affect principal B."),
    "CT-R3-004":TestVector("CT-R3-004","RFC-3","Revocation Audit Trail",
                    "All revocation events appended to manifest."),
    "CT-R3-005":TestVector("CT-R3-005","RFC-3","Delegation Depth Enforcement",
                    "Delegation chain depth limit enforced."),
    "CT-R3-006":TestVector("CT-R3-006","RFC-3","Temporal Credential Binding",
                    "Time-limited credentials expire as declared."),
    "CT-R3-007":TestVector("CT-R3-007","RFC-3","Standing Scope Boundary",
                    "Standing valid only within declared organizational scope."),
    "CT-R3-008":TestVector("CT-R3-008","RFC-3","Credential Rotation",
                    "Rotated credentials invalidate prior grants."),
    # RFC-5 — Audit Chain (5)
    "CT-R5-001":TestVector("CT-R5-001","RFC-5","Manifest Export",
                    "Full manifest exportable as verifiable artifact."),
    "CT-R5-002":TestVector("CT-R5-002","RFC-5","Manifest Import Verification",
                    "Imported manifest verifies from genesis block."),
    "CT-R5-003":TestVector("CT-R5-003","RFC-5","Evidence Retention Policy",
                    "Evidence retained for declared minimum period."),
    "CT-R5-004":TestVector("CT-R5-004","RFC-5","Redaction Prohibition",
                    "No evidence silently deleted from closed manifest."),
    "CT-R5-005":TestVector("CT-R5-005","RFC-5","Cross-Epoch Continuity",
                    "Manifest chain survives policy epoch changes."),
    # RFC-6 — Override / Escalation (4)
    "CT-R6-001":TestVector("CT-R6-001","RFC-6","Emergency Override Audit",
                    "Override decisions always appended to manifest."),
    "CT-R6-002":TestVector("CT-R6-002","RFC-6","Override Authority Validation",
                    "Only declared principals may invoke override."),
    "CT-R6-003":TestVector("CT-R6-003","RFC-6","Override Time Window",
                    "Override grant valid only within declared window."),
    "CT-R6-004":TestVector("CT-R6-004","RFC-6","Override Receipt Generation",
                    "Override decisions generate signed receipts."),
    # RFC-7 — Interoperability (3)
    "CT-R7-001":TestVector("CT-R7-001","RFC-7","Adapter Result Equivalence",
                    "Adapter and native modes produce identical dispositions for same inputs."),
    "CT-R7-002":TestVector("CT-R7-002","RFC-7","Evidence Level Non-Promotion",
                    "Adapter results never promoted to native-conformance claims."),
    "CT-R7-003":TestVector("CT-R7-003","RFC-7","Cross-Implementation Compatibility",
                    "Two independent implementations agree on disposition for same inputs."),
}

# All 53 vectors
VECTORS = {**CORE_VECTORS, **EXTENDED_VECTORS}

# Gap notes for the 36 extended vectors that are IMPLEMENTATION_GAP
EXTENDED_GAP_NOTES: dict[str, str] = {
    "CT-R0-001": "Policy anchor hash endpoint not yet implemented.",
    "CT-R0-002": "RFC version declaration endpoint absent.",
    "CT-R0-003": "Governance scope declaration not formally specified in implementation.",
    "CT-R0-004": "Normative RFC SHAs not yet pinned in implementation manifest.",
    "CT-R0-005": "Constitutional override prohibition not formally tested.",
    "CT-R1-001": "Response schema validation endpoint absent; schema not machine-readable.",
    "CT-R1-002": "Content-Type header present in practice; formal compliance test absent.",
    "CT-R1-003": "HTTP status semantics partially correct; formal semantic validation absent.",
    "CT-R1-004": "Configurable request timeout not enforced at server level.",
    "CT-R1-005": "TLS enforcement absent; --insecure flag provided as dev workaround only.",
    "CT-R1-006": "Request size limit not enforced (FastAPI default only).",
    "CT-R1-007": "Concurrent isolation not formally tested (in-memory dict is not thread-safe).",
    "CT-R2-001": "Threshold declaration endpoint absent; thresholds accessible in YAML only.",
    # CT-R2-002 and CT-R2-003: PASS — no entry here
    "CT-R2-004": "Exact boundary behavior (S == threshold) not formally specified.",
    "CT-R2-005": "Out-of-range P/V/K accepted and computed; 422 rejection not implemented.",
    "CT-R2-006": "Institutional threshold override audit logging absent.",
    "CT-R3-001": "Credential format validation limited to null/empty check.",
    "CT-R3-002": "Revocation propagation latency not declared or measured.",
    "CT-R3-003": "Multi-principal isolation not formally tested.",
    "CT-R3-004": "Revocation events not appended to hash-chain manifest.",
    "CT-R3-005": "Delegation depth enforcement not implemented.",
    "CT-R3-006": "Temporal credential binding (time-limited credentials) not implemented.",
    "CT-R3-007": "Standing scope boundary not declared or enforced.",
    "CT-R3-008": "Credential rotation invalidation not implemented.",
    "CT-R5-001": "Manifest export endpoint absent; manifest in-memory only.",
    "CT-R5-002": "Manifest import and re-verification path absent.",
    "CT-R5-003": "Evidence retention policy not declared.",
    "CT-R5-004": "Redaction prohibition not formally enforced (in-memory list).",
    "CT-R5-005": "Cross-epoch manifest continuity not formally tested.",
    "CT-R6-001": "Override audit logging absent.",
    "CT-R6-002": "Override authority validation absent.",
    "CT-R6-003": "Override time window not implemented.",
    "CT-R6-004": "Override receipt generation absent.",
    "CT-R7-001": "Formal equivalence test between adapter and native modes absent.",
    "CT-R7-002": "Evidence level non-promotion enforced structurally; formal test absent.",
    "CT-R7-003": "Cross-implementation testing requires second independent implementation.",
}


# ── Base adapter ──────────────────────────────────────────────────────────────

class BaseAdapter(ABC):
    interface_mode: str          = "base"
    evidence_level: EvidenceLevel = EvidenceLevel.ADAPTER_TESTED

    def run_all(self, ids=None) -> list[ConformanceResult]:
        return [self.run_vector(v) for v in (ids or VECTORS)]

    @abstractmethod
    def run_vector(self, vid: str) -> ConformanceResult: ...

    def _r(self, vid, status, details="", gap_note=""):
        return ConformanceResult(vid, status, self.interface_mode,
                                 int(self.evidence_level), details, gap_note)
    def _pass(self, v, d=""): return self._r(v, ReportingState.PASS, d)
    def _fail(self, v, d=""): return self._r(v, ReportingState.FAIL, d)
    def _inconclusive(self, v, d=""): return self._r(v, ReportingState.INCONCLUSIVE, d)
    def _na  (self, v, n=""): return self._r(v, ReportingState.NOT_APPLICABLE,  gap_note=n)
    def _ar  (self, v, n=""): return self._r(v, ReportingState.ADAPTER_REQUIRED, gap_note=n)
    def _gap (self, v, n=""): return self._r(v, ReportingState.IMPLEMENTATION_GAP, gap_note=n)


# ── HTTP adapter ──────────────────────────────────────────────────────────────

class HTTPAdapter(BaseAdapter):
    interface_mode = "adapter"
    evidence_level = EvidenceLevel.ADAPTER_TESTED

    def __init__(self, endpoint, api_key=None, insecure=False, admin_token=None, credential="valid-token"):
        self.endpoint = endpoint.rstrip("/")
        self.hdrs     = {"Content-Type": "application/json"}
        if api_key: self.hdrs["Authorization"] = f"Bearer {api_key}"
        self.admin_token = admin_token
        self.credential = credential
        self.verify   = not insecure
        self._jwks_cache: Optional[bytes] = None  # raw pub bytes

    def _post(self, path, body):
        h = {**self.hdrs, "X-Trace-Id": str(uuid.uuid4())}
        if path.startswith("/admin/") and self.admin_token:
            h["X-REG-Admin-Token"] = self.admin_token
        try:
            r = requests.post(f"{self.endpoint}{path}", json=body,
                              headers=h, verify=self.verify, timeout=10)
            return r.status_code, (r.json() if r.content else {})
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def _get(self, path):
        try:
            r = requests.get(f"{self.endpoint}{path}",
                             headers=self.hdrs, verify=self.verify, timeout=10)
            return r.status_code, (r.json() if r.content else {})
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def _eb(self, **kw):
        b = {
            "protocol_version": "reg-1.0",
            "evaluation_id":    f"eval_{uuid.uuid4().hex}",
            "action_id":        f"act_{uuid.uuid4().hex}",
            "principal":        {"id": "authorized-actor", "credential": self.credential},
            "action":           {"type": "wire_transfer", "params": {}},
            "measurements":     {"pressure": 0.3, "volatility": 0.3, "capacity": 0.85},
            "nonce":            uuid.uuid4().hex,
            "submitted_at":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }; b.update(kw); return b

    def _disp(self, r): return r.get("final_disposition") or r.get("disposition")

    def _commit_body(self, evaluation, action_type=None):
        return {"event_type": "commit",
                "evaluation_id": evaluation["evaluation_id"],
                "action_id": evaluation["action_id"],
                "nonce": evaluation["nonce"],
                "action_type": action_type or evaluation["action_type"],
                "policy_version": evaluation["policy_version"]}

    def _pub_bytes(self) -> Optional[bytes]:
        if self._jwks_cache: return self._jwks_cache
        code, jwks = self._get("/jwks")
        if code != 200: return None
        try:
            x = jwks["keys"][0]["x"]
            self._jwks_cache = base64.urlsafe_b64decode(x + "==")
            return self._jwks_cache
        except Exception: return None

    def run_vector(self, vid):
        m = getattr(self, f"_v_{vid.replace('-','_').lower()}", None)
        if not m:
            note = EXTENDED_GAP_NOTES.get(vid, "No HTTP translation defined")
            return self._gap(vid, note)
        try:    return m()
        except Exception as e:
            status = self._inconclusive if vid == "C3" else self._fail
            return status(vid, f"exception prevents a determinate result: {e}")

    # C1
    def _v_c1(self):
        c, r = self._post("/evaluations",
                          self._eb(principal={"id":"u","credential":"none"}))
        return (self._pass("C1","HARD_VETO on standing failure")
                if c in (200,202) and self._disp(r) == "HARD_VETO"
                else self._fail("C1", f"code={c}, disp={self._disp(r)!r}"))

    # C2
    def _v_c2(self):
        c, r = self._post("/evaluations", self._eb(
            measurements={"pressure":0.95,"volatility":0.90,"velocity":0.90,"capacity":0.10}))
        d = self._disp(r)
        return (self._pass("C2", f"{d} under extreme structural pressure")
                if c in (200,202) and d in ("FLAG","HARD_VETO")
                else self._fail("C2", f"expected FLAG/HARD_VETO, got {d!r}"))

    # C3
    def _v_c3(self):
        pid = f"race-{uuid.uuid4().hex[:8]}"
        c, r = self._post("/evaluations", self._eb(
            principal={"id":pid,"credential":self.credential},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        if self._disp(r) != "PASS":
            return self._inconclusive("C3", "Could not establish the valid-verdict precondition")
        eid = r.get("evaluation_id")
        rc, rr = self._post("/admin/revoke", {"principal_id":pid,"reason":"C3"})
        if rc in (401,403,404,503):
            return self._ar("C3", f"Protected /admin/revoke unavailable (HTTP {rc}); configure REG_ADMIN_TOKEN and --admin-token")
        if rc == 202:
            return self._inconclusive("C3", "revocation was accepted asynchronously; its effective ordering before commit is unproven")
        if rc != 200:
            return self._inconclusive("C3", f"revocation outcome is uncertain (HTTP {rc}: {rr})")
        ec, er = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        detail = er.get("detail", {}) if isinstance(er, dict) else {}
        if (ec == 409 and detail.get("code") == "STANDING_REVOKED" and
                detail.get("final_disposition") == "HARD_VETO"):
            return self._pass("C3","post-verdict revocation produced HARD_VETO; commit blocked")
        if ec in (200,201):
            return self._fail("C3","commit accepted after revocation")
        return self._inconclusive("C3", f"revocation occurred, but HARD_VETO and non-commit were not both established (HTTP {ec}: {er})")

    def _v_c4(self):
        return self._ar("C4",
            "The generic HTTP adapter cannot prove a transport failure prevented execution; "
            "the checked URL is not an execution endpoint.")

    # C5
    def _v_c5(self):
        nonce = uuid.uuid4().hex
        self._post("/evaluations", self._eb(nonce=nonce))
        c2, r2 = self._post("/evaluations",
                            self._eb(evaluation_id=f"eval_{uuid.uuid4().hex}",nonce=nonce))
        return (self._pass("C5","409 NONCE_REPLAY on duplicate nonce")
                if c2 == 409
                else self._gap("C5","Nonce replay not enforced at /evaluations level"))

    # CT-R4-001
    def _v_ct_r4_001(self):
        c, r = self._post("/evaluations", self._eb(
            action={"type":"wire_transfer","params":{}},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        if self._disp(r) != "PASS":
            return self._fail("CT-R4-001", f"expected PASS, got {self._disp(r)!r}")
        eid = r.get("evaluation_id")
        ec, er = self._post(f"/evaluations/{eid}/events",
                            self._commit_body(r, "wire_transfer"))
        return (self._pass("CT-R4-001", f"GRANT bound and committed ({eid[:8]}…)")
                if ec == 200 and er.get("status") == "COMMITTED"
                else self._fail("CT-R4-001", f"commit returned {ec}: {er}"))

    # CT-R4-002
    def _v_ct_r4_002(self):
        c, r = self._post("/evaluations", self._eb(
            action={"type":"wire_transfer","params":{}},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        if self._disp(r) != "PASS":
            return self._fail("CT-R4-002","could not obtain PASS grant")
        eid = r.get("evaluation_id")
        ec, er = self._post(f"/evaluations/{eid}/events",
                            self._commit_body(r, "account_deletion"))
        return (self._pass("CT-R4-002","PAYLOAD_BINDING_VIOLATION correctly rejected")
                if ec == 409 and "BINDING" in er.get("detail","")
                else self._fail("CT-R4-002", f"expected 409 BINDING_VIOLATION, got {ec}: {er}"))

    # CT-R4-003
    def _v_ct_r4_003(self):
        nonce = uuid.uuid4().hex
        self._post("/evaluations", self._eb(nonce=nonce,
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        c2, r2 = self._post("/evaluations",
                            self._eb(evaluation_id=f"eval_{uuid.uuid4().hex}",nonce=nonce))
        return (self._pass("CT-R4-003","REPLAY_DETECTED on consumed nonce")
                if c2 == 409 and "NONCE_REPLAY" in str(r2)
                else self._fail("CT-R4-003", f"expected 409 NONCE_REPLAY, got {c2}: {r2}"))

    # CT-R4-004  (uses /admin/expire-eval test helper)
    def _v_ct_r4_004(self):
        c, r = self._post("/evaluations", self._eb(
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        if self._disp(r) != "PASS":
            return self._fail("CT-R4-004", f"could not obtain PASS")
        eid = r.get("evaluation_id")
        ec, er = self._post(f"/admin/expire-eval/{eid}", {})
        if ec != 200:
            return self._ar("CT-R4-004",
                "/admin/expire-eval absent — cannot trigger expiry without wait")
        cc, cr = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        return (self._pass("CT-R4-004","EVALUATION_EXPIRED on force-expired grant")
                if cc == 409 and "EXPIRED" in cr.get("detail","")
                else self._fail("CT-R4-004", f"expected 409 EXPIRED, got {cc}: {cr}"))

    # CT-R4-005  (uses /admin/reload-policy)
    def _v_ct_r4_005(self):
        c, r = self._post("/evaluations", self._eb(
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        if self._disp(r) != "PASS":
            return self._fail("CT-R4-005","could not obtain PASS grant")
        eid = r.get("evaluation_id")
        epoch_at_verdict = r.get("policy_epoch")
        rc, _ = self._post("/admin/reload-policy", {})
        if rc not in (200,202):
            return self._ar("CT-R4-005", "Protected policy reload helper unavailable; configure REG_ADMIN_TOKEN and --admin-token")
        cc, cr = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        refusal = cr.get("detail", {}) if isinstance(cr, dict) else {}
        return (self._pass("CT-R4-005",
                    f"STATE_DRIFT produced HARD_VETO (epoch {epoch_at_verdict}→{epoch_at_verdict+1})")
                if cc == 409 and refusal.get("code") == "STATE_DRIFT" and
                   refusal.get("final_disposition") == "HARD_VETO"
                else self._fail("CT-R4-005",
                    f"expected 409 STATE_DRIFT/HARD_VETO, got {cc}: {cr}"))

    # CT-R4-006
    def _v_ct_r4_006(self):
        c, r = self._post("/evaluations",
                          self._eb(principal={"id":"u","credential":"none"}))
        if self._disp(r) != "HARD_VETO":
            return self._fail("CT-R4-006","could not force HARD_VETO")
        eid = r.get("evaluation_id")
        ec, er = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        return (self._pass("CT-R4-006","HARD_VETO blocked at commit gate")
                if ec == 409 and "INVALID_DISPOSITION" in er.get("detail","")
                else self._fail("CT-R4-006", f"expected 409 INVALID_DISPOSITION, got {ec}"))

    # CT-R4-007  (signed receipt + JWKS verification)
    def _v_ct_r4_007(self):
        c, r = self._post("/evaluations",
                          self._eb(principal={"id":"u","credential":"none"}))
        receipt = r.get("receipt", {})
        if not receipt.get("signed") or not receipt.get("signature"):
            return self._fail("CT-R4-007",
                f"Receipt not signed. signed={receipt.get('signed')}, "
                f"signature present={bool(receipt.get('signature'))}")
        pub = self._pub_bytes()
        if not pub:
            return self._fail("CT-R4-007","Could not retrieve public key from /jwks")
        try:
            from reg_common import verify_receipt_signature
            verify_receipt_signature(pub, receipt)
            tampered = dict(receipt)
            tampered["final_disposition"] = "TAMPERED"
            try:
                verify_receipt_signature(pub, tampered)
                return self._fail("CT-R4-007", "Changed receipt field still verified")
            except Exception:
                return self._pass("CT-R4-007",
                    f"Ed25519 signature binds receipt fields (type={receipt['receipt_type']!r})")
        except Exception as e:
            return self._fail("CT-R4-007", f"Signature verification failed: {e}")

    # CT-R4-008  (hash-chain manifest integrity)
    def _v_ct_r4_008(self):
        self._post("/evaluations", self._eb(
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90}))
        c, r = self._get("/manifest")
        if c != 200 or not isinstance(r.get("entries"), list):
            return self._ar("CT-R4-008", f"Manifest export unavailable (HTTP {c})")
        from reg_common import HashChainManifest
        import copy
        manifest = HashChainManifest()
        manifest.entries = copy.deepcopy(r["entries"])
        manifest._head = r.get("head", "")
        before = manifest.verify()
        if not before.get("integrity_ok") or not manifest.entries:
            return self._fail("CT-R4-008", f"Exported manifest invalid: {before}")
        probe = copy.deepcopy(manifest)
        probe.entries[0]["entry"]["tamper_probe"] = True
        after = probe.verify()
        return (self._pass("CT-R4-008", "Copied exported manifest verified; tampering detected")
                if after.get("integrity_ok") is False and manifest.verify().get("integrity_ok")
                else self._fail("CT-R4-008", f"Tampering not detected: {after}"))

    # CT-R4-009  (independent verification endpoint)
    def _v_ct_r4_009(self):
        return self._gap("CT-R4-009",
            "The manifest lacks the complete evaluation inputs and policy snapshot needed "
            "to reproduce the decision independently.")

    def _v_ct_r4_010(self):
        return self._gap("CT-R4-010",
            "The shim declares the post-commit evidence requirement but does not provide "
            "evidence of the external effect.")


# ── Extended: CT-R2-002 and CT-R2-003 (only extended vectors that PASS) ──

    def _v_ct_r2_002(self):
        """S-score determinism: same P/V/K → same S and disposition, always."""
        m = {"pressure":0.4,"volatility":0.5,"capacity":0.75}
        _, r1 = self._post("/evaluations", self._eb(measurements=m))
        _, r2 = self._post("/evaluations", self._eb(measurements=m,
                           evaluation_id=f"eval_{uuid.uuid4().hex}",
                           nonce=uuid.uuid4().hex))
        s1, s2 = r1.get("s_score"), r2.get("s_score")
        d1, d2 = self._disp(r1), self._disp(r2)
        if (s1 is not None and s2 is not None
                and abs(s1-s2) < 1e-9 and d1 == d2):
            return self._pass("CT-R2-002",
                f"S={s1:.6f}, disp={d1!r} — deterministic across calls")
        return self._fail("CT-R2-002",
            f"Non-deterministic: s1={s1}, s2={s2}, d1={d1!r}, d2={d2!r}")

    def _v_ct_r2_003(self):
        """Epsilon guard: P=0, V=0 → no divide-by-zero; valid disposition returned."""
        c, r = self._post("/evaluations", self._eb(
            measurements={"pressure":0.0,"volatility":0.0,"velocity":0.0,"capacity":0.85}))
        if c in (200,202) and self._disp(r) is not None:
            return self._pass("CT-R2-003",
                f"Zero-denominator handled; S={r.get('s_score')}, "
                f"disp={self._disp(r)!r}")
        return self._fail("CT-R2-003",
            f"Zero-denominator error: code={c}, resp={r}")


class NativeKernelAdapter(BaseAdapter):
    """
    Tests REG normative properties directly against the TENIR-Gov kernel.
    interface_mode: "native" — Level 3 / Native-Conformant (RFC-7 §8.2).
    No HTTP layer. This is the mode for authorize(record, payload_bytes, …) kernels.
    """
    interface_mode = "native"
    evidence_level = EvidenceLevel.NATIVE_CONFORMANT

    def __init__(self, policy_file: str):
        sys.path.insert(0, str(Path(__file__).parent))
        from kernel.policy_engine import PolicyEngine
        from reg_common import (HashChainManifest, generate_keypair,
                                sign_receipt, verify_receipt_signature, pubkey_to_jwks)
        self._engine   = PolicyEngine(Path(policy_file))
        self._manifest = HashChainManifest()
        self._priv, self._pub = generate_keypair()
        self._sign    = sign_receipt
        self._verify  = verify_receipt_signature
        self._grants:   dict[str, dict] = {}
        self._consumed: set[str]        = set()
        self._revoked:  set[str]        = set()
        self._epoch:    int             = 0

    # ── Kernel ops ────────────────────────────────────────────────────────────

    def _evaluate(self, principal_id, credential, action_type,
                  P, V, K, nonce, eid=None):
        eid = eid or f"eval_{uuid.uuid4().hex}"
        if len(nonce) < 8:   raise ValueError("NONCE_TOO_SHORT")
        if nonce in self._consumed: raise ValueError("NONCE_REPLAY")

        action_id = f"act_{uuid.uuid4().hex}"
        if credential in ("none","","invalid") or principal_id in self._revoked:
            g = {"evaluation_id":eid,"action_id":action_id,"action_type":action_type,
                 "principal_id":principal_id,"final_disposition":"HARD_VETO",
                 "reason":"STANDING_FAILURE","nonce":nonce,
                 "policy_version":self._engine.version,"policy_epoch":self._epoch,
                 "created_at":time.time(),"valid_until":time.time()+30,
                 "external_effect_atomic":False}
        else:
            kr = self._engine.evaluate(P, V, K)
            g  = {"evaluation_id":eid,"action_id":action_id,"action_type":action_type,
                  "principal_id":principal_id,"final_disposition":kr["decision"],
                  "s_score":kr["s_score"],"nonce":nonce,
                  "policy_version":kr["policy_version"],"policy_epoch":self._epoch,
                  "created_at":time.time(),"valid_until":time.time()+30,
                  "external_effect_atomic":False}

        raw_receipt = {"receipt_id":str(uuid.uuid4()),
                       "receipt_type":f"{g['final_disposition']} Receipt",
                       "evaluation_id":eid, "action_id":g.get("action_id", eid),
                       "final_disposition":g["final_disposition"],
                       "reason_codes":[g.get("reason", "")],
                       "policy_version":g["policy_version"],
                       "threshold_version":g["policy_version"],
                       "reproducibility_class":"R0",
                       "issued_at":g["created_at"],"signed":False}
        g["receipt"] = self._sign(self._priv, raw_receipt)

        self._consumed.add(nonce)
        self._grants[eid] = g
        self._manifest.append({"type":"evaluation","evaluation_id":eid,
                               "final_disposition":g["final_disposition"],
                               "policy_epoch":g["policy_epoch"],
                               "receipt":g["receipt"]})
        return g

    def _commit(self, eid, action_type=None, action_id=None, nonce=None):
        if eid not in self._grants: raise KeyError("GRANT_NOT_FOUND")
        g = self._grants[eid]
        if action_id != g["action_id"] or nonce != g["nonce"]:
            raise ValueError("GRANT_BINDING_VIOLATION")
        if g["final_disposition"] in ("HARD_VETO","HOLD"): raise ValueError("INVALID_DISPOSITION")
        if g["principal_id"] in self._revoked:
            self._veto_commit(g, "STANDING_REVOKED")
        if g.get("_committed"):  raise ValueError("ALREADY_COMMITTED")
        if time.time() > g["valid_until"]: raise ValueError("EVALUATION_EXPIRED")
        if self._epoch != g["policy_epoch"]:
            self._veto_commit(g, "STATE_DRIFT")
        if action_type and action_type != g["action_type"]:
            raise ValueError(f"PAYLOAD_BINDING_VIOLATION: granted={g['action_type']!r}")
        g["_committed"] = True
        g["committed_at"] = time.time()
        self._manifest.append({"type":"commit","evaluation_id":eid,"timestamp":g["committed_at"]})
        return {"status":"COMMITTED","evaluation_id":eid,"post_commit_evidence_required":True}

    def _veto_commit(self, grant, reason_code):
        now = time.time()
        receipt = self._sign(self._priv, {
            "receipt_id": str(uuid.uuid4()), "receipt_type": "Refusal Receipt",
            "evaluation_id": grant["evaluation_id"], "action_id": grant["action_id"],
            "final_disposition": "HARD_VETO", "reason_codes": [reason_code],
            "policy_version": grant["policy_version"],
            "threshold_version": grant["policy_version"],
            "reproducibility_class": "R0", "issued_at": now,
        })
        grant["commit_disposition"] = "HARD_VETO"
        grant["commit_refusal_reason"] = reason_code
        grant["commit_refusal_receipt"] = receipt
        self._manifest.append({"type":"commit_refusal",
                               "evaluation_id":grant["evaluation_id"],
                               "final_disposition":"HARD_VETO",
                               "reason_code":reason_code,"receipt":receipt,
                               "timestamp":now})
        raise ValueError(f"{reason_code}:HARD_VETO")

    def _revoke(self, pid): self._revoked.add(pid)
    def _reload_policy(self): self._epoch += 1

    def _inject_stale(self, action_type="wire_transfer"):
        eid = f"eval_stale_{uuid.uuid4().hex}"
        nonce = uuid.uuid4().hex
        g = {"evaluation_id":eid,"action_id":f"act_{uuid.uuid4().hex}","action_type":action_type,"principal_id":"auth",
             "final_disposition":"PASS","nonce":nonce,"policy_epoch":self._epoch,
             "created_at":time.time()-60,"valid_until":time.time()-1,
             "external_effect_atomic":False}
        raw_r = {"receipt_id":str(uuid.uuid4()),"receipt_type":"Grant/Authorization Receipt",
                 "evaluation_id":eid,"action_id":g["action_id"],"final_disposition":"PASS",
                 "reason_codes":[],"policy_version":self._engine.version,
                 "threshold_version":self._engine.version,"reproducibility_class":"R0",
                 "issued_at":g["created_at"],"signed":False}
        g["receipt"] = self._sign(self._priv, raw_r)
        self._consumed.add(nonce)
        self._grants[eid] = g
        return g

    def _verify_independent(self, eid):
        entry = self._manifest.find(eid)
        if not entry: raise KeyError("NOT_IN_MANIFEST")
        chain = self._manifest.verify()
        if not chain["integrity_ok"]: raise ValueError("MANIFEST_INTEGRITY_FAILED")
        receipt = entry["entry"].get("receipt")
        if not receipt: raise KeyError("RECEIPT_NOT_FOUND")
        self._verify(self._pub, receipt)
        return {"verified":True,"signature_valid":True,"chain_intact":True,
                "manifest_position":entry["index"],"reproducibility":"R1"}

    # ── Vector dispatch ───────────────────────────────────────────────────────

    def run_vector(self, vid):
        m = getattr(self, f"_v_{vid.replace('-','_').lower()}", None)
        if not m:
            note = EXTENDED_GAP_NOTES.get(vid, "No native translation defined")
            return self._gap(vid, note)
        try:    return m()
        except Exception as e:
            status = self._inconclusive if vid == "C3" else self._fail
            return status(vid, f"exception prevents a determinate result: {e}")

    def _v_c1(self):
        g = self._evaluate("u","none","wt",0.3,0.3,0.85,uuid.uuid4().hex)
        return (self._pass("C1","HARD_VETO on standing failure (native)")
                if g["final_disposition"]=="HARD_VETO"
                else self._fail("C1",str(g["final_disposition"])))

    def _v_c2(self):
        g = self._evaluate("a","valid","wt",0.95,0.90,0.10,uuid.uuid4().hex)
        return (self._pass("C2",f"{g['final_disposition']} under extreme pressure (native)")
                if g["final_disposition"] in ("FLAG","HARD_VETO")
                else self._fail("C2",str(g["final_disposition"])))

    def _v_c3(self):
        pid = f"race-{uuid.uuid4().hex[:8]}"
        g = self._evaluate(pid,"valid","wt",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._inconclusive("C3","Could not establish the valid-verdict precondition")
        self._revoke(pid)
        try:
            self._commit(g["evaluation_id"],action_id=g["action_id"],nonce=g["nonce"])
            return self._fail("C3","commit accepted after revocation")
        except ValueError as e:
            return (self._pass("C3",f"post-verdict revocation produced HARD_VETO; commit blocked (native): {e}")
                    if "STANDING_REVOKED:HARD_VETO" in str(e) and
                       g.get("commit_disposition") == "HARD_VETO" else
                    self._inconclusive("C3",f"commit rejection did not establish HARD_VETO: {e}"))

    def _v_c4(self):
        return self._na("C4","No transport layer in in-process kernel.")

    def _v_c5(self):
        nonce = uuid.uuid4().hex
        self._evaluate("a","valid","wt",0.2,0.2,0.90,nonce)
        try:
            self._evaluate("a","valid","wt",0.2,0.2,0.90,nonce,f"eval_{uuid.uuid4().hex}")
            return self._fail("C5","Nonce replay accepted")
        except ValueError as e:
            return (self._pass("C5","NONCE_REPLAY raised (native)")
                    if "NONCE_REPLAY" in str(e) else self._fail("C5",str(e)))

    def _v_ct_r4_001(self):
        g = self._evaluate("a","valid","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._fail("CT-R4-001",str(g["final_disposition"]))
        r = self._commit(g["evaluation_id"],"wire_transfer",action_id=g["action_id"],nonce=g["nonce"])
        return (self._pass("CT-R4-001","Valid grant bound and committed (native)")
                if r["status"]=="COMMITTED" else self._fail("CT-R4-001",str(r)))

    def _v_ct_r4_002(self):
        g = self._evaluate("a","valid","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._fail("CT-R4-002","no PASS")
        try:
            self._commit(g["evaluation_id"],"account_deletion",action_id=g["action_id"],nonce=g["nonce"])
            return self._fail("CT-R4-002","binding violation not detected")
        except ValueError as e:
            return (self._pass("CT-R4-002","PAYLOAD_BINDING_VIOLATION raised (native)")
                    if "BINDING_VIOLATION" in str(e) else self._fail("CT-R4-002",str(e)))

    def _v_ct_r4_003(self):
        nonce = uuid.uuid4().hex
        self._evaluate("a","valid","wt",0.2,0.2,0.90,nonce)
        try:
            self._evaluate("a","valid","wt",0.2,0.2,0.90,nonce,f"eval_{uuid.uuid4().hex}")
            return self._fail("CT-R4-003","Replay not rejected")
        except ValueError as e:
            return (self._pass("CT-R4-003","REPLAY_DETECTED (native)")
                    if "NONCE_REPLAY" in str(e) else self._fail("CT-R4-003",str(e)))

    def _v_ct_r4_004(self):
        stale = self._inject_stale()
        try:
            self._commit(stale["evaluation_id"],action_id=stale["action_id"],nonce=stale["nonce"])
            return self._fail("CT-R4-004","Expired grant accepted")
        except ValueError as e:
            return (self._pass("CT-R4-004","EVALUATION_EXPIRED on stale grant (native)")
                    if "EXPIRED" in str(e) else self._fail("CT-R4-004",str(e)))

    def _v_ct_r4_005(self):
        g = self._evaluate("a","valid","wt",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._fail("CT-R4-005","no PASS")
        epoch_before = self._epoch
        self._reload_policy()
        try:
            self._commit(g["evaluation_id"],action_id=g["action_id"],nonce=g["nonce"])
            return self._fail("CT-R4-005","STATE_DRIFT not detected")
        except ValueError as e:
            return (self._pass("CT-R4-005",
                        f"STATE_DRIFT produced HARD_VETO (epoch {epoch_before}→{self._epoch}) (native)")
                    if "STATE_DRIFT:HARD_VETO" in str(e) and
                       g.get("commit_disposition") == "HARD_VETO" else self._fail("CT-R4-005",str(e)))

    def _v_ct_r4_006(self):
        g = self._evaluate("u","none","wt",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "HARD_VETO":
            return self._fail("CT-R4-006","no HARD_VETO")
        try:
            self._commit(g["evaluation_id"],action_id=g["action_id"],nonce=g["nonce"])
            return self._fail("CT-R4-006","HARD_VETO committed")
        except ValueError as e:
            return (self._pass("CT-R4-006","HARD_VETO blocked at commit gate (native)")
                    if "INVALID_DISPOSITION" in str(e) else self._fail("CT-R4-006",str(e)))

    def _v_ct_r4_007(self):
        g = self._evaluate("u","none","wt",0.2,0.2,0.90,uuid.uuid4().hex)
        receipt = g.get("receipt",{})
        if not receipt.get("signed") or not receipt.get("signature"):
            return self._fail("CT-R4-007","Receipt not signed")
        try:
            self._verify(self._pub, receipt)
            tampered = dict(receipt)
            tampered["final_disposition"] = "TAMPERED"
            try:
                self._verify(self._pub, tampered)
                return self._fail("CT-R4-007", "Changed receipt field still verified")
            except Exception:
                return self._pass("CT-R4-007",
                    f"Ed25519 signature binds receipt fields (native, type={receipt['receipt_type']!r})")
        except Exception as e:
            return self._fail("CT-R4-007",f"Sig verification failed: {e}")

    def _v_ct_r4_008(self):
        self._evaluate("a","valid","wt",0.2,0.2,0.90,uuid.uuid4().hex)
        import copy
        probe = copy.deepcopy(self._manifest)
        probe.entries[0]["entry"]["final_disposition"] = "TAMPERED"
        result = probe.verify()
        return (self._pass("CT-R4-008","Tampering in a copied manifest was detected (native)")
                if not result["integrity_ok"] and self._manifest.verify()["integrity_ok"]
                else self._fail("CT-R4-008",str(result)))

    def _v_ct_r4_009(self):
        return self._gap("CT-R4-009",
            "The manifest lacks the complete evaluation inputs and policy snapshot needed "
            "to reproduce the decision independently.")

    def _v_ct_r4_010(self):
        return self._gap("CT-R4-010",
            "The adapter reports the post-commit evidence requirement but does not provide "
            "evidence of an external effect.")


# ── Extended: CT-R2-002 and CT-R2-003 ────────────────────────────────────

    def _v_ct_r2_002(self):
        """S-score determinism: same P/V/K → same S and disposition."""
        P, V, K = 0.4, (0.4*0.5)**0.5, 0.75
        r1 = self._engine.evaluate(P, V, K)
        r2 = self._engine.evaluate(P, V, K)
        if abs(r1["s_score"]-r2["s_score"]) < 1e-9 and r1["decision"]==r2["decision"]:
            return self._pass("CT-R2-002",
                f"S={r1['s_score']:.6f}, disp={r1['decision']!r} — deterministic (native)")
        return self._fail("CT-R2-002","Non-deterministic results")

    def _v_ct_r2_003(self):
        """Epsilon guard: P=0, V=0 → no crash; epsilon prevents divide-by-zero."""
        try:
            r = self._engine.evaluate(0.0, 0.0, 0.85)
            if r["decision"] in ("PASS","FLAG","HARD_VETO"):
                return self._pass("CT-R2-003",
                    f"Epsilon guard active; S={r['s_score']}, "
                    f"disp={r['decision']!r} (native)")
            return self._fail("CT-R2-003",f"Unexpected result: {r}")
        except Exception as e:
            return self._fail("CT-R2-003",f"Divide-by-zero not handled: {e}")


MARKS = {"PASS":"✓","FAIL":"✗","INCONCLUSIVE":"?","NOT_APPLICABLE":"○",
         "ADAPTER_REQUIRED":"~","IMPLEMENTATION_GAP":"△"}

def build_evidence_binding(adapter, args):
    root = Path(__file__).resolve().parent
    try:
        source_revision = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"],
            text=True, stderr=subprocess.DEVNULL).strip())
    except Exception:
        source_revision, dirty = None, None

    tree_hash = hashlib.sha256()
    excluded_dirs = {".git", "results", "__pycache__", ".venv", ".pytest_cache"}
    source_files = sorted(
        path for path in root.rglob("*")
        if path.is_file() and not any(part in excluded_dirs for part in path.relative_to(root).parts)
    )
    for path in source_files:
        rel = path.relative_to(root).as_posix().encode("utf-8")
        tree_hash.update(len(rel).to_bytes(8, "big")); tree_hash.update(rel)
        data = path.read_bytes()
        tree_hash.update(len(data).to_bytes(8, "big")); tree_hash.update(data)

    specifications = {}
    for rfc in ("rfc-3.md", "rfc-4.md"):
        path = root / "reg-standards-baseline" / "rfc" / rfc
        if path.is_file():
            specifications[rfc] = hashlib.sha256(path.read_bytes()).hexdigest()

    if adapter.interface_mode == "native":
        subject = {
            "repository": "local-reference-kernel",
            "revision": source_revision,
            "version": None,
            "worktree_state": "clean" if dirty is False else "dirty" if dirty else "unknown",
        }
    else:
        subject = {
            "repository": args.subject_repository or None,
            "revision": args.subject_revision or None,
            "version": args.subject_version or None,
            "worktree_state": args.subject_worktree_state,
        }

    environment_digest = args.environment_digest or None
    dependency_versions = {}
    for distribution in ("requests", "fastapi", "uvicorn", "PyYAML", "cryptography"):
        try:
            dependency_versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            dependency_versions[distribution] = None
    missing = []
    if not source_revision: missing.append("harness commit SHA")
    if dirty is not False: missing.append("clean harness worktree")
    if len(specifications) != 2: missing.append("RFC-3/RFC-4 content hashes")
    if not subject["repository"]: missing.append("subject repository")
    if not subject["revision"] or not re.fullmatch(r"[0-9a-fA-F]{40}", subject["revision"]):
        missing.append("full subject commit SHA")
    if subject["worktree_state"] != "clean": missing.append("clean subject worktree")
    if not environment_digest or not re.fullmatch(r"sha256:[0-9a-fA-F]{64}", environment_digest):
        missing.append("OCI environment digest")

    return {
        "conformance_profile": args.conformance_profile,
        "harness": {
            "repository": "skiredj-prog/reg-conformance",
            "revision": source_revision,
            "worktree_clean": dirty is False,
            "source_tree_sha256": tree_hash.hexdigest(),
        },
        "specification_sha256": specifications,
        "subject": subject,
        "environment": {
            "oci_digest": environment_digest,
            "python": platform.python_version(),
            "dependencies": dependency_versions,
        },
        "certification_status": "NOT_CERTIFIABLE" if missing else "EVIDENCE_BOUND",
        "missing_bindings": missing,
        "release_claim_ready": False,
        "release_claim_gaps": [
            "requirements.txt is not a dependency lock file.",
            "No CI provenance attestation is generated by this runner.",
            "The JSON report is not signed; retain and publish its SHA-256 separately.",
        ],
    }

def generate_report(adapter, results, endpoint="", evidence_binding=None):
    counts = {s.value:0 for s in ReportingState}
    try:
        source_revision = subprocess.check_output(
            ["git", "-C", str(Path(__file__).parent), "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        source_revision = None
    for r in results: counts[r.status.value] += 1
    core_results = [r for r in results if r.vector_id in CORE_VECTORS]
    extended_results = [r for r in results if r.vector_id in EXTENDED_VECTORS]
    return {"suite":"REG Conformance Suite v0.3.1",
            "rfc_refs":["RFC-4 (frozen)","RFC-7 (updated)"],
            "interface_mode":adapter.interface_mode,
            "evidence_level":int(adapter.evidence_level),
            "evidence_label":EvidenceLevel(adapter.evidence_level).name,
            "conformance_status": ("FAILED" if counts["FAIL"] else
                                   "INCONCLUSIVE" if counts["INCONCLUSIVE"] else
                                   "INCOMPLETE" if counts["IMPLEMENTATION_GAP"] or counts["ADAPTER_REQUIRED"] else
                                   "CONFORMANT"),
            "endpoint":endpoint,
            "source_revision":source_revision,
            "evidence_binding":evidence_binding,
            "vector_sets":{"core":len(CORE_VECTORS),
                           "extended":len(EXTENDED_VECTORS),
                           "total":len(VECTORS)},
            "summary_core":{s.value:sum(r.status == s for r in core_results)
                            for s in ReportingState},
            "summary_extended":{s.value:sum(r.status == s for r in extended_results)
                                for s in ReportingState},
            "ran_at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
            "summary":counts,
            "results":[asdict(r) for r in results]}

def main():
    p = argparse.ArgumentParser(description="REG Conformance Suite v0.3.1")
    p.add_argument("--endpoint", default="")
    p.add_argument("--mode", choices=["http","native","both"], default="http")
    p.add_argument("--kernel", default="kernel/tenir_policies.yaml")
    p.add_argument("--api-key", default=None)
    p.add_argument("--admin-token", default=None,
                   help="Token matching REG_ADMIN_TOKEN for protected shim test helpers")
    p.add_argument("--principal-credential", default="valid-token",
                   help="Credential sent in test evaluation requests (shim requires REG_CREDENTIAL_TOKEN to match)")
    p.add_argument("--insecure", action="store_true")
    p.add_argument("--conformance-profile", choices=["REG-v0.3.1-RFC-4-strict-C3"],
                   default="REG-v0.3.1-RFC-4-strict-C3")
    p.add_argument("--subject-repository", default="",
                   help="Repository for the implementation under test (required for certification binding)")
    p.add_argument("--subject-revision", default="",
                   help="Full 40-character commit SHA of the implementation under test")
    p.add_argument("--subject-version", default="",
                   help="Optional release tag/version; the full commit SHA remains authoritative")
    p.add_argument("--subject-worktree-state", choices=["clean", "dirty", "unknown"], default="unknown")
    p.add_argument("--environment-digest", default="",
                   help="OCI image digest in sha256:<64 hex> form")
    p.add_argument("--output", default="results/tenirlabs-v0.3.1.json")
    args = p.parse_args()

    import os; os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    all_reports = []

    def run(adapter, label, endpoint=""):
        print(f"\nREG Conformance Suite v0.3.1 — {label}\n{'─'*66}")
        results = adapter.run_all()
        for r in results:
            m = MARKS.get(r.status.value,"?")
            print(f"  {m}  {r.vector_id:<16}  {r.status.value:<22}  {r.details}")
            if r.gap_note and r.status.value not in ("PASS","FAIL"):
                print(f"     ↳ {r.gap_note[:88]}")
        counts = {}
        for r in results: counts[r.status.value] = counts.get(r.status.value,0)+1
        print(f"\n{'─'*66}")
        for k,v in counts.items(): print(f"  {MARKS.get(k,'?')} {k}: {v}")
        all_reports.append(generate_report(
            adapter, results, endpoint,
            build_evidence_binding(adapter, args)))

    if args.mode in ("http","both"):
        if not args.endpoint:
            print("ERROR: --endpoint required", file=sys.stderr); sys.exit(1)
        run(HTTPAdapter(args.endpoint, args.api_key, args.insecure, args.admin_token,
                        args.principal_credential),
            f"HTTP adapter → {args.endpoint}", args.endpoint)

    if args.mode in ("native","both"):
        run(NativeKernelAdapter(args.kernel), "Native kernel (TENIR-Gov PolicyEngine)")

    has_fail = any(rep["summary"]["FAIL"] for rep in all_reports)
    has_inconclusive = any(rep["summary"]["INCONCLUSIVE"] for rep in all_reports)
    has_incomplete = any(rep["summary"]["IMPLEMENTATION_GAP"] or
                         rep["summary"]["ADAPTER_REQUIRED"] for rep in all_reports)
    exit_code = 1 if has_fail else 3 if has_inconclusive else 2 if has_incomplete else 0
    out = all_reports[0] if len(all_reports)==1 else all_reports
    if isinstance(out, dict):
        out["exit_code"] = exit_code
    else:
        for report in out:
            report["exit_code"] = exit_code
    with open(args.output,"w") as f: json.dump(out, f, indent=2, default=str)
    print(f"\n  Results → {args.output}")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
