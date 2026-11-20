# W4 affected-property revalidation — W2.1c

Producer SHA **`3c390c30f3ed0deb030576b1ed9aa8dc1a7360f2`**, parent `95263530bbe095d97c9b662b51ee482fd96618d6`, [Draft PR #85](https://github.com/skiredj-prog/tenir_governance/pull/85). Draft/open/unmerged and exact head were verified at inspection. This is an **executed local follow-up**, separate from the code review reported by PMO as review ID 5688027256. W4 did not post another review/comment to #85 or change producer code.

Only the affected UNIQUE migration and terminal-state properties were revalidated. Key lifecycle, operation aliasing, native authority convergence, SIGKILL, CEB-01, B2 and full W3/E2E campaigns were not rerun. Prior reports retain their original source SHAs.

## Sources and execution

Four current producer files were fetched at the exact SHA and Git-blob checked before import; see [source-reference.json](source-reference.json). Historical provider `02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413`, blob `ebc0cdee36f19e4adbcfc713b5b8370725714f9f`, creates the actual old-schema fixture through its own API. That version permits two operation rows with one idempotency key; no SQL mutation or fabricated signed receipt was used to seed duplicates.

Environment: Linux WSL / Python 3.14.4 / SQLite 3.46.1, assertions enabled. Temporary stores and subprocesses were isolated. The current delivered script runs **three functions, all PASS**. Those functions and the additional native counterexamples are reported separately from the 139 W4 consumer-unit tests; no totals are added across suites/runs.

Commands, source hashes, environment, exit codes, transitions and actual observations are in [results/review.json](results/review.json) and the adjacent original stdout logs. All six recorded subprocess stderr streams were empty. Trace timestamps are raw observer/native timestamps, not an authenticated global ordering proof.

## P0-A — Migration: partial correction, still OPEN

| Case | Native observation | Verdict |
|---|---|---|
| Old store, one key row | Current constructor returns; PRAGMA confirms unique indexes on idempotency key and operation ID; a distinct-key write succeeds | **SCOPED PASS** for this clean legacy schema |
| Old store, two rows sharing a key | Current constructor returns; only the operation-ID unique index remains; a distinct-key write succeeds; the duplicate group still contains two rows | **REFUTED** as a generally validated upgrade / **P0 OPEN** |

The [IntegrityError handler](https://github.com/skiredj-prog/tenir_governance/blob/3c390c30f3ed0deb030576b1ed9aa8dc1a7360f2/w2_integration/proof_provider.py) suppresses failed index creation. The reproduced later distinct-key write does not surface that preexisting integrity problem. Fresh or clean-schema success cannot justify acceptance of the duplicate-bearing store.

Minimum producer correction: explicitly fail closed on an unresolvable duplicate-bearing schema, or use a reviewed deterministic remediation before accepting it. Verify the effective uniqueness constraint, not just successful constructor return or an index-name assertion. Duplicate detection/refusal must not silently discard receipts or arbitrarily select an effect. Agent 1 owns the implementation and negative regression tests.

## P0-B — Terminal protection: partial correction, still OPEN

| Case | Native observation | Verdict |
|---|---|---|
| Four terminals → RESERVED | All four calls raise RuntimeError; persisted state remains unchanged | **SCOPED PASS**, the original nonterminal regression is blocked |
| Actual completed bridge called again | Second call refuses `RECONCILED_CONFIRMED → RESERVED`; original terminal remains stored | **SCOPED PASS**, rejection rather than a demonstrated successful recovery/replay API |
| Different terminal → terminal | All 12 directed replacements among the four terminal labels return successfully | **REFUTED** for terminal-result immutability / **P0 OPEN** |
| Two writers after reading the same RESERVED state | Both native transition calls succeed, one to FAILED and one to RECONCILED_CONFIRMED; each reports predecessor RESERVED; only one final row value remains | **REFUTED** for the tested atomic terminal-decision property / **P0 OPEN** |

The concurrency check uses two real processes and a trace-hook barrier immediately after each actual predecessor read. It changes scheduling only; it does not modify code, local variables, return values, SQLite data or the guard. This is one reproducible affected-property interleaving, not a general security/concurrency qualification. Terminal initialization in fixtures uses the current public transition API and establishes no real provider authorization/effect.

Minimum producer correction: make legal predecessor validation and state/version update one atomic operation (transaction or checked compare-and-swap), reject contradictory terminal replacements and define identical terminal replay explicitly. Rejection must preserve the committed result. A Python check before a separate unconditioned write is insufficient for concurrent writers. Agent 1 implements it; W4 can revalidate this bounded property and W3 retains the broader campaign.

## Reproduction

Provide isolated writable snapshots of the four current files and the historical provider identified in `source-reference.json`, with the pinned W4 cryptography dependency installed:

```sh
python -B revalidate.py --sources /snapshots/3c390c3/w2_integration --previous-sources /snapshots/02ea1d3/w2_integration --out /tmp/w4-w21c-results
```

The harness Git-blob checks the snapshots before import (restoring fetched LF newlines if needed). It executes the delivered three-function script, historical clean/duplicate fixtures, current upgrade attempts and bounded terminal probes. The P0 status fields are derived from observations; absence of reproduction would be NOT_REPRODUCED, not an automatic closure. Producer sources are not vendored in this W4 package, and no replacement CEB or signatures are manufactured.

**W2.1c SCOPED PROGRESS / P0 MIGRATION OPEN / P0 TERMINAL OPEN / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.**
