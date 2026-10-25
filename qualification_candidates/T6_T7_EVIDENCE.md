# REG experimental native T6/T7 candidate evidence

**Status:** SCOPED_CANDIDATE_PASS / NORMATIVE_CONFORMANCE_HOLD
**Date:** 2026-10-25

## Immutable source and run linkage

- Implementation source: `skiredj-prog/tenir_governance@aa8f947adee87c793201fba47206543cd68c45ac` (experimental PR #65, **not** the published 5.7.0 source commit).
- REG harness source: `skiredj-prog/reg-conformance@3057d9e51a320f9d340f65989afb8b84753b6a31`.
- [Experimental native adapter CI run 40165565458](https://github.com/skiredj-prog/reg-conformance/actions/runs/40165565458): success.
- Companion capabilities run 40165565427: success.
- [Artifact 12588146895](https://github.com/skiredj-prog/reg-conformance/actions/runs/40165565458/artifacts/12588146895): archive `sha256:8615bb14673e76f55e918905c069612049b834d79e2ab2397e15e984055a18ac` (GitHub-reported archive digest). Internal output hashes and dependency freeze reside in artifact.

## Scope

- CT-R4-011: scoped, signed single-host runtime probe of UNKNOWN → RESOLVED (attested effect). Timeout or tampered evidence cannot promote state; exact replay is idempotent.
- CT-R4-012: scoped, signed single-host runtime probe of UNKNOWN → FAILED (attested non-execution), timeout remains UNKNOWN, altered signature rejected.
- CT-R4-013: IMPLEMENTATION_GAP. An attempt still cannot authorize an automatic or qualified new attempt on the same LEI (T8 required).
- Attempt + LEI + nonce + SHA-256 operation fingerprint are attested and checked against local store. Independent trusted sources must supply **correct** operation digest and truthful non-execution evidence; cryptography alone proves neither.

## Scope boundary

This CI **does not** demonstrate: production governor/dispatch coupling, dual-store atomicity, distributed linearizability, cryptographic root lifecycle/revocation freshness beyond fixed process configuration, external no-effect truthfulness, `tau_K` SLA liveness, or T8 retry authorization.

**Do not** update production or baseline manifests or mark CT-R4-011/012 `NATIVE_CONFORMANT` from this evidence alone. The 5.7.0 REG qualification in draft PR #47 remains distinct, and the 5.6.1 deployment baseline remains untouched.

## P0 governor operation binding — verified 2026-10-25

- Source candidate pinned at `skiredj-prog/tenir_governance@49afb1a1d9dbb1ca3e74d946fd1ea4fab1101c8a` (not GA).
- [REG experimental run 40167424102](https://github.com/skiredj-prog/reg-conformance/actions/runs/40167424102): **PASS**, including the actual JSON-backed `DurableOperationRegistry` bridge to `DualKernelGovernor` and the unconditional HOLD inspector.
- [Artifact 12588703936](https://github.com/skiredj-prog/reg-conformance/actions/runs/40167424102/artifacts/12588703936) archive SHA-256: `81aa0c51018ff47705c43d2b5d9c75c214d7e764313616daeeb024d0428d2564` (GitHub-reported archive digest). Artifact includes candidate report, dependency freeze and internal checksums.
- REG companion capabilities workflow on the same commit: **PASS**.
- TENIR-Gov candidate source run [40167328231](https://github.com/skiredj-prog/tenir_governance/actions/runs/40167328231): **47/47 PASS**, source Governance CI run [40167328229](https://github.com/skiredj-prog/tenir_governance/actions/runs/40167328229): **PASS**. Raft regression independent and not used as an approval condition for this scope.
- `governor_registry_observer.status=SCOPED_OBSERVATION_PASS`, `execution_authorized=false`; the external provider and budget settlement paths are **not exercised**. The source operation remains `UNKNOWN` after evidence recording.
- **Strict outcome: candidate read-only integration evidence PASS, normative T6/T7/HOLD and T8/GAP.** No promotion of REG catalogue/manifest or release claims.

## Atomic one-store candidate evidence — 2026-10-25

- Candidate source commit `skiredj-prog/tenir_governance@105ad0755c9730f6c003d46fb98acd5198710a3d`; experimental feature branch, **not** published 5.7.0.
- [Source CI run 40168273609](https://github.com/skiredj-prog/tenir_governance/actions/runs/40168273609): **66/66 PASS**, including atomic candidate source/attempt/evidence transactions, cross-process opposing attestations, process hard exits before and after SQLite COMMIT, idempotent recovery, and triggers protecting terminal records and events.
- [REG CI run 40168362170](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168362170): **PASS**, running signed CT-R4-011/012 experimental vectors, the existing read-only governor observer, and the new atomic one-store candidate with explicit no-execution-gate assertions.
- [REG Capabilities run 40168362177](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168362177): PASS.
- [Artifact 12590085095](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168362170/artifacts/12590085095): GitHub-reported archive SHA-256 `9d83523b1c9393f599d83c4e5bc8de5de4a845c03cc668898109f67878c40a71`. Internal per-file hash manifest and dependency freeze are included in the artifact.
- Classification: `atomic_source_attempt_candidate=SCOPED_ATOMIC_SQLITE_PASS`, `execution_authorized=false`, `normative_conformant=false`, `source_authority=candidate_projection_only`.
- **No GA claim**: the candidate SQLite source is **not** the production JSON `DurableOperationRegistry` and cannot authorize any governor dispatch, budget consumption, compensation or T8 new attempt. Moving live operations to a unified backend requires a migration and atomic production integration design, plus separate proof of external effect settlement under crash/partition.

## Same-file budget safety — 2026-10-25

- Pinned source `skiredj-prog/tenir_governance@18d24dda78f0234550311ddf1bbcb6a0d94621b2`.
- Source dedicated CI [40168586084](https://github.com/skiredj-prog/tenir_governance/actions/runs/40168586084): **69/69 PASS**, including candidate qualification co-located with actual `SQLiteConsensusBackend` without automatic budget mutation.
- Independent REG native experiment [40168660397](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168660397): **PASS**; Capabilities [40168660332](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168660332): PASS.
- [Artifact 12590005932](https://github.com/skiredj-prog/reg-conformance/actions/runs/40168660397/artifacts/12590005932), GitHub archive digest `sha256:3731ff44d3266882b1f845fb80e899aab79230adae764cc441f687d434c7f520`. The file-level hash manifest and dependency freeze are uploaded with the report.
- Machine result: `budget_colocation_guard.status=SCOPED_NO_SETTLEMENT_PASS`, `budget_mutated=false`, `execution_authorized=false`. The budget reservation remains `RESERVED` after signed proof of non-execution; it is not automatically refunded or released.
- **No inference of shared transaction**: existing governor JSON registry, SQLite budget and candidate proof operate under separate API transactions, even when the two latter structures physically share one SQLite database. Live execution authority remains HOLD.
