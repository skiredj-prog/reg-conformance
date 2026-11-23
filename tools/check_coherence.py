#!/usr/bin/env python3
"""Coherence check across REG vectors, REG+, the conformance tooling and REG-ARCH.

    python tools/check_coherence.py            # table; exit 1 on a finding not in the baseline
    python tools/check_coherence.py --strict   # exit 1 on any finding
    python tools/check_coherence.py --markdown # report for COHERENCE.md
    python tools/check_coherence.py --json

Each check has a stable id and returns an explicit PASS, FAIL,
CANNOT_EVALUATE, or NOT_APPLICABLE outcome. Missing required inputs,
missing dependencies, or unexpected exceptions are CANNOT_EVALUATE and
always block CI, including when a baseline entry exists. NOT_APPLICABLE
must be explicitly declared by a check with a reason; it is never
inferred from missing input. `coherence-baseline.json` lists known FAIL
findings awaiting a decision. A finding outside the baseline fails the build, so the
list can shrink but cannot grow unnoticed. A baseline entry whose check now
holds also fails, so the baseline is never left stale.

The check reads files only. It changes nothing and decides nothing: where two
sources disagree it reports both and does not say which one is right.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "coherence-baseline.json"
CHECKS = []


def cannot_evaluate(*reasons):
    """An invoked check cannot establish its subject; always blocks CI."""
    if not reasons or not all(isinstance(r, str) and r.strip() for r in reasons):
        raise ValueError("CANNOT_EVALUATE requires one or more non-empty reasons")
    return {"status": "CANNOT_EVALUATE", "evidence": list(reasons)}


def not_applicable(reason):
    """Explicit applicability decision; never infer this from missing files."""
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("NOT_APPLICABLE requires a reason")
    return {"status": "NOT_APPLICABLE", "evidence": [reason]}


def check(cid, layer, title):
    def deco(fn):
        CHECKS.append((cid, layer, title, fn))
        return fn
    return deco


def read(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8") if p.is_file() else ""


def few(items, n=6):
    items = sorted(items)
    return ", ".join(items[:n]) + (f" … (+{len(items) - n})" if len(items) > n else "")


def runner_module():
    sys.path.insert(0, str(ROOT))
    import runner
    return runner


VECTOR_FILES = tuple(sorted(p.stem for p in (ROOT / "vectors").glob("*.yaml")))   # the files compile.py reads, in its order


def load_vector_yaml():
    """-> ({file: parsed}, {file: error})"""
    ok, bad = {}, {}
    for name in VECTOR_FILES:
        try:
            ok[name] = yaml.safe_load(read(f"vectors/{name}.yaml")) or {}
        except yaml.YAMLError as e:
            bad[name] = " ".join(str(e).split())[:140]
    return ok, bad


def yaml_vectors(include_candidates=False):
    ok, _ = load_vector_yaml()
    out = []
    for name in VECTOR_FILES:
        d = ok.get(name, {})
        if "vectors" in d:
            out += d["vectors"]
        elif include_candidates and "candidates" in d:
            out += d["candidates"] + d.get("non_validated", [])
    return out


def vectors_md_rows():
    """VECTORS.md -> {id: (family, rfc, property, status)}"""
    rows = re.findall(r"^\|([A-Z][A-Z0-9\-]+)\|([^|]*)\|([^|]*)\|([^|]*)\|([A-Z]+)\|", read("VECTORS.md"), re.M)
    return {r[0]: r[1:] for r in rows}


# ── REG vectors ──────────────────────────────────────────────────────────────

@check("COH-V01", "REG vectors", "Vector source files are readable")
def v01():
    _, bad = load_vector_yaml()
    return [f"vectors/{n}.yaml does not parse: {e}" for n, e in bad.items()]


@check("COH-V02", "REG vectors", "The runner and the YAML sources register the same vectors")
def v02():
    r = set(runner_module().VECTORS)
    listed = [v["id"] for v in yaml_vectors(include_candidates=True)]
    y = {v["id"] for v in yaml_vectors()}
    out = []
    twice = sorted({i for i in listed if listed.count(i) > 1})
    if twice:
        out.append(f"listed more than once in vectors/*.yaml: {few(twice)}")
    published = [v.get("id") for v in json.loads(read("vectors/dist/vectors.json") or '{"vectors":[]}')["vectors"]]
    twice = sorted({i for i in published if published.count(i) > 1})
    if twice:
        out.append(f"listed more than once in vectors/dist/vectors.json: {few(twice)}")
    if r - y: out.append(f"{len(r - y)} in runner.py, absent from readable vectors/*.yaml: {few(r - y)}")
    if y - r: out.append(f"{len(y - r)} in vectors/*.yaml, absent from runner.py: {few(y - r)}")
    return out


@check("COH-V03", "REG vectors", "vectors/dist/vectors.json is what compile.py produces today")
def v03():
    _, bad = load_vector_yaml()
    if bad:
        return [f"vectors/compile.py cannot run: {few(bad)}.yaml unreadable; the published file cannot be regenerated"]
    want = {v["id"]: v for v in yaml_vectors(include_candidates=True)}
    have = {v["id"]: v for v in json.loads(read("vectors/dist/vectors.json") or '{"vectors":[]}')["vectors"]}
    out = []
    if set(want) - set(have): out.append(f"missing from dist: {few(set(want) - set(have))}")
    if set(have) - set(want): out.append(f"only in dist: {few(set(have) - set(want))}")
    changed = [i for i in set(want) & set(have) if want[i] != have[i]]
    if changed: out.append(f"content differs for: {few(changed)}")
    return out


@check("COH-V04", "REG vectors", "Vector sources follow vectors/schema.json")
def v04():
    try:
        import jsonschema
    except ImportError:
        return None
    schema = json.loads(read("vectors/schema.json"))
    ok, _ = load_vector_yaml()
    out = []
    for name, data in ok.items():
        errs = list(jsonschema.Draft7Validator(schema).iter_errors(data))
        if errs:
            kinds = sorted({e.message[:80] for e in errs})
            out.append(f"vectors/{name}.yaml: {len(errs)} schema error(s), e.g. {kinds[0]}")
    return out


def _stated_counts(text, pattern):
    return [int(n) for n in re.findall(pattern, text)]


@check("COH-V05", "REG vectors", "VECTORS.md lists every registered vector and states the right totals")
def v05():
    r = runner_module()
    rows = vectors_md_rows()
    out = []
    missing = set(r.VECTORS) - set(rows)
    if missing: out.append(f"registered but not listed: {few(missing)}")
    for n in _stated_counts(read("VECTORS.md"), r"registers (\d+) vector IDs"):
        if n != len(r.VECTORS):
            out.append(f"VECTORS.md states {n} registered vectors; runner.py registers {len(r.VECTORS)}")
    return out


@check("COH-V06", "REG vectors", "spec.md states the same totals as the runner")
def v06():
    r = runner_module()
    stated = set(_stated_counts(read("spec.md"), r"(?:dispatches|same) (\d+) (?:vectors|registered IDs)"))
    return [f"spec.md states {n}; runner.py registers {len(r.VECTORS)}" for n in sorted(stated) if n != len(r.VECTORS)]


@check("COH-V07", "REG vectors", "One status vocabulary for vectors")
def v07():
    y = {v["id"]: v.get("status") for v in yaml_vectors()}
    md = {i: row[3] for i, row in vectors_md_rows().items()}
    same = {"implemented": "IMPLEMENTED", "specified": "DECLARED", "proposal": "RESERVED", "lab_validated": "RESERVED"}
    out = []
    yv, mv = sorted({s for s in y.values() if s}), sorted(set(md.values()))
    out.append(f"vectors/*.yaml uses {yv}; VECTORS.md uses {mv}; vectors/schema.json allows "
               f"{json.loads(read('vectors/schema.json'))['properties']['vectors']['items']['properties']['status']['enum']}")
    clash = [i for i in set(y) & set(md) if same.get(y[i]) != md[i]]
    if clash: out.append(f"{len(clash)} vector(s) carry a different status in the two files: {few(clash)}")
    return out if clash or set(yv) - set(same) else []


@check("COH-V08", "REG vectors", "Where an id CT-Rn-… does not rest on RFC-n, the index says so")
def v08():
    rows = vectors_md_rows()
    off = {}
    for i, row in rows.items():
        m = re.match(r"CT-R(\d)-", i)
        if m and not row[1].strip().startswith(f"RFC-{m.group(1)}"):
            off.setdefault(m.group(1), []).append(i)
    if not off or "stable label, not a pointer" in read("VECTORS.md"):
        return []
    return [f"{len(ids)} vector(s) named CT-R{n}-… rest on {rows[ids[0]][1].strip()[:50]}, and VECTORS.md does not say that the prefix is only a label"
            for n, ids in sorted(off.items())]


def coverage():
    """(specified, exercised, registered untested, unregistered, registered outside the RFCs) from the registries."""
    ids, rows = set(runner_module().VECTORS), vectors_md_rows()
    spec = [i for i, r in rows.items() if r[3] in ("IMPLEMENTED", "DECLARED")]
    return (len(spec), sum(rows[i][3] == "IMPLEMENTED" for i in spec),
            sum(i in ids and rows[i][3] == "DECLARED" for i in spec), sum(i not in ids for i in spec),
            sum(rows[i][3] == "RESERVED" for i in ids if i in rows))


@check("COH-V09", "REG vectors", "The published coverage is what the registries give")
def v09():
    want = coverage()
    m = re.search(r"indexes (\d+) properties[^:]*: (\d+) are exercised by the runner, (\d+) are registered and not yet tested, "
                  r"(\d+) are not yet registered\. A further (\d+) registered ids", read("README.md"))
    if not m:
        return [f"README.md does not state the coverage; the registries give {want[0]} specified properties, {want[1]} exercised, "
                f"{want[2]} registered and untested, {want[3]} unregistered, and {want[4]} registered ids outside the frozen RFCs"]
    if tuple(map(int, m.groups())) != want:
        return [f"README.md states {tuple(map(int, m.groups()))}; the registries give {want} "
                "(specified, exercised, registered untested, unregistered, outside the RFCs)"]
    return []


@check("COH-V10", "Conformance tooling", "One suite version across runner, spec and shared module")
def v10():
    found = {}
    for rel, pat in (("runner.py", r"Conformance Suite v(\d+\.\d+\.\d+)"), ("spec.md", r"^# .*?v(\d+\.\d+\.\d+)"),
                     ("reg_common.py", r"Suite v(\d+\.\d+\.\d+)")):
        m = re.search(pat, read(rel), re.M)
        if m: found[rel] = m.group(1)
    return [", ".join(f"{k} says v{v}" for k, v in found.items())] if len(set(found.values())) > 1 else []


def native_run():
    """Outcome of each vector when the runner exercises the bundled reference kernel."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "r.json"
        subprocess.run([sys.executable, "runner.py", "--mode", "native", "--output", str(out)],
                       cwd=ROOT, capture_output=True, text=True)
        if not out.is_file():
            raise RuntimeError("native runner did not produce a report")
        return {r["vector_id"]: r["status"] for r in json.loads(out.read_text(encoding="utf-8"))["results"]}


