"""The coherence check is an instrument: these tests check the instrument, not the repository."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRACKED = ["tools", "vectors", "catalog", "capabilities", "profiles", "specs", "manuscript", "registry",
           "reg-standards-baseline", "kernel", "lifecycle", "runner.py", "reg_common.py", "shim.py", "spec.md",
           "VECTORS.md", "README.md", "CHANGELOG.md", "validate_profiles.py", "compatibility-rules-v2.yaml",
           "coherence-baseline.json", "policy.json", "requirements.txt"]


def run(root, *args):
    p = subprocess.run([sys.executable, "tools/check_coherence.py", *args], cwd=root, capture_output=True, text=True)
    return p.returncode, p.stdout


@pytest.fixture()
def copy(tmp_path):
    for name in TRACKED:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.is_file():
            shutil.copy(src, tmp_path / name)
    return tmp_path


def findings(root):
    return {r["id"] for r in json.loads(run(root, "--json")[1])["results"] if r["evidence"]}


def test_repository_matches_its_baseline():
    code, out = run(ROOT)
    assert code == 0, out


def test_a_new_incoherence_fails_the_build(copy):
    assert "COH-V01" not in findings(copy)
    with (copy / "vectors/core.yaml").open("a", encoding="utf-8") as f:
        f.write("\n  bad: [unclosed\n")
    assert run(copy)[0] == 1
    assert "COH-V01" in findings(copy)


def test_a_vector_added_to_one_registry_only_is_caught(copy):
    text = (copy / "vectors/commit.yaml").read_text(encoding="utf-8")
    (copy / "vectors/commit.yaml").write_text(text.replace("id: CT-R4-001", "id: CT-R4-099", 1), encoding="utf-8")
    assert "COH-V02" in findings(copy)


def test_a_stale_published_file_is_caught(copy):
    dist = copy / "vectors/dist/vectors.json"
    data = json.loads(dist.read_text(encoding="utf-8"))
    data["vectors"].pop()
    dist.write_text(json.dumps(data), encoding="utf-8")
    assert "COH-V03" in findings(copy)


def test_a_fixed_finding_must_leave_the_baseline(copy):
    base = copy / "coherence-baseline.json"
    data = json.loads(base.read_text(encoding="utf-8"))
    data["COH-P07"] = "pretend this is still open"
    base.write_text(json.dumps(data), encoding="utf-8")
    code, out = run(copy)
    assert code == 1 and "COH-P07" in out.splitlines()[-1]


def test_strict_mode_fails_while_any_finding_remains(copy):
    assert run(copy, "--strict")[0] == (1 if findings(copy) else 0)
