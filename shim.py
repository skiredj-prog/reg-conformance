#!/usr/bin/env python3
"""
REG Conformance Shim — v0.2 (RFC-4 frozen / RFC-7 updated)
============================================================
HTTP adapter exposing the REG /evaluations protocol surface, backed by the
TENIR-Gov kernel (kernel/policy_engine.py).

interface_mode: "adapter"   ← this is an HTTP adapter over the kernel,
                              not the kernel's native interface.

What changed in v0.2 (RFC-4 §1.3 / RFC-7 §8)
----------------------------------------------
- Action/payload binding enforced at commit time (CT-R4-002)
- Decision Receipt attached to every evaluation response (CT-R4-007 structural,
  unsigned — signing key absent, declared IMPLEMENTATION_GAP)
- external_effect_atomic: false on every response (CT-R4-010)
- CommitEvent accepts action_type for binding verification
- Reporting states: PASS | FAIL | NOT_APPLICABLE | ADAPTER_REQUIRED | IMPLEMENTATION_GAP

Endpoints
---------
POST /evaluations
POST /evaluations/{id}/events
POST /admin/revoke
GET  /evaluations/{id}/proof
GET  /health
"""

import hashlib, json, logging, sys, time, uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
from kernel.policy_engine import PolicyEngine

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger("reg.shim")

POLICY_FILE = Path(__file__).parent / "tenir_policies.yaml"
_engine = PolicyEngine(POLICY_FILE)

_evaluations: dict[str, dict] = {}
_commits: set[str] = set()
_revoked: set[str] = set()
_used_nonces: set[str] = set()

EVAL_WINDOW_SECONDS = 30


# ── Pydantic models ───────────────────────────────────────────────────────────

class Principal(BaseModel):
    id: str
    credential: str

class Action(BaseModel):
    type: str
    params: dict = Field(default_factory=dict)

class Measurements(BaseModel):
    pressure:   float = 0.5
    volatility: float = 0.5
    velocity:   Optional[float] = None
    capacity:   float = 0.85

class EvaluationRequest(BaseModel):
    protocol_version: str = "reg-1.0"
    evaluation_id:    str
    action_id:        str
    principal:        Principal
    action:           Action
    measurements:     Measurements = Field(default_factory=Measurements)
    nonce:            str
    submitted_at:     str

class CommitEvent(BaseModel):
    event_type:     str = "commit"
    action_type:    Optional[str] = None   # RFC-4 §1.3 payload binding check
    policy_version: Optional[str] = None
    signed_hash:    Optional[str] = None

class RevokeRequest(BaseModel):
    principal_id: str
    reason: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _record_hash(record: dict) -> str:
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, default=str).encode()
    ).hexdigest()

def _make_receipt(record: dict) -> dict:
    """
    Structural Decision Receipt (RFC-4 §3).
    Unsigned — cryptographic signing absent in v0.1 (IMPLEMENTATION_GAP).
    """
    disp = record.get("final_disposition", "UNKNOWN")
    receipt_type = {
        "PASS":      "Grant/Authorization Receipt",
        "FLAG":      "Conditional Decision Receipt",
        "HOLD":      "Suspension Receipt",
        "HARD_VETO": "Refusal Receipt",
    }.get(disp, "Unknown Receipt")

    payload = {
        "receipt_id":       str(uuid.uuid4()),
        "receipt_type":     receipt_type,
        "evaluation_id":    record.get("evaluation_id"),
        "final_disposition":disp,
        "policy_version":   record.get("policy_version"),
        "issued_at":        record.get("created_at"),
        "signed":           False,
        "signing_gap":      "IMPLEMENTATION_GAP — no signing key in v0.1",
    }
    payload["receipt_hash"] = _record_hash(payload)
    return payload


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="REG Conformance Shim", version="0.2.0")


