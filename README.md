# REG Conformance Suite

> **Vector catalogue:** https://skiredj-prog.github.io/reg-conformance/lab/
>
> The catalogue source lives in `vectors/*.yaml`. One vector is one pull request.
> A proposal becomes a named vector only after independent third-party validation.

**Runtime Execution Governance (REG) Conformance Suite** is an implementation-agnostic test vector collection for verifying compliance with the REG standard.

This repository defines and maintains machine-readable conformance vectors that describe what a REG-compliant runtime must do, how it must handle edge cases, and what audit records it must produce.

## Quick Start

### View Vectors

Open the **Lab Viewer**:
```bash
open https://skiredj-prog.github.io/reg-conformance/lab/
```

Or run locally:
```bash
python3 -m http.server 8000
open http://localhost:8000/lab/
```

### Work with Vectors

```bash
# List all vectors as JSON
cat vectors/dist/vectors.json | python3 -m json.tool

# Add a new vector
# → Edit vectors/core.yaml, vectors/commit.yaml, vectors/extended.yaml, or vectors/proposals.yaml
# → Run the compiler to regenerate the JSON bundle
python3 vectors/compile.py
```

## Vector Collections

The conformance suite is organized by RFC phase and vector category:

### Core Vectors (C1–C5 + CT-R4-001–CT-R4-010)

Minimal set of 15 requirements for REG compliance.

- **C1–C5** — Foundational runtime behavior (RFC-3, RFC-2, RFC-1)
- **CT-R4-001–CT-R4-010** — Commit-phase audit integrity (RFC-4)

→ See [`vectors/core.yaml`](vectors/core.yaml) and [`vectors/commit.yaml`](vectors/commit.yaml)

### Extended Vectors (CT-R0-001–CT-R7-003)

38 advanced scenarios covering:
- **CT-R0-001–CT-R0-005** — Constitution (RFC-0)
- **CT-R1-001–CT-R1-007** — Wire Protocol (RFC-1)
- **CT-R2-001–CT-R2-006** — Structure (RFC-2)
- **CT-R3-001–CT-R3-008** — Standing & Revocation (RFC-3)
- **CT-R5-001–CT-R5-005** — Audit Chain (RFC-5)
- **CT-R6-001–CT-R6-004** — Override & Escalation (RFC-6)
- **CT-R7-001–CT-R7-003** — Interoperability (RFC-7)

→ See [`vectors/extended.yaml`](vectors/extended.yaml)

## Vector Fields

Each vector documents:

| Field | Purpose |
|-------|----------|
| `id` | Unique identifier (e.g., C1, CT-R4-001) |
| `rfc` | RFC reference (e.g., RFC-3, RFC-4 §2.2) |
| `category` | core, commit, extended, or proposal |
| `property` | Normative property being tested |
| `input` | Test input or scenario |
| `intended` | Expected behavior per spec |
| `expected` | Expected outcome |
| `status` | implemented, specified, or proposal |
| `native` | Native mode result: PASS, FAIL, INCONCLUSIVE, NOT_APPLICABLE, ADAPTER_REQUIRED, or IMPLEMENTATION_GAP |
| `observed` | Observed native behavior |
| `reference` | RFC section or specification link |

## Structure

```
reg-conformance/
├── README.md                    # This file
├── vectors/
│   ├── core.yaml               # C1–C5, CT-R4-001–CT-R4-010
│   ├── commit.yaml             # Alias for commit-phase vectors
│   ├── extended.yaml           # CT-R0–CT-R7
│   ├── proposals.yaml          # Candidates under review
│   ├── schema.json             # JSON Schema validation
│   ├── compile.py              # YAML → JSON compiler
│   ├── CONTRIBUTING.md         # Contributing guidelines
│   └── dist/
│       └── vectors.json        # Generated bundle (committed)
└── lab/
    └── index.html              # Static web viewer
```

## Contributing

To propose a new conformance vector:

1. Choose the appropriate YAML file (`core.yaml`, `commit.yaml`, `extended.yaml`, or `proposals.yaml`)
2. Add an entry with `id`, `rfc`, `category`, `property`, `intended`, and `status`
3. Include optional but recommended fields: `input`, `expected`, `native`, `observed`, `reference`
4. Validate your YAML:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('vectors/core.yaml'))"
   ```
5. Recompile the JSON bundle:
   ```bash
   python3 vectors/compile.py
   ```
6. Submit a pull request with both the YAML and the regenerated `vectors/dist/vectors.json`

For detailed guidelines, see [`vectors/CONTRIBUTING.md`](vectors/CONTRIBUTING.md).

## Schema

All vectors validate against [`vectors/schema.json`](vectors/schema.json), which enforces:

- Required fields: `id`, `rfc`, `category`, `property`, `intended`, `status`
- Standardized enums for `category`, `status`, `native`
- Optional metadata: `input`, `expected`, `observed`, `reference`

## License

This repository is licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for details.

## References

- **REG Specification** — https://github.com/skiredj-prog/reg-conformance
- **Lab Viewer** — https://skiredj-prog.github.io/reg-conformance/lab/
- **Contributing Guide** — [`vectors/CONTRIBUTING.md`](vectors/CONTRIBUTING.md)
