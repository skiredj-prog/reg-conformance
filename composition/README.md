# RFC-3 §6 — Multi-TAU Composition Simulator

This directory contains a readable local reference implementation of the
strategy dispatch and conflict-resolution logic described in RFC-3 §6:
conflict classes C1–C4, Priority-Enforce, Serialize, Pareto-Restore,
Escalate, Fail-Closed Collectif, and precedence for an expired or ambiguous
composition decision window. The assertion suite is in `tests.py`.

This is a local simulator implementing RFC-3 §6 composition. It validates
the strategy dispatch and conflict resolution logic of the specification.
It is not a conformance suite. It has no CI, no evidence artifacts, and no
frozen G0 specification. It is published as a readable reference
implementation, not as an empirical claim.

The current model deliberately has important limits: `tau_k_seconds` is
provided as an input and is not derived by the simulator; LCR aggregation
uses a simple unweighted mean; progressive unblocking is a placeholder,
not runtime behavior; and `print()` output is not a structured audit log.
The local tests cover ten assertion scenarios, not production safety,
concurrency, or empirical effectiveness. Run locally from the repository
root with `python -m unittest composition.tests -v`.

Last verified: 2026-10-09
