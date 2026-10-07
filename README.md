# REG Conformance Suite

**Runtime Execution Governance (REG) Conformance Suite** is an implementation-agnostic test vector collection for verifying compliance with the REG standard.

This repository defines and maintains machine-readable conformance vectors that describe what a REG-compliant runtime must do, how it must handle edge cases, and what audit records it must produce.

## Quick Start

### View Vectors

Open the **Lab Viewer**:
```bash
open lab/index.html
```

Or serve locally:
```bash
python3 -m http.server 8000
open http://localhost:8000/lab/
```

### Work with Vectors

```bash
# List all vectors as JSON
cat vectors/dist/vectors.json | python3 -m json.tool

# Add a new vector
# → Edit vectors/core.yaml, vectors/extended.yaml, or vectors/proposals.yaml
# → Run the compiler to regenerate the JSON bundle
python3 vectors/compile.py
```

## Vector Collections

The conformance suite is organized into three main categories:

### 1. **Core Vectors (C1–C5)**

Minimal set of requirements for any REG-compliant runtime.

- **C1** — Compliant Runtime Actor
- **C2** — Constrained Input Policy Compliance
- **C3** — Denial When Controls Are Missing
- **C4** — Recovery After Transient Failure
- **C5** — Concurrent Vector Execution Isolation

→ See [`vectors/core.yaml`](vectors/core.yaml)

### 2. **Commit Vectors (CT-R4-001–CT-R4-010)**

Requirements for execution record integrity, audit trails, and replayability.

- **CT-R4-001** — Unique Execution Identifier
- **CT-R4-002** — Standard Timestamp
- **CT-R4-003** — Governing Policy Version
- **CT-R4-004** — Actor Identity
- **CT-R4-005** — Input Digest
- **CT-R4-006** — Execution Decision
- **CT-R4-007** — Reason Code
- **CT-R4-008** — Trace Reference
- **CT-R4-009** — Append-Only Semantics
- **CT-R4-010** — Replayability Without State Loss

→ See [`vectors/commit.yaml`](vectors/commit.yaml)

### 3. **Extended Vectors (R0–R7)**

Advanced scenarios covering edge cases, failure modes, and distributed systems behavior.

- **R0** — Null or Empty Governance Context Handling
- **R1** — Partial Policy Downgrade Rejection
- **R2** — Out-of-Order Event Consistency
- **R3** — Competing Decisions Convergence
- **R4** — Unsupported Artifact Type Rejection
- **R5** — Policy Rollback Audit Continuity
- **R6** — Timeout Condition Surfacing
- **R7** — Backward Compatibility for Legacy Records

→ See [`vectors/extended.yaml`](vectors/extended.yaml)

## Structure

```
reg-conformance/
├── README.md                    # This file
├── vectors/
│   ├── core.yaml               # C1–C5 vectors
│   ├── commit.yaml             # CT-R4-001–CT-R4-010 vectors
│   ├── extended.yaml           # R0–R7 vectors
│   ├── proposals.yaml          # Candidates, non-validated
│   ├── schema.json             # JSON Schema
│   ├── compile.py              # YAML → JSON compiler
│   ├── CONTRIBUTING.md         # How to propose vectors
│   └── dist/
│       └── vectors.json        # Generated, committed
└── lab/
    └── index.html              # Static Lab Viewer
```

## Taxonomy

### Categories

| Category | Purpose | Examples |
|----------|---------|----------|
| **core** | Foundational runtime behavior | C1–C5 |
| **commit** | Audit record requirements | CT-R4-001–CT-R4-010 |
| **extended** | Edge cases, failure modes | R0–R7 |
| **candidate** | Proposed vectors | — |
| **exploratory** | Under discussion | — |

### Status

| Status | Meaning |
|--------|----------|
| `valid` | Ratified; required for conformance |
| `proposed` | Candidate; under evaluation |
| `rejected` | Not accepted |
| `deprecated` | Superseded |

### Severity

| Level | Meaning |
|-------|----------|
| `critical` | Must be satisfied for any conformance claim |
| `high` | Required for production |
| `medium` | Recommended |
| `low` | Optional |

### Phases

Vectors apply to different runtime stages:

- **pre-execution** — Input validation, policy setup
- **execution** — Core governance logic
- **post-execution** — Result handling
- **commit** — Audit record creation
- **audit** — Record inspection
- **recovery** — Failure handling

## For Contributors

### Add a Vector

1. Edit the appropriate YAML file in `vectors/`
2. Compile the bundle:
   ```bash
   python3 vectors/compile.py
   ```
3. Submit a pull request with the YAML file and regenerated `vectors/dist/vectors.json`

### Vector Template

```yaml
- id: <unique-id>
  category: <core|commit|extended|candidate>
  status: <valid|proposed|rejected|deprecated>
  title: "<short-title>"
  description: "<detailed-description>"
  phase: <pre-execution|execution|post-execution|commit|audit|recovery>
  severity: <critical|high|medium|low>
  tags: ["<tag>", "<tag>"]
  assertions:
    - statement: "<what-must-be-true>"
      validation: <observable|measurable|auditable|deducible>
  failure_mode: <deny|audit|warn|abort|retry>
  rationale: "<why-this-matters>"
  spec_reference: "<REG-Spec-§-X.Y>"
  added_version: "1.0.0"
  dependencies: ["<vector-id>"]
```

For detailed guidelines, see [`vectors/CONTRIBUTING.md`](vectors/CONTRIBUTING.md).

## Schema

All vectors validate against [`vectors/schema.json`](vectors/schema.json), which enforces:

- Required fields: `id`, `category`, `status`, `title`, `description`
- Standardized enums for `category`, `status`, `phase`, `severity`, `failure_mode`
- Assertion structure with `statement` and optional `validation` type
- Optional metadata: `rationale`, `spec_reference`, `added_version`, `dependencies`, `notes`, `examples`

## License

This repository is licensed under the **Apache License 2.0**. See [`LICENSE`](LICENSE) for details.

## References

- **REG Specification** — [https://example.org/reg-spec/](https://example.org/reg-spec/)
- **Lab Viewer** — `lab/index.html`
- **Contributing Guide** — [`vectors/CONTRIBUTING.md`](vectors/CONTRIBUTING.md)
