"""Facts from code that has no history behind it — and the honesty that costs."""
import os
import shutil

import pytest

from honestcv.grounding import verify
from honestcv.matcher import match
from honestcv.mining.authenticity import render_no_history
from honestcv.mining.code_scanner import area_of_path, scan_code, scan_tree
from honestcv.models import FactBase, Person
from honestcv.render import render_resume


@pytest.fixture(scope="session")
def code_only(demo_repo, tmp_path_factory):
    """The same project, handed over as a folder: no .git, no authorship, no dates."""
    dest = tmp_path_factory.mktemp("codeonly") / "orders"
    shutil.copytree(demo_repo, dest)
    shutil.rmtree(dest / ".git")
    os.makedirs(dest / "node_modules" / "left-pad", exist_ok=True)
    (dest / "node_modules" / "left-pad" / "index.js").write_text("module.exports=1\n")
    (dest / "app.min.js").write_text("var a=1;" * 500)
    return str(dest)


@pytest.fixture
def scanned(code_only):
    fb = FactBase(person=Person(name="Demo Candidate"))
    fb.extend(scan_code(code_only, lang="en"))
    return fb


# -- what it reads ----------------------------------------------------------
def test_vendored_and_generated_files_are_ignored(code_only):
    paths = [f.path for f in scan_tree(code_only).files]
    assert not any("node_modules" in p for p in paths)
    assert not any(p.endswith(".min.js") for p in paths)
    assert "src/api/orders.py" in paths


def test_dot_github_is_not_mistaken_for_dot_git(code_only):
    # ".git" is ignored; a prefix test would also throw away ".github", where the
    # CI evidence lives.
    paths = [f.path for f in scan_tree(code_only).files]
    assert any(p.startswith(".github/") for p in paths)


def test_counts_are_counted(code_only):
    result = scan_tree(code_only)
    assert result.source_files
    assert result.lines == sum(f.lines for f in result.files)
    assert result.languages()[0][0] == "Python"


@pytest.mark.parametrize("path,area", [
    ("src/api/orders.py", "src/api"),
    ("tests/test_orders.py", "tests"),
    ("README.md", "(root)"),
])
def test_area_of_path(path, area):
    assert area_of_path(path) == area


# -- what it claims ---------------------------------------------------------
def test_every_code_fact_is_marked_and_file_backed(scanned):
    assert scanned.facts
    for fact in scanned.facts:
        assert fact.source == "code"
        assert fact.evidence
        assert {e.kind for e in fact.evidence} == {"file"}


def test_code_facts_are_weaker_than_commit_facts(scanned, mined):
    assert max(f.confidence for f in scanned.facts) < max(f.confidence for f in mined.facts)


def test_it_finds_what_an_interviewer_asks_about(scanned):
    templates = {f.template for f in scanned.facts}
    assert "code_project" in templates
    assert "code_tests" in templates
    skills = set(scanned.skills())
    assert {"Python", "Docker", "Kafka"} <= skills


def test_a_file_that_merely_defines_a_pattern_is_not_evidence(tmp_path):
    (tmp_path / "patterns.py").write_text(
        'import re\nMODEL = re.compile(r"__tablename__\\\\s*=|CREATE\\\\s+TABLE")\n', encoding="utf-8")
    (tmp_path / "other.py").write_text("x = 1\n" * 10, encoding="utf-8")
    facts = scan_code(str(tmp_path), lang="en")
    assert "code_models" not in {f.template for f in facts}


def test_a_repo_url_makes_file_evidence_clickable(code_only):
    facts = scan_code(code_only, repo_url="https://github.com/me/orders", lang="en")
    urls = [e.url for f in facts for e in f.evidence if e.url]
    assert urls
    assert all(u.startswith("https://github.com/me/orders/blob/main/") for u in urls)
    assert any("#L" in u for u in urls)


def test_an_empty_directory_yields_nothing(tmp_path):
    assert scan_code(str(tmp_path), lang="en") == []


# -- how it is presented ----------------------------------------------------
def test_the_resume_keeps_code_facts_in_their_own_section(scanned):
    text = render_resume(scanned, None, lang="en").text
    head, _, tail = text.partition("no commit history behind these")
    assert tail, "code section missing"
    assert "Built orders" in tail and "Built orders" not in head
    assert "cannot show who wrote them" in tail


def test_verify_warns_on_every_file_only_claim(scanned):
    rendered = render_resume(scanned, None, lang="en")
    report = verify(rendered.text, rendered.trace, scanned)
    assert report.errors == []
    assert report.ok() is True
    assert report.ok(strict=True) is False
    assert "weak_evidence" in {v.code for v in report.warnings}


def test_a_match_report_says_the_coverage_is_file_only(scanned, jd_en):
    from honestcv.matcher import render_match
    text = render_match(match(scanned, jd_en), "en")
    assert "rest on **files** alone" in text


def test_the_no_history_report_offers_a_way_up_not_a_way_round(code_only):
    text = render_no_history(code_only, "en")
    assert "no git history here" in text
    assert "cannot be scored" in text
    assert "Who wrote it" in text
    # It must never suggest manufacturing a past.
    assert "backdated to look like months of work is not" in text
