---
note: RN-001
title: FLAG admission, elapsed time, and state drift at commit
status: Ratified by the author, 18 November 2026
applies_to: RFC-0 v0.x §4, §6; RFC-4 v0.2 §1.1, §2.2, §5.2
effect: Clarifies frozen texts. Enters RFC-0 and RFC-4 at their next revision (RFC-4 v0.3).
---

# RN-001: FLAG admission, elapsed time, and state drift at commit

The frozen RFCs stay as they are. This note records how four of their clauses
are read from now on, and the vector changes that follow. Where this note and
a frozen text differ, the frozen text is amended by this note at its next
revision.

## 1. FLAG and admission (RFC-0 §4)

RFC-0 §4 lets execution proceed on `FLAG` "only under an explicitly defined
additional condition or supervision". Two statements, kept separate:

**1a.** A `FLAG` that carries an explicit condition or supervision counts as an
admission when effects are counted. A test that needs an admitted action
accepts it.

**1b.** A `FLAG` that carries no condition does not satisfy RFC-0 §4. It is an
implementation gap. It is recorded as such and stays open after 1a: a test that
goes forward on it reports that the condition was not observed.

Reason: reading "FLAG = admission" without requiring the condition would amend
the standard to fit a runtime.

## 2. A fail-safe bound and elapsed time are different objects (RFC-0 §6, RFC-4 §1.1)

**2a. Fail-safe bound.** A bound that the versioned policy declares fail-safe
refuses alone when it is exhausted. τ_K, the bound on waiting for a human
resolution of a `HOLD`, is such a bound when the policy supplies it. It is
never invented by the implementation (RFC-0 §6). Its exhaustion applies the
pre-declared exhaustion policy wherever a held operation could advance, without
requiring a timer.

**2b. Elapsed time as an epistemic input.** Any other elapsed time, in
particular the age of an admission already rendered (`PASS` or `FLAG`), is an
input to a fresh adjudication. It composes with the other inputs and does not
refuse alone, unless the policy also declares it fail-safe.

Sentence for RFC-4 v0.3: *"A bound the policy declares fail-safe refuses alone;
any other elapsed time is an epistemic input to readjudication."*

## 3. Replacement of CT-R4-004 (RFC-4 §5.2)

CT-R4-004 ("`valid_until` passed before commit → REJECT") is superseded by three
properties, to be registered under new identifiers, CT-R4-004 being marked
`superseded_by` them:

1. **No dispatch on a stale verdict.** No effect on a verdict older than the
   policy's freshness threshold without a fresh adjudication that includes the
   verdict's age.
2. **One direction.** All else equal, age never improves a disposition.
3. **Fail-safe bound.** A bound declared fail-safe refuses alone (2a).

Design rule, consistent with RFC-2: age acts as a modulator that contracts the
admissible region. It is not a term that a strong score elsewhere can buy back.

Until the new identifiers are registered, CT-R4-004 keeps its current text and
results, and reports cite this note next to it.

## 4. State drift at commit: the required outcome (RFC-4 §2.2; vectors C3, CT-R4-005)

RFC-4 §2.2 says the binding mechanism "MUST detect this and trigger HARD_VETO".
What REG requires is the outcome, not the label:

> No effect under a changed governance state, and the reported state class:
> either a terminal refusal, or a suspension with a declared resumption
> condition.

REG requires the resumption condition when the runtime suspends. It does not
impose the veto. Vectors C3 (standing revoked between verdict and commit) and
CT-R4-005 (policy epoch changed between verdict and commit) follow the same
rewrite: `expected` becomes "no effect; terminal refusal, or suspension with a
declared resumption condition". The registry edit is a separate change.

## What this note does not do

- It changes no recorded result and no vector count.
- It certifies nothing about any runtime.
- It does not decide the version of the next RFC-4 text beyond naming v0.3.
