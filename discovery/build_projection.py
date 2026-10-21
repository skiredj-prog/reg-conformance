"""Generate presentation-only REG Discovery projection; never read a UI-owned mapping."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
from discovery.resolve import CATALOG, resolve, load_catalog

HERE=Path(__file__).resolve().parent

def projection(build_time="2026-10-21T00:00:00Z"):
    version,sources,_=load_catalog()
    ids=sorted(sources)
    inputs=(CATALOG/"sources-v0.1.json").read_bytes()+(CATALOG/"assumptions-v0.1.json").read_bytes()
    digest=hashlib.sha256(inputs).hexdigest()
    reports={}
    for count in range(1,len(ids)+1):
        for selected in itertools.combinations(ids,count):
            key="+".join(selected)
            reports[key]=resolve({"selected_sources":list(selected),"generated_at":build_time,"max_findings":5})
    example=json.loads((HERE/"examples"/"payflow-request.json").read_text(encoding="utf-8"))
    example["generated_at"]=build_time
    return {"projection_version":"discovery-presentation-v0.1.0",
            "catalog_version":version,"catalog_sha256":digest,
            "sources":[{"source_id":s["source_id"],"name":s["name"],
                        "source_kind":s["source_kind"],"authority_uri":s["authority_uri"]}
                       for s in sorted(sources.values(),key=lambda x:x["source_id"])],
            "exploratory_reports":reports,
            "fictional_demo":{"label":"PayFlow (fictional premises)", "report":resolve(example)}}

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output",type=Path,required=True)
    cli.add_argument("--html",type=Path)
    args=cli.parse_args()
    data=projection()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    if args.html:
        template=(HERE/"preview"/"template.html").read_text(encoding="utf-8")
        # Presentation embeds one versioned projection only. Escape a script
        # termination sequence to prevent an injected source title from escaping
        # the JSON script tag. The viewer uses textContent, never innerHTML.
        payload=json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("<","\\u003c")
        args.html.parent.mkdir(parents=True,exist_ok=True)
        args.html.write_text(template.replace("/*REG_DISCOVERY_PROJECTION_JSON*/",payload),encoding="utf-8")
    print(f"Projection: {len(data['sources'])} sources, {len(data['exploratory_reports'])} selections; SHA256 {data['catalog_sha256'][:12]}")

if __name__=="__main__":
    main()
