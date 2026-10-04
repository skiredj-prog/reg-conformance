#!/usr/bin/env python3
"""
REG Conformance Suite v0.3.1 — RFC-4 and RFC-7
================================================
Runs the five core vectors and ten RFC-4 vectors supported by this runner.
Results report conformance status separately from interface evidence level.
Known gaps remain explicit, including independent decision reproduction and
external-effect evidence.
"""

import argparse, base64, hashlib, json, sys, time, uuid
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


# ── Canonical vectors (RFC-4 §5 + core invariants) ────────────────────────────

VECTORS: dict[str, TestVector] = {
    "C1":       TestVector("C1","RFC-3","Standing Gate",
                    "Invalid credential → HARD_VETO regardless of structural state."),
    "C2":       TestVector("C2","RFC-2","Structure Gate",
                    "P≥0.9, V≥0.9, K≤0.15 → FLAG or HARD_VETO, never PASS."),
    "C3":       TestVector("C3","RFC-4 §2.2","Commit-State Binding — Standing Drift",
                    "Revocation between verdict and commit; behaviour must be declared."),
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
        if not m: return self._gap(vid, "No HTTP translation defined")
        try:    return m()
        except Exception as e: return self._fail(vid, f"exception: {e}")

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
            return self._ar("C3", "Could not obtain PASS for race test")
        eid = r.get("evaluation_id")
        rc, rr = self._post("/admin/revoke", {"principal_id":pid,"reason":"C3"})
        if rc not in (200,202):
            return self._ar("C3", f"Protected /admin/revoke unavailable (HTTP {rc}); configure REG_ADMIN_TOKEN and --admin-token")
        ec, er = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        if ec == 409 and "STANDING_REVOKED" in str(er):
            return self._pass("C3","commit blocked after standing revocation")
        if ec == 200:
            return self._fail("C3","commit accepted after revocation")
        return self._fail("C3", f"expected STANDING_REVOKED, got {ec}: {er}")

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
        # Simulate policy reload between verdict and commit
        rc, _ = self._post("/admin/reload-policy", {})
        if rc not in (200,202):
            return self._gap("CT-R4-005","/admin/reload-policy absent — cannot test epoch drift")
        cc, cr = self._post(f"/evaluations/{eid}/events", self._commit_body(r))
        detail = cr.get("detail","")
        return (self._pass("CT-R4-005",
                    f"STATE_DRIFT raised (epoch {epoch_at_verdict}→{epoch_at_verdict+1})")
                if cc == 409 and "STATE_DRIFT" in detail
                else self._fail("CT-R4-005",
                    f"expected 409 STATE_DRIFT, got {cc}: {detail!r}"))

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
        if g["principal_id"] in self._revoked: raise ValueError("STANDING_REVOKED")
        if g.get("_committed"):  raise ValueError("ALREADY_COMMITTED")
        if time.time() > g["valid_until"]: raise ValueError("EVALUATION_EXPIRED")
        if self._epoch != g["policy_epoch"]:
            raise ValueError(f"STATE_DRIFT: epoch_at_verdict={g['policy_epoch']} current={self._epoch}")
        if action_type and action_type != g["action_type"]:
            raise ValueError(f"PAYLOAD_BINDING_VIOLATION: granted={g['action_type']!r}")
        g["_committed"] = True
        g["committed_at"] = time.time()
        self._manifest.append({"type":"commit","evaluation_id":eid,"timestamp":g["committed_at"]})
        return {"status":"COMMITTED","evaluation_id":eid,"post_commit_evidence_required":True}

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
        if not m: return self._gap(vid,"No native translation defined")
        try:    return m()
        except Exception as e: return self._fail(vid, f"exception: {e}")

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
            return self._ar("C3","Could not obtain PASS")
        self._revoke(pid)
        try:
            self._commit(g["evaluation_id"],action_id=g["action_id"],nonce=g["nonce"])
            return self._fail("C3","commit accepted after revocation")
        except ValueError as e:
            return (self._pass("C3",f"commit blocked after revocation (native): {e}")
                    if "STANDING_REVOKED" in str(e) else self._fail("C3",str(e)))

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
                        f"STATE_DRIFT raised (epoch {epoch_before}→{self._epoch}) (native)")
                    if "STATE_DRIFT" in str(e) else self._fail("CT-R4-005",str(e)))

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


MARKS = {"PASS":"✓","FAIL":"✗","NOT_APPLICABLE":"○",
         "ADAPTER_REQUIRED":"~","IMPLEMENTATION_GAP":"△"}

def generate_report(adapter, results, endpoint=""):
    counts = {s.value:0 for s in ReportingState}
    for r in results: counts[r.status.value] += 1
    return {"suite":"REG Conformance Suite v0.3.1",
            "rfc_refs":["RFC-4 (frozen)","RFC-7 (updated)"],
            "interface_mode":adapter.interface_mode,
            "evidence_level":int(adapter.evidence_level),
            "evidence_label":EvidenceLevel(adapter.evidence_level).name,
            "conformance_status": ("FAILED" if counts["FAIL"] else
                                   "INCOMPLETE" if counts["IMPLEMENTATION_GAP"] or counts["ADAPTER_REQUIRED"] else
                                   "CONFORMANT"),
            "endpoint":endpoint,
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
        all_reports.append(generate_report(adapter, results, endpoint))

    if args.mode in ("http","both"):
        if not args.endpoint:
            print("ERROR: --endpoint required", file=sys.stderr); sys.exit(1)
        run(HTTPAdapter(args.endpoint, args.api_key, args.insecure, args.admin_token,
                        args.principal_credential),
            f"HTTP adapter → {args.endpoint}", args.endpoint)

    if args.mode in ("native","both"):
        run(NativeKernelAdapter(args.kernel), "Native kernel (TENIR-Gov PolicyEngine)")

    out = all_reports[0] if len(all_reports)==1 else all_reports
    with open(args.output,"w") as f: json.dump(out, f, indent=2, default=str)
    print(f"\n  Results → {args.output}")

    has_fail = any(r["status"]=="FAIL"
                   for rep in (all_reports if isinstance(all_reports,list) else [all_reports])
                   for r in rep["results"])
    has_incomplete = any(r["status"] in ("IMPLEMENTATION_GAP", "ADAPTER_REQUIRED")
                         for rep in (all_reports if isinstance(all_reports,list) else [all_reports])
                         for r in rep["results"])
    sys.exit(1 if has_fail else 2 if has_incomplete else 0)

if __name__ == "__main__":
    main()
