"""The coherence check is an instrument: these tests check the instrument, not the repository."""
import re
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TRACKED = ["tools", "vectors", "catalog", "crosswalk", "capabilities", "profiles", "specs", "manuscript", "registry",
           "reg-standards-baseline", "kernel", "lifecycle", "runner.py", "reg_common.py", "shim.py", "spec.md",
           "VECTORS.md", "README.md", "CHANGELOG.md", "CLAIMS.md", "validate_profiles.py", "compatibility-rules-v2.yaml",
           "coherence-baseline.json", "coherence-applicability.json", "policy.json", "requirements.txt", "conformance-target.json",
           "capability-evidence-contract-v1.json", "evidence", "audits"]


def run(root, *args):
    env = os.environ.copy()
    if root != ROOT:
        # The caller declares that this isolated test fixture has no git metadata.
        # No checker may infer NOT_APPLICABLE merely from a missing file.
        env["COHERENCE_FIXTURE_MODE"] = "1"
    p = subprocess.run([sys.executable, "tools/check_coherence.py", *args],
                       cwd=root, capture_output=True, text=True, env=env)
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
    return {r["id"] for r in report(root)["results"]
            if r["status"] in ("FAIL", "CANNOT_EVALUATE")}


def check_result(root, cid):
    matches = [r for r in report(root)["results"] if r["id"] == cid]
    assert len(matches) == 1
    return matches[0]


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


def test_a_hand_edit_of_the_reg_arch_transcription_is_seen(copy):
    assert "COH-X06" not in findings(copy)
    transcription = copy / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md"
    text = transcription.read_text(encoding="utf-8")
    assert "Distinction des statuts" in text
    transcription.write_text(text.replace("Distinction des statuts", "Distinction des status"), encoding="utf-8")
    assert "COH-X06" in findings(copy)


def test_a_reg_arch_transcription_without_its_source_is_seen(copy):
    (copy / "audits" / "reg-arch-v0.4.1" / "REG-ARCH_v0.4.1-candidate.docx").unlink()
    assert "COH-X06" in findings(copy)


def test_coh_x06_missing_generator_is_a_finding(copy):
    (copy / "tools" / "reg_arch_markdown.py").unlink()
    result = check_result(copy, "COH-X06")
    assert result["status"] == "CANNOT_EVALUATE"
    assert any("tools/reg_arch_markdown.py" in reason for reason in result["evidence"])
    assert run(copy)[0] != 0


