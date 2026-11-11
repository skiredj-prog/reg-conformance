# REG Discovery — report contract v0.1 (draft)

REG Discovery is an **on-demand service**, optionally embeddable. It surfaces assumptions adjacent to an intended system behavior by interpreting curated references as *questions and conditional technical dependencies*.

This draft establishes a narrow, machine-checkable **report interchange contract**. It is **not** an inference engine, certification service, legal opinion, infrastructure audit, or a runtime TENIR-Gov integration.

## Boundaries

- Maintain existing `catalog/hypotheses-v1.yaml` / R1–R3 / 144-configuration conformance model untouched. These technical compatibility rules do **not** automatically convert laws into technical invariants.
- A selected framework establishes interest, **not** legal applicability.
- Classify each mapping as `direct_source_statement`, `analyst_inference` or `illustrative`. A technical invariant candidate does not become a legal requirement merely through adjacency to a source.
- Exploratory mode (no behavior supplied) returns **questions only**; contextualized mode requires a declared behavior and scope.
- `assessment: structural_conflict` would require a separately reviewable contradiction rule and explicit premises; the report schema alone does not establish such a proof.
- No `safe`, `compliant`, `certified`, `verified`, `guaranteed`, `demonstrated` or `approved` output status.
- The site's role is to **render** the validated, versioned projection; not to rewrite normative assumptions or compute legal interpretations.
- Do not distribute copyrighted full-text standards without an explicit license. Preserve source identity, edition, section and applicability uncertainty.
- The linked EU AI Act and NIST MAP example is expressly an **engineering inference**, not a direct legal mapping, binding applicability conclusion or audited finding.

## Draft files

- `contracts/report-v0.1.schema.json` — strict JSON Schema 2020-12 for the report.
- `examples/oversight-contextualized.json` — *illustrative*, not a customer assessment.
- `verify_report.py` — schema plus cross-reference and uniqueness integrity checks.
- `tests/test_discovery_report.py` — negative cases (unexpected legal claims, unverifiable refs, exploratory overclaim, duplicate identifiers).

## Next (separate PRs)

1. Versioned source catalogue with expert-checked applicability metadata (EU AI Act Art 14, GDPR Art 22, NIST MAP, ISO 42001 summary, OECD principles). Authoritative sources only; 5 cards are a target, **not** asserted as completed in this draft.
2. Curated assumption graph (max 12 families) with traceable source→assumption edges and explicit uncertainty.
3. Pure deterministic resolver + presentation-only projection.
4. Isolated site integration, usability and adversarial tests. No production/publishing.

Tracking: [REG Discovery implementation #37](https://github.com/skiredj-prog/reg-conformance/issues/37) and [GTM track](https://github.com/skiredj-prog/tenir-reg-demo/issues/1).
