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

## G0/G2 shadow registry inventory — 2026-10-25

- Source TENIR-Gov candidate `fe01013f635ba6117bcce56048b36beb6729ebec` on draft PR #65. Existing published TENIR-Gov 5.7.0 is **not** this source.
- [TENIR-Gov source CI 40169534749](https://github.com/skiredj-prog/tenir_governance/actions/runs/40169534749): **88/88 PASS** for native candidate, budget isolation, immutable G0/G2 shadow snapshot, duplicate JSON keys and corrupt source rejection, child hard exit before commit, cross-process source writer serialization and divergence HOLD.
- [Source Governance CI 40169534772](https://github.com/skiredj-prog/tenir_governance/actions/runs/40169534772): PASS.
- [REG independent run 40169588262](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169588262): PASS. [Capabilities run 40169588240](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169588240): PASS.
- [Artifact 12589837823](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169588262/artifacts/12589837823): reported archive digest `sha256:2b5fb259b255b020b7d70561dc2aa9135497c27ec21f71c1661ddb417d75a97e`. Includes machine report, internal SHA-256 manifest and dependency freeze.
- The machine classification `shadow_registry_migration.status=SCOPED_SHADOW_CAPTURE_PASS` is accompanied by `cutover_performed=false`, `execution_authorized=false` and `source_authority=JSON_REGISTRY`. This is **not** G3 cutover, G4 transactionally controlled execution or normative REG T6–T8 conformance.

## G1 frozen-source × SQLite budget parity preflight — 2026-10-25

- Source TENIR-Gov experimental candidate `22e0452150e382b87eba012eb6eac7c001737722`.
- [TENIR-Gov CI 40169877931](https://github.com/skiredj-prog/tenir_governance/actions/runs/40169877931): **97/97 PASS**, including nine G1 preflight tests for reserved/committed amount and key parity, missing ownership, orphan reservation, I8 violation, UNKNOWN budget state and rollback.
- [TENIR Governance CI 40169877940](https://github.com/skiredj-prog/tenir_governance/actions/runs/40169877940): PASS.
- [REG independent run 40169963549](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169963549): PASS, [Capabilities 40169963530](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169963530): PASS.
- [Artifact 12588938290](https://github.com/skiredj-prog/reg-conformance/actions/runs/40169963549/artifacts/12588938290): GitHub archive digest `sha256:132d617ef2cb202f4fca52b1751f41c84ca6801b6ae5de122a10db1bc321e994`. Machine report, SHA-256 file manifest and dependency freeze retained.
- Report: `shadow_budget_parity_preflight.status=SCOPED_G1_PARITY_PASS`, `source_authority=JSON_REGISTRY`, `budget_authority=SQLiteConsensusBackend`, `execution_authorized=false`, `cutover_authorized=false`. Budget state change after baseline is rejected and never automatically reconciled.

**No normative promotion:** this is a *preflight observation*, NOT actual one-store operation+attempt+budget authorization, source cutover, provider execution or full RFC-4 T6/T7/T8 qualification.

## G3 cooperative fenced-shadow handoff — 2026-10-25

- Pinned TENIR-Gov candidate source `4def8c9fd39ca758ef271be20d04a8916d67d6c1`; not published 5.7.0.
- [Source CI 40171276528](https://github.com/skiredj-prog/tenir_governance/actions/runs/40171276528): **109/109 PASS**, including 12 new G3 tests for monotonic `PREPARED → FENCED_SHADOW_HOLD`, stale JSON writers, marker deletion safety, corrupt marker HOLD, subprocess hard exit before/after marker, restart and two-process single epoch.
- [Governance CI 40171276493](https://github.com/skiredj-prog/tenir_governance/actions/runs/40171276493): PASS. The separate Raft run is not evidence for single-host G3 fencing until verified independently.
- [Independent REG G3 candidate CI 40171390160](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171390160): PASS; [Capabilities CI 40171389959](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171389959): PASS.
- [Artifact 12590371349](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171390160/artifacts/12590371349) archive digest `sha256:1fa8a6912c261916379b6a2bbebcdd7d4178aa389304cd532ad849a9200426bf`; machine report and dependency hashes retained.
- Machine result `g3_shadow_fencing.status=SCOPED_G3_FENCED_HOLD_PASS`, `legacy_writers_observed_blocked=true`, `execution_authorized=false`, `production_cutover=false`, `candidate_dispatch_authorized=false`.
- **Not a genuine G3 authority transfer:** only updated single-host JSON writer implementations honor the marker. Pre-fence binaries, malicious fence deletion, distributed writers and live external effects remain outside this proof. Shadow SQLite does not gain dispatch authority; actual unified transactional commit, G4 and T8 are still blocked.

## G3 finalized fence tamper regression — 2026-10-25

- TENIR-Gov candidate source pinned to `31da28b33cffec474c6321f139032e121b61860e`.
- [Source CI 40171619527](https://github.com/skiredj-prog/tenir_governance/actions/runs/40171619527): **110/110 scoped tests PASS**, with mandatory HOLD rather than automatic reconstruction of a missing marker/sentinel from an already finalized epoch. [Source Governance CI 40171619587](https://github.com/skiredj-prog/tenir_governance/actions/runs/40171619587): PASS.
- [REG experimental CI 40171689306](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171689306): PASS, [Capabilities 40171689307](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171689307): PASS.
- [Artifact 12590337070](https://github.com/skiredj-prog/reg-conformance/actions/runs/40171689306/artifacts/12590337070), GitHub archive SHA-256 `4a41d23bf6235e30226ea05ec27f0d1baad6f42662219d49d9ac3ad21fc39563`.
- `g3_shadow_fencing.status=SCOPED_G3_FENCED_HOLD_PASS`, `missing_finalized_marker_is_hold=true`, `legacy_writers_observed_blocked=true`, `execution_authorized=false`, `production_cutover=false`. All normative T6–T8 and G4 effect/settlement claims remain unpromoted.

## G1 candidate operation + attempt + actual SQLite budget transaction — 2026-10-25

- Source pin: `skiredj-prog/tenir_governance@09bd2d73ac5b70b825d500e2f8ace2e26a4e4aaa` (draft experimental code, not published 5.7.0).
- [Source CI run 40174415547](https://github.com/skiredj-prog/tenir_governance/actions/runs/40174415547): **135/135 scoped PASS**, including 25 explicit G1 atomic budget tests. [Governance Gate 40174415445](https://github.com/skiredj-prog/tenir_governance/actions/runs/40174415445) PASS.
- [REG independent CI 40174454700](https://github.com/skiredj-prog/reg-conformance/actions/runs/40174454700): PASS; [Capabilities CI 40174454695](https://github.com/skiredj-prog/reg-conformance/actions/runs/40174454695): PASS.
- [Artifact 12590889066](https://github.com/skiredj-prog/reg-conformance/actions/runs/40174454700/artifacts/12590889066), GitHub archive `sha256:9aebe0141bb2b97be14be055a6c7905cedc73001171f8f086d9d4fad21bb4334`; output JSON, file-hash report and dependency freeze retained.
- Machine verdict: `g1_atomic_budget_candidate.status=SCOPED_G1_ATOMIC_I8_CANDIDATE_PASS`, `candidate_namespace_only=true`, `single_sqlite_transaction=true`, `execution_authorized=false`, `production_cutover=false`, `normative_conformant=false`.
- These tests demonstrate ONE SQLite transaction spanning `candidate_sources`, `candidate_attempts`, `candidate_events`, existing `reservations` and `resources` budget rows. The `candidate:` namespace and explicit `experimental_only=True` activation are accidental-use guards; only disposable experimental budget stores are admissible. No external dispatch or actual production JSON `OperationState` authority is involved.
- **No normative REG promotion.** CT-R4-011/012 still candidate-scoped, T8 still implementation gap. G3 production cutover, effect-truth/settlement and G4 remain HOLD; PR #47 and deployed manifest are unmodified.
