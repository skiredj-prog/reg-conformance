# Reading notes for manuscript v7.2 — vocabulary shared with the REG suite

Status: ratified by the author on 23 November 2026; in force for readers of
v7.2.

History: drafted 19 November 2026 (`7b6f45e`); amended 19–20 November 2026
(`f9711c0`, `e247e1e`, `858b716`, `7080d49`); revised 23 November 2026 after a
check of every item against the manuscript, the REG texts in force and the
code of the evaluated membrane (this text).

Applies to: *Governing the Unobserved*, manuscript v7.2, 15 November 2026.
Zenodo version DOI 10.5281/zenodo.24249646, concept DOI
10.5281/zenodo.23270928; GitHub Release `7.2`, commit `98bf685`. Line numbers
refer to `manuscript/v7.2.md` at that commit. That file is byte-identical to
`v7.2-revised.md` in the Zenodo record (88,775 bytes, MD5
`db24afffd1333364d1a29b407eda8c39`; Zenodo metadata read on 23 November 2026).
In the PDF, use the section numbers.

This note does not edit the manuscript. It changes no result, no count and no
claim of v7.2. It records six items where v7.2 and REG material use one word
for different objects, and says how to read them. Here REG means the open,
independent standard specified by the RFCs in `reg-standards-baseline/` and
their dated revisions, and tested by this suite; the membrane evaluated in
v7.2 and TENIR-Gov are implementations that can be tested against it. A later
manuscript version may adopt these readings in its own text.

Each item gives its definitions and their normative source. Glossary ids
(`GL-…`, `glossary/glossary-v1.yaml`, draft) are cross-references only: this
note does not depend on the glossary being ratified.

Each item states what was checked. *Verified* means read in the file at the
revision named; *inferred* means reasoned from the text.

## ERR-7.2-01 — τ_K names two different bounds

**Where.** l.86 (§2.2, fault S2); l.229–230 (§4.4, rows `admit and await` and
`timeout`); l.383 (§6.1, "clock advance by τ_K"); l.485 (§7.1, S2).

**Text.** In these places τ_K is the time an admitted attempt waits in
`AWAITING` for a qualifying receipt; at t ≥ τ_K the attempt becomes `UNKNOWN`.

**Reading.** Read τ_K at these four places as **τ_R, the receipt qualification
window** (`GL-TAU-R`). In REG, τ_K is the organizational veto window, the bound
on human resolution of a `HOLD` (RFC-0 §6, RFC-5 §1, RN-001 §2a; `GL-TAU-K`).
The two bounds have different sources and different consequences: τ_R expiry
yields `UNKNOWN` (§4.4, row `timeout`); τ_K exhaustion applies the pre-declared
exhaustion policy, refusal by default (RFC-0 §6; RFC-4 v0.3 §2.2). (verified)

**Names in the code.** The membrane and the harnesses behind §§6–8 use the same
name for τ_R. In `tenir-conformance-s1-g1` at `d42499b`, the parameter
`tau_k_ms` sets the deadline of `AWAITING_QUALIFICATION`, after which
`check_qualification_timeouts` moves the attempt to `UNKNOWN`
(`src/tenir_conformance/membrane/membrane.py` l.754–772); the explorer's event
`advance(tau_K)` advances the clock by that value
(`experiments/e1_e2/e2_explore.py` l.154–159; the same event at `cf1b1ea`);
`e1_baseline.py` passes the same value (l.103). Read these names as τ_R too.
The code and the replay archive keep them. (verified)

