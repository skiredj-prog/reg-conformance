#!/usr/bin/env python3
"""Compile YAML vector files into a single JSON payload."""

from __future__ import annotations

import json
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required. Install it with: pip install pyyaml") from exc

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
OUTPUT = DIST / "vectors.json"


def load_yaml_file(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def main() -> None:
    files = sorted(ROOT.glob("*.yaml"))
    compiled = {
        "generated_from": [p.name for p in files],
        "vectors": [],
        "meta": {
            "source": "reg-conformance/vectors",
            "format": "reg-vector-v1"
        },
    }

    for path in files:
        data = load_yaml_file(path)
        if "vectors" in data:
            compiled["vectors"].extend(data["vectors"])
        elif "candidates" in data:
            compiled["vectors"].extend(data["candidates"])
            compiled["vectors"].extend(data.get("non_validated", []))

    DIST.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(compiled, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
