"""python -m harness --port package.module:ClassName [--probes] [--checks] [--output FILE]"""
from __future__ import annotations

import argparse
import json
import os
import sys

import runner as R
from . import properties
from .adapter import PortAdapter, load_port
from .scenarios import CHECKS, PROBES, SCENARIOS


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m harness",
                                description="Run the REG vector set against a RuntimePort.")
    p.add_argument("--port", required=True, help="package.module:ClassName")
    p.add_argument("--probes", action="store_true",
                   help="also run the harness effect probes (not REG vectors)")
    p.add_argument("--checks", action="store_true",
                   help="also run the property checks (not REG vectors)")
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
    probes = []
    if args.probes:
        probes = adapter.run_probes()
        print("\n  Harness probes (not REG vectors)")
        for r in probes:
            print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details or r.gap_note}")
        report["harness_probes"] = {
            "note": ("Not REG vectors. Excluded from every vector summary and from "
                     "conformance_status. The property view counts them, as probes."),
            "results": [R.asdict(r) for r in probes]}
    exercises = {vid: s.exercises for vid, s in CHECKS.items()}
    checks = []
    if args.checks:
        checks = adapter.run_checks()
        index = properties.index_rows()
        rows = {vid: {"row": row, **index.get(row, {})} for vid, row in exercises.items()}
        print("\n  Property checks (not REG vectors)")
        for r in checks:
            row = rows[r.vector_id]
            print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details or r.gap_note}")
            print(f"     ↳ row {row['row']}, {row.get('rfc', '?')}, {row.get('status', '?')}: "
                  f"{row.get('property', '')}"[:170])
            if r.details and r.gap_note:
                print(f"     ↳ {r.gap_note[:160]}")
        report["property_checks"] = {
            "note": ("Not REG vectors. Each one exercises a property indexed in VECTORS.md "
                     "that has no executable vector. Excluded from every vector summary and "
                     "from conformance_status. The property view counts them under the "
                     "family of the row they exercise. A row whose status is RESERVED is a "
                     "proposal the frozen RFCs do not specify."),
            "exercises": exercises,
            "rows": rows,
            "results": [R.asdict(r) for r in checks]}
    print("\n  " + "  ".join(f"{k}: {v}" for k, v in report["summary"].items() if v))

    # A second reading of the same results, by candidate property family.
    view = properties.view(results, probes, checks, registered=R.VECTORS,
                           executable=set(SCENARIOS) | set(PROBES) | set(CHECKS),
                           exercises=exercises)
    report["property_view"] = view
    print("\n" + "\n".join(properties.render(view)))

    # Which checks went forward on a FLAG, and whether its condition was observed.
    on_flag = sorted(c for c, f in adapter.facts.items() if f.get("admitted_on") == "FLAG")
    observed = {c: bool(adapter.facts[c].get("flag_conditions")) for c in on_flag}
    report["admission"] = {
        "rule": ("RFC-0 §4: PASS (ALLOW) and FLAG (ALLOW_WITH_MONITORING) both let execution "
                 "proceed. A FLAG proceeds only under an explicit condition or supervision."),
        "checks_admitted_on_flag": on_flag,
        "flag_condition_observed": observed,
        "facts": adapter.facts}
    if on_flag:
        print(f"\n  {len(on_flag)} check(s) went forward on FLAG (ALLOW_WITH_MONITORING, RFC-0 §4): "
              + ", ".join(on_flag))
        print(f"  Condition or supervision observed through the port: "
              f"{sum(observed.values())} of {len(on_flag)}")

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