@app.post("/evaluations", status_code=200)
async def evaluate(req: EvaluationRequest):
    # Nonce validation (RFC-4 §2.1)
    if len(req.nonce) < 8:
        raise HTTPException(status_code=422, detail="NONCE_TOO_SHORT")
    if req.nonce in _used_nonces:
        raise HTTPException(status_code=409, detail="NONCE_REPLAY")
    _used_nonces.add(req.nonce)

    # Standing gate (RFC-3)
    standing_fail = (
        req.principal.credential in ("none", "", "invalid")
        or req.principal.id in _revoked
    )

    if standing_fail:
        record = {
            "evaluation_id":      req.evaluation_id,
            "action_id":          req.action_id,
            "action_type":        req.action.type,
            "principal_id":       req.principal.id,
            "final_disposition":  "HARD_VETO",
            "reason":             "STANDING_FAILURE",
            "s_score":            None,
            "policy_version":     _engine.version,
            "created_at":         time.time(),
            "valid_until":        time.time() + EVAL_WINDOW_SECONDS,
            "nonce":              req.nonce,
            "external_effect_atomic": False,     # RFC-4 §1.1 / CT-R4-010
        }
        record["_hash"]   = _record_hash(record)
        record["receipt"] = _make_receipt(record)
        _evaluations[req.evaluation_id] = record
        return record

    # Structure gate via kernel (RFC-2)
    m = req.measurements
    P = m.pressure
    V = m.velocity if m.velocity is not None else (m.pressure * m.volatility) ** 0.5
    K = m.capacity

    kr = _engine.evaluate(P, V, K)

    record = {
        "evaluation_id":      req.evaluation_id,
        "action_id":          req.action_id,
        "action_type":        req.action.type,   # stored for CT-R4-002 binding
        "principal_id":       req.principal.id,
        "final_disposition":  kr["decision"],
        "s_score":            kr["s_score"],
        "rationale":          kr["rationale"],
        "policy_version":     kr["policy_version"],
        "created_at":         time.time(),
        "valid_until":        time.time() + EVAL_WINDOW_SECONDS,
        "nonce":              req.nonce,
        "measurements":       {"P": round(P, 6), "V": round(V, 6), "K": K},
        "external_effect_atomic": False,          # RFC-4 §1.1 / CT-R4-010
    }
    record["_hash"]   = _record_hash(record)
    record["receipt"] = _make_receipt(record)
    _evaluations[req.evaluation_id] = record
    return record


@app.post("/evaluations/{eval_id}/events", status_code=200)
async def commit_event(eval_id: str, event: CommitEvent):
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="EVALUATION_NOT_FOUND")

    rec = _evaluations[eval_id]

    # Non-PASS cannot cross commit (RFC-4 §5 / CT-R4-006)
    if rec["final_disposition"] in ("HARD_VETO", "HOLD"):
        raise HTTPException(status_code=409, detail="INVALID_DISPOSITION")

    # Duplicate commit guard (CT-R4-003 / CT-R4-004 old)
    if eval_id in _commits:
        raise HTTPException(status_code=409, detail="ALREADY_COMMITTED")

    # Expiry window (RFC-4 §2 / CT-R4-004)
    if time.time() > rec["valid_until"]:
        raise HTTPException(status_code=409, detail="EVALUATION_EXPIRED")

    # Action/payload binding verification (RFC-4 §1.3 / CT-R4-002)
    if event.action_type and event.action_type != rec["action_type"]:
        raise HTTPException(status_code=409,
                            detail=f"PAYLOAD_BINDING_VIOLATION: "
                                   f"granted={rec['action_type']!r} "
                                   f"attempted={event.action_type!r}")

    # Policy version lock
    if event.policy_version and event.policy_version != rec["policy_version"]:
        raise HTTPException(status_code=409, detail="POLICY_VERSION_MISMATCH")

    _commits.add(eval_id)
    rec["committed_at"]  = time.time()
    rec["commit_hash"]   = _record_hash({**rec, "committed": True})

    return {
        "status":      "COMMITTED",
        "eval_id":     eval_id,
        "commit_hash": rec["commit_hash"],
        "post_commit_evidence_required": True,   # RFC-4 §1.1 / CT-R4-010
    }


@app.post("/admin/revoke", status_code=200)
async def revoke(req: RevokeRequest):
    _revoked.add(req.principal_id)
    return {"revoked": req.principal_id, "reason": req.reason}


@app.get("/evaluations/{eval_id}/proof", status_code=200)
async def get_proof(eval_id: str):
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="EVALUATION_NOT_FOUND")
    if eval_id not in _commits:
        raise HTTPException(status_code=409, detail="NOT_YET_COMMITTED")

    rec = _evaluations[eval_id]
    return {
        "eval_id":           eval_id,
        "final_disposition": rec["final_disposition"],
        "eval_hash":         rec["_hash"],
        "commit_hash":       rec.get("commit_hash"),
        "receipt_hash":      rec["receipt"]["receipt_hash"],
        "policy_version":    rec["policy_version"],
        "proof_complete":    True,
        "manifest_signed":   False,
        "manifest_gap":      "IMPLEMENTATION_GAP — append-only ledger absent in v0.1",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "shim_version": "0.2.0",
            "interface_mode": "adapter",
            "policy": _engine.version, "institution": _engine.institution}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8099)