@check("COH-V11", "REG vectors", "The published result of each vector is what the runner reports today")
def v11():
    actual = native_run()
    if not actual:
        return ["runner.py --mode native produced no report: this check did not run"]
    stated = {v["id"]: v.get("native") for v in yaml_vectors() if v.get("native")}
    off = sorted(i for i in stated if i in actual and stated[i] != actual[i])
    return [f"{i}: vectors/*.yaml publishes {stated[i]}, the runner reports {actual[i]}" for i in off]


@check("COH-V12", "REG vectors", "A vector marked implemented is exercised by the runner")
def v12():
    actual = native_run()
    hollow = sorted(v["id"] for v in yaml_vectors() if v.get("status") == "implemented"
                    and actual.get(v["id"]) in ("IMPLEMENTATION_GAP", "ADAPTER_REQUIRED"))
    return [f"{len(hollow)} vector(s) are marked implemented in vectors/*.yaml while the runner returns a gap without testing them: {few(hollow)}"] if hollow else []


# ── REG+ ─────────────────────────────────────────────────────────────────────

def _profiles():
    return sorted((ROOT / "profiles").glob("*.yaml"))


def _run(args):
    return subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True).stdout


@check("COH-P01", "REG+", "The two profile validators agree")
def p01():
    required = (ROOT / "validate_profiles.py", ROOT / "tools/validate_profiles.py")
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.is_file()]
    if missing:
        return cannot_evaluate(*[f"required profile validator missing: {p}" for p in missing])
    names = [p.name for p in _profiles()]
    a_out = _run(["tools/validate_profiles.py"])
    b_out = _run(["validate_profiles.py"] + [f"profiles/{n}" for n in names])
    a = {n for n in names if re.search(rf"^OK\s+{re.escape(n)}", a_out, re.M)}
    b = {n for n in names if re.search(rf"✅ profiles/{re.escape(n)}", b_out)}
    if a == b:
        return []
    return [f"tools/validate_profiles.py accepts {len(a)}/{len(names)}, validate_profiles.py accepts {len(b)}/{len(names)}",
            f"accepted by one and rejected by the other: {few(a ^ b)}"]


