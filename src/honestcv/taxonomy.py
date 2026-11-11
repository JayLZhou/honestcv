"""Skill taxonomy: map file paths, dependency names and free text onto canonical skills.

Deliberately boring and deterministic. No model is involved, so the same input
always yields the same skills, which is what makes the grounding checks testable.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Dict, List, Set

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Short or ambiguous names that must match case-sensitively ("go to the office"
# is not Go; "a C grade" is not C).
STRICT_CASE = {"Go", "C", "C#", "C++", "R", "SQL", "CSS", "HTML", "AWS", "GCP", "LLM", "RAG"}


@lru_cache(maxsize=1)
def load_skills() -> Dict[str, dict]:
    with open(os.path.join(DATA_DIR, "skills.json"), encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=1)
def _ext_index() -> Dict[str, List[str]]:
    idx: Dict[str, List[str]] = {}
    for name, spec in load_skills().items():
        for ext in spec.get("ext", []):
            idx.setdefault(ext.lower(), []).append(name)
    return idx


@lru_cache(maxsize=1)
def _path_index() -> List[tuple]:
    out = []
    for name, spec in load_skills().items():
        for hint in spec.get("paths", []):
            out.append((hint.lower(), name))
    return out


@lru_cache(maxsize=1)
def _manifest_index() -> List[tuple]:
    out = []
    for name, spec in load_skills().items():
        for token in spec.get("manifest", []):
            out.append((token.lower(), name))
    # longest token first, so "spring-boot-starter" wins over "spring"
    return sorted(out, key=lambda kv: -len(kv[0]))


@lru_cache(maxsize=1)
def _text_patterns() -> List[tuple]:
    pats = []
    for name, spec in load_skills().items():
        terms = [name] + list(spec.get("aliases", []))
        for term in terms:
            escaped = re.escape(term)
            pattern = r"(?<![A-Za-z0-9_+#.])" + escaped + r"(?![A-Za-z0-9_+#])"
            flags = 0 if (name in STRICT_CASE and term[0].isupper()) else re.IGNORECASE
            pats.append((re.compile(pattern, flags), name))
    return pats


def canonical(term: str) -> str:
    """Return the canonical skill name for a term, or '' if unknown."""
    term_l = term.strip().lower()
    for name, spec in load_skills().items():
        if term_l == name.lower() or term_l in [a.lower() for a in spec.get("aliases", [])]:
            return name
    return ""


def skills_for_path(path: str) -> List[str]:
    """Skills implied by a file path (extension and well-known locations)."""
    found: Set[str] = set()
    low = path.lower().replace("\\", "/")
    base = os.path.basename(low)
    _, ext = os.path.splitext(base)
    for name in _ext_index().get(ext, []):
        found.add(name)
    for hint, name in _path_index():
        if hint in low or base == hint:
            found.add(name)
    # Kubernetes manifests are yaml in a k8s-shaped directory; plain yaml is not a skill.
    if ext in (".yml", ".yaml") and any(k in low for k in ("k8s/", "kubernetes/", "manifests/", "charts/")):
        found.add("Kubernetes")
    return sorted(found)


def skills_for_dependency(token: str) -> List[str]:
    """Skills implied by a dependency name pulled out of a manifest diff.

    Matching is on name parts, not raw substrings: `kafka-python` is evidence of
    Kafka, not of "Python", and a resume that claims otherwise falls apart the
    moment someone opens the file."""
    low = re.split(r"[<>=!~\[\s;,]", token.strip().lower())[0].strip("\"'")
    if not low:
        return []
    parts = set(re.split(r"[-_./]", low)) | {low}
    out: Set[str] = set()
    for needle, name in _manifest_index():
        if any(part == needle or part.startswith(needle) for part in parts):
            out.add(name)
        elif len(needle) >= 6 and needle in low:
            out.add(name)
    return sorted(out)


def skills_in_text(text: str) -> List[str]:
    """Canonical skills mentioned anywhere in free text (a commit subject, a JD line)."""
    if not text:
        return []
    out: Set[str] = set()
    for pattern, name in _text_patterns():
        if pattern.search(text):
            out.add(name)
    return sorted(out)


def category(skill: str) -> str:
    return load_skills().get(skill, {}).get("category", "other")


def all_skills() -> List[str]:
    return sorted(load_skills().keys())
