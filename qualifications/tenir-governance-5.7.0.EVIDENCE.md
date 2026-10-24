# Qualification evidence log — 2026-10-24

## CI observed

- Source: [GitHub Actions capabilities run 40134948385](https://github.com/skiredj-prog/reg-conformance/actions/runs/40134948385), job 120994379119, PR #47 branch head `4d2eee59006eeae7254fe1218d33ec83cd79a017`.
- Result: `success` for `python tools/make_capabilities.py --check`, `python tools/verify_capabilities.py`, `python tools/fill_catalog_guarantees.py --check`.
- CI reports 13 capability definitions structurally valid, and `CATALOG IN SYNC`.
- This workflow **did not** install/pin and exercise the TENIR-Gov 5.7.0 native runtime, run REG Conformance T6–T8 adapters, verify a wheel SHA, or demonstrate production-grade guarantees.

## Important claim boundaries from CI output

- `cap-linearizability-verification`: `effective_guarantee_demonstrated=false`.
- `cap-secure-consensus-transport`: `false`.
- `cap-exactly-once-external`: `false`.
- `cap-byzantine-tolerance`: `false`.
- `cap-i8-budget-disttx`: `null` (not evaluated).
- `cap-dedup-provider-key`: `null` (not evaluated).
- Positive declarations in other capability records were **schema-verified**, not independently re-proven by this CI job. Do not propagate them as new 5.7.0 evidence.

## Blockers

1. Run REG Conformance against pinned TENIR-Gov 5.7.0 artifact.
2. Record actual native implementation mapping and executed observations for CT-R4-011/012/013.
3. Attach immutable input/output hashes and environment manifest.
4. Review capability claims against their underlying evidence before REG+ promotion.

## Local execution limitation

A direct GitHub repository clone attempted in the analysis environment failed because GitHub hostname resolution/network access was unavailable. This is a tooling limitation, not a test failure in the repository. GitHub Actions above is the only executed CI observed for PR #47 in this pass.

**Qualification status remains PENDING_EXECUTION; no release or merge authorization.**