def test_coh_x06_missing_target_is_a_finding(copy):
    (copy / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md").unlink()
    result = check_result(copy, "COH-X06")
    assert result["status"] == "CANNOT_EVALUATE"
    assert any("v0.4.1-candidate/REG-ARCH.md" in reason for reason in result["evidence"])
    assert run(copy)[0] != 0


def test_coh_x06_both_missing_reports_both(copy):
    (copy / "tools" / "reg_arch_markdown.py").unlink()
    (copy / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md").unlink()
    result = check_result(copy, "COH-X06")
    assert result["status"] == "CANNOT_EVALUATE"
    assert len(result["evidence"]) == 2
    assert "tools/reg_arch_markdown.py" in " ".join(result["evidence"])
    assert "v0.4.1-candidate/REG-ARCH.md" in " ".join(result["evidence"])
    assert run(copy)[0] != 0


def test_coh_x06_present_and_divergent_fails(copy):
    doc = copy / "specs" / "reg-arch" / "v0.4.1-candidate" / "REG-ARCH.md"
    content = doc.read_text(encoding="utf-8")
    assert "Distinction des statuts" in content
    doc.write_text(content.replace("Distinction des statuts", "Distinction des STATUS"), encoding="utf-8")
    result = check_result(copy, "COH-X06")
    assert result["status"] == "FAIL"
    assert any("differs" in reason or "text drift" in reason for reason in result["evidence"])
    assert run(copy)[0] != 0


def test_coh_x06_source_docx_missing_is_not_a_pass(copy):
    (copy / "audits" / "reg-arch-v0.4.1" / "REG-ARCH_v0.4.1-candidate.docx").unlink()
    result = check_result(copy, "COH-X06")
    assert result["status"] == "CANNOT_EVALUATE"
    assert any(".docx" in reason for reason in result["evidence"])
    assert run(copy)[0] != 0


def test_cannot_evaluate_is_blocking_even_if_baselined(copy):
    baseline = copy / "coherence-baseline.json"
    b = json.loads(baseline.read_text(encoding="utf-8"))
    b["COH-X06"] = "this baseline entry may never whitelist missing required input"
    baseline.write_text(json.dumps(b), encoding="utf-8")
    (copy / "tools" / "reg_arch_markdown.py").unlink()
    status, _ = run(copy)
    assert status != 0
    assert "COH-X06" in report(copy)["cannot_evaluate"]


def test_coh_x06_old_fail_open_mutant_is_killed(copy):
    """Run the new negative tests against the old return-[] mutation, not just against the fix."""
    checker = copy / "tools" / "check_coherence.py"
    old = checker.read_text(encoding="utf-8")
    guarded = '    if missing:\n        return cannot_evaluate(*[f"required REG-ARCH input missing: {p}" for p in missing])'
    assert old.count(guarded) == 1
    checker.write_text(old.replace(guarded, "    if missing:\n        return []"), encoding="utf-8")
    shutil.copytree(ROOT / "tests", copy / "tests", ignore=shutil.ignore_patterns("__pycache__"))
    env = os.environ.copy()
    env["COHERENCE_FIXTURE_MODE"] = "1"
    selection = (
        "coh_x06_missing_generator_is_a_finding or "
        "coh_x06_missing_target_is_a_finding or "
        "coh_x06_both_missing_reports_both"
    )
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/test_coherence.py", "-k", selection,
         "--tb=short"], cwd=copy, capture_output=True, text=True, env=env,
    )
    mutation_log = (
        "MUTATION: old COH-X06 behavior restored (missing -> return [])\n"
        + f"Mutant pytest exit code: {p.returncode}\n\n"
        + p.stdout + "\n" + p.stderr
    )
    evidence_path = os.environ.get("COHERENCE_MUTATION_EVIDENCE_PATH")
    if evidence_path:
        output = Path(evidence_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(mutation_log, encoding="utf-8")
    assert p.returncode == 1, mutation_log
    assert "3 failed" in p.stdout, mutation_log


def test_declared_legacy_source_absence_is_explicit_not_applicable(copy):
    p01, p02 = check_result(copy, "COH-P01"), check_result(copy, "COH-P02")
    assert p01["status"] == "NOT_APPLICABLE"
    assert p02["status"] == "NOT_APPLICABLE"
    assert all("coherence-applicability.json" in x for x in p01["evidence"] + p02["evidence"])
    assert run(copy)[0] == 0


def test_undeclared_missing_source_is_cannot_evaluate(copy):
    # The manifest declares only the absence of the *retired* root validator.
    (copy / "tools" / "validate_profiles.py").unlink()
    p01 = check_result(copy, "COH-P01")
    assert p01["status"] == "CANNOT_EVALUATE"
    assert run(copy)[0] != 0


def test_missing_applicability_manifest_is_not_inferred_as_pass(copy):
    (copy / "coherence-applicability.json").unlink()
    assert check_result(copy, "COH-P01")["status"] == "CANNOT_EVALUATE"
    assert check_result(copy, "COH-P02")["status"] == "CANNOT_EVALUATE"
    assert run(copy)[0] != 0


def test_a_vector_count_quoted_in_claims_that_left_the_registry_is_caught(copy):
    # Review of pull request #80: CLAIMS.md quoted 59 vectors when the runner registered 61.
    claims = copy / "CLAIMS.md"
    text = claims.read_text(encoding="utf-8")
    assert "0 of 61 REG vectors executed (61 adapter\n> required)" in text
    claims.write_text(text.replace("0 of 61 REG vectors executed (61 adapter",
                                   "0 of 59 REG vectors executed (59 adapter"), encoding="utf-8")
    assert "COH-V13" in findings(copy)
    assert run(copy)[0] == 1


def test_a_vector_count_whose_parts_exceed_the_total_is_caught(copy):
    claims = copy / "CLAIMS.md"
    text = claims.read_text(encoding="utf-8")
    claims.write_text(text.replace("0 of 61 REG vectors executed (61 adapter",
                                   "3 of 61 REG vectors executed (61 adapter"), encoding="utf-8")
    assert "COH-V13" in findings(copy)


def test_claims_with_no_vector_count_is_a_finding_not_a_pass(copy):
    claims = copy / "CLAIMS.md"
    text = claims.read_text(encoding="utf-8")
    claims.write_text(text.replace("REG vectors executed", "vectors run"), encoding="utf-8")
    assert "COH-V13" in findings(copy)
