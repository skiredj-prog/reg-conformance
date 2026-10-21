# REG Translation Studio — bounded experimental preview

Standalone offline-capable UI for **candidate** mediation from L0 (user business intent) and L1 (user-declared source) into provisional L2/L3 artifacts and an **intentionally non-executable** L4 Python template.

This directory is an **experiment**, not part of the canonical REG+ catalogue, R1–R3 rules, conformance status machinery or TENIR-Gov runtime. No source document applicability is established, no approved invariant is generated and no guarantee is demonstrated.

The demo currently supports only narrow deterministic patterns:
- **Conditional settlement de-duplication** when latency exceeds an explicit ms threshold, retaining the original conditional form.
- **Conditional human approval** over an explicit amount threshold, without inventing a universal spending cap.
- **Data residency** and **audit trail** as distinct candidate obligations.
- **Out of catalogue** returns `UNMAPPED_PATTERN_GENERATED` with private routing intent; nothing is actually sent.

The generated Python always raises `NotImplementedError`; it never returns execution permission or falsely imports a runtime base class. All candidate identifiers are `CAND_...`, not canonical `I8` or other REG+ invariant IDs.

Privacy: private mode is the default; the browser never calls a backend. Public RFC links are blocked until user consent and contain no supplied policy text. Opening the link is *not* submitting an issue. The preview cannot route to a private GitHub repository; the routing label is a declared target only.

## Tests

```sh
cd translation_studio
npm install
npm test
```

The contract tests are primarily regression checks for the four illustrative examples. They do not establish full semantic preservation for arbitrary policy text.

## Future work

A semantic mediator must preserve provenance and ambiguity, use real normative source references and formal review gates, and bind code adapters to validated versioned TENIR-Gov interfaces. The first three demo samples are intentionally narrow and not sufficient to certify the Studio as an implementation-ready compiler.

**No production deployment, canonical profile modification, or automatic GitHub RFC creation in this PR.**
