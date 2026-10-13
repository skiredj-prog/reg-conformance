# Mapping to the public REG RFC corpus

**Status: documentary comparison only. All eight crosswalk rows remain `unverified`.**

## Public source boundary

The review used RFC-0 through RFC-7 frozen under `reg-standards-baseline/rfc/`, together with `spec.md` v0.3.1 and manuscript v7.0 as identified in the documentary report. No public document titled “REG Core Protocol v0.3.0” was found. Do not cite that title as an independently verified normative artifact.

## Findings

| Crosswalk item | Public source signal | Assessment |
|---|---|---|
| `AdmissionDecision` | RFC-0 §4: PASS / FLAG / HOLD / HARD_VETO | Partial conceptual mapping; no enum with the proposed name. FLAG has no direct equivalent in the suggested ALLOW / DENY / HOLD mapping. |
| `PermitStatus` | Single-use permit / EGE and `valid_until` references | Permit concept found; named status axis not found. |
| `PassageLifecycleStatus` | RFC-0 §5 lifecycle phases | Lifecycle concept found; named status axis not found. |
| `ExecutionStatus` | Manuscript attempt outcomes such as RESOLVED / FAILED | No equivalent axis for “effect attempted” identified under that name. |
| `ReconciliationStatus` | Reconciliation and evidence-bound reconciliation in manuscript | Operation found; named status axis not identified in the public RFCs. |
| `EvidenceStatus` | RFC-4 Decision Receipts, Evidence Manifest, tamper-evident evidence | Evidence artifacts do not prove a runtime write-status axis. Pending/failed evidence-write coverage remains unestablished. |
| `EvidenceVerificationStatus` | RFC-4 / CT-R4-008 and CT-R4-009: manifest integrity and independent verification | Strong conceptual counterpart, but exact normative state-axis label not identified. |
| `CLOSED ≠ COMMITTED` | RFC-0 Closure & Proof; RFC-4 Commit Gate | Conceptual distinction present; no normative status pair with those exact names identified. |

## OP-1: EvidenceStatus

**Status: NON RÉSOLU.**

The public materials examined define evidence artifacts and verification concepts but do not establish that a normative `EvidenceStatus` axis represents pending or failed evidence writes independently of the decision verdict.

Do not resolve OP-1 by assuming that the axis exists. Either locate an authoritative normative definition that explicitly covers pending/failed writes, or propose a core amendment. Any REG-EVD behavior that depends on this axis must remain conditional until then.

## Limits

- “Not found” means not identified in the bounded sources examined; it is not proof of absence from every possible unpublished artifact.
- A shared word is not semantic equivalence.
- A conformance vector or test ID is not, by itself, proof that a named normative state exists.
- This document makes no claim that the mappings have been validated by NIST, ISO, or the authors of REG.
