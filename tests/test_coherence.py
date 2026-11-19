"""The coherence check is an instrument: these tests check the instrument, not the repository."""
import re
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRACKED = ["tools", "vectors", "catalog", "crosswalk", "capabilities", "profiles", "specs", "manuscript", "registry",
           "reg-standards-baseline", "kernel", "lifecycle", "runner.py", "reg_common.py", "shim.py", "spec.md",
           "VECTORS.md", "README.md", "CHANGELOG.md", "validate_profiles.py", "compatibility-rules-v2.yaml",
           "coherence-baseline.json", "policy.json", "requirements.txt", "conformance-target.json",
           "capability-evidence-contract-v1.json", "evidence"]


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


def report(root):
    return json.loads(run(root, "--json")[1])


def findings(root):
    return {r["id"] for r in report(root)["results"] if r["evidence"]}


def test_repository_matches_its_baseline():
    code, out = run(ROOT)
    assert code == 0, out


def test_the_copy_used_by_these_tests_starts_clean(copy):
    code, out = run(copy)
    assert code == 0, out


def test_a_new_incoherence_fails_the_build(copy):
    assert "COH-V01" not in findings(copy)
    with (copy / "vectors/core.yaml").open("a", encoding="utf-8") as f:
        f.write("\n  bad: [unclosed\n")
    code, _ = run(copy)
    assert code == 1 and "COH-V01" in report(copy)["new"]


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


def test_a_quotation_that_left_its_source_is_caught(copy):
    assert "COH-X05" not in findings(copy)
    cat = copy / "catalog/capabilities-v1.yaml"
    cat.write_text(cat.read_text(encoding="utf-8").replace("at most one commit per reservation", "at most one commit"), encoding="utf-8")
    assert "COH-X05" in findings(copy)


def test_a_crosswalk_row_citing_an_unknown_vector_is_caught(copy):
    data = copy / "crosswalk/data/crosswalk.json"
    data.write_text(data.read_text(encoding="utf-8").replace('"vector_ref": "C5"', '"vector_ref": "C9"'), encoding="utf-8")
    assert "COH-X05" in findings(copy)


def test_published_coverage_is_checked(copy):
    assert "COH-V09" not in findings(copy)
    readme = copy / "README.md"
    text, n = re.subn(r"indexes \d+ properties", "indexes 31 properties", readme.read_text(encoding="utf-8"), count=1)
    assert n == 1  # the coverage sentence is where COH-V09 reads it
    readme.write_text(text, encoding="utf-8")
    assert "COH-V09" in findings(copy)


def test_an_unregistered_capability_file_is_caught(copy):
    assert "COH-P11" not in findings(copy)
    cat = copy / "catalog/capabilities-v1.yaml"
    cat.write_text(cat.read_text(encoding="utf-8").replace('  - id: "cap-byzantine-tolerance"\n', ""), encoding="utf-8")
    assert "COH-P11" in findings(copy)


def test_a_vector_file_the_compiler_reads_is_read_by_the_check(copy):
    (copy / "vectors/extra.yaml").write_text(
        "meta:\n  name: extra\n  version: 1.0.0\nvectors:\n  - id: CT-R9-001\n    rfc: RFC-9\n    category: extended\n"
        "    property: x\n    intended: y\n    status: proposal\n", encoding="utf-8")
    found = findings(copy)
    assert "COH-V02" in found and "COH-V03" in found


def test_the_readme_evidence_table_is_checked_against_the_verifier(copy):
    assert "COH-P14" not in findings(copy)
    readme = copy / "README.md"
    readme.write_text(readme.read_text(encoding="utf-8").replace("**`test.lock.cross-process`** (exigée par `cap.concurrency.file-lock`), ", ""), encoding="utf-8")
    assert "COH-P14" in findings(copy)


def test_a_vector_listed_twice_is_caught(copy):
    src = copy / "vectors/commit.yaml"
    text = src.read_text(encoding="utf-8")
    block = text[text.index("  - id: CT-R4-001"):text.index("  - id: CT-R4-002")]
    src.write_text(text + "\n" + block, encoding="utf-8")
    assert "COH-V02" in findings(copy)


def test_a_malformed_vector_reference_is_caught(copy):
    data = copy / "crosswalk/data/crosswalk.json"
    data.write_text(data.read_text(encoding="utf-8").replace('"vector_ref": "C3; CT-R4-005"', '"vector_ref": "c3 and CT-R4-005"'), encoding="utf-8")
    assert "COH-X05" in findings(copy)
