# TENIR-Gov 5.7.0 — REG Conformance qualification gate (P0)

**State: PENDING_EXECUTION — not qualified, not publishable.**

This dossier is separate from the existing `deployment-manifest.json`, which still describes the 5.6.1 baseline. Never silently rewrite the baseline as evidence for 5.7.0.

## Gate sequence

1. **Identify build:** record exact tested Git commit, wheel/sdist SHA256, imported `tenir_governance.__version__`, interpreter, OS, installation source and timestamp. The initial commit candidate in JSON is not proof of the installed code.
2. **Run suite:** execute REG Conformance's runner against the installed 5.7.0 artifact, capture complete command, adapter, output, exit code, raw structured results, hash, and CI URL if applicable. Any test that uses a lab membrane must be labelled *lab*, not *native governor*.
3. **T6–T8 native boundary:** for CT-R4-011, -012, -013, document the actual production-code adapter and its executed proof. An imported laboratory membrane, vector declaration or probe pass alone cannot be promoted to `NATIVE_CONFORMANT`.
4. **Backend scope:** distinguish local file-lock, localhost Raft and real multi-host deployment. Scope and external-effect limitations are recorded per configuration.
5. **Assess projection:** set independently `admissible_structural`, `implementation_tested`, `native_conformance_demonstrated`, and `effective_guarantee_demonstrated`. Never infer one from another.
6. **Publish last:** propagate reviewed results to REG+ and public interfaces with provenance and limitations; a version bump alone is not a qualification.

## Existing evidence gap

The 5.6.1 baseline manifest is still pinned to `implementation_version: 5.6.1`. The suite registers 18 core vectors including T6–T8, but its native adapters remain explicitly described as implementation gaps. The separate T7 probe references `tenir-conformance-s1-g1` laboratory code.

### Acceptance criteria

- [ ] Exact tested 5.7.0 source and package identified, with immutable hashes.
- [ ] Version guard and runner executed with retained output.
- [ ] All three T6–T8 vectors evaluated with explicit native-vs-lab provenance.
- [ ] No `IMPLEMENTATION_GAP` treated as `PASS`; no coverage percentage treated as a safety guarantee.
- [ ] Reviewed projection/regulatory scope and limitations included.
- [ ] Separate authorization before any REG+ or website publication.

No tag, release, PyPI upload, `main` merge or website change is authorized by this dossier.
