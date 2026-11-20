# W4 partial review of W2.1 — f1ada7b

Producer: `skiredj-prog/tenir_governance`, full SHA **`f1ada7b78d9f4c13656efc7f9f8c5a165394a9fb`**, parent `02ea1d3bcf5c6fca8e4de6bd7bf5c69cb63f4413`. Four imported source files are identified by their Git blob hashes in [source-reference.json](source-reference.json). Source snapshots were checked against those hashes before execution. The head-branch PR lookup returned no W2 PR at inspection.

This advances W4 from static preparation to **partial execution of the delivered native reconstructed LAB components**. It is not replay of an integrated native G4-A/I8 deployment, a CEB-01 acceptance, a W3 attack campaign or an external review of this author's W4 code. The producer still labels its B3/I8 fixtures reconstructed.

## Executed and observed

Linux WSL / Python 3.14.4 / SQLite 3.46.1, assertions enabled. Producer statements were neither patched nor replaced. Isolated temporary SQLite files were used; no producer branch, implementation or existing evidence bundle was changed.

| Claim / check | Evidence from this reproduction | Verdict and scope |
|---|---|---|
| Delivered tests | `test_w2_1.py` executes two functions; both print PASS and exit 0 | **PASS**, for the two delivered functions only. Do not label this three separate test cases or an E2E suite. |
| Restart test strength | Its `test_restart_persistence()` reopens only B3 in the same process after a completed scenario | **LIMITED**. It is not process crash/recovery, RC-01 reload or independent I8 write-count verification. |
| B3 file persistence | A scenario subprocess exits; a distinct subprocess reopens the same provider file and finds one effect row | **SCOPED PASS**, cooperative process-exit/reopen only. |
| I8 file persistence | The second subprocess reads operation `w4-restart-op`, reserved 100, settled 1, released 0 | **SCOPED PASS**, persistence of this local row/flag only; not proof of native single authority or exactly one physical/external effect. |
| Different request under the same idempotency key | Delivered conflict test runs and rejects the second request | **SCOPED PASS**, sequential path tested. Cross-operation races and privileged writers remain W3 work. |
| Failed settle before REPAIR | An unmodified scenario observed with Python's trace hook emits the settle exception before the REPAIR transition call | **SCOPED PASS**, observed call order. Observer events are not an authenticated durable producer journal. Raw Python return events include exception unwind and are not settlement-success evidence. |
| RC-01 restoration | The new process constructs `RC01Lab()` and observes `{}`; its constructor has no persistence input | **GAP / W2.1 INCOMPLETE**. RC-01 remains a dictionary in [lab_s1_bridge.py:22](https://github.com/skiredj-prog/tenir_governance/blob/f1ada7b78d9f4c13656efc7f9f8c5a165394a9fb/w2_integration/lab_s1_bridge.py#L22). |
| Receipt-key / sequence lifecycle | Reload returns the old stored receipt key ID, while the new constructor has a different key ID and sequence 0 | **GAP for continuity evidence**. This does not prove the old signature invalid. No persisted key history/epoch or independently held historical-key reference is delivered by these modules. |
| Equal request/key under another operation | Native provider returns the first operation's receipt for `alias-second-op`; database still has one row | **BINDING CONTRACT REQUIRED**, not an observed double effect. Exact W4 operation matching cannot treat this as a receipt for the second operation without a reviewed, evidenced alias relation or explicit producer refusal. |

See original raw stdout under `results/` and [review.json](results/review.json), including commands, exit codes, source digests, environment, native summary, observer events and restart values. All four subprocess stderr streams were empty. These local results are distinct from the 139 W4 fixture/unit tests and must not be added to them as a single assurance count.

## Required follow-up

1. **P0 before claiming W2.1 complete — Agent 1:** persist/reload RC-01 and its causal evidence; test re-entry in an actual new process, including the unresolved REPAIR window. Retain raw commands/results. Current cooperative completed-scenario reopen does not demonstrate SIGKILL recovery.
2. **Before native receipt/checkpoint acceptance — Agent 1 / Agent 0:** define the durable key/epoch/sequence lifecycle and export original signed message/signature plus historical verification material. Controlled rotation is possible; no requirement for one permanent key is imposed by this review.
3. **Before cross-operation proof import — Agent 1 / Agent 0:** specify whether same-key/same-request operations are aliases of one logical operation or must be refused, and supply authenticated/correlated evidence for the chosen semantics. Do not alter W4 expected operation IDs to hide the mismatch.
4. **Agent 2:** assess concurrency, changed request/key combinations, same-UID and privileged SQL on the pertinent SHA. This review does not absorb that campaign or infer its results from a sequential test.

W2.2 still requires the approved experimental G4-A boundary and native I8 authority convergence. A receipt with `execution_authorized=false` cannot be converted into dispatch authority. W2.3 still requires integrated subject identity/topology/deployment digest, actual crash/recovery and CEB-01. Five-identifier and causal mapping gaps from the earlier review are not closed by file-backed SQLite.

## Reproduction

Provide an isolated directory containing the four exact producer files from this SHA (not a later branch head), as listed in `source-reference.json`. No producer sources are vendored in this W4 package. The harness checks each Git blob before import; mismatches stop the run. Install the W4 pinned cryptography dependency in an isolated Linux Python environment.

```sh
python -B reproduce.py --sources /path/to/exact-snapshot/w2_integration --out /tmp/w4-w21-results
```

The harness runs the delivered script, a traced native scenario, a separate-process reopen and a sequential output-binding probe. The observer does not reconstruct a CEB, re-sign a receipt, manufacture missing journal bindings or substitute a model for the producer. It restores LF newlines when materializing a Windows source snapshot and validates exact Git blob content before import. Use a writable isolated snapshot, not a shared producer checkout.

**W2.1 PARTIAL / W4 PARTIAL COMPONENT REPRODUCTION COMPLETED / INTEGRATED REPLAY NOT RUN / INTEGRATION LOCK HOLD / E2E HOLD / PRODUCTION HOLD.**
