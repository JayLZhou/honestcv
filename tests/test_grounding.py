import re

import pytest

from honestcv.grounding import (Trace, claim_lines, normalise, render_report, verify,
                                verify_files)
from honestcv.matcher import match
from honestcv.models import Evidence, Fact, FactBase
from honestcv.render import render_resume


@pytest.fixture
def fb():
    base = FactBase()
    base.add(Fact(
        template="bugfix_work",
        payload={"repo": "o/r", "area": "api", "commits": 2, "subject": "a null deref"},
        text="Fixed 2 defects in api of o/r", skills=["Python"],
        evidence=[Evidence(kind="commit", ref="abc1234", repo="o/r",
                           url="https://github.com/o/r/commit/abc1234")],
        metrics={"commits": 2}))
    return base


def _doc_and_trace(fb, line):
    trace = Trace()
    fact = fb.facts[0]
    trace.add(normalise(line), fact_ids=[fact.id], evidence=fact.evidence_ids())
    return "# CV\n\n%s\n" % line, trace


def test_a_generated_document_verifies(mined, jd_en):
    rendered = render_resume(mined, match(mined, jd_en), lang="zh")
    report = verify(rendered.text, rendered.trace, mined)
    assert report.checked_lines > 5
    assert report.errors == []


def test_every_bullet_is_checked(mined):
    rendered = render_resume(mined, None, lang="en")
    assert len(claim_lines(rendered.text)) == report_lines(rendered)


def report_lines(rendered):
    return sum(1 for _ in rendered.trace.lines)


def test_a_line_added_by_hand_is_rejected(fb):
    line = "- Fixed 2 defects in api of o/r [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    doc += "- Led a team of 12 engineers\n"
    report = verify(doc, trace, fb)
    assert [v.code for v in report.errors] == ["untraced_claim"]
    assert not report.ok()


def test_a_number_that_is_not_in_the_evidence_is_rejected(fb):
    line = "- Fixed 2 defects in api of o/r, cutting latency by 90% [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    codes = [v.code for v in verify(doc, trace, fb).errors]
    assert "unbacked_number" in codes


def test_a_skill_the_fact_does_not_show_is_rejected(fb):
    line = "- Fixed 2 defects in api of o/r using Kubernetes [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    codes = [v.code for v in verify(doc, trace, fb).errors]
    assert "unbacked_skill" in codes


def test_a_claim_pointing_at_a_deleted_fact_is_rejected(fb):
    line = "- Fixed 2 defects in api of o/r [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    fb.remove(fb.facts[0].id)
    assert [v.code for v in verify(doc, trace, fb).errors] == ["unknown_fact"]


def test_unverifiable_language_is_a_warning_not_a_lie(fb):
    line = "- Expert in api of o/r, fixed 2 defects [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    report = verify(doc, trace, fb)
    assert [v.code for v in report.warnings] == ["unverifiable_language"]
    assert report.ok() and not report.ok(strict=True)


def test_a_claim_without_a_link_warns(fb):
    line = "- Fixed 2 defects in api of o/r"
    doc, trace = _doc_and_trace(fb, line)
    assert "missing_link" in [v.code for v in verify(doc, trace, fb).warnings]


def test_a_document_with_no_trace_cannot_be_verified(tmp_path, fb):
    doc = tmp_path / "resume.md"
    doc.write_text("- anything\n", encoding="utf-8")
    facts = tmp_path / "facts.json"
    fb.save(str(facts))
    report = verify_files(str(doc), str(facts))
    assert [v.code for v in report.errors] == ["missing_trace"]


def test_code_blocks_are_not_claims(fb):
    line = "- Fixed 2 defects in api of o/r [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    doc += "\n```\n- S (Situation):\n- 100% made up\n```\n"
    assert verify(doc, trace, fb).errors == []


def test_report_rendering_names_the_offending_line(fb):
    doc, trace = _doc_and_trace(fb, "- Fixed 2 defects in api of o/r [abc1234](https://github.com/o/r/commit/abc1234)")
    doc += "- invented\n"
    text = render_report(verify(doc, trace, fb), "en")
    assert "FAIL" in text and "invented" in text


def test_evidence_links_are_not_mistaken_for_numbers(fb):
    # A commit sha contains digits; stripping markup must happen before the number check.
    line = "- Fixed 2 defects in api of o/r [abc1234](https://github.com/o/r/commit/abc1234)"
    doc, trace = _doc_and_trace(fb, line)
    assert verify(doc, trace, fb).errors == []
    assert re.search(r"\d", line)
