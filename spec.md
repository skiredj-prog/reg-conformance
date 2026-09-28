# REG Conformance Spec — v0.1
**TENIR Labs** | 2026-09-28

Runtime Execution Governance (REG) Standard — conformance surface for the
five core invariants (C1–C5) and ten commit-integrity vectors (CT-R4-001–010).
All cases target the `POST /evaluations` surface and its event/proof sub-routes.

---

## Disposition vocabulary

| Value | Meaning |
|---|---|
| `PASS` | Action is admissible under current policy |
| `FLAG` | Marginal — human review required before commit |
| `HARD_VETO` | Action is inadmissible — commit must be blocked |

---

## Core invariants (C1–C5)

| Case | Description | Input | Expected | Pass criterion |
|---|---|---|---|---|
| C1 | Standing gate | `principal.credential = "none"` | `HARD_VETO` | HTTP 2xx + `final_disposition = HARD_VETO` |
| C2 | Structure gate | `pressure=0.95, velocity=0.90, capacity=0.10` | `FLAG` or `HARD_VETO` | HTTP 2xx + disposition ≠ `PASS` |
| C3 | Race condition | PASS verdict → `POST /admin/revoke` → commit | Commit blocked or documented | 409 (strict) or 200 + `IMPLEMENTATION_NOTE` (permissive) |
C3 distinguishes two valid architectural positions: strict (re-check Standing at commit time, returns 409) and permissive (Standing is evaluated at request time; revocation is prospective and affects future evaluations). The reference shim is permissive. Conformance does not require one or the other — it requires the choice to be declared.
| C4 | Fail-closed | `POST /nonexistent-503` | ≥ 400 or connection error | Client must treat any non-2xx as fail-closed |
| C5 | Idempotency | Same `Idempotency-Key`, conflicting body | `409` | HTTP 409 |

---

## Commit-integrity vectors (CT-R4 §5.2)

| Case | Description | Input | Expected | Pass criterion |
|---|---|---|---|---|
| CT-R4-001 | Commit records to ledger | PASS eval + `POST /evaluations/{id}/events {event_type: commit}` | `{"status":"COMMITTED"}` | HTTP 200 |
| CT-R4-002 | HARD_VETO unclearable | HARD_VETO eval + commit event | Rejected | HTTP 409 |
| CT-R4-003 | Orphan commit | `POST /evaluations/ghost_id/events` | Not found | HTTP 404 |
| CT-R4-004 | Duplicate commit | Two sequential commits on same eval | Second rejected | HTTP 409 on second call |
| CT-R4-005 | Expiry window | Commit after `EVAL_WINDOW_SECONDS` | Rejected | HTTP 409 `EVALUATION_EXPIRED`, or `NOT_TESTABLE` if window not enforced |
| CT-R4-006 | Short nonce | `nonce` length < 8 | Validation error | HTTP 422 |
| CT-R4-007 | Nonce replay | Two evaluations share the same nonce | Second rejected | HTTP 409 `NONCE_REPLAY` |
| CT-R4-008 | Revocation blocks eval | `POST /admin/revoke` → evaluate same principal | `HARD_VETO` | HTTP 2xx + `HARD_VETO` |
| CT-R4-009 | Emergency flag no standing | `action.type=emergency_override`, `credential=none` | `HARD_VETO` | HTTP 2xx + `HARD_VETO` — override flag cannot bypass standing gate |
| CT-R4-010 | Audit proof completeness | PASS eval + commit → `GET /evaluations/{id}/proof` | Proof with hashes | HTTP 200 + `proof_complete=true` |

---

## Thresholds (reference shim — kernel-r5-1.0.0)

| Parameter | Value |
|---|---|
| `hard_veto_below` | 0.75 |
| `flag_below` | 0.90 |
| `epsilon` | 1e-6 |
| Formula | `S = K / (P × V + ε)` |
| Commit window | 30 s |

Institutional deployments override thresholds via YAML policy file. The runner
is threshold-agnostic: it tests structural properties, not specific S-score values.

---

## Implementation gaps

`NOT_TESTABLE` is a first-class outcome. A case marked `NOT_TESTABLE` indicates
a missing endpoint or optional feature, not a conformance failure. It should be
disclosed as `IMPLEMENTATION_GAP` in any published results.
