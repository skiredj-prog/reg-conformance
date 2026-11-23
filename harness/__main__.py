"""python -m harness --port package.module:ClassName [--probes] [--checks] [--output FILE]"""
from __future__ import annotations

import argparse
import json
import os
import sys

import runner as R
from . import properties
from .adapter import EXIT_CODE_RULE_DATE, OUT_OF_EXIT_CODE, PortAdapter, load_port
from .scenarios import CHECKS, PHASES, PROBES, SCENARIOS


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
    every = {**SCENARIOS, **PROBES, **CHECKS}
    report = None   # built once the checks, which may report a row, have run

    def residue(r):
        """One console line: what an observed result does not establish."""
        if r.status.value in properties.OBSERVED:
            print("     ↳ not observed: " + "; ".join(every[r.vector_id].not_observed))

    probes = []
    probes_block = None
    if args.probes:
        probes = adapter.run_probes()
        print("\n  Harness probes (not REG vectors)")
        for r in probes:
            print(f"  {R.MARKS.get(r.status.value, '?')}  {r.vector_id:<16}  {r.status.value:<22}  {r.details or r.gap_note}")
            residue(r)
        probes_block = {
            "note": ("Not REG vectors. Excluded from every vector summary and from "
                     "conformance_status. The property view counts them, as probes."),
            "results": [R.asdict(r) for r in probes]}
    exercises = {vid: s.exercises for vid, s in CHECKS.items()}
    checks = []
    if args.checks:
        checks = adapter.run_checks()
        # Rule of 23 November 2026: a row with no scenario that a check
        # exercised is reported by the check. The check results stay as run.
        folded = PortAdapter.fold_checks(results, checks)
        for before, after in zip(results, folded):
            if after.status != before.status:
                print(f"  {R.MARKS.get(after.status.value, '?')}  {after.vector_id:<16}  "
                      f"{after.status.value:<22}  {after.details[:110]}")
        results = folded
    report = R.generate_report(adapter, results, "", R.build_evidence_binding(adapter, args))
    report["port"] = {"spec": args.port, "name": adapter.port.name,
                      "capabilities": sorted(adapter.port.capabilities)}
    if probes_block is not None:
        report["harness_probes"] = probes_block
    if args.checks:
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
        # P1 (review of 2026-11-23): where a FLAG condition is recorded, it is the
        # one the port's own deployment policy declares and the port acknowledges
        # at dispatch. The harness reads it back from the runtime; it is not a
        # condition of any deployment under supervision.
        "flag_conditions_provenance": (
            "port-declared and port-acknowledged: the FLAG conditions recorded here are "
            "declared by the port's deployment policy (a declaration of this harness) and "
            "acknowledged by the port when it dispatches; the harness reads them back from "
            "the runtime's decision and invents none. They are not conditions of any "
            "supervised deployment."),
        # P2: what a recorded acknowledgement does and does not establish.
        "what_an_acknowledgement_establishes": (
            "A recorded acknowledgement establishes that the runtime saw the declared "
            "condition acknowledged before it dispatched, in this process. It does not "
            "establish that the dispatch took effect outside this process, nor that any "
            "external production supervision of the condition exists: neither is observed "
            "by this harness."),
        # CLAIMS.md / RN-001 §1: a FLAG without a condition is an implementation gap,
        # recorded here; the result it went forward on carries the reserve.
        "implementation_gaps": sorted(c for c, f in adapter.facts.items() if f.get("implementation_gap")),
        "facts": adapter.facts}
    if on_flag:
        print(f"\n  {len(on_flag)} check(s) went forward on FLAG (ALLOW_WITH_MONITORING, RFC-0 §4): "
              + ", ".join(on_flag))
        print(f"  Port-declared condition read back and acknowledged through the port: "
              f"{sum(observed.values())} of {len(on_flag)}")
        print("  The condition is the port's own declaration; the acknowledgement proves "
              "neither effective dispatch outside this process nor external supervision.")

    s = report["summary"]
    code = 1 if s["FAIL"] else 3 if s["INCONCLUSIVE"] else \
        2 if s["IMPLEMENTATION_GAP"] or s["ADAPTER_REQUIRED"] else 0
    report["exit_code"] = code
    # What this run's exit code and conformance_status do not count, row by
    # row, with the reason each row carries. A reader of the report sees the
    # whole registered set; the code counts what can be tested on a subject.
    out_of_code = {r.vector_id: {"status": r.status.value, "reason": r.gap_note or r.details}
                   for r in results if r.status.value in OUT_OF_EXIT_CODE}
    report["exit_code_rule"] = {
        "date": EXIT_CODE_RULE_DATE,
        "rule": ("FAIL -> 1; else INCONCLUSIVE -> 3; else IMPLEMENTATION_GAP or ADAPTER_REQUIRED "
                 "-> 2; else 0. Since 2026-11-23 (standard author's decision, 15:07 UTC): a "
                 "registered row no ratified text specifies (RESERVED, or superseded by the "
                 "RFC-4 v0.3 revision) is NOT_SPECIFIED; a row the implementer declares outside "
                 "the runtime's perimeter, with a signed reason, is NOT_IN_PERIMETER; a row with "
                 "no neutral scenario whose property check passed in this run is "
                 "EXERCISED_BY_CHECK. These are listed below and do not enter the exit code or "
                 "conformance_status. Reports produced before that date are not reinterpreted."),
        "statuses_out_of_exit_code": list(OUT_OF_EXIT_CODE),
        "counted_in_exit_code": {k: s[k] for k in ("FAIL", "INCONCLUSIVE", "IMPLEMENTATION_GAP", "ADAPTER_REQUIRED")},
        "rows_out_of_exit_code": out_of_code}
    if out_of_code:
        tally = {}
        for v in out_of_code.values():
            tally[v["status"]] = tally.get(v["status"], 0) + 1
        print("  Out of the exit code (rule of " + EXIT_CODE_RULE_DATE + "): "
              + ", ".join(f"{k} {n}" for k, n in sorted(tally.items())))
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Results → {args.output}")
    return code


if __name__ == "__main__":
    sys.exit(main())
