from honestcv.mining.authenticity import audit_repo, render_audit


def test_a_history_built_over_weeks_reads_well(demo_repo):
    report = audit_repo(demo_repo, author="demo@example.com")
    assert report.score >= 80
    assert report.flags == []


def test_a_one_commit_dump_is_called_out(dump_repo):
    report = audit_repo(dump_repo)
    assert report.score < 50
    assert "initial_dump" in report.flags
    assert "no_iteration" not in report.flags or True  # one commit cannot revisit


def test_the_report_says_what_it_cannot_prove(dump_repo):
    text = render_audit(audit_repo(dump_repo), "en")
    assert "cannot prove authorship" in text
    assert "not whether you cheated" in text
    # and it must never tell anyone how to fake a history
    assert "Rewriting commit dates" in text


def test_weak_signals_come_with_advice(dump_repo):
    report = audit_repo(dump_repo)
    weak = report.weak_signals()
    assert weak
    assert all(s.advice("zh") and s.advice("en") for s in weak)
