import json

from honestcv.interview import (answer_template, facts_from_answers, load_answers,
                                questions, write_template)


def test_questions_cover_what_code_cannot_show():
    ids = {q["id"] for q in questions("zh")}
    assert {"role", "first_version_failed", "non_code_evidence", "non_tech_experience"} <= ids


def test_gap_questions_are_added_for_missing_skills():
    qs = questions("zh", gaps=["Kafka"])
    gap = [q for q in qs if q["id"] == "gap:Kafka"][0]
    assert "Kafka" in gap["text"]


def test_answers_become_self_reported_facts():
    facts = facts_from_answers({"role": "I was the only backend developer"}, "en")
    assert len(facts) == 1
    fact = facts[0]
    assert fact.source == "interview"
    assert [e.kind for e in fact.evidence] == ["self_report"]
    assert fact.confidence < 0.4          # weaker than a commit, by construction
    assert fact.text == "I was the only backend developer"


def test_nothing_is_invented_for_unanswered_questions():
    assert facts_from_answers({"role": "", "hardest": "  ", "redo": "没有"}, "zh") == []


def test_a_gap_answer_carries_the_skill_it_is_about():
    facts = facts_from_answers({"gap:Kubernetes": "I ran a cluster at my bootcamp"}, "en")
    assert "Kubernetes" in facts[0].skills


def test_skills_mentioned_in_an_answer_are_picked_up():
    facts = facts_from_answers({"decision": "I chose Redis over Memcached"}, "en")
    assert "Redis" in facts[0].skills


def test_the_answer_template_round_trips(tmp_path):
    path = tmp_path / "answers.json"
    write_template(str(path), "zh", gaps=["Kafka"])
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["answers"] == answer_template("zh", ["Kafka"])
    assert "gap:Kafka" in payload["_questions"]
    payload["answers"]["role"] = "一个人做的"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    assert load_answers(str(path)) == {"role": "一个人做的"}
