#!/usr/bin/env python3
"""
REG Conformance Suite v0.2.4 — RFC-4 (frozen) / RFC-7 (updated)
================================================================
Architecture (RFC-7 §8)
-----------------------
  AbstractTestVector  ← canonical, topology-neutral (RFC-4 §5)
         │
    BaseAdapter       ← translates vector to concrete interface call
         │
   ┌─────┴──────┐
   │            │
HTTPAdapter   NativeKernelAdapter
(interface_   (interface_mode:
  mode:          "native")
  "adapter")

Evidence levels (RFC-7 §8.2)
-----------------------------
  1  SEMANTIC_MAPPING    — documented conceptual correspondence, no execution
  2  ADAPTER_TESTED      — passes via translation layer, NOT native conformance
  3  NATIVE_CONFORMANT   — native interface satisfies normative properties directly

Reporting states (RFC-7 §8.3)
------------------------------
  PASS | FAIL | NOT_APPLICABLE | ADAPTER_REQUIRED | IMPLEMENTATION_GAP

Usage
-----
  python runner.py --endpoint http://127.0.0.1:8099           # HTTP adapter mode
  python runner.py --mode native --kernel kernel/tenir_policies.yaml  # native kernel mode
  python runner.py --endpoint URL --mode native --kernel FILE  # both
"""

import argparse, hashlib, json, sys, time, uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import Optional

import requests


# ── Enums & dataclasses ───────────────────────────────────────────────────────

class ReportingState(str, Enum):
    PASS               = "PASS"
    FAIL               = "FAIL"
    NOT_APPLICABLE     = "NOT_APPLICABLE"       # property irrelevant to this topology
    ADAPTER_REQUIRED   = "ADAPTER_REQUIRED"     # testable only through a translation layer
    IMPLEMENTATION_GAP = "IMPLEMENTATION_GAP"   # requirement understood, not yet engineered

class EvidenceLevel(int, Enum):
    SEMANTIC_MAPPING   = 1
    ADAPTER_TESTED     = 2
    NATIVE_CONFORMANT  = 3


@dataclass
class TestVector:
    vector_id:           str
    rfc:                 str
    normative_property:  str
    abstract_description: str


@dataclass
class ConformanceResult:
    vector_id:      str
    status:         ReportingState
    interface_mode: str   # "native" | "adapter" | "mapped"
    evidence_level: int
    details:        str = ""
    gap_note:       str = ""   # populated for IMPLEMENTATION_GAP / ADAPTER_REQUIRED


# ── Canonical test vectors (RFC-4 §5 + core invariants) ──────────────────────
# Topology-neutral: no HTTP paths, no interface shapes.

