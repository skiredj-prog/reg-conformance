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
INDEX = Path(__file__).resolve().parents[1] / "VECTORS.md"
OBSERVED = ("PASS", "FAIL", "INCONCLUSIVE")
NOTE = ("Candidate families, a reading aid. Not part of the frozen RFCs, not a "
        "conformance statement. Effect probes and property checks are counted "
        "here under their own ids; the REG vector summary is unchanged.")


def load(path: Path = FILE) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    known = set(data["families"]) | set(data["groups"])
    stray = sorted(set(data["checks"].values()) - known)
    if stray:
        raise ValueError(f"checks attached to unknown families: {stray}")
    return data


def index_rows(path: Path = INDEX) -> dict:
    """The rows of VECTORS.md: id -> its RFC anchor, property and status.
    IMPLEMENTED and DECLARED rows are specified by the frozen RFCs; a RESERVED
    row is a proposal the RFCs do not specify. Empty if the index is absent."""
    rows = {}
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines:
        if line.startswith("|") and not line.startswith(("|---", "| vector_id")):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 5:
                rows[cells[0]] = {"rfc": cells[2], "property": cells[3], "status": cells[4]}
    return rows


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


def _worst(found) -> str | None:
    """One state for several observed results: a failure outweighs a pass."""
    for state in ("FAIL", "PASS", "INCONCLUSIVE"):
        if state in found:
            return state
    return None


def view(results, probe_results=(), check_results=(), *, registered=(), executable=(),
         exercises=None, data=None) -> dict:
    """Group one run's results by family.

    results, probe_results, check_results: objects with `vector_id` and
    `status`. registered: ids of the registered REG vectors. executable: ids
    that have a scenario in this harness (vectors, probes, property checks).
    exercises: property check id -> the VECTORS.md row it exercises. A
    property check is counted under the family of that row.
    """
    data = data or load()
    registered, executable = set(registered), set(executable)
    exercises = dict(exercises or {})
    stray = sorted(set(exercises.values()) - set(data["checks"]))
    if stray:
        raise ValueError(f"property checks exercise rows the index does not have: {stray}")
    statuses = {r.vector_id: _status(r) for r in results}
    statuses.update({r.vector_id: _status(r) for r in probe_results})
    statuses.update({r.vector_id: _status(r) for r in check_results})

    members, extra = {}, {}
    for row, family in data["checks"].items():
        members.setdefault(family, []).append(row)
    for check, row in exercises.items():
        extra.setdefault(row, []).append(check)

    def own(row):           # every check that exercises this row, the row itself first
        return [row] + extra.get(row, [])

    def has_check(row):     # something in this harness can execute it
        return any(c in executable for c in own(row))

    def runnable(row):
        return row in registered or row.startswith("HX-") or bool(extra.get(row))

    def observed(row):
        return {statuses[c] for c in own(row) if statuses.get(c) in OBSERVED}

    out = {}
    for key, meta in list(data["families"].items()) + list(data["groups"].items()):
        rows = members.get(key, [])
        checks = {c: statuses[c] for row in rows for c in own(row) if c in statuses}
        counts = {s: sum(v == s for v in checks.values()) for s in OBSERVED}
        indexed = [r for r in rows if not r.startswith("HX-")]
        out[key] = {
            "title": meta["title"],
            "dimension": meta.get("dimension"),
            "core": key in data["families"],
            "indexed": len(indexed),
            "registered": sum(r in registered for r in rows),
            "executable": sum(has_check(r) for r in rows),
            # Indexed in VECTORS.md, with no registered vector.
            "unregistered": sum(r not in registered for r in indexed),
            # Indexed in VECTORS.md, with neither a registered vector nor a property check.
            "no_check": sum(not runnable(r) for r in indexed),
            **counts,
            # Rows and probes that have a check and gave no observation on this subject.
            "not_run": sum(runnable(r) and not observed(r) for r in rows),
            "state": _state(counts),
            "checks": checks,
        }

    core = [f for f in out.values() if f["core"]]
    summary = {"families": len(core),
               **{s: sum(f["state"] == s for f in core)
                  for s in ("has_pass", "has_fail", "inconclusive", "not_exercised")}}
    # The same run read row by row: how much of the index this harness can
    # execute, and how much of it gave an observation on this subject.
    rows = [r for r in data["checks"] if not r.startswith("HX-")]
    states = [_worst(observed(r)) for r in rows]
    index = {"indexed": len(rows),
             "with_check": sum(has_check(r) for r in rows),
             "observed": sum(s is not None for s in states),
             **{s: states.count(s) for s in OBSERVED}}
    return {"note": NOTE, "source": "harness/properties.yaml", "status": data.get("status"),
            "summary": summary, "index": index, "families": out,
            "unattached": sorted(set(statuses) - set(data["checks"]) - set(exercises))}


def render(v: dict) -> list:
    """Console lines for a property view."""
    lines = ["  By property (candidate families: a reading aid, not a conformance statement)"]

    def line(key, f, width):
        cells = [f"PASS {f['PASS']}", f"FAIL {f['FAIL']}"]
        if f["INCONCLUSIVE"]:
            cells.append(f"inconclusive {f['INCONCLUSIVE']}")
        cells.append(f"not run {f['not_run']}")
        if f["no_check"]:
            cells.append(f"no check {f['no_check']}")
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
    i = v["index"]
    seen = ", ".join(f"{k} {i[k]}" for k in OBSERVED if i[k]) or "none"
    lines.append(f"  {i['indexed']} indexed properties: {i['with_check']} have an executable check "
                 f"in this harness; {i['observed']} gave an observation on this subject ({seen})")
    return lines
