# Glossary

`glossary-v1.yaml` names each term shared by manuscript v7.2, the frozen RFCs
and this suite once, with its source and its known clashes. It is a versioned
contract: RFC revisions, vectors, CLAIMS and the projection layer cite a term by
its `GL-` id. Status: draft (v1.0.0), not in force until ratified.

Rules, in short: the published manuscript is never edited (its reading notes
are in [`../manuscript/ERRATA-v7.2.md`](../manuscript/ERRATA-v7.2.md)); frozen
RFC terms keep their RFC sense; historical logs keep their old identifiers and
are read through `aliases`.

| Term | Canonical meaning | Clash |
|---|---|---|
| `I1`–`I8` | Manuscript §4.5a invariants | Suite used `I8` for budget conservation until catalogue v1.1.0, now `BUD` |
| `τ_K` | HOLD resolution window (RFC-0 §6, RFC-5 §1, RN-001 §2a) | v7.2 §2.2, §4.4, §6.1, §7.1 write `τ_K` for the receipt window |
| `τ_R` | Receipt qualification window, AWAITING → UNKNOWN | New name; ERR-7.2-01 |
| bound of an authorization | Passing it: no effect under or attributed to that authorization; a fresh authorization only as a declared policy (RFC-4 v0.3 §2.1) | CT-R4-004a |
| bound of a held attempt | Reaching it: pre-declared disposition, refusal by default, terminal for that attempt identity (RFC-4 v0.3 §2.2, RFC-0 §6) | CT-R4-004b; v0.2 CT-R4-004 mixed the two objects |
| `CONFIRMED_NONEXECUTION`, `UNKNOWN` | Recorded state, by what the evidence establishes: not executed (never dispatched, or dispatched with a qualified rejection observed or a qualified attestation) / not established, reconciliation required | Adds to the block, never replaces it |
| `FAILED` (and other σ labels) | Runtime label, not canonical (v6.3 as cited by the author); mapped before reporting | v7.2 and T7/T8 use it as a state (ERR-7.2-05); T7 (dispatch + verified attestation) maps to CONFIRMED_NONEXECUTION |
| `RESOLVED`, `PENDING`, `AWAITING`, `ESCALATED` | Runtime labels, mapped by evidence: CONFIRMED_EXECUTION (name to confirm against v6.3) / no record while open, then by evidence / UNKNOWN / UNKNOWN | Decided 2026-11-19 |
| verdict age, freshness threshold | Withdrawn as a rule (RFC-4 v0.3 §4) | RN-001 §2b "epistemic input" reading |
| `CT-R4-005` | Suite vector: governance state changes between verdict and commit; outcome per RN-001 §4 | RFC-4 §2.2 says HARD_VETO, RFC-4 §5.2 says REJECT; v7.2 §10.1 uses the id for the S11 commit binding (ERR-7.2-02) |
| T6, T7, T8 | Lifecycle transitions of `tenir-conformance-s1-g1@8bc0e5e` | v7.2 names only T7; suite citations of "v7.2 §4.4, T6/T8" are wrong |
| `PASS` | Disposition (RFC-0 §4) or test outcome (CLAIMS) | Qualify as `disposition PASS` / `outcome PASS` |
| REG | Open, independent standard | v7.2 §3 calls it a TENIR concern (ERR-7.2-03) |
| `E1`, `E2` | `EXP-` manuscript experiments, `EXT-` exteriority registry | Same letters, different objects |

`tests/test_glossary.py` checks the file, its links to the errata, and the
guard patterns: an ambiguous use outside the allowed and pending files fails,
and a pending file that no longer matches fails too.

Pending renames in `runner.py`, `vectors/`, `VECTORS.md` and the TENIR-Gov
port were not made in v0.7.0; they wait for the next suite revision.
