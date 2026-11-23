"""python -m harness --port package.module:ClassName [--probes] [--checks] [--output FILE]"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback

import runner as R
from . import properties
from .adapter import PortAdapter, load_port
from .scenarios import CHECKS, PHASES, PROBES, SCENARIOS


# Exit codes. 4 comes first: a run in which a test did not run to a result
# is not a conformance result, whatever the other tests gave.
EXIT_HARNESS_ERROR = 4


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse exits 2 on a usage error, and 2 means "gaps" to the workflow:
        # a run that never started must not read as a clean one.
        self.print_usage(sys.stderr)
        self.exit(EXIT_HARNESS_ERROR, f"{self.prog}: error: {message}\n")


def main(argv=None):
    # Parsed outside the guard, so that --help keeps 0 and a usage error its 4.
    args = _parser().parse_args(argv)
    try:
        return _run(args)
    except (Exception, SystemExit):
        # The harness itself stopped (a port that cannot load, a port that breaks
        # a harness rule, a port that calls sys.exit). Python would exit 1, which
        # reads as FAIL, or whatever code the port chose, 0 included: not a result.
        traceback.print_exc()
        print("\n  HARNESS_ERROR: the run stopped before a result; the subject was not "
              "evaluated.", file=sys.stderr)
        return EXIT_HARNESS_ERROR


def _parser():
    p = _Parser(prog="python -m harness",
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
    return p


def _run(args):
    adapter = PortAdapter(load_port(args.port))
    results = adapter.run_all()
    for r in results:
        print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details}")
        if r.gap_note and r.status.value not in ("PASS", "FAIL"):
            print(f"     ↳ {r.gap_note[:120]}")
    report = R.generate_report(adapter, results, "", R.build_evidence_binding(adapter, args))
    report["port"] = {"spec": args.port, "name": adapter.port.name,
                      "capabilities": sorted(adapter.port.capabilities)}
    every = {**SCENARIOS, **PROBES, **CHECKS}

    def residue(r):
        """One console line: what an observed result does not establish."""
        if r.status.value in properties.OBSERVED:
            print("     ↳ not observed: " + "; ".join(every[r.vector_id].not_observed))

    probes = []
    if args.probes:
        probes = adapter.run_probes()
        print("\n  Harness probes (not REG vectors)")
        for r in probes:
            print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details or r.gap_note}")
            residue(r)
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
            residue(r)
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

    # Where each scenario observes and what its result does not establish,
    # with the conditions this run observed under.
    port = adapter.port
    report["observation"] = {
        "note": ("A result holds for the case submitted, at the point named, under the "
                 "conditions below. `not_observed` lists what it does not establish. The "
                 "harness sets no duration: bounds are the ones the port declares for the "
                 "subject."),
        "conditions": {"effect_window_s": port.effect_window,
                       "clock_mode": port.clock_mode or None,
                       "declared_bounds_s": dict(port.bounds),
                       "exhaustion_policy": port.exhaustion_policy},
        "phases": list(PHASES),
        "checks": {vid: {"at": sc.at, "not_observed": list(sc.not_observed)}
                   for vid, sc in every.items()}}
    declared = ", ".join(f"{k} {v:g} s" for k, v in sorted(port.bounds.items())) or "none"
    print(f"\n  Observed under: effect window {port.effect_window:g} s; clock "
          f"{port.clock_mode or 'not declared'}; declared bounds: {declared}")
    if not args.checks and not args.probes:
        print("  What each result does not establish is in the report, under `observation`.")

    # Which checks went forward on a FLAG, and whether its condition was observed.
    on_flag = sorted(c for c, f in adapter.facts.items() if f.get("admitted_on") == "FLAG")
    observed = {c: bool(adapter.facts[c].get("flag_conditions")) for c in on_flag}
    report["admission"] = {
        "rule": ("RFC-0 §4: PASS (ALLOW) and FLAG (ALLOW_WITH_MONITORING) both let execution "
                 "proceed. A FLAG proceeds only under an explicit condition or supervision."),
        "checks_admitted_on_flag": on_flag,
        "flag_condition_observed": observed,
        # CLAIMS.md / RN-001 §1: a FLAG without a condition is an implementation gap,
        # recorded here; the result it went forward on carries the reserve.
        "implementation_gaps": sorted(c for c, f in adapter.facts.items() if f.get("implementation_gap")),
        "facts": adapter.facts}
    if on_flag:
        print(f"\n  {len(on_flag)} check(s) went forward on FLAG (ALLOW_WITH_MONITORING, RFC-0 §4): "
              + ", ".join(on_flag))
        print(f"  Condition or supervision observed through the port: "
              f"{sum(observed.values())} of {len(on_flag)}")

    s = report["summary"]
    # Vectors, probes and property checks alike: none may stand in for a result.
    errors = sorted(r.vector_id for r in [*results, *probes, *checks]
                    if r.status == R.ReportingState.HARNESS_ERROR)
    report["harness_errors"] = errors
    if errors:
        # Probe and check results never enter conformance_status; a test that did
        # not run does: the run as a whole is not a conformance result.
        report["conformance_status"] = "HARNESS_ERROR"
        print(f"\n  HARNESS_ERROR on {len(errors)} test(s): " + ", ".join(errors))
        print("  These did not run to a result. The run is not a conformance result.")
    code = EXIT_HARNESS_ERROR if errors else 1 if s["FAIL"] else 3 if s["INCONCLUSIVE"] else \
        2 if s["IMPLEMENTATION_GAP"] or s["ADAPTER_REQUIRED"] else 0
    report["exit_code"] = code
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Results → {args.output}")
    return code


if __name__ == "__main__":
    sys.exit(main())
