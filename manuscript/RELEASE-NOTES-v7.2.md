# Manuscript v7.2 — Governing the Unobserved

Zenodo version DOI [10.5281/zenodo.24249646](https://doi.org/10.5281/zenodo.24249646); concept DOI 10.5281/zenodo.23270928. Supersedes v7.1 (DOI 10.5281/zenodo.23314839), which remains published and unchanged.

**Editorial.** Sections 6.4–6.5 precede Section 7; notation and references are normalized; the companion middleware description no longer claims signature verification that the inspected method does not perform.

**Evidence.** On 15 November 2026 the existing E1 and E2 harnesses were replayed against the historical, current and latest membrane revisions (`evidence/v7.2/replay-2026-11-15/`):

- the historical E2 outputs (Table 1) reproduce field for field from the archived explorer `cf1b1ea` with membrane overlay `84e46d9`; they are no longer described as unrecoverable;
- the archived current E2 CI artifact (Table 3) dispatches first-attempt effects but never reaches a `FAILED` attempt or a second admitted attempt (`process` events raise `NONCE_REQUIRED`; unsigned non-execution claims are rejected), so the admission guard is never tested on the case `I1` depends on; it is retained but not used as evidence;
- Table 4 re-runs the current explorer at `d42499b` with caller nonces and Ed25519-signed attestations: `I1` fails only in the adversarial world (hidden effect plus accepted false attestation), shortest trace three transitions;
- the three-transition trace violates `I1` with a verified signature on `d42499b` and `8bc0e5e`;
- E1 with signed negative evidence reproduces the committed `e1_results.txt` byte for byte on `d42499b` and `8bc0e5e`.

The replay adapted existing harnesses (13-line explorer patch, E1 signed-evidence patch); it added no event, invariant, state key or scenario. No general safety proof, production certification or journal acceptance is claimed.

**Files.** Zenodo PDF SHA-256 `9c471275fd8832f6af6ad56887a868fff59b583017d60efeea3aea7002a044c2`; replay archive `replay-2026-11-15.zip` SHA-256 `4b408850592934690af803ac734f15c831c3de716e1eca34c3a47bfef7740650`.
