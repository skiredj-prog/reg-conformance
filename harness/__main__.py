"""python -m harness --port package.module:ClassName [--probes] [--output FILE]"""
from __future__ import annotations

import argparse
import json
import os
import sys

import runner as R
from .adapter import PortAdapter, load_port


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness",
                                description="Run the REG vector set against a RuntimePort.")
    p.add_argument("--port", required=True, help="package.module:ClassName")
    p.add_argument("--probes", action="store_true",
                   help="also run the harness effect probes (not REG vectors)")
    p.add_argument("--conformance-profile", default="REG-v0.3.1-RFC-4-strict-C3")
    p.add_argument("--subject-repository", default="")
    p.add_argument("--subject-revision", default="")
    p.add_argument("--subject-version", default="")
    p.add_argument("--subject-worktree-state", choices=["clean", "dirty", "unknown"], default="unknown")
    p.add_argument("--environment-digest", default="")
    p.add_argument("--output", default="results/port-run.json")
    args = p.parse_args(argv)

    adapter = PortAdapter(load_port(args.port))
    results = adapter.run_all()
    for r in results:
        print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details}")
        if r.gap_note and r.status.value not in ("PASS", "FAIL"):
            print(f"     ↳ {r.gap_note[:120]}")
    report = R.generate_report(adapter, results, "", R.build_evidence_binding(adapter, args))
    report["port"] = {"spec": args.port, "name": adapter.port.name,
                      "capabilities": sorted(adapter.port.capabilities)}
    if args.probes:
        probes = adapter.run_probes()
        print("\n  Harness probes (not REG vectors)")
        for r in probes:
            print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details or r.gap_note}")
        report["harness_probes"] = {
            "note": "Not REG vectors. Excluded from every summary and from conformance_status.",
            "results": [R.asdict(r) for r in probes]}
    print("\n  " + "  ".join(f"{k}: {v}" for k, v in report["summary"].items() if v))

    s = report["summary"]
    code = 1 if s["FAIL"] else 3 if s["INCONCLUSIVE"] else \
        2 if s["IMPLEMENTATION_GAP"] or s["ADAPTER_REQUIRED"] else 0
    report["exit_code"] = code
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Results → {args.output}")
    return code


if __name__ == "__main__":
    sys.exit(main())