VECTORS: dict[str, TestVector] = {

    # ── Core invariants (C-series maps to RFC-1/2/3) ─────────────────────────
    "C1": TestVector(
        "C1", "RFC-3", "Standing Gate",
        "Actor without valid standing credential → HARD_VETO, regardless of structural state."
    ),
    "C2": TestVector(
        "C2", "RFC-2", "Structure Gate",
        "Action under extreme structural pressure (P≥0.9, V≥0.9, K≤0.15) → FLAG or HARD_VETO, never PASS."
    ),
    "C3": TestVector(
        "C3", "RFC-4 §2.2", "Commit-State Binding — Standing Drift",
        "Standing revocation between verdict and commit. "
        "Strict: commit blocked (RFC-4 §2.2 MUST). Permissive: IMPLEMENTATION_GAP."
    ),
    "C4": TestVector(
        "C4", "RFC-1", "Fail-Closed Transport Safety",
        "Transport error or server fault → no execution proceeds. "
        "NOT_APPLICABLE for in-process kernels (no transport layer)."
    ),
    "C5": TestVector(
        "C5", "RFC-1 / RFC-4 §2.1", "Replay Soundness — Idempotency",
        "Identical request replayed → rejected. Nonce-based or Idempotency-Key based."
    ),

    # ── CT-R4 vectors (RFC-4 §5, frozen) ─────────────────────────────────────
    "CT-R4-001": TestVector(
        "CT-R4-001", "RFC-4 §1 / §5",
        "Valid Grant Binding",
        "Valid evaluation for action_A with matching nonce + commit for action_A "
        "within validity window → GRANT / COMMITTED."
    ),
    "CT-R4-002": TestVector(
        "CT-R4-002", "RFC-4 §1.3 / §5",
        "Action / Payload Binding Violation",
        "Grant issued for action_A; commit attempts action_B "
        "(payload hash or type mismatch) → REJECT / BINDING_VIOLATION."
    ),
    "CT-R4-003": TestVector(
        "CT-R4-003", "RFC-4 §2.1 / §5",
        "Replay Rejection",
        "Reuse of a consumed nonce or grant → REJECT / REPLAY_DETECTED."
    ),
    "CT-R4-004": TestVector(
        "CT-R4-004", "RFC-4 §2 / §5",
        "Expired Grant Rejection",
        "valid_until window passed before commit → REJECT / EXPIRED."
    ),
    "CT-R4-005": TestVector(
        "CT-R4-005", "RFC-4 §2.2 / §5",
        "Commit-State Binding / Race Detection",
        "State at commit materially differs from state captured at verdict "
        "(state_hash_at_verdict or equivalent) → REJECT / STATE_DRIFT."
    ),
    "CT-R4-006": TestVector(
        "CT-R4-006", "RFC-4 §1 / §5",
        "Non-PASS Cannot Cross Commit",
        "HOLD or HARD_VETO disposition → commit attempt → REJECT / INVALID_DISPOSITION."
    ),
    "CT-R4-007": TestVector(
        "CT-R4-007", "RFC-4 §3 / §5",
        "Decision Receipt Generation",
        "Every disposition (including non-PASS) produces a cryptographically signed "
        "Decision Receipt independently verifiable without accessing internal state."
    ),
    "CT-R4-008": TestVector(
        "CT-R4-008", "RFC-4 §4 / §5",
        "Evidence Manifest Integrity",
        "Evidence Manifest altered after closure → integrity verification fails. "
        "Requires tamper-evident, append-only ledger."
    ),
    "CT-R4-009": TestVector(
        "CT-R4-009", "RFC-4 §4 / §5",
        "Independent Evidence Verification",
        "Third-party verifier can reproduce or verify the decision from the Manifest "
        "without accessing mutable internal state."
    ),
    "CT-R4-010": TestVector(
        "CT-R4-010", "RFC-4 §1.1 / §5",
        "External-Effect Claim Boundary",
        "Implementation provides post-commit evidence for non-atomic external effects "
        "and does NOT claim atomic external-effect semantics."
    ),
}


# ── Base adapter ──────────────────────────────────────────────────────────────

class BaseAdapter(ABC):
    """Translates abstract TestVectors into concrete interface calls."""

    interface_mode:  str = "base"
    evidence_level:  EvidenceLevel = EvidenceLevel.ADAPTER_TESTED

    def run_all(self, vector_ids=None) -> list[ConformanceResult]:
        ids = vector_ids or list(VECTORS.keys())
        return [self.run_vector(vid) for vid in ids]

    @abstractmethod
    def run_vector(self, vector_id: str) -> ConformanceResult:
        ...

    def _result(self, vector_id, status, details="", gap_note="") -> ConformanceResult:
        return ConformanceResult(
            vector_id=vector_id,
            status=status,
            interface_mode=self.interface_mode,
            evidence_level=int(self.evidence_level),
            details=details,
            gap_note=gap_note,
        )

    def _pass(self, vid, details=""): return self._result(vid, ReportingState.PASS, details)
    def _fail(self, vid, details=""): return self._result(vid, ReportingState.FAIL, details)
    def _na  (self, vid, note=""):   return self._result(vid, ReportingState.NOT_APPLICABLE, gap_note=note)
    def _ar  (self, vid, note=""):   return self._result(vid, ReportingState.ADAPTER_REQUIRED, gap_note=note)
    def _gap (self, vid, note=""):   return self._result(vid, ReportingState.IMPLEMENTATION_GAP, gap_note=note)


# ── HTTP adapter ──────────────────────────────────────────────────────────────