@check("COH-P02", "REG+", "One set of compatibility rules")
def p02():
    files = [f for f in ("catalog/compatibility-rules-v1.yaml", "compatibility-rules-v2.yaml") if (ROOT / f).is_file()]
    if len(files) < 2:
        return cannot_evaluate(
            "expected compatibility rule sources are missing; cannot compare v1 and v2"
        )
    users = {f: [p.relative_to(ROOT).as_posix() for p in list((ROOT / "tools").glob("*.py")) + [ROOT / "validate_profiles.py"]
                 if p.is_file() and p.name != "check_coherence.py" and Path(f).name in p.read_text(encoding="utf-8")] for f in files}
    return [f"{f} is read by {users[f] or 'no tool'}" for f in files]


@check("COH-P03", "REG+", "One quorum rule")
def p03():
    exact = [f for f in ("specs/consensus-contract-v1.md", "README.md") if re.search(r"quorum = f \+ 1", read(f))]
    if re.search(r'quorum:\s*"crash \+ 1"', read("catalog/capabilities-v1.yaml")): exact.append("catalog/capabilities-v1.yaml")
    majority = [f for f in ("compatibility-rules-v2.yaml", "validate_profiles.py") if re.search(r"total_nodes\s*(//|/)\s*2\)?\s*\+\s*1", read(f))]
    if exact and majority:
        return [f"quorum = f + 1 in {few(exact)}; quorum >= floor(n/2) + 1 in {few(majority)}",
                "they differ whenever n > 2f + 1: for n = 5 and f = 1 the first gives 2, the second 3, and two quorums of 2 need not intersect"]
    return []


