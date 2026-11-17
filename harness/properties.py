"""Property view: a second reading of one run, by candidate family.

The families in properties.yaml are candidates. They are not part of the
frozen RFCs and they are not ratified. This module groups the results a run
already produced: it changes no result, no status and no tally, and it draws
no conclusion. It counts.

A family line answers one question: among the checks that exercise this
property, how many were observed to pass or fail on this subject, and how
many could not be run.
"""
from __future__ import annotations

from pathlib import Path

import yaml

FILE = Path(__file__).with_name("properties.yaml")
OBSERVED = ("PASS", "FAIL", "INCONCLUSIVE")
NOTE = ("Candidate families, a reading aid. Not part of the frozen RFCs, not a "
        "conformance statement. Effect probes are counted here as probes; the "
        "REG vector summary is unchanged.")


def load(path: Path = FILE) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    known = set(data["families"]) | set(data["groups"])
    stray = sorted(set(data["checks"].values()) - known)
    if stray:
        raise ValueError(f"checks attached to unknown families: {stray}")
    return data


def _status(result) -> str:
    return getattr(result.status, "value", result.status)


def _state(counts: dict) -> str:
    if counts["FAIL"]:
        return "has_fail"
    if counts["PASS"]:
        return "has_pass"
    if counts["INCONCLUSIVE"]:
        return "inconclusive"
    return "not_exercised"


def view(results, probe_results=(), *, registered=(), executable=(), data=None) -> dict:
    """Group one run's results by family.

    results, probe_results: objects with `vector_id` and `status`.
    registered: ids of the registered REG vectors. executable: ids that have a
    scenario in this harness (vectors and probes).
    """
    data = data or load()
    registered, executable = set(registered), set(executable)
    probes = {r.vector_id: _status(r) for r in probe_results}
    statuses = {r.vector_id: _status(r) for r in results}
    statuses.update(probes)

    members = {}
    for check, family in data["checks"].items():
        members.setdefault(family, []).append(check)

    out = {}
    for key, meta in list(data["families"].items()) + list(data["groups"].items()):
        ids = members.get(key, [])
        runnable = [c for c in ids if c in registered or c.startswith("HX-")]
        checks = {c: statuses[c] for c in ids if c in statuses}
        counts = {s: sum(v == s for v in checks.values()) for s in OBSERVED}
        out[key] = {
            "title": meta["title"],
            "dimension": meta.get("dimension"),
            "core": key in data["families"],
            "indexed": sum(not c.startswith("HX-") for c in ids),
            "registered": sum(c in registered for c in ids),
            "executable": sum(c in executable for c in ids),
            # Indexed in VECTORS.md, with no registered vector to run.
            "unregistered": sum(not c.startswith("HX-") and c not in registered for c in ids),
            **counts,
            "not_run": sum(checks.get(c) not in OBSERVED for c in runnable),
            "state": _state(counts),
            "checks": checks,
        }

    core = [f for f in out.values() if f["core"]]
    summary = {"families": len(core),
               **{s: sum(f["state"] == s for f in core)
                  for s in ("has_pass", "has_fail", "inconclusive", "not_exercised")}}
    return {"note": NOTE, "source": "harness/properties.yaml", "status": data.get("status"),
            "summary": summary, "families": out,
            "unattached": sorted(set(statuses) - set(data["checks"]))}


def render(v: dict) -> list:
    """Console lines for a property view."""
    lines = ["  By property (candidate families: a reading aid, not a conformance statement)"]

    def line(key, f, width):
        cells = [f"PASS {f['PASS']}", f"FAIL {f['FAIL']}"]
        if f["INCONCLUSIVE"]:
            cells.append(f"inconclusive {f['INCONCLUSIVE']}")
        cells.append(f"not run {f['not_run']}")
        if f["unregistered"]:
            cells.append(f"no vector {f['unregistered']}")
        return f"  {key:<{width}} {f['title'][:54]:<54}  " + "  ".join(cells)

    core = [(k, f) for k, f in v["families"].items() if f["core"]]
    lines += [line(k, f, max(len(k) for k, _ in core)) for k, f in core]
    seen = [(k, f) for k, f in v["families"].items()
            if not f["core"] and (f["PASS"] or f["FAIL"] or f["INCONCLUSIVE"])]
    if seen:
        lines.append("  Outside the candidate core")
        lines += [line(k, f, max(len(k) for k, _ in seen)) for k, f in seen]
    s = v["summary"]
    tail = (f"  {s['families']} candidate families: {s['has_pass']} with a passing check and "
            f"no failing one, {s['has_fail']} with a failing check")
    if s["inconclusive"]:
        tail += f", {s['inconclusive']} inconclusive only"
    lines.append(tail + f", {s['not_exercised']} not exercised")
    return lines