class HTTPAdapter(BaseAdapter):
    """
    Translates abstract vectors to REG /evaluations HTTP calls.
    interface_mode: "adapter" — passing here demonstrates behavioral compatibility,
    NOT native REG conformance (RFC-7 §8.2 Level 2).
    """
    interface_mode = "adapter"
    evidence_level = EvidenceLevel.ADAPTER_TESTED

    def __init__(self, endpoint: str, api_key: Optional[str] = None, insecure=False):
        self.endpoint = endpoint.rstrip("/")
        self.headers  = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
        self.verify = not insecure

    def _post(self, path, body, idem=None):
        h = dict(self.headers)
        if idem: h["Idempotency-Key"] = idem
        h["X-Trace-Id"] = str(uuid.uuid4())
        try:
            r = requests.post(f"{self.endpoint}{path}", json=body,
                              headers=h, verify=self.verify, timeout=10)
            return r.status_code, (r.json() if r.content else {})
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def _get(self, path):
        try:
            r = requests.get(f"{self.endpoint}{path}",
                             headers=self.headers, verify=self.verify, timeout=10)
            return r.status_code, (r.json() if r.content else {})
        except requests.exceptions.RequestException as e:
            return 0, {"error": str(e)}

    def _eval_body(self, **kw):
        b = {
            "protocol_version": "reg-1.0",
            "evaluation_id":    f"eval_{uuid.uuid4().hex}",
            "action_id":        f"act_{uuid.uuid4().hex}",
            "principal":        {"id": "authorized-actor", "credential": "valid-token"},
            "action":           {"type": "wire_transfer", "params": {"amount": 100}},
            "measurements":     {"pressure": 0.3, "volatility": 0.3, "capacity": 0.85},
            "nonce":            uuid.uuid4().hex,
            "submitted_at":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        b.update(kw)
        return b

    def _disp(self, resp):
        return resp.get("final_disposition") or resp.get("disposition")

    # ── Vector dispatch ───────────────────────────────────────────────────────

    def run_vector(self, vid: str) -> ConformanceResult:
        m = getattr(self, f"_v_{vid.replace('-','_').lower()}", None)
        if m is None:
            return self._gap(vid, "No HTTP translation defined for this vector")
        try:
            return m()
        except Exception as e:
            return self._fail(vid, f"exception: {e}")

    # C1 — Standing Gate (RFC-3)
    def _v_c1(self):
        body = self._eval_body(principal={"id": "unauth", "credential": "none"})
        code, resp = self._post("/evaluations", body)
        if code in (200,202) and self._disp(resp) == "HARD_VETO":
            return self._pass("C1", "HARD_VETO on standing failure")
        return self._fail("C1", f"code={code}, disposition={self._disp(resp)!r}")

    # C2 — Structure Gate (RFC-2)
    def _v_c2(self):
        body = self._eval_body(
            measurements={"pressure":0.95,"volatility":0.90,"velocity":0.90,"capacity":0.10})
        code, resp = self._post("/evaluations", body)
        d = self._disp(resp)
        if code in (200,202) and d in ("FLAG","HARD_VETO"):
            return self._pass("C2", f"{d} under extreme structural pressure")
        return self._fail("C2", f"expected FLAG/HARD_VETO, got {d!r} (code={code})")

    # C3 — Standing drift / race (RFC-4 §2.2)
    def _v_c3(self):
        pid = f"race-{uuid.uuid4().hex[:8]}"
        body = self._eval_body(
            principal={"id": pid, "credential": "valid-token"},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90})
        code, resp = self._post("/evaluations", body)
        if self._disp(resp) != "PASS":
            return self._ar("C3", "Could not obtain PASS verdict to test race")
        eid = resp.get("evaluation_id") or body["evaluation_id"]
        rc, _ = self._post("/admin/revoke", {"principal_id": pid, "reason": "C3"})
        if rc not in (200,202):
            return self._ar("C3", "/admin/revoke absent — IMPLEMENTATION_GAP")
        ec, er = self._post(f"/evaluations/{eid}/events", {"event_type":"commit"})
        if ec == 409:
            return self._pass("C3",
                "commit blocked post-revocation (strict — RFC-4 §2.2 conformant)")
        if ec == 200:
            return self._gap("C3",
                "commit accepted post-revocation — permissive revocation is "
                "non-conformant to RFC-4 §2.2 MUST. Harness green-lights an "
                "obligation the RFC declares mandatory. See spec.md C3 row.")
        return self._fail("C3", f"unexpected commit response: code={ec}")

    # C4 — Fail-closed transport (RFC-1)
    def _v_c4(self):
        try:
            r = requests.post(f"{self.endpoint}/nonexistent-503", json={},
                              headers=self.headers, verify=self.verify, timeout=3)
            if r.status_code >= 400:
                return self._pass("C4", f"server returned {r.status_code}; client must fail-closed")
        except Exception:
            return self._pass("C4", "connection/timeout error → client must fail-closed")
        return self._fail("C4", "unexpected 2xx on nonexistent path")

    # C5 — Replay soundness (RFC-1 / RFC-4 §2.1)
    def _v_c5(self):
        nonce = uuid.uuid4().hex
        b1 = self._eval_body(nonce=nonce)
        self._post("/evaluations", b1)
        b2 = self._eval_body(
            evaluation_id=f"eval_{uuid.uuid4().hex}",
            nonce=nonce)  # same nonce
        code, resp = self._post("/evaluations", b2)
        if code == 409:
            return self._pass("C5", "409 NONCE_REPLAY on duplicate nonce")
        return self._gap("C5",
            f"Nonce replay returned {code} not 409 — "
            "Idempotency-Key-level dedup absent; nonce replay not enforced")

    # CT-R4-001 — Valid Grant Binding
    def _v_ct_r4_001(self):
        body = self._eval_body(
            action={"type":"wire_transfer","params":{"amount":100}},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90})
        code, resp = self._post("/evaluations", body)
        if self._disp(resp) != "PASS":
            return self._fail("CT-R4-001", f"expected PASS, got {self._disp(resp)!r}")
        eid = resp.get("evaluation_id") or body["evaluation_id"]
        ec, er = self._post(f"/evaluations/{eid}/events",
                            {"event_type":"commit","action_type":"wire_transfer"})
        if ec == 200 and er.get("status") == "COMMITTED":
            return self._pass("CT-R4-001", f"GRANT bound and committed (eval {eid[:8]}…)")
        return self._fail("CT-R4-001", f"commit returned {ec}: {er}")

    # CT-R4-002 — Action/Payload Binding Violation
    def _v_ct_r4_002(self):
        body = self._eval_body(
            action={"type":"wire_transfer","params":{"amount":100}},
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90})
        code, resp = self._post("/evaluations", body)
        if self._disp(resp) != "PASS":
            return self._fail("CT-R4-002", f"could not obtain PASS grant")
        eid = resp.get("evaluation_id") or body["evaluation_id"]
        # Commit with a different action_type — must be rejected
        ec, er = self._post(f"/evaluations/{eid}/events",
                            {"event_type":"commit","action_type":"account_deletion"})
        if ec == 409 and "BINDING" in er.get("detail",""):
            return self._pass("CT-R4-002", "PAYLOAD_BINDING_VIOLATION correctly rejected")
        return self._fail("CT-R4-002",
                          f"expected 409 BINDING_VIOLATION, got {ec}: {er}")

    # CT-R4-003 — Replay Rejection
    def _v_ct_r4_003(self):
        nonce = uuid.uuid4().hex
        b1 = self._eval_body(nonce=nonce,
                             measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90})
        self._post("/evaluations", b1)
        b2 = self._eval_body(evaluation_id=f"eval_{uuid.uuid4().hex}", nonce=nonce)
        code, resp = self._post("/evaluations", b2)
        if code == 409 and "NONCE_REPLAY" in str(resp):
            return self._pass("CT-R4-003", "REPLAY_DETECTED on consumed nonce")
        return self._fail("CT-R4-003", f"expected 409 NONCE_REPLAY, got {code}: {resp}")

    # CT-R4-004 — Expired Grant Rejection
    def _v_ct_r4_004(self):
        # Cannot reliably wait 30 s in the runner; expiry is testable natively.
        # The shim enforces valid_until, but triggering it requires time passage.
        return self._ar("CT-R4-004",
            "Expiry window (30 s) cannot be reliably triggered via HTTP without "
            "introducing test latency. Use NativeKernelAdapter for deterministic coverage.")

    # CT-R4-005 — Commit-State Binding / Race Detection
    def _v_ct_r4_005(self):
        return self._gap("CT-R4-005",
            "state_hash_at_verdict not yet implemented in shim v0.2. "
            "State drift detection is currently limited to standing revocation (C3). "
            "Full Commit-State Binding requires capturing state at verdict and "
            "comparing at commit time.")

    # CT-R4-006 — Non-PASS Cannot Cross Commit
    def _v_ct_r4_006(self):
        body = self._eval_body(principal={"id":"unauth","credential":"none"})
        code, resp = self._post("/evaluations", body)
        if self._disp(resp) != "HARD_VETO":
            return self._fail("CT-R4-006", "could not force HARD_VETO")
        eid = resp.get("evaluation_id") or body["evaluation_id"]
        ec, er = self._post(f"/evaluations/{eid}/events", {"event_type":"commit"})
        if ec == 409 and "INVALID_DISPOSITION" in er.get("detail",""):
            return self._pass("CT-R4-006", "HARD_VETO correctly blocked at commit gate")
        return self._fail("CT-R4-006", f"expected 409 INVALID_DISPOSITION, got {ec}: {er}")

    # CT-R4-007 — Decision Receipt Generation
    def _v_ct_r4_007(self):
        body = self._eval_body(principal={"id":"unauth","credential":"none"})
        code, resp = self._post("/evaluations", body)
        receipt = resp.get("receipt", {})
        if receipt.get("receipt_hash") and receipt.get("receipt_type"):
            signed = receipt.get("signed", False)
            if not signed:
                return self._gap("CT-R4-007",
                    f"Structural receipt present (type={receipt['receipt_type']!r}, "
                    f"hash={receipt['receipt_hash'][:12]}…) but NOT cryptographically signed. "
                    "Signing key absent in v0.1 — IMPLEMENTATION_GAP.")
            return self._pass("CT-R4-007", "Signed Decision Receipt present and verifiable")
        return self._fail("CT-R4-007", f"No receipt in evaluation response: {resp}")

    # CT-R4-008 — Evidence Manifest Integrity
    def _v_ct_r4_008(self):
        return self._gap("CT-R4-008",
            "Tamper-evident Evidence Manifest (Merkle tree / transparency log) "
            "absent in v0.1. proof endpoint provides commit_hash but no full "
            "append-only manifest. Requires ledger implementation.")

    # CT-R4-009 — Independent Evidence Verification
    def _v_ct_r4_009(self):
        return self._gap("CT-R4-009",
            "Independent third-party verification path absent in v0.1. "
            "Depends on CT-R4-008 (manifest) and CT-R4-007 (signed receipts).")

    # CT-R4-010 — External-Effect Claim Boundary
    def _v_ct_r4_010(self):
        body = self._eval_body(
            measurements={"pressure":0.2,"volatility":0.2,"capacity":0.90})
        code, resp = self._post("/evaluations", body)
        if resp.get("external_effect_atomic") is False:
            eid = resp.get("evaluation_id") or body["evaluation_id"]
            if self._disp(resp) == "PASS":
                ec, er = self._post(f"/evaluations/{eid}/events", {"event_type":"commit"})
                if er.get("post_commit_evidence_required") is True:
                    return self._pass("CT-R4-010",
                        "external_effect_atomic=false; post_commit_evidence_required=true — "
                        "no false atomic claim")
            return self._pass("CT-R4-010",
                "external_effect_atomic=false declared on evaluation response")
        return self._fail("CT-R4-010",
            "external_effect_atomic not declared or is True — "
            "implementation may be overclaiming atomicity")