@check("COH-P04", "REG+", "Profiles use only declared axis values")
def p04():
    axes = (yaml.safe_load(read("catalog/hypotheses-v1.yaml")) or {}).get("axes", {})
    out = []
    for p in _profiles():
        cfg = (yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("config", {})
        for axis, value in cfg.items():
            if axis in axes and value not in axes[axis]["values"]:
                out.append(f"profiles/{p.name}: {axis}={value} is not one of {axes[axis]['values']}")
    return out


def _capabilities():
    return [(p, json.loads(p.read_text(encoding="utf-8"))) for p in sorted((ROOT / "capabilities").glob("v*/*.json"))]


@check("COH-P05", "REG+", "A capability marked demonstrated carries a real evidence hash")
def p05():
    bad = [p.name for p, d in _capabilities() if d["validation"].get("effective_guarantee_demonstrated") is True
           and re.fullmatch(r"0{64}", d["evidence"].get("test_results_hash", ""))]
    return [f"{len(bad)} capability file(s) say demonstrated: true with a hash of 64 zeros: {few(bad)}"] if bad else []


@check("COH-P06", "REG+", "Every invariant a capability cites is defined in the catalogue")
def p06():
    defined = {i["id"] for i in (yaml.safe_load(read("catalog/capabilities-v1.yaml")) or {}).get("normative_invariants", [])}
    cited = {}
    for p, d in _capabilities():
        for i in d["declaration"].get("invariants_required", []):
            if i not in defined: cited.setdefault(i, []).append(p.name)
    return [f"{i} is cited by {len(f)} capability file(s) and defined nowhere in catalog/capabilities-v1.yaml (defined: {sorted(defined)})"
            for i, f in sorted(cited.items())]


def _catalogue():
    return yaml.safe_load(read("catalog/capabilities-v1.yaml")) or {}


def _catalogue_capabilities():
    return {v["capability_id"] for axis in (_catalogue().get("capabilities") or {}).values() for v in axis.values()}


@check("COH-P10", "REG+", "Every normative invariant is attached to something that exists")
def p10():
    cat, caps = _catalogue(), _catalogue_capabilities()
    records = {r["id"] for r in cat.get("guarantee_records") or []}
    cited = {i for _, d in _capabilities() for i in d["declaration"].get("invariants_required", [])}
    out = []
    for inv in cat.get("normative_invariants", []):
        ghosts = [t for t in inv.get("applies_to", []) if t not in caps] + [t for t in inv.get("guarantee_records", []) if t not in records]
        if ghosts:
            out.append(f"{inv['id']} applies to {few(ghosts)}, which the catalogue does not define")
        if not inv.get("applies_to") and not inv.get("guarantee_records") and inv["id"] not in cited:
            out.append(f"{inv['id']} is defined and attached to no capability")
    return out


@check("COH-P11", "REG+", "Every capability file is registered in the catalogue, and the reverse")
def p11():
    cat, caps = _catalogue(), _catalogue_capabilities()
    records = {r["id"]: r for r in cat.get("guarantee_records") or []}
    files = {d.get("capability_id") for _, d in _capabilities()}
    if not files:
        return cannot_evaluate("capability declaration inventory is absent; cannot check catalogue coverage")
    axes = (yaml.safe_load(read("catalog/hypotheses-v1.yaml")) or {}).get("axes", {})
    out = []
    if files - set(records):
        out.append(f"{len(files - set(records))} of {len(files)} capability files are not registered under guarantee_records in the catalogue: {few(files - set(records))}")
    if set(records) - files:
        out.append(f"registered in the catalogue without a capability file: {few(set(records) - files)}")
    for rid, r in records.items():
        if r.get("refines") and r["refines"] not in caps:
            out.append(f"{rid} refines {r['refines']}, which is not a catalogue capability")
        for axis, value in (r.get("applies_when") or {}).items():
            if axis not in axes or value not in axes[axis]["values"]:
                out.append(f"{rid} applies when {axis}={value}, which the hypotheses catalogue does not declare")
    return out


@check("COH-P15", "REG+", "A capability record is attached only to configurations inside the perimeter it declares")
def p15():
    perimeters = {d["capability_id"]: d["declaration"].get("deployment_perimeter") or {} for _, d in _capabilities()}
    try:
        configs = [c for c in json.loads(read("catalog/valid-configurations-v1.json"))["configurations"] if c.get("admissible_structural")]
    except (ValueError, KeyError):
        return None
    out = []
    for r in _catalogue().get("guarantee_records") or []:
        when, perimeter = r.get("applies_when"), perimeters.get(r["id"], {})
        if not when or not perimeter:
            continue
        matched = [c["config"] for c in configs if all(c["config"].get(k) == v for k, v in when.items())]
        outside = [c for c in matched if any(c.get(k) != v for k, v in perimeter.items())]
        if outside:
            out.append(f"{r['id']} declares {perimeter} and is attached to {len(matched)} admissible configurations, {len(outside)} of them outside it")
    return out


@check("COH-P12", "REG+", "A capability's test command names files that exist in the declared target")
def p12():
    source = os.environ.get("REG_TARGET_SOURCE")
    if not source or not Path(source).is_dir():
        return None          # needs a checkout of the target: set REG_TARGET_SOURCE
    missing = {}
    for _, d in _capabilities():
        absent = [f for f in re.findall(r"[\w./-]+\.py", d["evidence"].get("test_command", "")) if not (Path(source) / f).is_file()]
        if absent:
            missing[d["capability_id"]] = absent
    if not missing:
        return []
    claimed = [c for _, d in _capabilities() if (c := d["capability_id"]) in missing and d["validation"].get("effective_guarantee_demonstrated") is True]
    out = [f"{len(missing)} capability file(s) name test files that are not in the target source: {few(missing)}"]
    if claimed:
        out.append(f"of these, marked demonstrated: {few(claimed)}")
    return out


def _effective():
    """{profile name: (errors, warnings)} from tools/verify_effective_guarantees.py."""
    sys.path.insert(0, str(ROOT / "tools"))
    import verify_effective_guarantees as veg
    caps = veg.load_capabilities()
    return {p.name: veg.check_profile(str(p), caps) for p in _profiles()}


@check("COH-P13", "REG+", "An attestation cites a capability that its profile's configuration claims")
def p13():
    out = []
    for name, (_, warnings) in _effective().items():
        loose = sorted(set(re.findall(r"attestation ([\w.\-]+)/([\w.\-]+) non réclamée", " ".join(warnings))))
        if loose:
            cfg = (yaml.safe_load(read(f"profiles/{name}")) or {}).get("config", {})
            out.append(f"profiles/{name} (CONCURRENCY={cfg.get('CONCURRENCY')}) carries {len(loose)} attestation(s) for "
                       f"{few({c for c, _ in loose})}, which that configuration does not claim: {few({e for _, e in loose})}")
    return out


@check("COH-P14", "REG+", "README's evidence table names what the verifier reports missing")
def p14():
    rows = dict(re.findall(r"^\| `([\w.\-]+\.yaml)` \|.*\|([^|]*)\|\s*$", read("README.md"), re.M))
    out = []
    for name, (errors, _) in _effective().items():
        missing = sorted(set(re.findall(r"preuve ([\w.\-]+) manquante", " ".join(errors))))
        if name not in rows:
            out.append(f"profiles/{name} has no row in README's evidence table")
        elif "toutes" not in rows[name]:
            unnamed = [m for m in missing if m not in rows[name]]
            if unnamed:
                out.append(f"README's row for {name} does not name {few(unnamed)}, which tools/verify_effective_guarantees.py reports missing")
    return out


@check("COH-P07", "REG+", "Capability file names match their ids")
def p07():
    off = [f"{p.name} holds id {d.get('capability_id')}" for p, d in _capabilities() if p.stem != d.get("capability_id")]
    return off


@check("COH-P08", "REG+", "Evidence is bound to the declared target revision")
def p08():
    target = (json.loads(read("conformance-target.json") or "{}").get("implementation") or {})
    if not target.get("version"):
        return ["conformance-target.json is absent or names no version: no revision is declared as the one under test"]
    tv, tc, older = target["version"], target.get("source_commit", ""), {}
    for p in _profiles():
        text = p.read_text(encoding="utf-8")
        for v in re.findall(r"tenir_governance[@ ](\d+\.\d+\.\d+)", text):
            if v != tv:
                older.setdefault(v, set()).add(f"profiles/{p.name}")
        for c in re.findall(r"tenir_governance@([0-9a-f]{7,40})\b", text):
            if not tc.startswith(c):
                older.setdefault(c[:7], set()).add(f"profiles/{p.name}")
    unbound = []
    for p, d in _capabilities():
        v, c = d["evidence"].get("implementation_version"), d["evidence"].get("source_commit")
        if v and v != tv:
            older.setdefault(str(v), set()).add("capabilities/")
        elif c and not tc.startswith(c):
            older.setdefault(c[:7], set()).add("capabilities/")
        elif v == tv and not c and d["validation"].get("effective_guarantee_demonstrated") is True:
            unbound.append(d["capability_id"])
    if unbound:
        return [f"marked demonstrated on the target version without stating a source commit: {few(unbound)}"]
    if not older:
        return []
    return [f"the declared target is tenir-governance {tv}; evidence is bound to "
            + "; ".join(f"{k} ({few(v, 2)})" for k, v in sorted(older.items())) + " and has not been replayed on the target"]


@check("COH-P09", "Conformance tooling", "Every release tag has a CHANGELOG entry")
def p09():
    try:
        tags = subprocess.run(["git", "-C", str(ROOT), "tag", "--list", "v*"], capture_output=True, text=True).stdout.split()
    except OSError as exc:
        return cannot_evaluate(f"git tag listing could not execute: {exc}")
    releases = sorted((t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)), key=lambda t: tuple(map(int, t[1:].split("."))))
    entries = set(re.findall(r"^## \[?(v\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M))
    if not releases or not entries:
        return None
    as_tuple = lambda t: tuple(map(int, t[1:].split(".")))
    first = min(entries, key=as_tuple)
    absent = [t for t in releases if t not in entries and as_tuple(t) >= as_tuple(first)]
    return [f"released without a CHANGELOG entry: {few(absent)} (CHANGELOG.md starts at {first})"] if absent else []


# ── across layers ────────────────────────────────────────────────────────────

@check("COH-X01", "Across layers", "An identifier means one thing")
def x01():
    out = []
    manuscripts = sorted((ROOT / "manuscript").glob("v*.md"))
    reg_plus = {i["id"]: i.get("name") for i in (yaml.safe_load(read("catalog/capabilities-v1.yaml")) or {}).get("normative_invariants", [])}
    if manuscripts:
        text = manuscripts[-1].read_text(encoding="utf-8")
        paper = {f"I{n}": name.strip() for n, name in re.findall(r"\*\*\$?I_?(\d)\$? — ([^*]+)\*\*", text)}
        same = lambda x, y: re.sub(r"[^a-z0-9]", "", x.lower()) == re.sub(r"[^a-z0-9]", "", (y or "").lower())
        for i in sorted(set(paper) & set(reg_plus)):
            if same(paper[i], reg_plus[i]):
                continue
            out.append(f"{i} is “{paper[i]}” in manuscript/{manuscripts[-1].name} and “{reg_plus[i]}” in catalog/capabilities-v1.yaml")
    consensus = dict(re.findall(r"^## \d+\. ([^(\n]+?) \((C[1-9])\)", read("specs/consensus-contract-v1.md"), re.M))
    vectors = runner_module().CORE_VECTORS
    for name, cid in sorted(consensus.items(), key=lambda kv: kv[1]):
        if cid in vectors:
            out.append(f"{cid} is “{name}” in specs/consensus-contract-v1.md and vector “{vectors[cid].normative_property}” in runner.py")
    return out


def _vector_refs(row):
    """The ids a row cites: the whole field is '—' or ids separated by ';'."""
    return [t.strip() for t in row.get("vector_ref", "").split(";")]


def crosswalk_rows():
    try:
        return json.loads(read("crosswalk/data/crosswalk.json"))
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as exc:
        raise ValueError(f"crosswalk/data/crosswalk.json could not be read and parsed: {exc}") from exc


@check("COH-X02", "Across layers", "Something links REG vectors to REG+ properties")
def x02():
    known = set(runner_module().VECTORS)
    rows = [r for r in crosswalk_rows() if r.get("framework", "").startswith("REG+")
            and any(t in known for t in _vector_refs(r))]
    if rows:
        return []
    return ["no crosswalk row relates a REG vector to a REG+ capability or invariant; no REG+ file cites a vector id "
            "and the runner cites no REG+ invariant",
            "the registered vectors test RFC-0 to RFC-7; REG+ (BUD, LIN, AGR, consensus) is tested by evidence types and capability files only"]


@check("COH-X05", "Across layers", "Crosswalk rows are well formed, cite vectors that exist and quote text that is still there")
def x05():
    rows, out = crosswalk_rows(), []
    try:
        import jsonschema
        errs = list(jsonschema.Draft202012Validator(json.loads(read("crosswalk/schema.json"))).iter_errors(rows))
        if errs:
            out.append(f"{len(errs)} schema error(s), e.g. {errs[0].message[:90]}")
    except ImportError:
        return None
    known = set(runner_module().VECTORS)
    for r in rows:
        refs = _vector_refs(r)
        for vid in refs:
            if vid not in known and not (vid == "—" and len(refs) == 1):
                out.append(f"{r['id']} cites “{vid}”, which runner.py does not register")
        src = r.get("source") or {}
        m = re.match(r"https://github\.com/skiredj-prog/reg-conformance/blob/[0-9a-f]{40}/([^#]+)", src.get("url", ""))
        if m and src.get("official_wording") not in read(m.group(1)):
            out.append(f"{r['id']} quotes “{src['official_wording'][:50]}”, which is no longer in {m.group(1)}")
    return out


@check("COH-X03", "Across layers", "REG-ARCH is present, or the README says where it lives")
def x03():
    spec = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and re.search(r"REG-ARCH[_ -]v?\d", p.name)]
    if spec or re.search(r"REG-ARCH[^\n]*not ratified[^\n]*`[\w./-]*reg-arch[\w./-]*`", read("README.md")):
        return []
    return ["files refer to REG-ARCH; no REG-ARCH specification file is on this branch and README.md does not say where the candidate lives"]


@check("COH-X04", "Across layers", "README.md introduces every component of the repository")
def x04():
    readme = read("README.md")
    parts = {"runner.py": r"runner\.py", "vectors/": r"vectors/", "reg-standards-baseline/": r"reg-standards-baseline|RFC-\d",
             "crosswalk/": r"crosswalk", "lifecycle/": r"lifecycle/|LIFECYCLE", "capabilities/": r"capabilities/",
             "harness/": r"harness"}
    absent = [k for k, pat in parts.items() if (ROOT / k.rstrip("/")).exists() and not re.search(pat, readme)]
    out = [f"present in the repository, absent from README.md: {few(absent, 8)}"] if absent else []
    return out


@check("COH-X06", "Across layers", "The REG-ARCH Markdown transcription matches the DOCX it is generated from")
def x06():
    script = ROOT / "tools" / "reg_arch_markdown.py"
    target = ROOT / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md"
    source = ROOT / "audits" / "reg-arch-v0.4.1" / "REG-ARCH_v0.4.1-candidate.docx"
    required = (script, target, source)
    missing = [p.relative_to(ROOT).as_posix() for p in required if not p.is_file()]
    if missing:
        return cannot_evaluate(*[f"required REG-ARCH input missing: {p}" for p in missing])
    done = subprocess.run([sys.executable, str(script), "--check"], capture_output=True, text=True)
    if done.returncode == 0:
        return [] if "REG-ARCH Markdown matches its DOCX:" in done.stdout else cannot_evaluate(
            "reg_arch_markdown.py returned success without the expected verification receipt"
        )
    problems = [line[5:] for line in done.stdout.splitlines() if line.startswith("FAIL ")]
    return problems or cannot_evaluate(
        f"reg_arch_markdown.py could not evaluate (exit {done.returncode}): "
        + (done.stderr.strip() or done.stdout.strip() or "no diagnostic")[:500]
    )


# ── driver ───────────────────────────────────────────────────────────────────

def run_all():
    results = []
    for cid, layer, title, fn in CHECKS:
        try:
            outcome = fn()
            if isinstance(outcome, dict):
                status, evidence = outcome.get("status"), outcome.get("evidence")
                if status not in {"PASS", "FAIL", "CANNOT_EVALUATE", "NOT_APPLICABLE"}:
                    raise ValueError(f"unrecognized check status: {status!r}")
                if not isinstance(evidence, list) or not all(isinstance(x, str) for x in evidence):
                    raise TypeError("structured check result needs a list of text evidence")
                if status in {"FAIL", "CANNOT_EVALUATE", "NOT_APPLICABLE"} and not evidence:
                    raise ValueError(f"{status} needs an explanation")
                if status == "PASS" and evidence:
                    raise ValueError("PASS cannot include findings")
            elif outcome is None:
                status = "CANNOT_EVALUATE"
                evidence = ["check returned None without an explicit applicability decision"]
            elif isinstance(outcome, list):
                status = "FAIL" if outcome else "PASS"
                evidence = outcome
            else:
                raise TypeError(f"unsupported outcome type: {type(outcome).__name__}")
        except Exception as exc:
            status = "CANNOT_EVALUATE"
            evidence = [f"check could not run: {type(exc).__name__}: {exc}"]
        results.append({"id": cid, "layer": layer, "title": title,
                        "status": status, "evidence": evidence})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args(argv)

    results = run_all()
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else {}
    findings = {r["id"] for r in results if r["status"] == "FAIL"}
    cannot = {r["id"] for r in results if r["status"] == "CANNOT_EVALUATE"}
    not_applicable_ids = {r["id"] for r in results if r["status"] == "NOT_APPLICABLE"}
    new = sorted(findings - set(baseline))
    healed = sorted(set(baseline) - findings - cannot - not_applicable_ids)

    if args.json:
        print(json.dumps({"results": results, "new": new, "healed": healed,
                          "cannot_evaluate": sorted(cannot),
                          "skipped": sorted(not_applicable_ids)}, indent=2, ensure_ascii=False))
    elif args.markdown:
        print("# Coherence report\n")
        print("Generated by `python tools/check_coherence.py --markdown`. Do not edit by hand.\n")
        print(f"{len(findings)} FAIL, {len(cannot)} CANNOT_EVALUATE, "
              f"{len(not_applicable_ids)} NOT_APPLICABLE across {len(results)} checks. "
              "A non-evaluable check never passes, regardless of baseline.\n")
        layer = None
        for r in results:
            if r["layer"] != layer:
                layer = r["layer"]
                print(f"\n## {layer}\n")
            print(f"### {r['id']} — {r['title']}: {r['status']}\n")
            for evidence in r["evidence"]:
                print(f"- {evidence}")
            if r["id"] in baseline and r["status"] == "FAIL":
                print(f"\nAwaiting: {baseline[r['id']]}")
            print()
    else:
        icons = {"PASS": "✓", "FAIL": "✗", "CANNOT_EVALUATE": "!", "NOT_APPLICABLE": "–"}
        for r in results:
            print(f"{icons[r['status']]} {r['id']} [{r['status']}]  {r['title']}")
            for evidence in r["evidence"]:
                print(f"      {evidence}")
        print(f"\n{len(findings)} FAIL, {len(cannot)} CANNOT_EVALUATE in {len(results)} checks "
              f"| new: {new or 'none'} | fixed but still in baseline: {healed or 'none'}"
              + (f" | not applicable: {sorted(not_applicable_ids)}" if not_applicable_ids else ""))

    # A known FAIL may remain in the baseline; CANNOT_EVALUATE never may.
    if args.strict:
        return 1 if findings or cannot else 0
    return 1 if cannot or new or healed else 0

if __name__ == "__main__":
    sys.exit(main())
