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
| verdict age, freshness threshold | RN-001 §2b, §3; no symbol | — |
| `CT-R4-005` | Suite vector: governance state changes between verdict and commit; outcome per RN-001 §4 | RFC-4 §2.2 says HARD_VETO, RFC-4 §5.2 says REJECT; v7.2 §10.1 uses the id for the S11 commit binding (ERR-7.2-02) |
| T6, T7, T8 | Lifecycle transitions of `tenir-conformance-s1-g1@8bc0e5e` | v7.2 names only T7; suite citations of "v7.2 §4.4, T6/T8" are wrong |
| `PASS` | Disposition (RFC-0 §4) or test outcome (CLAIMS) | Qualify as `disposition PASS` / `outcome PASS` |
| REG | Open, independent standard | v7.2 §3 calls it a TENIR concern (ERR-7.2-03) |
| `E1`, `E2` | `EXP-` manuscript experiments, `EXT-` exteriority registry | Same letters, different objects |

`tests/test_glossary.py` checks the file, its links to the errata, and the
guard patterns: an ambiguous use outside the allowed and pending files fails,
and a pending file that no longer matches fails too.

Pending renames in `runner.py`, `vectors/` and `VECTORS.md` wait for PR #77,
which edits the same files.
