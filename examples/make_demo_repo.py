#!/usr/bin/env python3
"""Build a small git repository that looks like three weeks of real evenings.

Used by the demo and by the tests. It is deliberately ordinary: a few features,
a bug found later and fixed, tests written along the way, one dependency added.
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, timedelta

START = date(2026, 3, 2)

COMMITS = [
    (0,  "chore: project skeleton", {"README.md": "# orders\n", "requirements.txt": "fastapi\n"}),
    (0,  "feat: accept an order over HTTP", {"src/api/orders.py": "def create_order(payload):\n    return {'id': 1}\n"}),
    (1,  "feat: validate order payloads before accepting them",
     {"src/api/orders.py": "def create_order(payload):\n    if not payload.get('items'):\n        raise ValueError('empty order')\n    return {'id': 1}\n"}),
    (2,  "test: cover the empty-order case",
     {"tests/test_orders.py": "def test_empty_order():\n    assert True\n"}),
    (3,  "feat: store orders in postgres",
     {"src/store/db.py": "QUERY = 'insert into orders values (%s)'\n", "requirements.txt": "fastapi\npsycopg2-binary\n"}),
    (4,  "fix: reject duplicate order ids (#12)",
     {"src/store/db.py": "QUERY = 'insert into orders values (%s) on conflict do nothing'\n"}),
    (5,  "test: duplicate ids are rejected",
     {"tests/test_orders.py": "def test_empty_order():\n    assert True\n\n\ndef test_duplicate():\n    assert True\n"}),
    (7,  "feat: dispatch accepted orders to the warehouse queue",
     {"src/dispatch/queue.py": "def publish(order):\n    pass\n", "requirements.txt": "fastapi\npsycopg2-binary\nkafka-python\n"}),
    (8,  "fix: dispatch dropped orders when the queue was slow",
     {"src/dispatch/queue.py": "def publish(order, retries=3):\n    for _ in range(retries):\n        pass\n"}),
    (9,  "docs: how to run the service locally", {"README.md": "# orders\n\n## Running locally\n"}),
    (10, "build: run the service in docker",
     {"Dockerfile": "FROM python:3.11-slim\n", "docker-compose.yml": "services:\n  api:\n    build: .\n"}),
    (11, "ci: run tests on every push",
     {".github/workflows/ci.yml": "on: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n"}),
    (12, "perf: avoid re-reading the order on every dispatch",
     {"src/dispatch/queue.py": "CACHE = {}\n\n\ndef publish(order, retries=3):\n    CACHE[order] = True\n"}),
    (14, "fix: cache returned stale orders after an update",
     {"src/dispatch/queue.py": "CACHE = {}\n\n\ndef publish(order, retries=3):\n    CACHE.pop(order, None)\n"}),
    (15, "feat: add a redis-backed cache for warehouse lookups",
     {"src/store/cache.py": "import redis\n\n\ndef get(key):\n    return None\n", "requirements.txt": "fastapi\npsycopg2-binary\nkafka-python\nredis\n"}),
    (16, "test: the cache is invalidated on update",
     {"tests/test_cache.py": "def test_invalidation():\n    assert True\n"}),
    (18, "refactor: split the order handler into validate and persist",
     {"src/api/orders.py": "def validate(payload):\n    if not payload.get('items'):\n        raise ValueError('empty order')\n\n\ndef create_order(payload):\n    validate(payload)\n    return {'id': 1}\n"}),
    (19, "fix: validation error returned a 500 instead of a 400 (#21)",
     {"src/api/orders.py": "def validate(payload):\n    if not payload.get('items'):\n        raise ValueError('empty order')\n\n\ndef create_order(payload):\n    try:\n        validate(payload)\n    except ValueError:\n        return {'status': 400}\n    return {'id': 1}\n"}),
    (20, "test: a bad payload returns 400",
     {"tests/test_orders.py": "def test_empty_order():\n    assert True\n\n\ndef test_duplicate():\n    assert True\n\n\ndef test_bad_payload():\n    assert True\n"}),
    (22, "docs: write down what happens when the queue is down",
     {"README.md": "# orders\n\n## Running locally\n\n## Failure modes\n"}),
]


def run(repo: str, *args: str, env=None) -> None:
    subprocess.run(["git", "-C", repo, *args], check=True, capture_output=True, env=env)


def build(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", path], check=True, capture_output=True)
    run(path, "config", "user.name", "Demo Candidate")
    run(path, "config", "user.email", "demo@example.com")
    run(path, "remote", "add", "origin", "https://github.com/demo/orders.git")
    for day, message, files in COMMITS:
        for rel, content in files.items():
            full = os.path.join(path, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(content)
        hour = 9 + (day * 5) % 13          # evenings and weekends, like real side work
        stamp = "%s %02d:%02d:00 +0000" % (
            (START + timedelta(days=day)).isoformat(), hour, (day * 7) % 60)
        env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        run(path, "add", "-A")
        run(path, "commit", "-q", "-m", message, env=env)
    return path


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "demo-repo"
    print(build(target))
