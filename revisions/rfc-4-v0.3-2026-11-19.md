---
revision: RFC-4 v0.3
title: Commit & Execution Proof — bounds on authorizations and on held attempts
date: 2026-11-19
status: Ratified by the author on 2026-11-19, amended by the author on 2026-11-20; in force from reg-conformance v0.7.0; outside the frozen baseline
amendments:
  - "2026-11-20, author's decision (02:20 UTC): a qualified rejection observed after dispatch establishes non-execution, as in manuscript v7.2 §4.3 and §4.4 (§2.2, §2.3)"
revises: reg-standards-baseline/rfc/rfc-4.md v0.2 (Frozen, 2026-10-02), not edited
supersedes_clauses:
  - "RFC-4 v0.2 §5.2 item 4 (CT-R4-004): superseded_by CT-R4-004a, CT-R4-004b"
  - "RFC-4 v0.2 §2.2, last sentence (HARD_VETO on drift): superseded_by §3 of this revision (RN-001 §4)"
amends_notes:
  - "RN-001 §2b and §3: the reading 'elapsed time is an epistemic input / forces a readjudication' is withdrawn as a rule (§4 of this revision)"
---

# RFC-4 v0.3 — revision of 19 November 2026

## 0. Status and how to read this text

RFC-4 v0.2 is frozen. It stays in `reg-standards-baseline/` unchanged, and the
results already recorded against it (including the reference kernel's PASS on
CT-R4-004) keep referring to that stable text.

This revision is dated and sits outside the baseline. It states which v0.2
clauses it supersedes (front matter); every other v0.2 clause stands as
written. The author ratified it on 19 November 2026 and amended §2.2 and §2.3
on 20 November 2026, before the release: a qualified rejection observed after
dispatch also establishes non-execution (§2.3). It is in force from
reg-conformance v0.7.0 and stays outside the frozen baseline: RFC-4 v0.2 is not
edited, and each superseded clause is named, with what supersedes it, in the
front matter. Whether it later enters a new frozen version of the baseline is a
separate decision.

## 1. Which object carries the bound

