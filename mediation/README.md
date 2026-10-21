# REG Mediation v0.1 — PREVENT / PREPARE

**Status:** experimental, non-authoritative; stacked on REG Discovery PR #39.
**Purpose:** Give the two customer journeys a compatible technical handoff without
building a universal legal compiler, code generator or centralized data platform.

## Two independent entries, one reviewable draft

| Entry | Starts with | Returns | Never asserts |
|---|---|---|---|
| `PREVENT` | A declared intent, optionally a validated REG Discovery report | Assumption lineage, questions, unreviewed candidate properties | Legal applicability, an approved REG+ profile, a demonstrated invariant or deployment permission |
| `PREPARE` | An inventory of declared controls and referenced evidence | Missing evidence, referenced-but-unverified evidence, outstanding review questions | Audit completion, proof of effectiveness or regulatory compliance |

Both preserve source provenance and versioned contracts; neither requires the other.
`PREPARE` does not require TENIR-Gov, and `PREVENT` does not require Discovery.

## What is deliberately not implemented

- No natural-language semantic mediation. A pasted rule is not translated into a normative profile.
- No REG+ catalog mutations, no extension of R1–R3, no rewriting the 144-configuration model.
- No canonical invariant IDs assigned (e.g. REG+ I8 remains aggregate budget conservation).
- No `Evaluate/Commit/Record` generator; TENIR-Gov runtime integration is separate and requires a verified adapter.
- No automatic GitHub issue/RFC and **no user-data transmission** in this CLI.
- No persistent store, user accounts, legal opinion or automatic compliance claims.

This is a **bounded proof of contract**, not a complete service.

## Input examples

```sh
python -m mediation.engine --input mediation/examples/prevent-standalone.json --output /tmp/reg-prevent.json
python -m mediation.engine --input mediation/examples/prepare-payflow.json --output /tmp/reg-prepare.json
```

To bridge from Discovery, pass its full **validated** v0.1 report as
`discovery_report` to `PREVENT`. Use `selected_finding_ids` to choose explicit
findings, or omit it to include all returned findings. A purely exploratory
report (no declared behavior) also needs an independent user `intent`; the
selected framework alone does not establish an obligation.

```json
{
  "schema_version": "0.1.0",
  "entry": "PREVENT",
  "scope": "Fictional payment service",
  "intent": "A settlement must not produce two external effects.",
  "discovery_report": { "schema_version": "0.1.0", "...": "full validated report" }
}
```

For `PREPARE`, `controls[].evidence_ids` are *references*, not proof. If a
referenced ID has no matching `evidence[]` item, the output lists it as
missing. If all IDs are present, the output remains
`EVIDENCE_REVIEW_REQUIRED`, not `VERIFIED`.

## Statuses

- `NEEDS_CLARIFICATION`: standalone or selected Discovery questions, no
  qualified contradiction.
- `DECLARED_PREMISE_CONFLICT`: at least one selected finding is explicitly
  a structural contradiction **in declared premises**, not an observed system failure.
- `EVIDENCE_INCOMPLETE`: a declared control has no evidence reference or
  at least one unresolved reference.
- `EVIDENCE_REVIEW_REQUIRED`: every declared reference exists in the supplied
  inventory; validity, relevance and sufficiency remain unverified.

Every output has `profile: null`, `profile_status: NOT_ADMITTED`,
`code_generation: NOT_GENERATED`, `github_publication: NOT_REQUESTED`,
`review_required: true`, and explicit limitations.

## Checks

```sh
python -m pip install 'pytest>=8,<10' 'jsonschema>=4,<5'
python -m pytest -q discovery/tests/ mediation/tests/
```

The `mediation.verify.validate_result` function validates the strict output
schema and checks foreign-key integrity, evidence partitions and status
consistency. All examples are fictional. The code performs no I/O except
reading a CLI request and writing a local output.

## Future work — customer-value gated

A prospect-facing PREVENT/ PREPARE web demonstration could consume **only**
the versioned output. Before adding real user documents, design a consent,
retention and access boundary. Before permitting mediation approval, require
human authority, verified source applicability, and tests backed by actual
REG+ contracts. No automatic authority promotion.
