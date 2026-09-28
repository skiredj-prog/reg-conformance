# REG Conformance Suite v0.1

Implementation-agnostic conformance runner for the Runtime Execution Governance (REG) Standard.
Five core invariants (C1–C5) and ten commit-integrity vectors (CT-R4-001–010).

## Requirements

```
pip install requests
```

## Usage

```bash
# Point at any REG-compatible endpoint
python runner.py --endpoint http://localhost:8099

# With auth
python runner.py --endpoint https://your-reg-server.example.com --api-key YOUR_TOKEN

# Dev / no TLS
python runner.py --endpoint http://localhost:8099 --insecure --output results/my-impl.json
```

## Running the reference shim (TENIR-Gov kernel)

```bash
pip install fastapi uvicorn pyyaml
uvicorn shim:app --host 127.0.0.1 --port 8099
python runner.py --endpoint http://127.0.0.1:8099
```

## Output

Console table + `results/tenirlabs-v1.json` (schema: see spec.md).

## License

Apache 2.0 — TENIR Labs / Abdelaziz Skiredj
