# REG Lifecycle — Repository & Artifact Governance v0.1

**Date:** 2026-10-24  
**Status:** Working proposal — not approved or normative  
**References:** REG-ARCH v0.1 §§2, 3, 5, 6, 9, 10, 12–13; REG Exteriority Registry v0.1  
**Decision authority:** To be designated. This text cannot ratify itself.

## 1. Separation of authority

- **REG-ARCH / `specs/reg-arch/`:** specifies lanes, objects, gates, events, boundaries and traceability. Its amendments require an explicit authority decision and a new version or amendment; no silent rewriting.
- **`reg-conformance`:** defines conformance contracts and evaluates bounded implementation claims. A passing test is not proof that every REG-ARCH requirement is met.
- **Runtime repositories (e.g. `tenir_governance`):** source of implementation behavior, versioned code, and its runtime test outputs.
- **Product repositories (TENIR Labs/X-Ray, Translation Studio, Discover, REG+):** source of product scenarios, internal validations, defects and product versions.
- **PMO:** maintains cross-repository registry of identifiers, dependencies, decisions, owners and publication readiness. It does not override architectural or audit authorities.
- **Website/release collateral:** derived representations only; they cite exact source versions and approved claim scope.

A repository location grants **no normative, evidentiary or certification status**.

## 2. Artifact types and homes

| Kind | Primary home | Promotion / reuse |
| --- | --- | --- |
| Architectural requirement or normative amendment | `specs/reg-arch/` | Decision and new revision required |
| Contract, profile or test design for conformance | `reg-conformance/specs/`, `profiles/`, `tests/` | Linked to a versioned requirement |
| Product scenario, observation and defect | Owning product's `scenarios/`, `validations/`, issue tracker | Remain product-owned |
| Conformance scenario adopted from product tests | `reg-conformance/scenario-suite/` (create when first adopted) | Link exact external source, do not silently copy a moving file |
| Bounded verification result | `reg-conformance/assessments/` | Records method/version/result/exclusions |
| Raw evidence and integrity metadata | `reg-conformance/evidence/` when actually used for a conformance assessment; otherwise product repo | Immutable references/digests, not proof of truth |
| Cross-system decisions, dependencies, claim inventory | PMO registry (location to be decided) | Records responsible authority; cannot decide on its behalf |
| Release notes, badges, public claims | Implementer/site repositories | Derived from decision and verification records |

**No empty scaffolding:** create a directory only with its first real object and documented owner.

## 3. Lifecycle (one object; no file migration as status change)

1. **REGISTERED:** stable id, type, owner, source repo/path/commit, version, purpose, synthetic/real boundary.
2. **SPECIFIED:** scenario, expected outcome, test criteria and exclusions stated before execution.
3. **EXECUTED:** method, environment, timestamp, implementation SHA, inputs and raw observations recorded. Executed ≠ passed.
4. **QUALIFIED:** provenance and integrity checked, evidence bound to exact object/requirement/version; scope and unresolved discrepancies recorded. Capture, attachment and qualification remain distinct (REG-ARCH-009).
5. **VERIFIED (bounded):** verifier, versioned method, examined evidence, PASS/FAIL/INCONCLUSIVE and permitted conclusion explicitly recorded (REG-ARCH-014).
6. **PROMOTION REQUESTED:** proposed conformance claim or approved representation, exact version/scope and authority named.
7. **DECIDED / APPLIED separately:** acceptance or refusal with reason, then recorded application against expected version; no automatic promotion (REG-ARCH-006, 011, 015).
8. **PUBLISHED / SUPERSEDED / WITHDRAWN:** new traceable event, not deletion; public output must include provenance, caveats, exclusions and status (REG-ARCH-016, 023).

A failed test may produce a defect without preventing the original observation from being retained. A revised scenario gets a new revision and references the prior one. A release on a different SHA needs its own qualification.

## 4. Minimal linked record

```yaml
artifact_id: XR-VAL-2026-001
artifact_type: product_scenario_validation
owner: TENIR Labs / X-Ray
product_version: "0.5"
source: {repository: null, path: TENIR-XRay-v0.5-scenario-validation.md, commit: null}
status: EXECUTED_INTERNAL
scenario_kind: synthetic
method: browser_flow_and_edge_cases
runtime_engine_invoked: false
reg_arch_requirement_refs: []
conformance_claim: none
findings: [XR-01, XR-02, XR-03, XR-04, XR-05, XR-06]
decision: NOT_READY_FOR_UNSUPERVISED_CLIENT_PILOT
evidence_refs: []
limits: "No actual company assessed; no REG or TENIR-Gov engine tested."
```

The `null` fields signal missing repository provenance and must not be filled by guessing. Example identifiers and labels are **proposed**, not pre-existing registry entries.

## 5. Adoption into the conformance suite

A product validation is **not** added to `scenario-suite/` solely because it exists. Its adoption requires:
- Named REG-ARCH requirement and exact revision, or a separate approved conformance contract;
- Stable source reference (repository/path/commit and digest where applicable);
- Test protocol with deterministic input/expected result, versioned environment and explicit negative cases;
- Clear distinction between illustrative fixture, executed test, author evidence and independent verification;
- Named reviewer and a recorded admission decision. Missing authority means **candidate only**;
- No broader claim than the measured scope; an external provider outcome is not inferred from a local receipt.

## 6. X-Ray v0.5 — first classification

`TENIR-XRay-v0.5-scenario-validation.md` describes a **synthetic internal browser validation** and six XR findings. Its reported decision is **internal contradictory testing only; not ready for unsupervised client pilot**. It exercised neither REG nor TENIR-Gov. It therefore stays **product validation**, not a REG-ARCH conformance result. If a specific scenario is later reused for e.g. REG-ARCH-006 or -019, create a separate, versioned conformance test contract referencing the original. No proof is promoted by folder relocation.

## 7. Gates for public claims

A public claim requires: approved wording + exact subject/version/SHA + evidence and verifier scope + known exclusions + decision reference + publication/supersession record. `C3`, multi-host, certification and external effects must never be inferred from single-host tests or hashes alone.

## 8. Open decisions

- Who can approve REG-ARCH and amendments? Who separately admits invariants under E3?
- What repository owns TENIR Labs assets and where should PMO registry live?
- Which schema and automation implements the minimal linked record?
- Which REG-ARCH requirement and test protocol should be the first adopted conformance scenario?

**Status rule:** until those decisions are made, this governance document is a proposal; it must not be used to declare a new mandatory standard or an implementation conformant.
