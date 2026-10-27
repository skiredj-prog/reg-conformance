"""W4.4 offline audit kit: reproducible report and immutable evidence packaging.

Produces no new attestations and never signs native evidence.
The report distinguishes inventory integrity from operational truth.
"""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from .verifier import verify

def canonical(value):
    return (json.dumps(value,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")

def _entries(bundle):
    root=Path(bundle).resolve(strict=True)
    manifest=root/"proof-manifest-v1.json"
    if manifest.is_symlink() or not manifest.is_file(): raise ValueError("Manifest missing")
    data=json.loads(manifest.read_text("utf-8"))
    paths=["proof-manifest-v1.json"]
    for row in data.get("artifacts",[]):
        if not isinstance(row,dict) or not isinstance(row.get("path"),str): raise ValueError("Bad inventory")
        name=row["path"]
        p=Path(name)
        if p.is_absolute() or ".." in p.parts or "\\" in name or name in paths:raise ValueError("Untrusted path")
        file=root/p
        if file.is_symlink() or not file.is_file() or not file.resolve().is_relative_to(root):
            raise ValueError("Missing/linked/outside artifact")
        paths.append(name)
    return root,sorted(paths)

def report(bundle, claim=None):
    result=verify(Path(bundle),claim)
    return {
       "report_version":"proof01-w4-audit/1",
       "inventory_result":result,
       "assurance_level":"documentary-inventory-only",
       "operational_assurance":"NOT_ESTABLISHED",
       "source_provenance":"UNVERIFIED",
       "independent_witness":"UNVERIFIED",
       "integration_lock":"NOT_EVALUATED",
       "limitations":[
           "No inspection of live producer side effects",
           "No signature or external independent witness evaluation",
           "No completeness guarantee for external effects",
           "A matching hash does not attest content truth",
       ],
    }

def package(bundle, output, claim=None):
    root,files=_entries(bundle)
    summary=report(root,claim)
    if summary["inventory_result"]["code"]!="SEMANTIC_PROOF_NOT_ESTABLISHED":
        raise ValueError("Bundle fails W4 inventory gate")
    out=Path(output)
    if out.resolve().is_relative_to(root):raise ValueError("Output must be outside evidence bundle")
    if out.exists():raise ValueError("Refuse to overwrite existing audit artifact")
    # Never mutate original evidence. Deterministic member ordering/timestamps.
    with zipfile.ZipFile(out,"x",compression=zipfile.ZIP_STORED) as z:
        for name in files:
            b=(root/name).read_bytes()
            info=zipfile.ZipInfo("evidence/"+name,(1980,1,1,0,0,0))
            info.external_attr=0o100644<<16
            z.writestr(info,b)
        info=zipfile.ZipInfo("reports/audit-report.json",(1980,1,1,0,0,0))
        info.external_attr=0o100644<<16
        z.writestr(info,canonical(summary))
    return {"archive":str(out),"sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
            "inventory":summary["inventory_result"]["code"],"operational_assurance":"NOT_ESTABLISHED"}

def main():
    p=argparse.ArgumentParser(description="PROOF-01 W4 offline non-certifying audit bundle")
    p.add_argument("bundle",type=Path)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--claim")
    args=p.parse_args()
    try:
        print(json.dumps(package(args.bundle,args.output,args.claim),indent=2))
    except (ValueError,OSError,json.JSONDecodeError) as error:
        p.exit(2,f"W4 fail-closed: {error}\n")

if __name__=="__main__":main()