The confusion this revision removes: v0.2 CT-R4-004 speaks of the window of an
**admission** (the grant's `valid_until`). Scenarios built on it were later
read as a **held attempt** that expired (a `HOLD` left past τ_K). These are two
objects with two consequences. The rewrite makes them two clauses and two
vectors, so the two cannot be read as one.

| Object that carries the bound | What the bound extinguishes | Consequence when the bound is passed | Clause | Vector |
|---|---|---|---|---|
| The **authorization** (grant, approval, permit) | The right to act under that authorization | No effect under the expired authorization. A fresh authorization may then be obtained: that is a deployment policy, not a defect of REG. | §2.1 | CT-R4-004a |
| The **held attempt** (`HOLD`, escalation) | The attempt itself | Pre-declared disposition; refusal by default, terminal for that attempt identity. A later effect requires a new attempt identity. | §2.2 | CT-R4-004b (REG-STATE-024; RFC-0 §6) |

REG fixes no duration. Each bound is the one the deployment declares.

## 2. Normative clauses

### 2.1 Validity of the authority at the time of the effect

An effect MUST NOT be produced under an authorization whose declared bound has
passed at the moment the effect would take place. The bound is declared by the
deployment; REG fixes no duration. The observable is: the identity of the
action, the authorization under which it was attempted, and whether an effect
was produced. Any mechanism that establishes validity at that moment (window,
revocation, policy epoch, suspension) satisfies the clause.

If the deployment's declared policy allows a fresh authorization after expiry,
an effect MAY then take place; it MUST be attributed to the new authorization,
with its own identity and its own evidence. No effect may be attributed to the
expired authorization.

A fresh authorization is legitimate only as a declared policy for this object,
and only if all four hold:

1. it is declared explicitly, not implied;
2. it is a fresh evaluation against the current state, not a laundering of the
   expired approval;
3. the effect, if any, is attributed to the new authorization, with its own
   identity and evidence;
4. the effect is never attributed to the expired authorization.

It is not a global rule. In particular it does not apply to a held attempt
(§2.2): there, RFC-0 §6 makes refusal the default, and readjudication is not an
automatic exit.

### 2.2 Disposition of a held attempt at its declared bound

When a held attempt reaches the bound declared for it, the deployment's
pre-declared disposition applies. The default disposition is refusal, terminal
for that attempt identity. A later effect requires a new attempt identity. The
transition MUST be recorded with the bound, the disposition applied and the
resulting state, expressed in the canonical vocabulary.

The record MUST distinguish what the available evidence establishes, not
what the dispatch history suggests. Non-execution is established when the
attempt was never dispatched, or when it was dispatched and either a
qualified rejection of that dispatch was observed or a qualified, verified
non-execution attestation exists: the attempt is then recorded as
established non-execution. When dispatch was possible and the evidence does
not establish the outcome (no qualified rejection observed, and the
attestation absent, contradictory or not qualified), the attempt is recorded
as unknown, with reconciliation required.
Closing the hold does not establish what happened outside.

A bound that the deployment declares but that the runtime cannot receive or
apply counts as not applied. A late approval, resolution or exit authorization
arriving after the bound does not reopen the attempt.

### 2.3 The epistemic axis is orthogonal

Every expiry, of either object, also produces a record of what is known. The
recorded state follows what the available evidence establishes, not the
history of the dispatch. `CONFIRMED_NONEXECUTION` means that the available
evidence establishes that the outcome was not executed (canonical vocabulary,
as cited by the author).

| What the available evidence establishes at expiry | Recorded state |
|---|---|
| Non-execution: the attempt was never dispatched; or it was dispatched and a qualified rejection of that dispatch was observed, or a qualified, verified non-execution attestation exists | `CONFIRMED_NONEXECUTION` |
| Dispatch was possible and the outcome is not established: no qualified rejection observed, and the attestation absent, contradictory or not qualified | `UNKNOWN`, reconciliation required |

Example: dispatch occurred, but a qualified attestation establishes
non-execution: `CONFIRMED_NONEXECUTION`. A verified attestation completes the
reconciliation; the dispatch does not keep the attempt `UNKNOWN`.

A qualified rejection is one that manuscript v7.2 §4.4 records as `dispatch,
rejection observed`: the runtime observed the rejection of that dispatch, and
the outcome is qualified with no effect recorded. Manuscript v7.2 §4.3 lets
`NEA` hold on matching evidence: an observed rejection, a kernel veto before
dispatch (one case of never dispatched), or an attestation accepted under
`non_execution_attested`.

A qualified, verified non-execution attestation is one that meets all four
conditions manuscript v7.2 §4.4 sets for `non_execution_attested`: the
attempt is on a path eligible for T7 or reconcile-`FAILED` (non-terminal or
`UNKNOWN`); qualifying evidence is bound to the attempt (`id`, `LEI`,
`nonce`) and fresh; the observed effect count is zero; and a signed
attestation is accepted under the path's verification rules. As there, it
establishes neither that the attestation is true of the external world nor
that the caller-supplied verification key is legitimate: those remain the
manuscript's assumption A and its trust-root obligation (S7/D11).

This record adds to the blocking of §2.1 and §2.2; it never replaces it.
"Epistemic input" and "barrier" are not two options: every expiry is both. The
question each clause answers is which constraint applies, according to which
object carries the bound.

`FAILED` is not a term of the canonical vocabulary (v6.3, as cited by the
author). It is a runtime label and MUST be mapped by the rule above: to
`CONFIRMED_NONEXECUTION` when the evidence establishes non-execution (never
dispatched; dispatched with a qualified rejection observed, as in the
manuscript v7.2 row `dispatch, rejection observed`; or dispatched with a
qualified, verified non-execution attestation, as in transition T7), to
`UNKNOWN` with reconciliation otherwise. A report that shows `FAILED`
without this mapping does not establish the recorded state of §2.2.

## 3. State drift at commit (carries RN-001 §4)

v0.2 §2.2 ends: "the binding mechanism MUST detect this and trigger
HARD_VETO". This revision keeps the detection and replaces the required
label by the required outcome:

> No effect under a changed governance state, and the reported state class:
> either a terminal refusal, or a suspension with a declared resumption
> condition.

`HARD_VETO` is one terminal refusal; REG does not impose it. When the runtime
suspends, the Suspension Receipt carries the resumption condition. CT-R4-005
and C3 follow this outcome.

## 4. What this revision withdraws

RN-001 §2b and §3 read "any other elapsed time … is an epistemic input to
readjudication" and replaced CT-R4-004 by three properties (CT-R4-014 no
dispatch on a stale verdict without readjudication, CT-R4-015 age never
improves a disposition, CT-R4-016 a fail-safe bound refuses alone). As a
single rule, "expiry forces a readjudication" would make a late approval
followed by readjudication and an effect conformant, which contradicts the
RFC-0 §6 default for a `HOLD`. This revision withdraws that reading:

