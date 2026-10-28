# W4 partial review — W2.1b / PR #85

Producer SHA: **`95263530bbe095d97c9b662b51ee482fd96618d6`**, parent `f1ada7b78d9f4c13656efc7f9f8c5a165394a9fb`. [TENIR PR #85](https://github.com/skiredj-prog/tenir_governance/pull/85) was open/unmerged, **not Draft**, at inspection. The new commit changes three W2 files: persistent RC-01, UNIQUE idempotency key on newly created effects tables, and stronger same-process reopen assertions.

This version-specific review supplements [the previous review](../w2-f1ada7b/REVIEW.md). Its earlier RC-01 nonpersistence finding applies to f1ada7b, not automatically to this SHA. Four exact Git blobs were checked before native component imports; see [source-reference.json](source-reference.json). Producer files were not edited and are not vendored here.

## Reproduced results

Linux WSL, Python 3.14.4, SQLite 3.46.1, assertions enabled. Native temporary stores, cooperative subprocess exit/reopen; no SIGKILL, no production subject or original historical ZIP equivalence.

| Check | Observation | Verdict |
|---|---|---|
| Delivered script | Both test functions PASS; the restart function reopens B3 and RC-01 in the same process | **SCOPED PASS**, two delivered functions, not a whole-system recovery suite |
| New process opens completed scenario | B3 row, I8 reserved/settled/released tuple and RC-01 `RECONCILED_CONFIRMED` are recovered | **SCOPED PASS**; earlier RC-01 terminal-value persistence gap corrected for this path |
| Failed settlement precedes REPAIR | Observer records RuntimeError before REPAIR transition | **SCOPED PASS**, in-process instrumentation rather than native authenticated journal |
| Fresh effects schema | PRAGMA shows a unique index on `idempotency_key` as well as operation ID | **SUPPORTED for this fresh schema**, no full concurrent response/effect semantics inferred |
| Old schema opened by new code | An effects database created by actual f1ada7b code is opened successfully by 9526353; PRAGMA still lists only the operation-ID unique index | **GAP / schema-dependent protection**. Existing databases are not migrated or rejected by this constructor |
| Completed operation replay | Running the same scenario again on its persisted files produces `RECONCILED_CONFIRMED → RESERVED`, then dispatch/UNKNOWN/REPAIR/terminal again; counts still report one row/settled flag | **GAP for safe recovery/replay**; durable last-state storage does not enforce legal terminal transitions or immutable history. This observation does not establish a second provider effect |
| Signing lifecycle | Stored receipt key ID differs from newly constructed provider key; sequence starts at zero | **OPEN**, historical verification material/epoch and sequence lifecycle still absent from delivered export |
| Equal key/request, second operation | Returns first operation's receipt; one effects row | **ALIAS CONTRACT OPEN**, no observed double effect; direct operation matching remains incompatible without an evidenced mapping or refusal |

Raw commands, source digests, environment, exit codes, native outputs and observer events are in [results/review.json](results/review.json) and adjacent stdout logs. All seven subprocess stderr streams were empty. Test counts are not combined with the separate 139-test W4 consumer suite. This reproduction does not invoke the W4 native bundle verifier or establish native differential agreement.

## Priority follow-up

- **P0 before claiming safe restart/replay:** Agent 1 should enforce documented legal transitions and provide a recovery entry point that resumes the persisted state. A terminal operation must not silently re-enter reservation/dispatch without an explicitly justified new operation/contract. Retain versioned causal evidence; last-state overwrite alone does not provide it.
- **P0 for any upgrade of existing laboratory stores:** migrate/validate the actual idempotency schema, or refuse unsupported schemas. If this version supports fresh stores only, declare that restriction and make the constructor reject legacy ones. Same source SHA with a different preexisting schema is a different assurance condition. W3 remains responsible for concurrency and bypass attacks.
- **Before native proof acceptance:** define key/epoch/history and original signed-byte export; define same-key/same-request operation alias semantics and five-identifier authorization/dispatch links. Preserve G4-A's execution restrictions and independently establish native I8 authority convergence in W2.2.

Agent 0 owns architectural convergence and the broad PR/base review: #85 targets main and includes inherited G4-A/G3 changes beyond the three-file increment examined here. Agent 1 owns fixes and Draft status. W4 did not modify #85 or promote a gate; Agent C retains B2 custody.

## Reproduction

Supply writable isolated source snapshots of the four files listed in `source-reference.json` for 9526353, plus the f1ada7b provider source for the legacy-schema check. No shared producer checkout should be used. Each current file's Git blob, and the prior provider blob, is checked before import. Source LF normalization restores fetched Git content on Windows; mismatches stop execution. With the pinned W4 cryptography dependency installed:

```sh
python -B reproduce.py --sources /snapshots/9526353/w2_integration --previous-sources /snapshots/f1ada7b/w2_integration --out /tmp/w4-w21b-results
```

Omitting `--previous-sources` skips the old-schema probe; it must not be described as having run. The harness imports real delivered modules and observes their calls, rather than patching their state machine, manufacturing a CEB or re-signing evidence. It records Python trace return events without interpreting exception unwind as settlement success.

**W2.1b PARTIAL / COMPLETED-STATE PERSISTENCE SCOPED PASS / INTEGRATED REPLAY NOT RUN / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.**
