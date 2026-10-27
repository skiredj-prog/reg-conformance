# PROOF-01 / W4.4 — Offline auditor package

Role: Agent 3. Stacked on W4.3 / REG PR #57. This is **packaging and independent inspection**, not system assurance or a producer of operational evidence.

Run offline after installing pinned W4 source and cryptography dependency:

```bash
python -m unittest discover -s proof01_w4/tests -v
python -m proof01_w4.auditor ./ceb01-evidence ../auditor.zip --trust-store ../trusted-keys.json --claim signed-trace-integrity
```

Inputs (candidate CEB-01/0.1): `proof-manifest-v1.json`, `convergence.json`, `reports/test-results.json`, `reports/proof-obligations.json`, plus original `evidence/**` files. The current synthetic fixture expects `events.json` and `checkpoint.json` if cryptographic semantic validation is requested. This is not claimed compatible with native B3.

Outputs are reproducible ZIP entries including original bytes, `auditor/report.json`, `auditor/README.txt`, `SHA256SUMS.txt`; archive hash emitted by CLI. No source evidence is mutated, keys are not packaged, no re-signing and no native SUT changes.

**Strict gates:** Even with signed synthetic events and all hashes valid, the kit forces `integration_lock=UNVERIFIED` and `production_gate=HOLD`. No `TEST_PASS` makes `SECURITY_FAIL` disappear. Trust store and provenance must come from outside evidence bundle. The archive's own SHA-256 attests bytes, not provenance, effect completeness, regulatory certification or independence of witness.

Remaining: real W2 CEB-01 source SHA + deployment digest + topology ID; W3 independent trust custody and attacks; native receipt adapter; auditor report field-level conformance to PMO versioned machine-readable contracts; external observer completeness; independent rerun on two verifier instances.

Never merge to main or label PROOF-01 PASS on basis of this draft.
