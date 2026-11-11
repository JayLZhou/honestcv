from honestcv.jd import parse_jd
from honestcv.matcher import match


def test_sections_are_classified(jd_en):
    assert jd_en.title == "Junior Backend Engineer"
    assert jd_en.company == "Northwind Logistics"
    must = " | ".join(r.text for r in jd_en.must_haves())
    nice = " | ".join(r.text for r in jd_en.nice_to_haves())
    assert "Kafka" in must and "Kubernetes" in nice


def test_prose_about_the_team_is_not_a_requirement(jd_en):
    texts = [r.text for r in jd_en.requirements]
    assert not any(t.startswith("We run the order pipeline") for t in texts)


def test_benefits_are_ignored(jd_en):
    assert not any("office" in r.text for r in jd_en.requirements)


def test_chinese_jds_parse_the_same_way(jd_zh):
    must = " | ".join(r.text for r in jd_zh.must_haves())
    assert "Kafka" in must
    assert any("Kubernetes" in r.text for r in jd_zh.nice_to_haves())
    assert "PostgreSQL" in jd_zh.skills()


def test_a_bare_bullet_list_still_parses():
    jd = parse_jd("- Strong Python\n- Some Kubernetes\n")
    assert len(jd.requirements) == 2
    assert jd.requirements[0].skills == ["Python"]


def test_coverage_gaps_and_unread_stay_separate(mined, jd_en):
    report = match(mined, jd_en)
    covered = {c.requirement.text for c in report.covered()}
    assert any("Kafka" in t for t in covered)
    assert "Kubernetes" in report.gap_skills(("nice",))
    # A requirement with no recognisable skill is reported as unread, never as covered.
    unread = [r.text for r in report.unread()]
    assert any("explain a bug" in t for t in unread)
    assert all(r.skills == [] for r in report.unread())


def test_an_alternative_already_met_is_not_a_gap(mined, jd_en):
    # The JD says "FastAPI or Django". Having FastAPI must not produce a Django gap.
    report = match(mined, jd_en)
    assert "Django" not in report.gap_skills()


def test_ranked_facts_put_the_relevant_work_first(mined, jd_en):
    report = match(mined, jd_en)
    ranked = report.ranked_facts()
    assert ranked
    top_skills = {s for f in ranked[:4] for s in f.skills}
    assert top_skills & {"Kafka", "PostgreSQL", "Docker", "Python"}


def test_coverage_ratio_counts_only_readable_requirements(mined, jd_en):
    report = match(mined, jd_en)
    assert 0.0 < report.coverage_ratio("must") <= 1.0
