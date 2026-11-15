# Releases — Governing the Unobserved

Audited on 15 November 2026 against GitHub and the Zenodo record metadata.

Concept DOI: [10.5281/zenodo.23270928](https://doi.org/10.5281/zenodo.23270928). **23270929 is the original version DOI, not the concept DOI.**

| Manuscript version | Date | Zenodo version DOI | Git source | Status |
|---|---|---|---|---|
| v1 (v7.0) | 2026-10-09 | [23270929](https://doi.org/10.5281/zenodo.23270929) | History before PR #13 | Published historical, uncorrected text |
| v7.1 (second Zenodo record) | 2026-10-12 | [23314839](https://doi.org/10.5281/zenodo.23314839) | `manuscript/v7.1.md`; annotated tag `v7.1` → `9f2a03d7e1c3cce346b1c9d36671fc33edada5ac` | Published preprint; frozen |
| v7.2 | 2026-11-15 | [24249646](https://doi.org/10.5281/zenodo.24249646) | `manuscript/v7.2.md`; tag `7.2` (GitHub release, commit `98bf685`); replay in `manuscript/evidence/v7.2/replay-2026-11-15/` | Published preprint with replay archive; journal submission candidate, not submitted or accepted |

## Published PDF fingerprints

Zenodo metadata lists:

- v1 PDF: MD5 `328f60592f2bcdf1214f2f9a9b570425`.
- v7.1 PDF: MD5 `baad4b8aff168024fdbaa4e53af03b9c`.
- v7.2 PDF (as uploaded to Zenodo 10.5281/zenodo.24249646): SHA-256 `9c471275fd8832f6af6ad56887a868fff59b583017d60efeea3aea7002a044c2`. Built with pandoc 3.1.3 / XeLaTeX from `manuscript/v7.2.md` at tag `7.2`. Replay archive SHA-256 `4b408850592934690af803ac734f15c831c3de716e1eca34c3a47bfef7740650`.
- The prior repository register also records v7.1 SHA-256 `4603c9aff1f0ec7a8f9c336ea6ba5f0d7d3efab1cf9c5bbeba7d5c143529c9b0`; this SHA-256 was retained, not recomputed in this audit.

The second Zenodo record intentionally contains both PDFs. A filename in that record is not by itself evidence that both files contain the corrected text.

## Preservation and release rules

1. Keep every published Markdown version alongside its successors in `main`. Never rename or overwrite `manuscript/v7.1.md` when adding v7.2. At audit time its blob was `4ee1aec7c844ea4739ac0dc8c70a7598baeef359`, identical in `main` and tag `v7.1`.
2. Freeze published tags. The v7.1 tag targets `9f2a03d`, not the earlier rename commit `f4c7c95`.
3. A manuscript release, software release, Zenodo preprint and journal version of record are distinct. Software releases `v0.x` do not establish manuscript publication. At the 15 November audit no v7.1 or v7.2 GitHub Release existed; v7.1 has a Git tag. v7.2 was then published as the GitHub Release `7.2` (lightweight tag on `98bf685`); it carries no attached PDF, and the Zenodo record is the citable artifact.
4. Generate the public release PDF from the final reviewed tag, compute its SHA-256, and record it in a follow-up register commit without moving the tag. The locally prepared candidate PDF is not a tag-derived release artifact.
5. Keep confidential title pages, declarations, editorial correspondence and anonymization maps outside the public repository. The anonymous review copy is a separate derivative; it is not the archival public manuscript.

## Changes in v7.2

- Move §§6.4–6.5 before §7 and remove repeated trailing paragraphs; normalize math and restore references.
- Correct the concept DOI and v7.1 tag provenance.
- Separate the historical three-transition E2 counterexample from the current depth-eight artifact, which records no violations in all four worlds. Preserve the historical counts; add current Table 3 with verified artifact provenance. No new experiment was run.
- Archive the current E2 JSON files and S12 XML under `evidence/v7.2/`, with a hash manifest. S12 XML records seven tests; S12c is a separate workflow gate.
- Correct the v5.4.1 companion middleware description: `authorize_exit()` constructs an `ExitReceipt` from caller-provided fields; the inspected method does not verify a signature or independently establish authority.
- State reproduction limits: catch-all exceptions in the current explorer and an unpinned companion dependency in the CI workflow. (The 15 November audit also recorded the historical explorer as unavailable; the replay below supersedes that point.)
- Replay of 15 November 2026 (`evidence/v7.2/replay-2026-11-15/`): Table 1 reproduced from the archived explorer `cf1b1ea` with membrane overlay `84e46d9`; the archived current artifact (Table 3) shown never to admit a second attempt; Table 4 re-run with caller nonces and signed attestations; three-transition trace with a verified signature on `d42499b` and `8bc0e5e`; E1 with signed negative evidence byte-identical to the committed output on both revisions. No event, invariant, state key or scenario added.
- Prepare a 203-word abstract, seven keywords and a Methodology / Evaluation Paper category for STANAIC.

## Publication record for v7.2

Performed on 15 November 2026, in this order:

1. Reviewed manuscript and replay evidence merged to `main` (#67, wording correction #68); `main` at `98bf685`.
2. Zenodo version `10.5281/zenodo.24249646` created under concept `23270928` with `v7.2-revised.pdf`, `v7.2-revised.md` (identical to `manuscript/v7.2.md` at `98bf685`), `replay-2026-11-15.zip` and `SHA256SUMS`. The PDF was built with pandoc 3.1.3 / XeLaTeX from that Markdown; its SHA-256 is recorded above.
3. GitHub Release `7.2` published on `98bf685`, creating the lightweight tag `7.2`. The tag name departs from the `v7.1` convention; it is kept rather than replaced, because it is already public.

For later versions, prefer an annotated tag `v<version>` on the merged commit before the Zenodo deposit, and do not move a published tag. A GitHub or Zenodo release is not journal acceptance.

## STANAIC status

The [official submission page](https://journal.stanaic.org/submit.html), inspected on 2026-11-15, says submissions are not yet open and manuscripts must not be submitted by email. Recheck the final author guidance and fee policy when the OJS route opens. See `PUBLICATION-AUDIT-v7.2.md` for the audit and outstanding readiness items.
