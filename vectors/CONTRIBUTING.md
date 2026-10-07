# REG Conformance Vector Collection

This directory contains machine-readable conformance vectors for the Runtime Execution Governance (REG) standard.

## Files

- `core.yaml` — core validation scenarios (`C1`..`C5`)
- `commit.yaml` — commit-phase vectors (`CT-R4-001`..`CT-R4-010`)
- `extended.yaml` — extended conformance scenarios (`R0`..`R7`)
- `proposals.yaml` — candidate or non-validated proposals
- `schema.json` — JSON Schema for validating vector structure
- `compile.py` — converts YAML vectors into the bundled JSON artifact

## Contribution workflow

1. Add a new vector to the most relevant YAML file.
2. Keep the identifier format consistent with the surrounding set.
3. Ensure each entry includes a description and status.
4. Run:

```bash
python3 vectors/compile.py
```

5. Review the generated artifact in `vectors/dist/vectors.json`.

## Notes

- Proposed but non-validated items belong in `proposals.yaml`.
- Finalized vectors should be placed in the category-specific YAML files above.
