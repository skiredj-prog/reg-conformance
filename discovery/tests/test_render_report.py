import copy
import json
from pathlib import Path
from discovery.resolve import resolve
from discovery.render_report import render_report

ROOT=Path(__file__).resolve().parents[1]
EX=json.loads((ROOT/"examples"/"payflow-request.json").read_text(encoding="utf-8"))

def test_escaping_and_external_resource_free():
    req=copy.deepcopy(EX)
    req["behavior"]["claim"]="<script>alert('compliant')</script>"
    html=render_report(resolve(req))
    assert "<script>alert(" not in html
    assert "&lt;script&gt;" in html
    assert 'fetch(' not in html
    assert '<link rel=' not in html
    assert 'DECLARED-PREMISE CONFLICT' in html

def test_empty_behavior_is_exploratory():
    html=render_report(resolve({"selected_sources":["EU_AI_ACT_14"]}))
    assert "No concrete behavior has been declared" in html
    assert "0 declared conflicts" in html
