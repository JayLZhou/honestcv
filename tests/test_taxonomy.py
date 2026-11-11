import pytest

from honestcv.taxonomy import canonical, skills_for_dependency, skills_for_path, skills_in_text


@pytest.mark.parametrize("path,expected", [
    ("src/api/handlers.py", "Python"),
    ("Dockerfile", "Docker"),
    ("k8s/deployment.yaml", "Kubernetes"),
    ("infra/main.tf", "Terraform"),
    (".github/workflows/ci.yml", "CI/CD"),
    ("tests/test_orders.py", "Testing"),
])
def test_paths_imply_skills(path, expected):
    assert expected in skills_for_path(path)


@pytest.mark.parametrize("dep,expected", [
    ("confluent-kafka", ["Kafka"]),
    ("psycopg2-binary", ["PostgreSQL"]),
    ("redis>=4.0", ["Redis"]),
    ("react-dom", ["React"]),
])
def test_dependencies_imply_skills(dep, expected):
    assert skills_for_dependency(dep) == expected


def test_kafka_python_is_not_evidence_of_a_python_claim():
    # The substring trap: a dependency named *-python does not prove the language,
    # and a resume bullet saying it would fall apart when someone opens the file.
    assert skills_for_dependency("kafka-python") == ["Kafka"]


def test_text_matching_respects_word_boundaries():
    assert "Go" not in skills_in_text("please go to the second floor")
    assert "Go" in skills_in_text("Golang experience required")
    assert set(skills_in_text("We use Kafka, k8s and FastAPI")) >= {"Kafka", "Kubernetes", "FastAPI"}


def test_aliases_resolve_to_canonical_names():
    assert canonical("k8s") == "Kubernetes"
    assert canonical("postgres") == "PostgreSQL"
    assert canonical("something nobody uses") == ""
