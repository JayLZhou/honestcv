import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "examples"))

from make_demo_repo import build  # noqa: E402

EXAMPLES = os.path.join(ROOT, "examples")


@pytest.fixture(scope="session")
def demo_repo(tmp_path_factory):
    """Three weeks of ordinary work: features, a fix on top of them, tests, deps."""
    path = tmp_path_factory.mktemp("repos") / "orders"
    return build(str(path))


@pytest.fixture(scope="session")
def dump_repo(tmp_path_factory):
    """The opposite: a finished project dropped in as one commit."""
    import subprocess
    path = tmp_path_factory.mktemp("repos") / "dumped"
    os.makedirs(path / "src", exist_ok=True)
    for i in range(12):
        (path / "src" / ("mod%d.py" % i)).write_text("def f%d():\n    return %d\n" % (i, i) * 20)
    subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True, capture_output=True)
    for args in (["config", "user.name", "Dump"], ["config", "user.email", "dump@example.com"],
                 ["add", "-A"], ["commit", "-q", "-m", "initial commit"]):
        subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)
    return str(path)


@pytest.fixture
def mined(demo_repo):
    from honestcv.mining import mine_repo
    from honestcv.models import FactBase, Person
    fb = FactBase(person=Person(name="Demo Candidate", email="demo@example.com"))
    fb.extend(mine_repo(demo_repo, author="demo@example.com", lang="en"))
    return fb


@pytest.fixture
def jd_en():
    from honestcv.jd import load_jd
    return load_jd(os.path.join(EXAMPLES, "jd-backend-en.txt"))


@pytest.fixture
def jd_zh():
    from honestcv.jd import load_jd
    return load_jd(os.path.join(EXAMPLES, "jd-backend-zh.txt"))