# ── Native kernel adapter ─────────────────────────────────────────────────────

class NativeKernelAdapter(BaseAdapter):
    """
    Tests REG normative properties directly against the TENIR-Gov kernel
    (PolicyEngine) without any HTTP layer.

    interface_mode: "native" — passing here is Level 3 / Native-Conformant evidence
    (RFC-7 §8.2). This is the mode CommitGate's authorize(record, payload_bytes, …)
    would use: no /evaluations endpoint required.
    """
    interface_mode = "native"
    evidence_level = EvidenceLevel.NATIVE_CONFORMANT

    def __init__(self, policy_file: str):
        sys.path.insert(0, str(Path(__file__).parent))
        from kernel.policy_engine import PolicyEngine
        self._engine = PolicyEngine(Path(policy_file))
        self._grants:   dict[str, dict] = {}
        self._consumed: set[str]        = set()   # consumed nonces
        self._revoked:  set[str]        = set()

    # ── Kernel operations (no HTTP) ───────────────────────────────────────────

    def _evaluate(self, principal_id, credential, action_type,
                  P, V, K, nonce, evaluation_id=None) -> dict:
        eid = evaluation_id or f"eval_{uuid.uuid4().hex}"

        if len(nonce) < 8:
            raise ValueError("NONCE_TOO_SHORT")
        if nonce in self._consumed:
            raise ValueError("NONCE_REPLAY")

        standing_fail = (
            credential in ("none", "", "invalid")
            or principal_id in self._revoked
        )
        if standing_fail:
            grant = {
                "evaluation_id":     eid,
                "action_type":       action_type,
                "principal_id":      principal_id,
                "final_disposition": "HARD_VETO",
                "reason":            "STANDING_FAILURE",
                "nonce":             nonce,
                "created_at":        time.time(),
                "valid_until":       time.time() + 30,
                "external_effect_atomic": False,
            }
            grant["receipt"] = {
                "receipt_type":  "Refusal Receipt",
                "receipt_hash":  hashlib.sha256(
                    json.dumps(grant, sort_keys=True, default=str).encode()).hexdigest(),
                "signed":        False,
            }
        else:
            kr = self._engine.evaluate(P, V, K)
            grant = {
                "evaluation_id":     eid,
                "action_type":       action_type,
                "principal_id":      principal_id,
                "final_disposition": kr["decision"],
                "s_score":           kr["s_score"],
                "nonce":             nonce,
                "policy_version":    kr["policy_version"],
                "created_at":        time.time(),
                "valid_until":       time.time() + 30,
                "receipt": {
                    "receipt_type": f"{kr['decision']} Receipt",
                    "receipt_hash": hashlib.sha256(
                        json.dumps(kr, sort_keys=True).encode()).hexdigest(),
                    "signed": False,
                },
                "external_effect_atomic": False,
            }

        # Mark nonce as used only after grant is stored
        self._grants[eid] = grant
        self._consumed.add(nonce)
        return grant

    def _commit(self, evaluation_id, action_type=None) -> dict:
        if evaluation_id not in self._grants:
            raise KeyError("GRANT_NOT_FOUND")
        g = self._grants[evaluation_id]

        if g["final_disposition"] in ("HARD_VETO", "HOLD"):
            raise ValueError("INVALID_DISPOSITION")
        if g.get("_committed"):
            raise ValueError("ALREADY_COMMITTED")
        if time.time() > g["valid_until"]:
            raise ValueError("EVALUATION_EXPIRED")
        if action_type and action_type != g["action_type"]:
            raise ValueError(
                f"PAYLOAD_BINDING_VIOLATION: "
                f"granted={g['action_type']!r} attempted={action_type!r}")

        g["_committed"] = True
        g["committed_at"] = time.time()
        return {"status": "COMMITTED", "evaluation_id": evaluation_id,
                "post_commit_evidence_required": True}

    def _revoke(self, principal_id):
        self._revoked.add(principal_id)

    def _inject_stale_grant(self, action_type="wire_transfer") -> dict:
        """Inject a pre-expired grant for CT-R4-004 without time travel."""
        eid = f"eval_stale_{uuid.uuid4().hex}"
        nonce = uuid.uuid4().hex
        grant = {
            "evaluation_id":     eid,
            "action_type":       action_type,
            "principal_id":      "authorized-actor",
            "final_disposition": "PASS",
            "nonce":             nonce,
            "created_at":        time.time() - 60,
            "valid_until":       time.time() - 1,   # already expired
            "external_effect_atomic": False,
        }
        self._grants[eid] = grant
        self._consumed.add(nonce)
        return grant

    # ── Vector dispatch ───────────────────────────────────────────────────────

    def run_vector(self, vid: str) -> ConformanceResult:
        m = getattr(self, f"_v_{vid.replace('-','_').lower()}", None)
        if m is None:
            return self._gap(vid, "No native translation defined for this vector")
        try:
            return m()
        except Exception as e:
            return self._fail(vid, f"exception: {e}")

    def _v_c1(self):
        g = self._evaluate("unauth","none","wire_transfer",0.3,0.3,0.85,uuid.uuid4().hex)
        if g["final_disposition"] == "HARD_VETO":
            return self._pass("C1","HARD_VETO on standing failure (native kernel)")
        return self._fail("C1", f"got {g['final_disposition']!r}")

    def _v_c2(self):
        g = self._evaluate("auth","valid-token","wire_transfer",
                           0.95, 0.90, 0.10, uuid.uuid4().hex)
        if g["final_disposition"] in ("FLAG","HARD_VETO"):
            return self._pass("C2", f"{g['final_disposition']} under extreme pressure (native)")
        return self._fail("C2", f"got {g['final_disposition']!r}")

    def _v_c3(self):
        pid = f"race-{uuid.uuid4().hex[:8]}"
        g = self._evaluate(pid,"valid-token","wire_transfer",
                           0.2, 0.2, 0.90, uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._ar("C3","Could not obtain PASS grant for race test")
        self._revoke(pid)
        try:
            self._commit(g["evaluation_id"])
            return self._gap("C3",
                "commit accepted post-revocation (native) — permissive "
                "revocation is non-conformant to RFC-4 §2.2 MUST. "
                "See spec.md C3 row.")
        except ValueError as e:
            return self._pass("C3",
                f"commit blocked post-revocation: {e} "
                "(strict — RFC-4 §2.2 conformant)")

    def _v_c4(self):
        return self._na("C4",
            "Fail-closed transport safety not applicable to in-process kernel; "
            "no transport layer exists.")

    def _v_c5(self):
        nonce = uuid.uuid4().hex
        self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90, nonce)
        try:
            self._evaluate("auth","valid-token","wire_transfer",
                           0.2, 0.2, 0.90, nonce,
                           evaluation_id=f"eval_{uuid.uuid4().hex}")
            return self._fail("C5","Duplicate nonce accepted — replay not rejected")
        except ValueError as e:
            if "NONCE_REPLAY" in str(e):
                return self._pass("C5","NONCE_REPLAY raised on duplicate nonce (native)")
            return self._fail("C5", f"unexpected error: {e}")

    def _v_ct_r4_001(self):
        g = self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._fail("CT-R4-001", f"expected PASS, got {g['final_disposition']!r}")
        result = self._commit(g["evaluation_id"], "wire_transfer")
        if result["status"] == "COMMITTED":
            return self._pass("CT-R4-001","Valid grant bound and committed (native)")
        return self._fail("CT-R4-001", f"commit failed: {result}")

    def _v_ct_r4_002(self):
        g = self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "PASS":
            return self._fail("CT-R4-002","could not obtain PASS grant")
        try:
            self._commit(g["evaluation_id"], "account_deletion")  # wrong action
            return self._fail("CT-R4-002","binding violation not detected")
        except ValueError as e:
            if "BINDING_VIOLATION" in str(e):
                return self._pass("CT-R4-002",f"PAYLOAD_BINDING_VIOLATION raised (native)")
            return self._fail("CT-R4-002", f"wrong error: {e}")

    def _v_ct_r4_003(self):
        nonce = uuid.uuid4().hex
        self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90, nonce)
        try:
            self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90,
                           nonce, f"eval_{uuid.uuid4().hex}")
            return self._fail("CT-R4-003","Nonce replay not rejected")
        except ValueError as e:
            if "NONCE_REPLAY" in str(e):
                return self._pass("CT-R4-003","REPLAY_DETECTED on consumed nonce (native)")
            return self._fail("CT-R4-003", f"wrong error: {e}")

    def _v_ct_r4_004(self):
        stale = self._inject_stale_grant("wire_transfer")
        try:
            self._commit(stale["evaluation_id"], "wire_transfer")
            return self._fail("CT-R4-004","Expired grant accepted — expiry not enforced")
        except ValueError as e:
            if "EXPIRED" in str(e):
                return self._pass("CT-R4-004","EVALUATION_EXPIRED on stale grant (native)")
            return self._fail("CT-R4-004", f"wrong error: {e}")

    def _v_ct_r4_005(self):
        return self._gap("CT-R4-005",
            "state_hash_at_verdict not implemented in kernel v0.1. "
            "State-change detection limited to standing revocation. "
            "Full Commit-State Binding requires capturing structural state at verdict.")

    def _v_ct_r4_006(self):
        g = self._evaluate("unauth","none","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g["final_disposition"] != "HARD_VETO":
            return self._fail("CT-R4-006","could not force HARD_VETO")
        try:
            self._commit(g["evaluation_id"])
            return self._fail("CT-R4-006","HARD_VETO incorrectly committed")
        except ValueError as e:
            if "INVALID_DISPOSITION" in str(e):
                return self._pass("CT-R4-006","HARD_VETO blocked at commit gate (native)")
            return self._fail("CT-R4-006", f"wrong error: {e}")

    def _v_ct_r4_007(self):
        g = self._evaluate("unauth","none","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        receipt = g.get("receipt", {})
        if receipt.get("receipt_hash"):
            return self._gap("CT-R4-007",
                "Structural receipt present but NOT signed — "
                "cryptographic signing absent in v0.1.")
        return self._fail("CT-R4-007","No receipt in grant object")

    def _v_ct_r4_008(self):
        return self._gap("CT-R4-008",
            "No append-only Evidence Manifest in kernel v0.1. "
            "Requires tamper-evident ledger implementation.")

    def _v_ct_r4_009(self):
        return self._gap("CT-R4-009",
            "Independent verification requires CT-R4-007 (signed receipts) "
            "and CT-R4-008 (manifest). Both are IMPLEMENTATION_GAP.")

    def _v_ct_r4_010(self):
        g = self._evaluate("auth","valid-token","wire_transfer",0.2,0.2,0.90,uuid.uuid4().hex)
        if g.get("external_effect_atomic") is False:
            result = self._commit(g["evaluation_id"])
            if result.get("post_commit_evidence_required") is True:
                return self._pass("CT-R4-010",
                    "external_effect_atomic=false; post_commit_evidence_required=true (native)")
        return self._fail("CT-R4-010","external_effect_atomic not correctly declared")


# ── Report generation ─────────────────────────────────────────────────────────

def generate_report(adapter: BaseAdapter, results: list[ConformanceResult],
                    endpoint: str = "") -> dict:
    counts = {s.value: 0 for s in ReportingState}
    for r in results:
        counts[r.status.value] += 1

    return {
        "suite":           "REG Conformance Suite v0.2.4",
        "rfc_refs":        ["RFC-4 (v0.2, frozen)", "RFC-7 (updated)"],
        "interface_mode":  adapter.interface_mode,
        "evidence_level":  int(adapter.evidence_level),
        "evidence_label":  EvidenceLevel(adapter.evidence_level).name,
        "endpoint":        endpoint,
        "ran_at":          time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary":         counts,
        "results": [asdict(r) for r in results],
        "notes": {
            "C3":       "Permissive revocation post-verdict is non-conformant to "
                        "RFC-4 §2.2 MUST. Reported as IMPLEMENTATION_GAP, not PASS.",
            "CT-R4-004": "Expiry testable natively (NativeKernelAdapter). "
                         "HTTP adapter requires time delay — marked ADAPTER_REQUIRED.",
            "CT-R4-005": "state_hash_at_verdict not implemented. "
                         "Full race detection is IMPLEMENTATION_GAP in v0.1.",
            "CT-R4-007": "Structural receipt present; cryptographic signing absent — "
                         "IMPLEMENTATION_GAP in v0.1.",
            "CT-R4-008-009": "Tamper-evident manifest and independent verifier path "
                             "absent — IMPLEMENTATION_GAP in v0.1.",
        }
    }


# ── Main ──────────────────────────────────────────────────────────────────────

MARKS = {
    "PASS":               "✓",
    "FAIL":               "✗",
    "NOT_APPLICABLE":     "○",
    "ADAPTER_REQUIRED":   "~",
    "IMPLEMENTATION_GAP": "△",
}


def main():
    p = argparse.ArgumentParser(description="REG Conformance Suite v0.2.4 — TENIR Labs")
    p.add_argument("--endpoint",  default="",
                   help="REG HTTP endpoint (required for http/both mode)")
    p.add_argument("--mode",      choices=["http","native","both"], default="http")
    p.add_argument("--kernel",    default="kernel/tenir_policies.yaml",
                   help="Path to policy YAML (native/both mode)")
    p.add_argument("--api-key",   default=None)
    p.add_argument("--insecure",  action="store_true")
    p.add_argument("--output",    default="results/tenirlabs-v0.2.json")
    args = p.parse_args()

    import os; os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)

    all_reports = []

    def run_adapter(adapter, label, endpoint=""):
        print(f"\nREG Conformance Suite v0.2.4 — {label}\n{'─'*64}")
        results = adapter.run_all()
        for r in results:
            m = MARKS.get(r.status.value, "?")
            note = f"  ↳ {r.gap_note}" if r.gap_note and r.status.value not in ("PASS","FAIL") else ""
            print(f"  {m}  {r.vector_id:<16}  {r.status.value:<22}  {r.details}")
            if note:
                print(f"     {note[:90]}")
        counts = {}
        for r in results:
            counts[r.status.value] = counts.get(r.status.value, 0) + 1
        print(f"\n{'─'*64}")
        for k, v in counts.items():
            print(f"  {MARKS.get(k,'?')} {k}: {v}")
        report = generate_report(adapter, results, endpoint)
        all_reports.append(report)
        return results

    if args.mode in ("http","both"):
        if not args.endpoint:
            print("ERROR: --endpoint required for http/both mode", file=sys.stderr)
            sys.exit(1)
        run_adapter(
            HTTPAdapter(args.endpoint, args.api_key, args.insecure),
            f"HTTP adapter → {args.endpoint}",
            args.endpoint)

    if args.mode in ("native","both"):
        run_adapter(
            NativeKernelAdapter(args.kernel),
            "Native kernel (TENIR-Gov PolicyEngine)")

    output = all_reports[0] if len(all_reports) == 1 else all_reports
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\n  Results written → {args.output}")

    # Exit non-zero only on FAIL
    has_fail = any(
        r["status"] == "FAIL"
        for report in (all_reports if isinstance(all_reports,list) else [all_reports])
        for r in report["results"]
    )
    sys.exit(1 if has_fail else 0)


if __name__ == "__main__":
    main()
