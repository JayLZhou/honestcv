from honestcv.models import Evidence, Fact, FactBase, Person


def _fact(text="did a thing", skills=("Python",), sha="abc1234"):
    return Fact(template="feature_work", payload={"repo": "o/r", "subject": text},
                text=text, skills=list(skills),
                evidence=[Evidence(kind="commit", ref=sha, repo="o/r",
                                   url="https://github.com/o/r/commit/" + sha)])


def test_ids_are_deterministic_and_content_addressed():
    assert _fact().id == _fact().id
    assert _fact().id != _fact(text="did another thing").id


def test_evidence_ids_differ_per_commit():
    assert _fact(sha="aaa").evidence[0].eid != _fact(sha="bbb").evidence[0].eid


def test_adding_the_same_fact_twice_is_a_no_op():
    fb = FactBase()
    assert fb.add(_fact()) is True
    assert fb.add(_fact()) is False
    assert len(fb.facts) == 1


def test_confidence_ranks_a_pr_above_a_self_report():
    pr = Fact(template="t", evidence=[Evidence(kind="pr", ref="1")])
    said = Fact(template="t", evidence=[Evidence(kind="self_report", ref="q")])
    assert pr.confidence > said.confidence
    assert Fact(template="t").confidence == 0.0


def test_remining_a_repo_replaces_instead_of_duplicating():
    fb = FactBase()
    fb.add(_fact())
    assert fb.drop_source("git", repo="o/r") == 1
    assert fb.facts == []


def test_roundtrip_through_json(tmp_path):
    fb = FactBase(person=Person(name="Li", links={"github": "https://github.com/li"}))
    fb.add(_fact())
    path = fb.save(str(tmp_path / "f.json"))
    back = FactBase.load(path)
    assert back.person.name == "Li"
    assert back.facts[0].id == fb.facts[0].id
    assert back.facts[0].evidence[0].url.endswith("abc1234")


def test_numeric_claims_cover_payload_metrics_and_period():
    fact = Fact(template="t", payload={"commits": 7}, metrics={"days": 22},
                period=["2026-03-02", "2026-03-24"])
    claims = " ".join(fact.numeric_claims())
    assert "7" in claims and "22" in claims and "2026-03-02" in claims
