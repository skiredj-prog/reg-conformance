# PROOF-01 W4.4 — Offline auditor package (candidate)

Owner for integration: Agent 3. Sprint 1 review proposal based on PR #59 at
`6567ee6efe1a2f1b91a1eac5ee62694cd9dd4ce1`. No change to W2/W3 authority.

Usage from checkout root:

```sh
python -m unittest discover -s proof01_w4/tests -v
python -m proof01_w4.auditor /path/to/unmodified/evidence-bundle --output /tmp/w4-audit.zip --claim receipt-integrity
sha256sum /tmp/w4-audit.zip
python -m proof01_w4.auditor --verify-archive /tmp/w4-audit.zip --claim receipt-integrity
```

The archive contains `evidence/**` from the original bundle and
`reports/audit-report.json`. The audit report is **not** an attestation of
external-effect correctness, production protection, witness independence
or PROOF-01 E2E convergence. W4.4's packaging tool validates the documentary
manifest with the shared W4 inventory checker on captured bytes. Evidence is
never modified or signed by the package tool.

Capture reads the manifest once and only its declared artifacts. An immutable
in-memory byte map feeds both verification and ZIP serialization. Producer
paths are not reopened after verification. A change during capture that breaks
a captured manifest digest is rejected. A source change after capture does not
alter the verified bytes exported; this is not a claim that the source remains
unchanged or that the whole filesystem was captured atomically.

The completed ZIP is replayed before writing and after reading back the output.
Replay recomputes every declared digest and the documentary report, refuses
extra/duplicate entries, and compares the embedded report with the recomputed
one. It never extracts files or executes bundle content. It is a second check
of the output, not the mechanism that fixes producer verification/copy races.

Directory capture requires POSIX `dir_fd`, `O_DIRECTORY` and `O_NOFOLLOW` support
(tested on Linux/WSL). Parent and leaf symlinks and special files are refused;
FIFO opens are nonblocking. Unsupported platforms fail closed for packaging.
Offline ZIP replay does not require POSIX. The reviewer must control the output
directory. This is not a sandbox against an administrator or a compromised
Python process, and an archive can still be changed after the command returns.

Resource bounds: 16 MiB per file, 64 MiB total uncompressed content, at most
1024 ZIP members, and 65 MiB input ZIP bytes. These are candidate implementation
limits, not changes to CEB-01 or REG-ARCH. Large bundles require a reviewed bound
change or a future streaming design; they must not bypass verification.

The generated ZIP has deterministic member order and timestamp (two runs
on identical bundle bytes produce the same SHA-256). The tool refuses
overwrite, symlinks, missing or mismatched evidence, path traversal, duplicate
JSON keys and out-of-scope requests. Stable JSON report formatting is not a
claim of JCS/RFC 8785 canonicalization. Existing source signatures remain opaque
original bytes; this tool does not verify native B3 signatures.

Exit 0 means documentary inventory/replay succeeded; the report still says
`INDETERMINATE` and `operational_assurance=NOT_ESTABLISHED`. A self-consistent
replacement of the manifest, evidence and report is not authenticated by these
checks. An external archive digest and independent trust/custody are separate
requirements. The historical standalone `verifier.verify(path)` and synthetic
semantic replay are not promoted to a native, atomic evidence interface here.

**Important limitation:** This is a reproducible documentary artifact only,
not the final RFC-7 kit: native B3 wire adapter, independent trusted signature
verification of native receipts, separate witness custody, exhaustive effect
observability and common integrated deployment identity remain open.

Reference pins (PMO TENIR #83): W4.2 `b9be88341c23438a8e553ea64a4e6d55ea96faee`;
W4.3 `cd0090a8b5ead41ecfe6721474a7673afd8b33e2`.
No source hash is an integrated G4-A+B3+RC-01+I8 SUT hash.
