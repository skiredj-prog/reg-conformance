"""Checks on glossary/glossary-v1.yaml, the shared vocabulary contract.

1. The file is well formed: version, unique ids, required fields.
2. Every errata item it cites exists in manuscript/ERRATA-v7.2.md, and back.
3. Each guard pattern matches only in the files the glossary allows or lists
   as pending. A new ambiguous use fails; a pending file that no longer
   matches fails too, so the pending list is never left stale.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY = yaml.safe_load((ROOT / "glossary" / "glossary-v1.yaml").read_text(encoding="utf-8"))
ERRATA = (ROOT / "manuscript" / "ERRATA-v7.2.md").read_text(encoding="utf-8")

SCANNED = {".md", ".yaml", ".yml", ".py", ".json"}
# The manuscript is published and never edited; the glossary and errata quote
# the old uses on purpose; evidence logs and results are history (rule R3).
EXCLUDED_DIRS = {".git", "manuscript", "glossary", "evidence", "results", "experiments"}
EXCLUDED_FILES = {"tests/test_glossary.py"}


def suite_files():
    for p in ROOT.rglob("*"):
        rel = p.relative_to(ROOT)
        if not p.is_file() or p.suffix not in SCANNED:
            continue
        if rel.parts[0] in EXCLUDED_DIRS or rel.as_posix() in EXCLUDED_FILES:
            continue
        yield rel.as_posix(), p


def pending_files(term):
    out = set()
    for item in term.get("pending", []) or []:
        where = item.get("where")
        for w in ([where] if isinstance(where, str) else where or []):
            out.add(w)
    return out


def test_well_formed():
    assert re.fullmatch(r"\d+\.\d+\.\d+", GLOSSARY["version"])
    ids = [t["id"] for t in GLOSSARY["terms"]]
    assert len(ids) == len(set(ids)), "duplicate glossary id"
    for t in GLOSSARY["terms"]:
        assert t["id"].startswith("GL-"), t["id"]
        for field in ("canonical", "kind", "definition", "finding"):
            assert field in t, f"{t['id']} lacks {field}"


def test_errata_cross_references():
    cited = set(re.findall(r"ERR-7\.2-\d\d", yaml.safe_dump(GLOSSARY)))
    present = set(re.findall(r"^## (ERR-7\.2-\d\d)", ERRATA, flags=re.M))
    assert cited <= present, f"glossary cites missing errata: {sorted(cited - present)}"
    for gid in re.findall(r"`(GL-[A-Z0-9-]+)`", ERRATA):
        assert gid in {t["id"] for t in GLOSSARY["terms"]}, f"errata cites unknown {gid}"


def test_guards():
    problems = []
    files = list(suite_files())
    for term in GLOSSARY["terms"]:
        guard = term.get("guard")
        if not guard:
            continue
        rx = re.compile(guard["pattern"])
        allowed = set(guard.get("allowed") or [])
        pending = pending_files(term)
        hits = {rel for rel, p in files if rx.search(p.read_text(encoding="utf-8", errors="replace"))}
        for rel in sorted(hits - allowed - pending):
            problems.append(f"{term['id']}: new use of /{guard['pattern']}/ in {rel}")
        for rel in sorted((pending - allowed) - hits):
            if (ROOT / rel).exists():
                problems.append(f"{term['id']}: {rel} is listed as pending but no longer matches; close the pending item")
    assert not problems, "\n".join(problems)
