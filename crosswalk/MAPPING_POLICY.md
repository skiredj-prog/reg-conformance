# Mapping policy — REG crosswalk

A row in `crosswalk.json` is a **claim**: a REG mechanism addresses a clause of an external
framework, within a stated limit. This policy defines what a row must contain before it is
merged, and what a status is allowed to mean.

A mapping is not a certification, and nothing in this crosswalk establishes that a system
is conformant to any framework.

## 1. Every mapping states its source

- The clause must be read in the **official text** of the framework, not taken from a
  secondary summary or a title alone.
- Record the framework identifier and version, the clause identifier, the **exact official
  wording** the mapping relies on (quoted, short), and the URL and access date of the source.
- A clause title that differs from the official text is a defect, not a paraphrase.

## 2. Every mapping states its limit

Each row must say what the mechanism **does not** cover, in the `description` field. A
mapping without a stated limit is not accepted.

Examples of limits that must be stated when relevant:
- an automated mechanism does not replace a human decision where the clause requires one;
- the mechanism checks a property of the execution, not the truth of an external fact;
- the mechanism covers a tested path, not the whole system.

## 3. Status vocabulary

| Status | Meaning | Who sets it |
|---|---|---|
| `unverified` | A proposal derived from analysis; no executable test yet. | Author of the proposal |
| `specified-in-rfc4` | Described in RFC-4; no executable test in the lab repository. | Maintainer |
| `planned` | Catalogued in `vectors.json`; no executable test yet. | Maintainer |
| `tested` | An executable test covers the vector. The row carries an `evidence` object. | **Maintainer review only** |
| `frozen` | The source document is frozen and its vectors are covered by other rows. | Maintainer |

`verified-by-vector` is not used. It asserted a verification without evidence.

## 4. Evidence

- A row may be `tested` only if it has a non-null `source` (section 1) and an `evidence` object naming the test file, the commit
  SHA that ran, and the CI run or pull request.
- Test names must resolve at the cited commit. A reviewer checks this before merge.
- Automated jobs (CI) may **propose** evidence fields. They never change `verification_status`.
  A maintainer changes the status in a reviewed pull request.

## 5. Withdrawals

A mapping that proves wrong is not deleted silently. It is kept with a `Correspondence
withdrawn` note in its description, and its status returns to `unverified`, as for the two
ISO rows that were withdrawn on review.

## 6. Proposals not yet admissible

The following proposals are **not** admitted until their clause text has been read and a
limit has been written:

- EU AI Act Art. 14 (human oversight) mapped to `HARD_VETO`: an automated veto is not
  human oversight by itself.
- EU AI Act Art. 55 (general-purpose AI model obligations) mapped to `ADAPTER_COMPATIBILITY`:
  the article addresses model providers, not execution adapters.
- ISO/IEC 42001 §8.4 mapped to `HARD_VETO` and `HOLD`: clause numbering and wording to be
  checked against the official text.

## 7. Review checklist (for every pull request touching `crosswalk/`)

- [ ] The clause text was read in the official source; source URL and access date recorded.
- [ ] The description is in English and states what the mechanism does not cover.
- [ ] `verification_status` is consistent with the evidence present.
- [ ] Every `tested` row has an `evidence` object whose test names resolve at the cited commit.
- [ ] `crosswalk.json` validates against the schema.
- [ ] No automated job changed a status.
