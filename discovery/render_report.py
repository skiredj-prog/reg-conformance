"""Self-contained, printable Discovery HTML from a validated report."""
import argparse
import html
import json
from pathlib import Path
from discovery.verify_report import validate_report

def escape(v):
    return html.escape(str(v),quote=True)

def render_report(report):
    validate_report(report)
    source_by_id={s["source_id"]:s for s in report["selected_sources"]}
    pieces=[]
    names={"open_question":"OPEN QUESTION","conditional":"CONDITIONAL","structural_conflict":"DECLARED-PREMISE CONFLICT"}
    for f in report["findings"]:
        refs=" · ".join('<a href="%s" target="_blank" rel="noopener noreferrer">%s § %s</a>' % (
            escape(source_by_id[r["source_id"]]["authority_uri"]),escape(r["source_id"]),escape(r["section"])
        ) for r in f["source_refs"])
        invariants="".join("<li>%s: %s</li>" % (escape(x["id"]),escape(x["condition"])) for x in f["candidate_invariants"])
        pieces.append('<article><p class="eyebrow">%s · %s · analyst inference</p><h2>%s</h2><p>%s</p><h3>What to clarify</h3><p>%s</p><h3>Candidate invariants — not confirmed guarantees</h3><ul>%s</ul><p class="refs">%s</p></article>' % (
            escape(f["assumption_id"]),escape(names[f["assessment"]]),escape(f["title"]),
            escape(f["failure_path"]),escape(f["clarifying_question"]),invariants,refs
        ))
    if report["behavior"]:
        intro='<section><p class="eyebrow">Declared behavior, not audited</p><h2>%s</h2><p>%s</p></section>' % (
            escape(report["behavior"]["claim"]),escape(report["behavior"]["scope"]))
    else:
        intro="<section><h2>Exploratory analysis</h2><p>No concrete behavior has been declared. All findings are questions, not conclusions.</p></section>"
    conflicts=sum(f["assessment"]=="structural_conflict" for f in report["findings"])
    summary=("Contradictions among explicitly declared premises only, not observed failures." if conflicts else
             "No structural contradiction can be established from the information supplied.")
    sources="".join('<li><a href="%s" target="_blank" rel="noopener noreferrer">%s</a> — %s — applicability not assessed</li>' % (
        escape(s["authority_uri"]),escape(s["source_id"]),escape(s["source_kind"])) for s in report["selected_sources"])
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>REG Discovery · %s</title><style>
:root{font-family:system-ui,-apple-system,sans-serif;color:#15283a;background:#eef2f7}*{box-sizing:border-box}
body{margin:0}main{max-width:860px;padding:30px 20px;margin:auto}
header,section,article{background:white;border:1px solid #d7e1eb;border-radius:12px;padding:25px;margin:0 0 16px}
header{background:#10263d;color:white;padding:36px}header .eyebrow{color:#7cbeeb}
h1{font-size:33px;margin:7px 0}h2{font-size:21px}h3{font-size:13px;color:#45647c;text-transform:uppercase;margin:18px 0 6px}
.eyebrow{font-size:11px;letter-spacing:.1em;color:#376f9f;font-weight:700}
article{border-left:4px solid #4073a0}p,li{line-height:1.6}a{color:#236ea2}.refs,small{font-size:12px;color:#556575}
button{background:#176090;color:white;border:none;border-radius:6px;padding:12px;cursor:pointer}
@media print{body{background:white}main{max-width:none;padding:0}button{display:none}header,section,article{break-inside:avoid}}
</style></head><body><main>
<header><p class="eyebrow">REG — BEYOND THE CHECKLIST</p><h1>Discovery Report</h1><p>%s · %s · %s</p></header>
<section><p class="eyebrow">EXECUTIVE DISCOVERY</p><h2>%s findings · %s declared conflicts</h2><p>%s</p><small>Selected sources do not establish legal applicability.</small></section>
%s%s
<section><h2>Referenced materials</h2><ul>%s</ul><small>Technical mappings are analyst inferences. This exploratory report does not audit the implementation, authorize deployment or demonstrate any regulatory compliance or technical guarantee.</small></section>
<button onclick="window.print()">Print / Save as PDF</button>
</main></body></html>""" % (escape(report["report_id"]),escape(report["report_id"]),escape(report["generated_at"]),escape(report["catalog_version"]),len(report["findings"]),conflicts,escape(summary),intro,"".join(pieces),sources)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    report=json.loads(args.report.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(render_report(report),encoding="utf-8")
    print("Wrote",args.output)

if __name__=="__main__":
    main()
