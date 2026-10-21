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


## Guided syntax interpretation v0.1 — narrow extension, no contract migration

The **original** `mediation.engine.mediate()` PREVENT/PREPARE v0.1 output
schema remains **unchanged**. An optional companion `mediation.guided.guide()`
composes that validated draft with a **separate**, versioned
`mediation.interpret.interpret()` syntax proposal:

- Entire sentence must match an explicitly supported FR/EN grammar.
- Two narrowly conditional demonstrations: **settlement duplicate-effect
  constraint only when latency > N ms**, and **human approval on payments
  strictly greater than X MAD/EUR/USD, prior to execution**.
- One conjunction: **customer data residency AND access logging**. Each is a
  separate syntax candidate. The authorized region remains unresolved.
- No semantic fallback, inferred thresholds, unsupported qualifiers, arbitrary
  grammar, canonical invariant IDs or executable code.
- Unknown wording and added exceptions return `ABSTAIN_UNSUPPORTED` and zero
  candidates. Even recognized wording remains `SYNTAX_CANDIDATES_UNVERIFIED`
  with `meaning_verified=false` and `review_required=true`.
- `mediation.verify_syntax.validate_syntax_result()` validates the strict
  `contracts/syntax-v0.1.schema.json` **and replays the full source text**
  through the deterministic grammar. Edits to a candidate's threshold, timing,
  properties, source quote or authority status are rejected.

### Reproduce the two-way customer-facing examples

```sh
python -m mediation.guided \
  --input mediation/examples/prevent-conditional-settlement.json \
  --output /tmp/reg-guided-settlement.json

python -m mediation.guided \
  --input mediation/examples/prevent-conditional-approval.json \
  --output /tmp/reg-guided-approval.json

python -m mediation.guided \
  --input mediation/examples/prepare-payflow.json \
  --output /tmp/reg-guided-prepare.json
```

`PREVENT` now has a **bounded, optional** syntax preview that shows the
trigger, proposed property and unresolved questions without changing its
canonical mediation status. `PREPARE` remains a **separate entry** with
`syntax_interpretation = null`, retaining existing missing-evidence
classification. A validated Discovery report can also be supplied to
`PREVENT` as before; the report remains the source of the findings, and
unrecognized behavior text simply abstains. Discovery findings are **not**
silently translated into obligations.

**Integration discipline:** this is a Python-side companion artifact. The
standalone browser Translation Studio still uses its local illustrative parser;
a real browser/API handoff to this contract has **not** been implemented.
Do not claim this is a semantically complete policy compiler or a production
REG+ / TENIR-Gov adapter.

### Review gate before any further extension

Before recognizing another sentence family: document the exact accepted
syntax, show at least one adversarial formulation that must abstain, preserve
source quotation, and add verification plus CI coverage. A broader semantic
mediator must have an explicit human confirmation and source-applicability
workflow rather than silently generalizing these patterns.
