# Sprint 1 — W4.3/W4.4 correction candidate

Review date: 2026-10-28. Status: **LOCAL REVIEW CANDIDATE / CI NOT RUN FOR THIS CHANGE / W2 PENDING / E2E HOLD**.

## Basis and branch choice

This local proposal starts from [REG PR #59](https://github.com/skiredj-prog/reg-conformance/pull/59), full SHA `6567ee6efe1a2f1b91a1eac5ee62694cd9dd4ce1`, on branch `draft/proof01-sprint1-w4-hardening` in an isolated clone. #59 is selected for its explicit artifact inventory, refusal to overwrite an output and documentary-only report. [#58](https://github.com/skiredj-prog/reg-conformance/pull/58) remains a separate candidate; it is not merged or silently superseded on GitHub. Its additional CEB diagnostics can be reviewed separately when native interfaces are available. No native compatibility is inferred from either branch.

The sprint 0 packet and normative PR #50 are unchanged. The user's peer-review verdict allows development but does not validate sprint 0 completely or authorize E2E assurance. Peer review confirmed the W4.4 pattern statically; it did not independently inspect the local sprint 0 reproductions. This proposal supplies code and Linux execution evidence for a new review.

## Changes and why

| Finding | Candidate correction | Verification |
|---|---|---|
| S0-F01: positive differential vector refuted | Return independently reconstructed capacity together with reserved/committed balances | Positive trace plus modified/missing capacity, state and event-count negatives |
| S0-F05: duplicate discovery | Import the fixture module instead of exposing its TestCase alias | Eight duplicate executions removed, no assertion removed |
| S0-F02: verified bytes differ from ZIP bytes | Capture once into immutable bytes, verify those bytes, serialize the same map | Actual concurrent writer changes source receipt/manifest after validation; exported original bytes remain valid |
| Mutation during capture | Captured manifest digests must match captured artifacts | Mutation between manifest and receipt capture rejected before output |
| Untrusted paths and archives | Descriptor-relative POSIX capture, no-follow paths, bounded reads, no ZIP extraction | Parent/leaf links, FIFO, path aliases, duplicate JSON keys/ZIP entries, extra evidence, size/count negatives |
| Misleading final report | Replay final ZIP and compare recomputed documentary report | Altered ZIP receipt or promoted report refused |
| CI checkout ambiguity | Workflow explicitly checks out and checks PR head SHA, records environment and preserves raw test log | Workflow prepared; no new remote run is claimed |

`verify_snapshot` shares the inventory validation with the existing path verifier. The independent state oracle still does not call the semantic replay engine. No assurance escalation, synthetic-to-native mapping or signature rewriting is added.

## Local Linux evidence

Baseline #59 on Linux WSL: 38 executions, 37 successes and the one expected positive-vector failure. Eight executions are duplicates. The first corrected run: **50 unique tests, 50 successes, zero failures/errors/skips**, Python 3.14.4, cryptography 46.0.5. The review packet outside this checkout records the final source commit, pinned dependency rerun and raw logs separately. Do not add baseline and corrected execution counts.

Count: `38 - 8 duplicates + 3 differential negatives + 17 snapshot/archive tests = 50`.

The concurrent tests use two threads and explicit events to force a writer between verification and packaging. They are deterministic interleaving tests, not a stress campaign or proof against a privileged host adversary. Production remains HOLD. SHA256 checks and two successful serializations on identical inputs are not independent attestations.

## Portability and limits

Packaging now requires POSIX descriptor APIs and refuses unsupported capture platforms; this is intentional rather than falling back to a path-check/read race. Final ZIP replay remains portable. Resource limits and the trusted output-directory assumption are detailed in `W44_AUDITOR_KIT.md`.

No B3 native adapter, RC-01 state interpretation, provider effect, I8 execution or independent witness has been substituted with a mock. The archive report remains inventory-only. Authenticity, capture completeness, deployment identity and native semantics are separate open gates.

## Review and promotion gates

1. Review this diff against #59, not against main: the existing W4 stack remains inherited.
2. Reproduce `python -B -m unittest discover -s proof01_w4/tests -v` on the frozen candidate SHA under Linux.
3. Independently inspect the concurrent probes and replay a captured ZIP.
4. Obtain a remote CI run on the actual candidate SHA before claiming GitHub CI closure.
5. The W4 owner decides how to integrate this local proposal and reconcile #58/#59. No source-lock promotion is implicit.
6. W2 identity and native evidence must be supplied under existing [TENIR issue #81](https://github.com/skiredj-prog/tenir_governance/issues/81); see `W2_ACCEPTANCE.md`. E2E, production and ratification remain HOLD.
