# RFC-3 §6 — Multi-TAU Composition Simulator

This directory contains a readable local reference implementation of the
strategy dispatch and conflict-resolution logic described in RFC-3 §6:
conflict classes C1–C4, Priority-Enforce, Serialize, Pareto-Restore,
Escalate, Fail-Closed Collectif, and precedence for an expired or ambiguous
composition decision window. The assertion suite is in `tests.py`.

This is a scenario-level reference simulator for RFC-3 §6 composition, not
a production enforcement component and not the RFC-4 S1–S6 conformance
campaign. GitHub Actions runs the assertion suite in `tests.py`; the current
suite contains 17 unit tests. The latest recorded successful run is linked
from the repository's Actions workflow.

The current model deliberately has important limits: `tau_k_seconds` is
provided as an input and is not derived or attested by the simulator; LCR
aggregation uses a simple unweighted mean; progressive unblocking is a
placeholder, not runtime behavior; and `print()` output is not a structured
audit log. Passing tests establishes only that these tested scenarios match
the simulator's current behavior. It does not establish production safety,
concurrency correctness, exhaustive formal conformance, or empirical
effectiveness. Run locally from the repository root with
`python -m unittest composition.tests -v`.

Last verified: 2026-10-09 (17 unit tests; GitHub Actions)
