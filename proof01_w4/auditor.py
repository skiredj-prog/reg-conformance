"""PROOF-01 W4.4 reproducible offline auditor kit packaging.

Does not create source evidence, private keys, signatures, or a positive
system assurance verdict. Bundle is treated as untrusted data.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import zipfile

from .verifier import verify
from .semantic import check

REQUIRED = ("proof-manifest-v1.json", "convergence.json",
            "reports/test-results.json", "reports/proof-obligations.json")
MAX_FILE_BYTES = 50 * 1024 * 1024

def digest(data):
    return hashlib.sha256(data).hexdigest()

def safe_tree(root):
    root = Path(root).resolve(strict=True)
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise ValueError("Symlink forbidden: " + rel)
        if path.is_file():
            if path.stat().st_size > MAX_FILE_BYTES:
                raise ValueError("Oversized evidence file: " + rel)
            yield rel, path.read_bytes()
        elif not path.is_dir():
            raise ValueError("Unsupported filesystem entry: " + rel)

def auditor_report(bundle, trust_store=None, claim=None):
    root = Path(bundle).resolve(strict=True)
    integrity = verify(root, claim)
    if trust_store:
        semantic = check(root, trust_store, claim or "signed-trace-integrity")
    else:
        semantic = {"outcome": "INDETERMINATE", "code": "TRUST_ANCHORS_NOT_PROVIDED"}
    missing = [name for name in REQUIRED if not (root / name).is_file() or (root / name).is_symlink()]
    problems = []
    if missing:
        problems.append({"code": "CEB01_REQUIRED_FILES_MISSING", "paths": missing})
    convergence = {}
    convpath = root / "convergence.json"
    if convpath.is_file() and not convpath.is_symlink():
        try:
            convergence = json.loads(convpath.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError, OSError):
            problems.append({"code": "CONVERGENCE_INVALID"})
    expected_fields = ("integration_sha", "deployment_manifest_sha256", "topology_id")
    if not isinstance(convergence, dict) or any(
        not isinstance(convergence.get(k), str) or not convergence[k]
        for k in expected_fields
    ):
        problems.append({"code": "INTEGRATION_LOCK_UNESTABLISHED"})
    obligations = {}
    path = root / "reports/proof-obligations.json"
    if path.is_file() and not path.is_symlink():
        try:
            obligations = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeError, OSError):
            problems.append({"code": "OBLIGATIONS_INVALID"})
    # No unverified production PASS. This stage is packaging and
    # consistency reporting only, never a substantive system proof.
    disposition = "HOLD"
    return {"schema_version": "proof01-auditor-report/1",
            "source_lock": "REFERENCED_NOT_INDEPENDENTLY_VERIFIED",
            "integration_lock": "UNVERIFIED",
            "production_gate": disposition,
            "integrity": integrity, "semantic": semantic,
            "proof_obligations": obligations,
            "problems": problems,
            "limitations": [
                "Bundle and its included convergence claims may be self-declared",
                "Native B3 / real G4-A adapter and independent witness custody not established",
                "External provider effect completeness not demonstrated",
                "Source Lock and integrated SUT are separate gates"
            ]}

def make_kit(bundle, output, trust_store=None, claim=None):
    root = Path(bundle).resolve(strict=True)
    out = Path(output).resolve()
    if out.is_relative_to(root):
        raise ValueError("Kit ZIP must be outside the evidence bundle")
    report = auditor_report(root, trust_store, claim)
    source = dict(safe_tree(root))
    generated = {
        "auditor/report.json": (json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode(),
        "auditor/README.txt": (
            "PROOF-01 offline auditor package: immutable copied evidence and report.\n"
            "Inspect auditor/report.json. HOLD is mandatory pending common-SUT convergence.\n"
            "Trust anchors, custody and producer attestations must be independently obtained.\n"
            "SHA256SUMS.txt checks transport integrity only, not authenticity or effect truth.\n"
            "For re-verification use original pinned W4 source plus external trust store.\n"
        ).encode(),
    }
    names = list(source) + list(generated)
    if any(n.startswith("auditor/") or n=="SHA256SUMS.txt" for n in source):
        raise ValueError("Reserved auditor output filename inside source bundle")
    all_entries = {**source, **generated}
    checksums = "".join(f"{digest(data)}  {name}\n" for name,data in sorted(all_entries.items()))
    all_entries["SHA256SUMS.txt"] = checksums.encode()
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for name,data in sorted(all_entries.items()):
            info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o100644<<16
            archive.writestr(info,data)
    return {"zip_sha256":digest(out.read_bytes()),"files":len(all_entries),"report":report}

def main():
    p=argparse.ArgumentParser(description="PROOF-01 W4.4 offline auditor kit")
    p.add_argument("bundle",type=Path);p.add_argument("output",type=Path)
    p.add_argument("--trust-store",type=Path);p.add_argument("--claim")
    args=p.parse_args()
    print(json.dumps(make_kit(args.bundle,args.output,args.trust_store,args.claim),indent=2,sort_keys=True))
if __name__=="__main__":main()
