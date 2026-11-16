#!/usr/bin/env python3
"""Assemble the evidence bundle of one harness run.

    make_evidence_bundle.py --report report.json --log run.log --out DIR [--zip FILE]

Writes into DIR: the report and log unchanged, environment.json, verdict.json
and SHA256SUMS, then optionally a zip of DIR.

verdict.json is a summary for machines. It is derived from the report only and
is never a certification: `certifying` is always false.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

LEVELS = {1: "SEMANTIC_MAPPING", 2: "ADAPTER_TESTED", 3: "NATIVE_CONFORMANT"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_verdict(report: dict) -> dict:
    binding = report.get("evidence_binding") or {}
    probes = (report.get("harness_probes") or {}).get("results", [])
    level = int(report["evidence_level"])
    if level >= 3:
        raise SystemExit("refusing to bundle: a port run cannot carry evidence level 3")
    passed = [r["vector_id"] for r in report["results"] if r["status"] == "PASS"]
    return {
        "schema": "reg-evidence-verdict/1",
        "certifying": False,
        "statement": ("Diagnostic result of one harness run. Not a certification, not a "
                      "conformance claim, and not evidence about any build other than the "
                      "subject revision below."),
        "harness": binding.get("harness"),
        "subject": binding.get("subject"),
        "port": report.get("port"),
        "evidence_level": level,
        "evidence_label": LEVELS[level],
        "binding_status": binding.get("certification_status"),
        "missing_bindings": binding.get("missing_bindings", []),
        "reg_vectors": {
            "total": report["vector_sets"]["total"],
            "status": report["conformance_status"],
            "summary": report["summary"],
            "passed": passed,
        },
        "effect_probes": {
            "note": "Harness probes. Not REG vectors; excluded from reg_vectors above.",
            "results": {r["vector_id"]: r["status"] for r in probes},
        },
        "ran_at": report.get("ran_at"),
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--report", required=True)
    p.add_argument("--log", default="")
    p.add_argument("--out", required=True)
    p.add_argument("--zip", default="")
    args = p.parse_args(argv)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    report_path = out / "report.json"
    shutil.copyfile(args.report, report_path)
    if args.log and Path(args.log).is_file():
        shutil.copyfile(args.log, out / "run.log")
    report = json.loads(report_path.read_text(encoding="utf-8"))

    try:
        freeze = subprocess.check_output([sys.executable, "-m", "pip", "freeze"],
                                         text=True, stderr=subprocess.DEVNULL).splitlines()
    except Exception:
        freeze = None
    env = {"python": platform.python_version(), "platform": platform.platform(),
           "pip_freeze": freeze,
           "ci": {k: os.environ.get(k) for k in (
               "GITHUB_REPOSITORY", "GITHUB_SHA", "GITHUB_REF", "GITHUB_RUN_ID",
               "GITHUB_RUN_ATTEMPT", "GITHUB_WORKFLOW", "GITHUB_EVENT_NAME", "RUNNER_OS",
               "ImageOS", "ImageVersion")}}
    (out / "environment.json").write_text(json.dumps(env, indent=2), encoding="utf-8")
    verdict = build_verdict(report)
    (out / "verdict.json").write_text(json.dumps(verdict, indent=2), encoding="utf-8")

    names = sorted(f.name for f in out.iterdir() if f.is_file() and f.name != "SHA256SUMS")
    (out / "SHA256SUMS").write_text(
        "".join(f"{sha256(out / n)}  {n}\n" for n in names), encoding="utf-8")
    if args.zip:
        with zipfile.ZipFile(args.zip, "w", zipfile.ZIP_DEFLATED) as z:
            for n in names + ["SHA256SUMS"]:
                z.write(out / n, n)
    v = verdict["reg_vectors"]
    print(f"bundle: {out} | level {verdict['evidence_level']} {verdict['evidence_label']} | "
          f"REG {v['status']} {v['summary']['PASS']}/{v['total']} PASS | "
          f"probes {verdict['effect_probes']['results'] or 'not run'} | certifying: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())
