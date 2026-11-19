import os

import pytest

from honestcv.cli import main

EXAMPLES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "examples")
JD = os.path.join(EXAMPLES, "jd-backend-en.txt")


@pytest.fixture
def workspace(tmp_path, demo_repo, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--name", "Demo Candidate"]) == 0
    assert main(["--lang", "en", "mine", demo_repo, "--author", "demo@example.com"]) == 0
    return tmp_path


def test_init_refuses_to_clobber(workspace):
    assert main(["init"]) == 1
    assert main(["init", "--force"]) == 0


def test_mine_without_a_fact_base_tells_you_what_to_do(tmp_path, monkeypatch, demo_repo):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        main(["mine", demo_repo])
    assert "honestcv init" in str(exc.value)


def test_mining_twice_does_not_duplicate(workspace, demo_repo, capsys):
    from honestcv.models import FactBase
    before = len(FactBase.load("honestcv.json").facts)
    main(["--lang", "en", "mine", demo_repo, "--author", "demo@example.com"])
    assert len(FactBase.load("honestcv.json").facts) == before


def test_the_whole_pipeline_produces_verified_documents(workspace):
    assert main(["--lang", "en", "resume", "--jd", JD, "-o", "cv.md"]) == 0
    assert main(["--lang", "en", "letter", "--jd", JD, "-o", "letter.md"]) == 0
    assert main(["--lang", "en", "practice", "--jd", JD, "-o", "practice.md"]) == 0
    for name in ("cv.md", "letter.md", "practice.md"):
        assert os.path.exists(name) and os.path.exists(name.replace(".md", ".trace.json"))
        assert main(["--lang", "en", "verify", name]) == 0


def test_verify_fails_on_an_edited_document(workspace):
    main(["--lang", "en", "resume", "--jd", JD, "-o", "cv.md"])
    with open("cv.md", "a", encoding="utf-8") as fh:
        fh.write("- Scaled the platform to 10 million users\n")
    assert main(["--lang", "en", "verify", "cv.md"]) == 1


def test_plan_needs_a_gap_to_plan_for(workspace):
    assert main(["plan"]) == 1
    assert main(["--lang", "en", "plan", "--skill", "Kubernetes", "-o", "plan.md"]) == 0
    assert "Kubernetes" in open("plan.md", encoding="utf-8").read()


def test_interview_answers_are_recorded(workspace, tmp_path):
    answers = tmp_path / "a.json"
    answers.write_text('{"role": "Only backend developer on the project"}', encoding="utf-8")
    assert main(["--lang", "en", "interview", "--answers", str(answers)]) == 0
    assert main(["--lang", "en", "resume", "-o", "cv.md"]) == 0
    assert "Only backend developer" in open("cv.md", encoding="utf-8").read()


def test_questions_can_be_written_as_a_template(workspace, tmp_path):
    out = tmp_path / "q.json"
    assert main(["questions", "--jd", JD, "--template", str(out)]) == 0
    assert "gap:Kubernetes" in out.read_text(encoding="utf-8")


def test_audit_is_readable_and_machine_readable(workspace, demo_repo, capsys):
    assert main(["audit", demo_repo, "--author", "demo@example.com", "--json"]) == 0
    assert '"score"' in capsys.readouterr().out


def test_facts_listing(workspace, capsys):
    assert main(["facts", "--skill", "Kafka"]) == 0
    assert "Kafka" in capsys.readouterr().out


def test_scanning_code_without_history(tmp_path, monkeypatch, demo_repo, capsys):
    import shutil
    target = tmp_path / "orders"
    shutil.copytree(demo_repo, target)
    shutil.rmtree(target / ".git")
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--name", "Demo"]) == 0

    # audit on a directory with no history reports, rather than failing
    assert main(["--lang", "en", "audit", str(target)]) == 0
    assert "no git history here" in capsys.readouterr().out

    assert main(["--lang", "en", "scan", str(target)]) == 0
    out = capsys.readouterr().out
    assert "come from files, not commits" in out

    from honestcv.models import FactBase
    before = len(FactBase.load("honestcv.json").facts)
    main(["--lang", "en", "scan", str(target)])          # re-scanning replaces
    assert len(FactBase.load("honestcv.json").facts) == before

    assert main(["--lang", "en", "resume", "-o", "cv.md"]) == 0
    assert main(["--lang", "en", "verify", "cv.md"]) == 0          # warnings only
    assert main(["--lang", "en", "verify", "cv.md", "--strict"]) == 1


def test_scanning_an_empty_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    main(["init", "--name", "Demo"])
    (tmp_path / "empty").mkdir()
    assert main(["scan", str(tmp_path / "empty")]) == 1