**Unaffected.** §3.1 (τ_K as a component of Ω) and §9 ("τ_K is a supplied
input" to the composition simulator) use τ_K in the REG sense. §9 is verified
against `composition/simulator.py` (`tau_k_seconds`). §3.1 is inferred: Ω is
not exercised in the paper and is not defined in the frozen RFCs.

**Effect on results.** None. The S2 scenario, the E1 enumeration (§8) and the
E2 explorations (§6) use one bound, τ_R (5,000 ms in both harnesses). `HOLD`
appears there only as the client projection of §4.2, with no resolution
window. (verified in `e1_baseline.py` and `e2_explore.py` at `d42499b`)

## ERR-7.2-02 — `CT-R4-005` is cited for a check that does not test it

**Where.** l.10 (changelog 7.1, item 5); l.61 (§1.1, traceability list);
l.647 (§10.1).

**Text.** "`CT-R4-005` (state at verdict). The implemented check binds the
transition and payload hashes at verdict and at commit. Drift of the external
environment between verdict and commit is not captured. This limit is
declared, not simulated."

**What CT-R4-005 is.** A vector of the REG suite, "Commit-State Binding / Race
Detection": the state at commit materially differs from the state captured at
verdict (RFC-4 v0.2 §2.2 and §5.2, item 5). The suite instantiates it as a
change of governance state, `policy_epoch`, between verdict and commit
(`vectors/commit.yaml`, at tag `7.2` and since; `GL-CT-R4-005`). The outcome
required from v0.7.0 is no effect under the changed state, with either a
terminal refusal or a suspension carrying a declared resumption condition
(RN-001 §4; RFC-4 v0.3 §3). The identifier appears in no revision of
`tenir-conformance-s1-g1` (git history of all branches searched), so at l.61 it
can only refer to this suite's vector. (verified)

**Reading.** The check that §10.1 describes is the S11 commit binding (§7.9;
`GL-MEM-COMMIT-BINDING`): the transition and the payload are bound at verdict
and at commit. That is an action and payload binding, the property of
`CT-R4-002`, and the membrane's own test of it carries that label
(`tests/test_g0_s11_transition.py`,
`test_ct_r4_002_grant_for_one_action_cannot_commit_another`, at `d42499b`). It
does not test CT-R4-005. Read l.647 as: "CT-R4-005 (state at verdict) is not
tested by the evaluated membrane. Its commit check binds the transition and
payload hashes at verdict and at commit (S11). A change of state between
verdict and commit is not captured. This limit is declared, not simulated."
Read l.10 and l.61 accordingly: they name a scope decision on the suite vector.
(verified; that `CT-R4-001` is the other close vector is inferred)

**Scope of the declared limit.** The limit is wider than l.647 writes. The
evaluated membrane captures neither drift of the external environment nor a
change of governance state between verdict and commit, which is the instance
the suite tests: it has no policy epoch and no state hash; its only epochs are
those of trust-root keys (`attestation.py`). (verified at `d42499b`)

**Effect on results.** None: no result of v7.2 rests on CT-R4-005. This item
replaces the reading of the 19–20 November draft, which took `CT-R4-005` in
§10.1 as a name for the S11 commit binding.

## ERR-7.2-03 — "REG" as a TENIR concern

**Where.** l.120 (§3): "TENIR separates four concerns: … an independent proof
lifecycle (REG) …".

**Reading.** REG is an open, independent standard. It standardizes the
execution boundary and its proof obligations, not the architecture that
implements them (RFC-0, Editorial Principle; `GL-REG`). It is not a component
of TENIR. Read l.120 without "(REG)": TENIR has an independent proof-lifecycle
concern; its implementations, like any other, can be tested against the
outcomes REG requires. (verified in RFC-0)

**Unaffected.** The companion "REG Core Protocol" working paper (l.114), and
the statements that the results are not production REG certification or
conformance (l.512, l.532, l.568) or certification against the suite (l.660),
use REG in the standard sense.

**Effect on results.** None.

## ERR-7.2-04 — I8 in suite and TENIR-Gov material

**Where.** §4.5a and §5.3 (I8, attempt-history permanence). No error in v7.2.

**Note for readers of the suite and of TENIR-Gov.** Up to catalogue v1.1.0
(tag `v0.6.2` included), the suite used `I8` for aggregate budget
conservation. From suite v0.7.0 (catalogue 1.2.0) it calls that invariant
`BUD` (`GL-INV-BUD`; `GL-INV-I8`). `I8` still means `BUD`, not the manuscript's
I8, in:

- `tenir_governance` up to 5.7.6: code, CHANGELOG and `.zenodo.json`
  (verified at `1881c90`);
- the evidence field `I8_maintained` (`specs/evidence-type-specs-v1.md`), kept
  under that name by the author's decision of 20 November 2026;
- `harness/ports/tenir_gov.py` ("membrane invariant I8"), which names the
  TENIR-Gov invariant;
- suite files and evidence logs written before v0.7.0.

No suite vector exercises the manuscript's I8 today. (verified at `33c6302`)

**Effect on results.** None.

## ERR-7.2-05 — `FAILED` and the other attempt labels are runtime labels

**Where.** `FAILED`: §1.1 (l.51); §4.0–§4.5a (l.152–281); §5 (l.307–367);
§6.1–§6.2 (l.385, l.443, l.449); §10.1 (l.641); Appendix A.2 (l.708). The other
labels of σ (§4.1): `RESOLVED`, `PENDING`, `AWAITING`, `UNKNOWN`, `ESCALATED`.

**Text.** v7.2 uses `FAILED`, with `RESOLVED`, `PENDING`, `AWAITING`,
`UNKNOWN` and `ESCALATED`, as states of its model.

**Reading.** These are labels of the modelled membrane and of its
implementation. `FAILED` is not a term of REG's canonical vocabulary, and a REG
report maps it before stating a recorded state (RFC-4 v0.3 §2.3, in force from
suite v0.7.0; `GL-RUNTIME-LABEL`, `GL-STATE-RECORDED`). The recorded state
follows what the available evidence establishes, not the dispatch history:

| v7.2 label and path | Recorded state in REG |
|---|---|
| `FAILED`, never dispatched (kernel veto before dispatch, §4.3, §10.1) | `CONFIRMED_NONEXECUTION` |
| `FAILED`, dispatched, qualified rejection observed (§4.4, `dispatch, rejection observed`) | `CONFIRMED_NONEXECUTION` |
| `FAILED`, dispatched, qualified and verified non-execution attestation (§4.4, `declare failed (T7)` and `reconcile, FAILED`, under the four conditions of `non_execution_attested`) | `CONFIRMED_NONEXECUTION` |
| Any label, dispatch possible, no qualified rejection observed, attestation absent, contradictory or not qualified | `UNKNOWN`, reconciliation required |

Each path of the paper's `NEA` predicate (§4.3) has a matching row: an
observed rejection, an accepted attestation, and a kernel veto before dispatch
(one case of "never dispatched"). The REG case "never dispatched" is wider: it
also covers, for example, a held attempt refused before any dispatch. The two
lists are not equivalent. Within the paper's own argument (§4–§5), `FAILED`
keeps the meaning the paper gives it, including the `NEA` condition.

The other labels follow the same rule (author's decisions of 19 November 2026):
`AWAITING` maps to `UNKNOWN`, with reconciliation required once τ_R has passed
without a qualifying receipt; `UNKNOWN` and `ESCALATED` map to `UNKNOWN`,
reconciliation required; `PENDING` has no recorded outcome while open, then
the state the evidence establishes; `RESOLVED`, reached only on a qualified
bound receipt or on bound fresh reconcile evidence (§4.4), is established
execution. REG's texts in force do not yet name established execution; the
draft glossary proposes `CONFIRMED_EXECUTION`.

**Example.** v7.2 reaches `FAILED` after a dispatch on a verified
non-execution attestation (§4.4, `declare failed (T7)` and `reconcile,
FAILED`). Dispatch occurred, but the qualified attestation establishes
non-execution: the recorded state is `CONFIRMED_NONEXECUTION` (author's
decision of 19 November 2026).

**Two limits of the mapping.** (1) The recorded state is relative to the
evidence, not to the world. In the adversarial runs (§5.4, Table 4), a false
attestation, correctly bound and signed by a trusted key, also maps to
`CONFIRMED_NONEXECUTION`. That is the U3 limitation (§4.0, Proposition 3); the
mapping does not remove it (RFC-4 v0.3 §2.3, assumption A). (verified)
(2) In the historical model of Table 1 (membrane `84e46d9`), a qualified
declaration carries no signed attestation (§4.0, §6.2). A `FAILED` reached that
way after a possible dispatch does not meet the conditions of a verified
attestation and maps to `UNKNOWN`. Table 1 reports no count of such states.
(inferred from RFC-4 v0.3 §2.3 and v7.2 §4.0)

**Effect on results.** None on the paper's results. A REG result quoted from
the paper's runs states its mapped state, or says that the label is unmapped.

## ERR-7.2-06 — "dispositions" in §1.1

**Where.** l.51 (§1.1): the membrane "produces the dispositions `PASS`, `HOLD`,
`QUARANTINE_LOCK`, and `FAILED` at the execution boundary".

**Reading.** In REG a disposition is one of `PASS`, `FLAG`, `HOLD`,
`HARD_VETO` (RFC-0 §4; also v7.2 §3.1, D(τ, Ω); `GL-DISPOSITION`). Of the four
words at l.51, `PASS` and `HOLD` are dispositions. `QUARANTINE_LOCK` is an
LEI-level guard (§4.0, l.142 and l.189; the quarantine set Q of §4.1).
`FAILED` is an attempt label (ERR-7.2-05). The evaluated membrane returns the
dispositions `PASS`, `HOLD` and `HARD_VETO`, the last on a kernel veto (§10.1;
enum `Disposition`, `membrane.py` l.47–50 at `d42499b`). Read l.51 as: the
membrane returns the dispositions `PASS`, `HOLD` and `HARD_VETO`, maintains the
LEI-level guard `QUARANTINE_LOCK`, and records attempt labels such as
`FAILED`. (verified)

**Effect on results.** None.

## Examined, not errata

- I2, permit single-use: same meaning in the suite (`GL-INV-I2`).
- §3.1, D(τ, Ω) ∈ {`PASS`, `FLAG`, `HOLD`, `HARD_VETO`}, and the client
  projection (`UNKNOWN`, `HOLD`) of §4.2: same meaning as RFC-0 §4.
- S1–S12 (`GL-SCENARIO-S`): the same campaign as in the companion repository.
  The campaign has no S9 (§7.1, l.492): it has eleven numbered scenarios, S1–S8
  and S10–S12, several with sub-cases (S1a–c, S12a–h). "Twelve scenarios" is a
  miscount.
- E1 and E2 (`GL-E-IDS`): in v7.2, E1 is the 53-sequence baseline comparison
  (§8) and E2 the bounded explicit-state exploration (§6).
- Hypothesis Lab outcomes `PASS`, `FAIL`, `VACUOUS`, `ANOMALY` (§7.11): defined
  in the paper, with inverted semantics for adversarial models. They are not
  REG test outcomes and are not reported as such.

## Not an erratum: transitions T6 and T8

v7.2 §4.4 names only T7 (`declare failed (T7)`). Suite vectors `CT-R4-011` and
`CT-R4-013` cite "Manuscript v7.2 §4.4, transition T6" and "transition T8"
(`vectors/core.yaml`, `runner.py`, `VECTORS.md`,
`lifecycle/register_core_lifecycle.py` at `33c6302`). The fault is in the suite
citations. T6 is this suite's own name (`LIFECYCLE_INTEGRATION.md`;
`lifecycle/attempt_state.py`) for the behaviour of the §4.4 row `receipt`, a
bound in-window receipt that resolves an awaiting attempt
(`lifecycle/t7_membrane_probe.py`); `tenir-conformance-s1-g1` does not use the
name at `d42499b`, at `8bc0e5e` or on its main. T7 and T8 are named in
`tenir-conformance-s1-g1` (membrane docstring "S1–S4 + T7/T8";
`tests/test_t7_t8_failed_retry.py`; at `d42499b` and `8bc0e5e`). The next suite
revision will cite those sources (`GL-LIFECYCLE-T`). Likewise, `CT-R4-013`
treats `retry_eligible` as an admission condition, as at revision `8bc0e5e`;
v7.2 §4.4 states that it is an audit annotation at `d42499b` and a condition
from `8bc0e5e` (l.244; `GL-RETRY-ELIGIBLE`). Both are correct for their
revision. The labels these transitions use (`RESOLVED`, `FAILED`) are runtime
labels; see ERR-7.2-05. (verified)

## Ratification

Ratified by the author on 23 November 2026; see the status line. The
manuscript, its Zenodo record and the tag `7.2` are not changed.
