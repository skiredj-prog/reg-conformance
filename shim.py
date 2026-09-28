#!/usr/bin/env python3
"""
REG Conformance Shim — v0.1
============================
Exposes the REG Standard /evaluations protocol surface, backed by the
TENIR-Gov kernel (core/policy_engine.py).  No Neo4j, no NSL, no Ollama.

Endpoints implemented
---------------------
POST /evaluations                   — core adjudication
POST /evaluations/{id}/events       — commit event (CT-R4 vectors)
POST /admin/revoke                  — standing revocation (C3)
GET  /evaluations/{id}/proof        — audit proof (CT-R4-010)
GET  /health                        — liveness check

Disposition vocabulary
----------------------
PASS       ←→ kernel PASS   (S ≥ flag_below)
FLAG       ←→ kernel FLAG   (hard_veto_below ≤ S < flag_below)
HARD_VETO  ←→ kernel HARD_VETO (S < hard_veto_below, or standing failure)
"""

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
from core.policy_engine import PolicyEngine

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("reg.shim")

# ── Policy engine (singleton) ─────────────────────────────────────────────────
POLICY_FILE = Path(__file__).parent / "tenir_policies.yaml"
_engine = PolicyEngine(POLICY_FILE)

# ── In-memory stores (sufficient for conformance suite scope) ─────────────────
_evaluations: dict[str, dict] = {}   # eval_id → record
_commits: set[str] = set()           # eval_ids that have been committed
_revoked: set[str] = set()           # revoked principal ids
_used_nonces: set[str] = set()       # replay guard

EVAL_WINDOW_SECONDS = 30             # CT-R4-005 expiry window

# ── Pydantic models ───────────────────────────────────────────────────────────

class Principal(BaseModel):
    id: str
    credential: str

class Action(BaseModel):
    type: str
    params: dict = Field(default_factory=dict)

class Measurements(BaseModel):
    pressure: float = 0.5
    volatility: float = 0.5
    velocity: Optional[float] = None   # if absent, derive from pressure×volatility
    capacity: float = 0.85

class EvaluationRequest(BaseModel):
    protocol_version: str = "reg-1.0"
    evaluation_id: str
    action_id: str
    principal: Principal
    action: Action
    measurements: Measurements = Field(default_factory=Measurements)
    nonce: str
    submitted_at: str

class CommitEvent(BaseModel):
    event_type: str = "commit"
    policy_version: Optional[str] = None
    signed_hash: Optional[str] = None

class RevokeRequest(BaseModel):
    principal_id: str
    reason: str = ""

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="REG Conformance Shim", version="0.1.0")


def _disposition(decision: str) -> str:
    """Normalise kernel verdict → REG disposition label."""
    return decision  # kernel already uses PASS / FLAG / HARD_VETO


def _record_hash(record: dict) -> str:
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


# ── POST /evaluations ─────────────────────────────────────────────────────────

@app.post("/evaluations", status_code=status.HTTP_200_OK)
async def evaluate(req: EvaluationRequest):
    # ── Nonce replay guard (CT-R4-006 / C5 analog) ───────────────────────────
    if req.nonce in _used_nonces:
        raise HTTPException(status_code=409, detail="NONCE_REPLAY")
    if len(req.nonce) < 8:
        raise HTTPException(status_code=422, detail="NONCE_TOO_SHORT")
    _used_nonces.add(req.nonce)

    # ── Principal standing check (C1 / CT-R4-008) ─────────────────────────────
    standing_fail = (
        req.principal.credential in ("none", "", "invalid")
        or req.principal.id in _revoked
    )
    if standing_fail:
        record = {
            "evaluation_id": req.evaluation_id,
            "action_id": req.action_id,
            "principal_id": req.principal.id,
            "final_disposition": "HARD_VETO",
            "reason": "STANDING_FAILURE",
            "s_score": None,
            "policy_version": _engine.version,
            "created_at": time.time(),
            "nonce": req.nonce,
        }
        record["_hash"] = _record_hash(record)
        _evaluations[req.evaluation_id] = record
        return record

    # ── Derive P, V, K ───────────────────────────────────────────────────────
    m = req.measurements
    P = m.pressure
    V = m.velocity if m.velocity is not None else (m.pressure * m.volatility) ** 0.5
    K = m.capacity

    kernel_result = _engine.evaluate(P, V, K)

    record = {
        "evaluation_id": req.evaluation_id,
        "action_id": req.action_id,
        "principal_id": req.principal.id,
        "final_disposition": _disposition(kernel_result["decision"]),
        "s_score": kernel_result["s_score"],
        "rationale": kernel_result["rationale"],
        "policy_version": kernel_result["policy_version"],
        "created_at": time.time(),
        "nonce": req.nonce,
        "measurements": {"P": round(P, 6), "V": round(V, 6), "K": K},
    }
    record["_hash"] = _record_hash(record)
    _evaluations[req.evaluation_id] = record
    return record


# ── POST /evaluations/{id}/events ─────────────────────────────────────────────

@app.post("/evaluations/{eval_id}/events", status_code=status.HTTP_200_OK)
async def commit_event(eval_id: str, event: CommitEvent):
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="EVALUATION_NOT_FOUND")

    rec = _evaluations[eval_id]

    # Can't commit a HARD_VETO (CT-R4-002)
    if rec["final_disposition"] == "HARD_VETO":
        raise HTTPException(status_code=409, detail="CANNOT_COMMIT_VETO")

    # Duplicate commit guard (CT-R4-004)
    if eval_id in _commits:
        raise HTTPException(status_code=409, detail="ALREADY_COMMITTED")

    # Expiry window check (CT-R4-005)
    age = time.time() - rec["created_at"]
    if age > EVAL_WINDOW_SECONDS:
        raise HTTPException(status_code=409, detail="EVALUATION_EXPIRED")

    # Policy version lock (CT-R4-007)
    if event.policy_version and event.policy_version != rec["policy_version"]:
        raise HTTPException(status_code=409, detail="POLICY_VERSION_MISMATCH")

    _commits.add(eval_id)
    rec["committed_at"] = time.time()
    rec["commit_hash"] = _record_hash({**rec, "committed": True})
    return {"status": "COMMITTED", "eval_id": eval_id,
            "commit_hash": rec["commit_hash"]}


# ── POST /admin/revoke ────────────────────────────────────────────────────────

@app.post("/admin/revoke", status_code=status.HTTP_200_OK)
async def revoke(req: RevokeRequest):
    _revoked.add(req.principal_id)
    log.info(f"[shim] Revoked principal: {req.principal_id}")
    return {"revoked": req.principal_id, "reason": req.reason}


# ── GET /evaluations/{id}/proof ───────────────────────────────────────────────

@app.get("/evaluations/{eval_id}/proof", status_code=status.HTTP_200_OK)
async def get_proof(eval_id: str):
    if eval_id not in _evaluations:
        raise HTTPException(status_code=404, detail="EVALUATION_NOT_FOUND")
    if eval_id not in _commits:
        raise HTTPException(status_code=409, detail="NOT_YET_COMMITTED")

    rec = _evaluations[eval_id]
    return {
        "eval_id": eval_id,
        "final_disposition": rec["final_disposition"],
        "eval_hash": rec["_hash"],
        "commit_hash": rec.get("commit_hash"),
        "policy_version": rec["policy_version"],
        "proof_complete": True,
    }


# ── GET /health ───────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "policy": _engine.version,
            "institution": _engine.institution}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8099)
