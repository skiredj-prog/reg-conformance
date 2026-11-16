#!/usr/bin/env python3
"""Coherence check across REG vectors, REG+, the conformance tooling and REG-ARCH.

    python tools/check_coherence.py            # table; exit 1 on a finding not in the baseline
    python tools/check_coherence.py --strict   # exit 1 on any finding
    python tools/check_coherence.py --markdown # report for COHERENCE.md
    python tools/check_coherence.py --json

Each check has a stable id and returns evidence lines; no evidence means the
check holds. `coherence-baseline.json` lists the findings that are known and
awaiting a decision. A finding outside the baseline fails the build, so the
list can shrink but cannot grow unnoticed. A baseline entry whose check now
holds also fails, so the baseline is never left stale.

The check reads files only. It changes nothing and decides nothing: where two
sources disagree it reports both and does not say which one is right.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "coherence-baseline.json"
CHECKS = []


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


VECTOR_FILES = ("commit", "core", "extended", "proposals")   # compile.py order (sorted)


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
        out += d.get("vectors", [])
        if include_candidates:
            out += d.get("candidates", []) + d.get("non_validated", [])
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
    y = {v["id"] for v in yaml_vectors()}
    out = []
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
        return ["jsonschema is not installed: this check did not run"]
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


@check("COH-V08", "REG vectors", "A vector id CT-Rn-… refers to RFC-n")
def v08():
    rows = vectors_md_rows()
    off = {}
    for i, row in rows.items():
        m = re.match(r"CT-R(\d)-", i)
        if m and not row[1].strip().startswith(f"RFC-{m.group(1)}"):
            off.setdefault(m.group(1), []).append(i)
    titles = {n: (re.search(r"^# (.+)$", read(f"reg-standards-baseline/rfc/rfc-{n}.md"), re.M) or [None, "?"])[1] for n in off}
    return [f"{len(ids)} vector(s) named CT-R{n}-… are attributed elsewhere by VECTORS.md ({rows[ids[0]][1].strip()[:40]}); "
            f"RFC-{n} is “{titles[n][:60]}”" for n, ids in sorted(off.items())]


@check("COH-V09", "REG vectors", "The registered suite and the normative properties cover each other")
def v09():
    r = set(runner_module().VECTORS)
    rows = vectors_md_rows()
    reserved = [i for i in r if i in rows and rows[i][3] == "RESERVED"]
    outside = [i for i in rows if i not in r]
    out = []
    if reserved: out.append(f"{len(reserved)} of {len(r)} registered vectors are RESERVED in VECTORS.md: the frozen RFCs do not specify them")
    if outside:
        fam = sorted({re.sub(r"-?\d+$", "", i) for i in outside})
        out.append(f"{len(outside)} properties the RFCs do specify ({', '.join(fam)}) are listed in VECTORS.md but not registered in the runner")
    return out


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
            return {}
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
    if not ((ROOT / "validate_profiles.py").is_file() and (ROOT / "tools/validate_profiles.py").is_file()):
        return []
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
        return []
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


@check("COH-P10", "REG+", "Every normative invariant is cited by at least one capability")
def p10():
    defined = {i["id"] for i in (yaml.safe_load(read("catalog/capabilities-v1.yaml")) or {}).get("normative_invariants", [])}
    cited = {i for _, d in _capabilities() for i in d["declaration"].get("invariants_required", [])}
    idle = sorted(defined - cited)
    return [f"defined in catalog/capabilities-v1.yaml and required by no capability file: {few(idle)}"] if idle and cited else []


@check("COH-P07", "REG+", "Capability file names match their ids")
def p07():
    off = [f"{p.name} holds id {d.get('capability_id')}" for p, d in _capabilities() if p.stem != d.get("capability_id")]
    return off


@check("COH-P08", "REG+", "Evidence refers to one pinned subject revision")
def p08():
    pins = {}
    for rel in [p.relative_to(ROOT).as_posix() for p in _profiles()] + [".github/workflows/lifecycle.yml", "deployment-manifest.json", "README.md"]:
        for m in re.findall(r"tenir_governance(?:\.git)?@([0-9a-f]{7,40}|\d+\.\d+\.\d+)", read(rel)):
            pins.setdefault(m[:7], set()).add(rel)
    for _, d in _capabilities():
        v = d["evidence"].get("implementation_version")
        if v: pins.setdefault(str(v), set()).add("capabilities/")
    return [f"{len(pins)} different subject revisions are cited: " + "; ".join(f"{k} ({few(v, 2)})" for k, v in sorted(pins.items()))] if len(pins) > 1 else []


@check("COH-P09", "Conformance tooling", "Every release tag has a CHANGELOG entry")
def p09():
    try:
        tags = subprocess.run(["git", "-C", str(ROOT), "tag", "--list", "v*"], capture_output=True, text=True).stdout.split()
    except OSError:
        return []
    releases = sorted((t for t in tags if re.fullmatch(r"v\d+\.\d+\.\d+", t)), key=lambda t: tuple(map(int, t[1:].split("."))))
    entries = set(re.findall(r"^## \[?(v\d+\.\d+\.\d+)", read("CHANGELOG.md"), re.M))
    if not releases or not entries:
        return []
    newest = max(entries, key=lambda t: tuple(map(int, t[1:].split("."))))
    late = [t for t in releases if t not in entries and tuple(map(int, t[1:].split("."))) > tuple(map(int, newest[1:].split(".")))]
    return [f"released without a CHANGELOG entry: {few(late)} (CHANGELOG.md stops at {newest})"] if late else []


# ── across layers ────────────────────────────────────────────────────────────

@check("COH-X01", "Across layers", "An identifier means one thing")
def x01():
    out = []
    manuscripts = sorted((ROOT / "manuscript").glob("v*.md"))
    reg_plus = {i["id"]: i.get("name") for i in (yaml.safe_load(read("catalog/capabilities-v1.yaml")) or {}).get("normative_invariants", [])}
    if manuscripts:
        text = manuscripts[-1].read_text(encoding="utf-8")
        paper = {f"I{n}": name.strip() for n, name in re.findall(r"\*\*\$?I_?(\d)\$? — ([^*]+)\*\*", text)}
        for i in sorted(set(paper) & set(reg_plus)):
            out.append(f"{i} is “{paper[i]}” in manuscript/{manuscripts[-1].name} and “{reg_plus[i]}” in catalog/capabilities-v1.yaml")
    consensus = dict(re.findall(r"^## \d+\. ([^(\n]+?) \((C[1-9])\)", read("specs/consensus-contract-v1.md"), re.M))
    vectors = runner_module().CORE_VECTORS
    for name, cid in sorted(consensus.items(), key=lambda kv: kv[1]):
        if cid in vectors:
            out.append(f"{cid} is “{name}” in specs/consensus-contract-v1.md and vector “{vectors[cid].normative_property}” in runner.py")
    return out


@check("COH-X02", "Across layers", "Something links REG vectors to REG+ properties")
def x02():
    r_src = read("runner.py") + "".join(read(f"vectors/{n}.yaml") for n in VECTOR_FILES)
    v_in_plus = sum(len(re.findall(r"CT-R\d-\d{3}", p.read_text(encoding="utf-8", errors="ignore")))
                    for d in ("catalog", "specs", "capabilities", "profiles") for p in (ROOT / d).rglob("*") if p.is_file())
    plus_in_v = len(re.findall(r"\bI8\b|\bLIN\b|\bAGR\b|aggregate budget|quorum", r_src))
    mapping = [f for f in ("registry/coverage.yaml", "catalog/vector-coverage.yaml") if (ROOT / f).is_file()]
    if v_in_plus == 0 and plus_in_v == 0 and not mapping:
        return ["no REG+ file cites a vector id, the runner and vector sources cite no REG+ invariant, and no mapping file exists",
                "the registered vectors test RFC-0 to RFC-7; REG+ (I8, LIN, AGR, consensus) is tested by evidence types and capability files only"]
    return []


@check("COH-X03", "Across layers", "REG-ARCH is present where it is referred to")
def x03():
    spec = [p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and re.search(r"REG-ARCH[_ -]v?\d", p.name)]
    refs = [p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts
            and p.suffix in (".md", ".json", ".yaml", ".yml", ".py")
            and p.name not in ("check_coherence.py", "coherence-baseline.json", "test_coherence.py")
            and "REG-ARCH" in p.read_text(encoding="utf-8", errors="ignore")]
    if refs and not spec:
        return [f"{len(refs)} file(s) refer to REG-ARCH ({few(refs, 3)}); no REG-ARCH specification file is on this branch"]
    return []


@check("COH-X04", "Across layers", "README.md introduces every component of the repository")
def x04():
    readme = read("README.md")
    parts = {"runner.py": r"runner\.py", "vectors/": r"vectors/", "reg-standards-baseline/": r"reg-standards-baseline|RFC-\d",
             "crosswalk/": r"crosswalk", "lifecycle/": r"lifecycle/|LIFECYCLE", "capabilities/": r"capabilities/",
             "harness/": r"harness"}
    absent = [k for k, pat in parts.items() if (ROOT / k.rstrip("/")).exists() and not re.search(pat, readme)]
    return [f"present in the repository, absent from README.md: {few(absent, 8)}"] if absent else []


# ── driver ───────────────────────────────────────────────────────────────────

def run_all():
    results = []
    for cid, layer, title, fn in CHECKS:
        try:
            evidence = fn()
        except Exception as e:                      # a check that cannot run is itself a finding
            evidence = [f"check could not run: {type(e).__name__}: {e}"]
        results.append({"id": cid, "layer": layer, "title": title, "evidence": evidence})
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    args = ap.parse_args(argv)

    results = run_all()
    baseline = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.is_file() else {}
    findings = {r["id"] for r in results if r["evidence"]}
    new, healed = sorted(findings - set(baseline)), sorted(set(baseline) - findings)

    if args.json:
        print(json.dumps({"results": results, "new": new, "healed": healed}, indent=2, ensure_ascii=False))
    elif args.markdown:
        print("# Coherence report\n")
        print("Generated by `python tools/check_coherence.py --markdown`. Do not edit by hand.\n")
        print(f"{len(findings)} of {len(results)} checks report a finding. "
              "Where two sources disagree, both are quoted; the report does not say which is right.\n")
        layer = None
        for r in results:
            if r["layer"] != layer:
                layer = r["layer"]; print(f"\n## {layer}\n")
            mark = "FINDING" if r["evidence"] else "holds"
            print(f"### {r['id']} — {r['title']}: {mark}\n")
            for e in r["evidence"]:
                print(f"- {e}")
            if r["id"] in baseline and r["evidence"]:
                print(f"\nAwaiting: {baseline[r['id']]}")
            print()
    else:
        for r in results:
            print(f"{'✗' if r['evidence'] else '✓'} {r['id']}  {r['title']}")
            for e in r["evidence"]:
                print(f"      {e}")
        print(f"\n{len(findings)} finding(s) in {len(results)} checks | new: {new or 'none'} | fixed but still in baseline: {healed or 'none'}")

    if args.strict:
        return 1 if findings else 0
    return 1 if new or healed else 0


if __name__ == "__main__":
    sys.exit(main())
