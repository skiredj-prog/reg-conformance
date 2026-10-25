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
