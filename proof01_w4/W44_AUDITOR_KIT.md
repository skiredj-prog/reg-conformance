# PROOF-01 W4.4 — Offline auditor package (candidate)

Owner: Agent 3. Stacked on W4.3; no change to W2/W3 authority or evidence.

Usage from checkout root:

```sh
python -m unittest discover -s proof01_w4/tests -v
python -m proof01_w4.auditor /path/to/unmodified/evidence-bundle --output /tmp/w4-audit.zip --claim receipt-integrity
sha256sum /tmp/w4-audit.zip
```

The archive contains `evidence/**` from the original bundle and
`reports/audit-report.json`. The audit report is **not** an attestation of
external-effect correctness, production protection, witness independence
or PROOF-01 E2E convergence. W4.4's packaging tool validates the documentary
manifest with W4.1 before including evidence. Evidence is never modified
or signed by the package tool.

The generated ZIP has deterministic member order and timestamp (two runs
on identical bundle bytes produce the same SHA-256). The tool refuses
overwrite, symlinks, missing or mismatched evidence, path traversal and
out-of-scope requests.

**Important limitation:** This is a reproducible documentary artifact only,
not the final RFC-7 kit: native B3 wire adapter, independent trusted signature
verification of native receipts, separate witness custody, exhaustive effect
observability and common integrated deployment identity remain open.

Reference pins (PMO TENIR #83): W4.2 `b9be88341c23438a8e553ea64a4e6d55ea96faee`;
W4.3 `cd0090a8b5ead41ecfe6721474a7673afd8b33e2`.
No source hash is an integrated G4-A+B3+RC-01+I8 SUT hash.
