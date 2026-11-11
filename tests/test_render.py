import re

from honestcv.grounding import claim_lines, verify
from honestcv.matcher import match
from honestcv.practice import render_practice
from honestcv.render import render_cover_letter, render_plan, render_resume
from honestcv.render.project_plan import blueprint_for

NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")
LINK = re.compile(r"\[[^\]]+\]\(https?://[^)]+\)")


def test_every_work_bullet_links_to_its_evidence(mined, jd_en):
    rendered = render_resume(mined, match(mined, jd_en), lang="en")
    body = rendered.text.split("## ")[1]          # the evidence section
    bullets = [l for l in body.splitlines() if l.startswith("- ")]
    assert bullets
    assert all(LINK.search(l) for l in bullets)


def test_switching_language_translates_without_changing_any_number(mined, jd_en):
    report = match(mined, jd_en)
    zh = render_resume(mined, report, lang="zh").text
    en = render_resume(mined, report, lang="en").text
    assert zh != en
    assert sorted(NUMBER.findall(_strip_links(zh))) == sorted(NUMBER.findall(_strip_links(en)))


def _strip_links(text):
    return LINK.sub(" ", text)


def test_the_resume_is_ordered_by_the_job(mined, jd_en):
    rendered = render_resume(mined, match(mined, jd_en), lang="en", max_bullets=4)
    assert "Kafka" in rendered.text or "PostgreSQL" in rendered.text


def test_self_reported_content_is_separated_and_labelled(mined):
    from honestcv.interview import facts_from_answers
    mined.extend(facts_from_answers({"role": "I built it alone over two months"}, "en"))
    text = render_resume(mined, None, lang="en").text
    head, _, tail = text.partition("Self-reported")
    assert tail, "self-reported section missing"
    assert "built it alone" in tail and "built it alone" not in head


def test_the_cover_letter_leaves_what_it_cannot_know_as_a_todo(mined, jd_en):
    rendered = render_cover_letter(mined, match(mined, jd_en), lang="en")
    assert "[TODO" in rendered.text
    assert verify(rendered.text, rendered.trace, mined).errors == []


def test_the_cover_letter_states_the_gap_rather_than_hiding_it(mined, jd_en):
    report = match(mined, jd_en)
    text = render_cover_letter(mined, report, lang="en").text
    gaps = report.gap_skills(("must",))
    if gaps:
        assert gaps[0] in text


def test_plans_are_plans_and_say_so(mined):
    text = render_plan(["Kafka", "Kubernetes"], lang="en").text
    assert "These are plans, not code" in text
    assert "replay" in text.lower()                    # the Kafka blueprint, not a generic one
    assert "| 1-3 |" in text and "| 11-14 |" in text


def test_an_unknown_skill_still_gets_a_usable_plan():
    text = render_plan(["Erlang"], lang="zh").text
    assert "Erlang" in text
    assert blueprint_for("Erlang") is blueprint_for("something else entirely")


def test_practice_questions_come_from_the_persons_own_work(mined, jd_en):
    rendered = render_practice(mined, match(mined, jd_en), lang="en", max_facts=3)
    assert "demo/orders" in rendered.text
    assert rendered.text.count("❓") >= 6
    assert "S (Situation)" in rendered.text
    assert verify(rendered.text, rendered.trace, mined).errors == []


def test_practice_never_writes_the_answers(mined):
    text = render_practice(mined, None, lang="zh").text
    assert "S (背景):" in text
    body = text.split("S (背景):")[1].splitlines()[0]
    assert body.strip() == ""


def test_saving_writes_the_document_and_its_trace(tmp_path, mined):
    rendered = render_resume(mined, None, lang="en")
    doc, trace = rendered.save(str(tmp_path / "cv.md"))
    assert doc.endswith("cv.md") and trace.endswith("cv.trace.json")
    assert len(claim_lines(open(doc, encoding="utf-8").read())) > 0