- CT-R4-014 and CT-R4-015: `superseded_by` CT-R4-004a. Their readjudication
  framing is not the rule; §2.1 admits a fresh authorization only as a declared
  policy under its four conditions.
- CT-R4-016: `superseded_by` CT-R4-004b, which states the same refusal with
  the attempt identity and the record of §2.2–2.3.

RN-001 §1 (FLAG and admission), §2a (fail-safe bound) and §4 (state drift)
are unaffected. The three identifiers stay registered; none had a probe or a
recorded result.

## 5. Vectors

| Vector | Clause | Input | Expected |
|---|---|---|---|
| CT-R4-004 | v0.2 §5.2 item 4 | `valid_until` passed before commit | REJECT / EVALUATION_EXPIRED. Kept with its text and results; `superseded_by` CT-R4-004a, CT-R4-004b. |
| CT-R4-004a | §2.1 | Commit under an authorization whose declared bound has passed | No effect attributed to the expired authorization. Any refusal mechanism satisfies the clause; an effect under that authorization fails. An effect under a fresh authorization is out of the probe and is checked against §2.1 conditions 1 to 4. |
| CT-R4-004b | §2.2, §2.3; REG-STATE-024; RFC-0 §6 | Held attempt left past its declared bound, then any advance (commit, resolve, approval, dispatch) under the same attempt identity | No effect under that identity; pre-declared disposition (default refusal) recorded with the bound and the resulting state in the canonical vocabulary. A suspension that merely continues is not a terminal refusal. |

## 6. Mapping to STANAIC STA-EA-02 (a mapping, not a design question)

REG admits both deployment models: a bounded grant, where the authorization
carries the bound (§2.1), and a fresh adjudication at each crossing, that is,
a fresh authorization in the sense of §2.1, admitted as a declared policy
under its four conditions. Whether STANAIC STA-EA-02 is compatible with one
or both of them, and which it prefers, is for its author to say; a written
answer has been announced. That answer maps STA-EA-02 onto §2.1 and §2.2. It
does not change them, and no mapping is made here before it.

## 7. Application to TENIR-Gov 5.7.0 (informative, as measured)

This is not a conformance statement. It records that this revision does not
erase the gap reported for 5.7.0.

- **CT-R4-004b.** Characterization probe of 18 November (tenir_governance issue
  #140, cases C2b and C2c): with a τ_K of 60 s exhausted, `resolve_hold` with
  sufficient evidence, then `dispatch`, produced one effect; after
  `escalate_hold`, a late `authorize_exit(approve=True)`, then `resolve_hold`
  and `dispatch`, produced one effect. The same attempt identity advanced past
  its bound: **FAIL** under §2.2. Limit of the probe: τ_K was set by replacing
  the in-memory `HoldRecord`, because no public path lets a policy supply τ_K
  to a governor-created `HOLD` (C2a). Under §2.2, a bound that is declared but
  that the runtime cannot receive or apply counts as not applied, so C2a does
  not make the clause vacuous.
- **CT-R4-004a.** On the default governor path an admitted operation carries
  no validity window (`harness/ports/tenir_gov.py`, `STALE_GRANT` not
  declared). The vector cannot be exercised: not observed, not PASS.
- The withdrawn reading would have changed the first result: "late approval →
  readjudication → effect" would have counted as conformant. Under this
  revision it does not.
