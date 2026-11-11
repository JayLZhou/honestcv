from honestcv.mining import list_authors, mine_repo, repo_identity
from honestcv.mining.git_miner import GitError, area_of, classify, read_commits
import pytest


def test_identity_comes_from_the_remote(demo_repo):
    slug, base = repo_identity(demo_repo)
    assert slug == "demo/orders"
    assert base == "https://github.com/demo/orders"


def test_every_mined_fact_carries_checkable_evidence(mined):
    assert mined.facts
    for fact in mined.facts:
        assert fact.evidence, fact.text
        for ev in fact.evidence:
            assert ev.url.startswith("https://github.com/demo/orders/")


def test_numbers_in_facts_are_counted_not_estimated(demo_repo, mined):
    commits = read_commits(demo_repo, author="demo@example.com")
    sustained = [f for f in mined.facts if f.kind == "sustained"][0]
    assert sustained.payload["commits"] == len(commits)
    assert sustained.payload["first"] == min(c.date for c in commits)
    assert sustained.payload["last"] == max(c.date for c in commits)


def test_the_sustained_fact_claims_no_skills(mined):
    # "I committed for 22 days" is not evidence of Kafka. Letting this fact carry
    # skills made it match every requirement in a JD.
    sustained = [f for f in mined.facts if f.kind == "sustained"][0]
    assert sustained.skills == []


def test_dependencies_the_person_added_become_adoption_facts(mined):
    adopted = {s for f in mined.facts if f.kind == "adoption" for s in f.skills}
    assert {"Kafka", "Redis", "PostgreSQL"} <= adopted
    assert "Python" not in adopted      # came from `kafka-python`, not from a real adoption


def test_small_infrastructure_commits_are_not_lost(mined):
    tools = {s for f in mined.facts if f.template == "setup_tool" for s in f.skills}
    assert "Docker" in tools and "CI/CD" in tools


def test_issue_references_become_linked_facts(mined):
    issue_facts = [f for f in mined.facts if f.template == "issue_closed"]
    assert issue_facts
    refs = {e.ref for f in issue_facts for e in f.evidence if e.kind == "issue"}
    assert "#12" in refs or "#21" in refs


def test_author_filter_excludes_other_people(demo_repo):
    assert mine_repo(demo_repo, author="someone-else@example.com") == []
    assert [c for c in read_commits(demo_repo, author="demo")] != []


def test_list_authors_reports_the_history(demo_repo):
    authors = list_authors(demo_repo)
    assert authors[0][1] == "demo@example.com"
    assert authors[0][2] > 10


@pytest.mark.parametrize("subject,kind", [
    ("fix: dropped orders when the queue was slow", "bugfix"),
    ("perf: avoid re-reading the order", "perf"),
    ("test: cover the empty-order case", "test"),
    ("refactor: split the handler", "refactor"),
    ("feat: accept an order over HTTP", "feature"),
    ("修复了重复下单的问题", "bugfix"),
])
def test_commit_classification(subject, kind):
    class C:
        paths = ["src/a.py"]
    C.subject = subject
    assert classify(C()) == kind


def test_area_ignores_root_config_when_source_files_were_touched():
    class C:
        subject = "feat: x"
        paths = ["requirements.txt", "src/dispatch/queue.py"]
    assert area_of(C()) == "src/dispatch"


def test_a_directory_without_git_fails_clearly(tmp_path):
    with pytest.raises(GitError):
        read_commits(str(tmp_path))
