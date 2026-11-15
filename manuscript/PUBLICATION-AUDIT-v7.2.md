# Publication audit of manuscript v7.2

Audit date: 15 November 2026. Scope: manuscript provenance, cited artifacts, editorial accuracy and submission preparation. This is not a new empirical campaign, formal proof verification, security certification or independent reproduction of the study.

## GitHub and Zenodo provenance

The repository was inspected at `main` commit `a2ec724bc75f4b89128dc6e5e54a3ff309a8fc68`. Its manuscript directory contained `v7.1.md`, `RELEASES.md` and `CORRECTIONS-v7.0.md`; no v7.2 manuscript existed. No applicable `AGENTS.md` was present in the recursive tree. Open pull requests were inspected for overlap; no manuscript-v7.2 PR was present.

The annotated [v7.1 tag](https://github.com/skiredj-prog/reg-conformance/tree/v7.1) resolves through tag object `06c265791abb2d1bb84a414c54decdcb1d674a66` to commit `9f2a03d7e1c3cce346b1c9d36671fc33edada5ac`. The manuscript blob `4ee1aec7c844ea4739ac0dc8c70a7598baeef359` is identical in the tag and inspected `main`. The earlier guide's `f4c7c95` tag attribution was wrong. The GitHub release collection contained software/RFC releases, but no v7.1 or v7.2 manuscript Release. A tag is not a GitHub Release.

The [v7.1 Zenodo metadata](https://zenodo.org/api/records/23314839) and [original-record metadata](https://zenodo.org/api/records/23270929) both identify concept DOI `10.5281/zenodo.23270928`. The supplied guide incorrectly used the original version DOI `23270929` as the concept DOI. The v7.1 record contains both original and revised PDFs, with the MD5 values retained in `RELEASES.md`; the PDF bytes themselves were not rehashed. The preprint metadata lists CC BY 4.0.

## Evidence inspected and corrections made

| Finding | Evidence | Resolution |
|---|---|---|
| Historical and current E2 findings were blurred | [Run 38198777951](https://github.com/skiredj-prog/tenir-conformance-s1-g1/actions/runs/38198777951), commit `d42499b`, downloaded current JSON | Abstract and Proposition 3 now distinguish the historical witness; new Table 3 records the current outputs |
| Current E2 archive contains zero recorded violations in all worlds | Four JSON files; empty `violations` and `shortest_counterexamples`; depth 8 | Preserve historical tables; do not interpret current zero counts as proof or equivalent coverage |
| E2 output completeness is not established by a successful run | [Explorer at d42499b](https://github.com/skiredj-prog/tenir-conformance-s1-g1/blob/d42499bc8685c03612893d711598fe641ab31d44/experiments/e1_e2/e2_explore.py) catches all event-application exceptions | Disclose error/rejection ambiguity and the need for a controlled coverage comparison |
| S12 report contains seven tests, not eight | [Run 38202044948](https://github.com/skiredj-prog/tenir-conformance-s1-g1/actions/runs/38202044948), commit `4671dff`, inspected JUnit XML | Specify a, b, d, e, f, g, h; S12c is a separate ND-1 workflow gate |
| S12e was described too broadly | XML name is `test_s12e_missing_required_target_postcondition_holds_before_kernel` | State the actual archived test purpose; declarative attribute truth remains an assumption |
| Companion exit was described as requiring a signed receipt | [v5.4.1 hold.py](https://github.com/skiredj-prog/tenir_governance/blob/v5.4.1/tenir_governance/operations/hold.py), `HoldManager.authorize_exit()` | It records caller-provided fields; the inspected method does not verify a signature or independently establish authority |
| Reproduction appendix lacked a current-output route | [Pinned CI workflow](https://github.com/skiredj-prog/tenir-conformance-s1-g1/blob/d42499bc8685c03612893d711598fe641ab31d44/.github/workflows/s1.yml) | Add separate current-run commands and disclose its unpinned companion dependency |
| Supplied bibliography had a wrong page range | Publisher-deposited Crossref record for [Helland's Queue article](https://doi.org/10.1145/2181796.2187821) | Correct 30–39 to 30–46 and add DOI |

The downloaded E2 ZIP matched SHA-256 `82d3d53efb3a6a3a5ad6aa4c44b92532f5fbfddf0909f8f1f1f02748c0682970`; the S12 ZIP matched `c4a5c1f2d2ebc7308f97a258125efd4ff1a6df4ff86dca5d1f5d4def73a25a8b`. These matched GitHub's artifact digests. Unmodified member bytes are preserved in `evidence/v7.2/` with origin and member hashes. GitHub listed artifact expiry on 10 January 2027, so preserving the small text outputs avoids relying only on expiring CI downloads.

The current E2 states/transitions are: honest 675/25,297; false_attest 1,539/56,111; hidden_honest 1,059/41,807; adversarial 2,307/88,567. S12 XML reports 7 tests, 0 failures, 0 errors and 0 skips. The [committed E1 output](https://github.com/skiredj-prog/tenir-conformance-s1-g1/blob/d42499bc8685c03612893d711598fe641ab31d44/experiments/e1_e2/e1_results.txt) agrees with Table 8.2 and the 96 blocked retries across 51 traces. This is comparison with stored evidence, not a new execution.

## Scientific limits that remain

- The original historical E2 script is unavailable. Its historical tables and reported witness cannot be labelled reproduced by the current archive.
- The current explorer's catch-all exception path obscures whether an event was intentionally rejected or failed unexpectedly. A controlled study with error classification and fixed dependencies is needed to explain the historical/current coverage discrepancy.
- The historical workflow installed `tenir_governance` from an unpinned Git URL. The downloaded E2 archive does not identify that resolved dependency commit. The new appendix does not promise a byte-identical rerun from the lab commit alone.
- Table 2 forensic counts, earlier scenario CI totals and the Hypothesis Lab milestone totals were retained as attributed historical claims; this audit did not independently re-run them.
- The v5.4.1 source inspection is not a complete audit of its authorization architecture. Presence of an exit API does not close the evaluated harness's limitation or demonstrate external authorization security.
- This publication audit does not re-prove the conditional theorem. No Torky infrastructure-scale benchmark is imported into the membrane evidence: it concerns a separate system and cannot substantiate these membrane claims without a defined experimental connection.

## Journal preparation

The journal pages were inspected directly in the browser after web retrieval and local DNS failed. They label themselves launch-phase drafts. The [submission page](https://journal.stanaic.org/submit.html) explicitly says the OJS route is not yet open and manuscripts must not be submitted by email. No submission, email or journal account action was performed.

The [author guidance](https://journal.stanaic.org/author-guidelines.html) recommends a 150–250-word abstract, 4–7 keywords, article category, consistent references, separate title page, cover letter, declarations and appropriate supplements. The revised abstract has 203 whitespace-delimited words and seven keywords. Methodology / Evaluation Paper is a supported [article category](https://journal.stanaic.org/article-types.html).

The [review policy](https://journal.stanaic.org/peer-review.html) uses double-anonymous review in staging, normally with two independent reviewers; final defaults remain to be ratified. A separate anonymous derivative and confidential editorial documents are prepared locally. Public preprints, the title and specialized technical material remain searchable, so anonymity cannot be guaranteed. The editor must approve the route for reproducibility artifacts. The confidential derivative and its identifier map are not part of the public repository update.

The [preprint policy](https://journal.stanaic.org/preprint-policy.html) requires transparent disclosure of earlier versions and changes. The [AI policy](https://journal.stanaic.org/ai-use-policy.html) calls for disclosure beyond routine language/formatting work and human responsibility. The [independence policy](https://journal.stanaic.org/editorial-independence.html) requires conflict management and independent handling for leadership submissions. Applicable author declarations must be confirmed, not inferred.

At inspection, APC remained under review, ISSN was not assigned, and the site made no DOI/indexing claim. The inspected guidance did not specify a manuscript-wide word limit, mandatory template, file format or reference style. These remain to be checked against the final platform requirements. Candidate PDFs are prepared for review, not represented as journal-mandated or tag-derived release files.

## Readiness conclusion

The v7.2 source and evidence record are prepared for review. Journal submission awaits the official opening, completed author declarations, human approval of the scientific corrections, and an agreed anonymous evidence route. Historical/current exploration differences remain disclosed scientific limitations. Publishing a preprint does not imply journal acceptance or conformance certification.

## Addendum — replay of 15 November 2026

This addendum is later than the audit above and supersedes it where they conflict. The existing E1 and E2 harnesses were re-run against archived and current membrane revisions; scripts, patches, outputs and SHA-256 values are in `evidence/v7.2/replay-2026-11-15/`.

- **Historical E2 (Table 1).** The explorer archived at tag `archive/forensic/e2-key-audit-20261009` (`cf1b1ea`) with membrane overlay `84e46d9` reproduces all four historical outputs field for field, runtime excepted. The first limit above ("historical E2 script is unavailable … cannot be labelled reproduced") is withdrawn: the script behind the first Zenodo version is not preserved, but the archived explorer reproduces its figures.
- **Current E2 artifact (Table 3).** An instrumented replay reproduces the CI counts and shows that every dispatch-class event raises `NONCE_REQUIRED` and every qualified non-execution claim is rejected for a missing signature. The zero-violation result therefore exercises no dispatch; the artifact is retained, not used as evidence.
- **Current revision with nonces and signed attestations (Table 4).** With a 13-line explorer patch (caller nonce; Ed25519 attestation from the repository test signer), `I1` fails only in the adversarial world (305,429 occurrences at depth 7, shortest trace 3); honest, false_attest and hidden_honest record none within depth 8, 7 and 8.
- **Three-transition trace and E1.** The trace violates `I1` with a verified signature on `d42499b` and `8bc0e5e`. The committed E1 script collapses M1 on the current membrane; with signed negative evidence its output is byte-identical to the committed `e1_results.txt` on both revisions.
- **Kernel dependency.** The replay used the local kernel fallback and reproduced the CI counts, so the unpinned companion kernel does not affect them. The pin remains advisable.

Remaining limits: the catch-all exception handler in the unmodified explorer, Table 2 and Hypothesis Lab totals not re-run, no fixpoint reached in any world, and evidence derived from harness ground truth (an upper bound on what a real attestation channel provides). The manuscript was revised accordingly and published as Zenodo version [10.5281/zenodo.24249646](https://doi.org/10.5281/zenodo.24249646).

