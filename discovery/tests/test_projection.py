from discovery.build_projection import projection

def test_all_31_nonempty_source_combinations_have_a_report():
    p=projection()
    assert p["projection_version"]=="discovery-presentation-v0.1.0"
    assert len(p["sources"])==5
    assert len(p["exploratory_reports"])==31
    assert len(p["catalog_sha256"])==64
    assert all(report["mode"]=="exploratory" for report in p["exploratory_reports"].values())
    assert all(all(f["assessment"]=="open_question" for f in report["findings"]) for report in p["exploratory_reports"].values())

def test_fictional_payflow_is_explicitly_separate_from_exploratory():
    p=projection()
    assert "fictional" in p["fictional_demo"]["label"].lower()
    assert p["fictional_demo"]["report"]["mode"]=="contextualized"
    assert p["fictional_demo"]["report"]["limitations"]["not_implementation_audit"]

def test_projection_generation_is_deterministic():
    assert projection()==projection()
