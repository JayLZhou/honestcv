"""Core data model: Evidence, Fact, FactBase.

The whole tool rests on one rule: *every* user-facing claim must trace back to
a Fact, and every Fact must carry Evidence. Renderers may reorder, translate and
format facts. They may never introduce one.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

SCHEMA_VERSION = "1"

# Evidence kinds, ordered from strongest (externally checkable) to weakest.
EVIDENCE_KINDS = (
    "commit",      # a commit the person authored, ideally with a public URL
    "pr",          # a merged pull request
    "issue",       # an issue they closed / referenced
    "release",     # a tagged release
    "file",        # a file in a repository
    "document",    # certificate, reference letter, training record (path or URL)
    "self_report",  # answered in the guided interview; true but not externally checkable
)

STRENGTH = {
    "commit": 0.9,
    "pr": 1.0,
    "issue": 0.7,
    "release": 0.8,
    "file": 0.5,
    "document": 0.6,
    "self_report": 0.25,
}


def _short_hash(*parts: str) -> str:
    h = hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()
    return h[:8]


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Evidence:
    kind: str
    ref: str                      # commit sha, PR number, file path, document path
    repo: str = ""                # "owner/name" or a local path
    url: str = ""                 # clickable link; empty when the repo is private/local
    date: str = ""                # ISO-8601 date (YYYY-MM-DD)
    summary: str = ""
    stats: Dict[str, int] = field(default_factory=dict)

    @property
    def eid(self) -> str:
        return "ev_" + _short_hash(self.kind, self.repo, self.ref)

    @property
    def label(self) -> str:
        if self.kind == "commit":
            return self.ref[:7]
        if self.kind == "pr":
            return "PR #%s" % self.ref.lstrip("#")
        if self.kind == "issue":
            return "#%s" % self.ref.lstrip("#")
        return self.ref

    def link(self) -> str:
        """Markdown link when verifiable, plain label otherwise."""
        if self.url:
            return "[%s](%s)" % (self.label, self.url)
        return "`%s`" % self.label

    @property
    def strength(self) -> float:
        return STRENGTH.get(self.kind, 0.3)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["eid"] = self.eid
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Evidence":
        return cls(
            kind=d["kind"],
            ref=d.get("ref", ""),
            repo=d.get("repo", ""),
            url=d.get("url", ""),
            date=d.get("date", ""),
            summary=d.get("summary", ""),
            stats=dict(d.get("stats", {})),
        )


@dataclass
class Fact:
    """One thing the person actually did.

    ``template`` + ``payload`` are what renderers are allowed to use: the template
    carries the wording (per language), the payload carries only values that came
    out of the evidence. ``text`` is the materialised default-language sentence,
    kept so a human can read the fact base directly.
    """

    template: str
    payload: Dict[str, Any] = field(default_factory=dict)
    text: str = ""
    skills: List[str] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    source: str = "git"           # git | interview | document
    kind: str = "work"            # feature | bugfix | refactor | test | infra | adoption | sustained | self_report
    period: Optional[List[str]] = None   # [first_date, last_date]
    metrics: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            self.id = "f_" + _short_hash(
                self.template,
                json.dumps(self.payload, sort_keys=True, ensure_ascii=False),
                ",".join(sorted(e.eid for e in self.evidence)),
            )

    @property
    def confidence(self) -> float:
        """Evidence strength in [0, 1]. Many independent artefacts beat one big claim."""
        if not self.evidence:
            return 0.0
        best = max(e.strength for e in self.evidence)
        breadth = min(len(self.evidence), 10) / 10.0
        span_bonus = 0.0
        if self.period and self.period[0] != self.period[1]:
            span_bonus = 0.05
        return round(min(0.98, best * (0.7 + 0.3 * breadth) + span_bonus), 3)

    def evidence_ids(self) -> List[str]:
        return [e.eid for e in self.evidence]

    def numeric_claims(self) -> List[str]:
        """Every number this fact is allowed to put in front of a recruiter."""
        out: List[str] = []
        for value in list(self.payload.values()) + list(self.metrics.values()):
            if isinstance(value, bool):
                continue
            if isinstance(value, (int, float)):
                out.append(str(value))
            elif isinstance(value, str):
                out.append(value)
        if self.period:
            out.extend(self.period)
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "template": self.template,
            "payload": self.payload,
            "text": self.text,
            "skills": self.skills,
            "evidence": [e.to_dict() for e in self.evidence],
            "source": self.source,
            "kind": self.kind,
            "period": self.period,
            "metrics": self.metrics,
            "notes": self.notes,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Fact":
        return cls(
            template=d["template"],
            payload=dict(d.get("payload", {})),
            text=d.get("text", ""),
            skills=list(d.get("skills", [])),
            evidence=[Evidence.from_dict(e) for e in d.get("evidence", [])],
            source=d.get("source", "git"),
            kind=d.get("kind", "work"),
            period=d.get("period"),
            metrics=dict(d.get("metrics", {})),
            notes=d.get("notes", ""),
            id=d.get("id", ""),
        )


@dataclass
class Person:
    name: str = ""
    headline: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    links: Dict[str, str] = field(default_factory=dict)
    # Anything here is self-reported: it is rendered, but marked as unverified.
    education: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Person":
        return cls(
            name=d.get("name", ""),
            headline=d.get("headline", ""),
            email=d.get("email", ""),
            phone=d.get("phone", ""),
            location=d.get("location", ""),
            links=dict(d.get("links", {})),
            education=list(d.get("education", [])),
            languages=list(d.get("languages", [])),
        )


@dataclass
class FactBase:
    person: Person = field(default_factory=Person)
    facts: List[Fact] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    version: str = SCHEMA_VERSION

    # -- mutation -------------------------------------------------------
    def add(self, fact: Fact) -> bool:
        """Add a fact unless an identical one is already there. Returns True if added."""
        if any(f.id == fact.id for f in self.facts):
            return False
        self.facts.append(fact)
        self.updated_at = _now()
        return True

    def extend(self, facts: Iterable[Fact]) -> int:
        return sum(1 for f in facts if self.add(f))

    def remove(self, fact_id: str) -> bool:
        before = len(self.facts)
        self.facts = [f for f in self.facts if f.id != fact_id]
        if len(self.facts) != before:
            self.updated_at = _now()
            return True
        return False

    def drop_source(self, source: str, repo: str = "") -> int:
        """Drop facts from one source (optionally one repo) so re-mining is idempotent."""
        keep, dropped = [], 0
        for f in self.facts:
            same_source = f.source == source
            same_repo = (not repo) or any(e.repo == repo for e in f.evidence)
            if same_source and same_repo:
                dropped += 1
            else:
                keep.append(f)
        self.facts = keep
        if dropped:
            self.updated_at = _now()
        return dropped

    # -- queries --------------------------------------------------------
    def get(self, fact_id: str) -> Optional[Fact]:
        for f in self.facts:
            if f.id == fact_id:
                return f
        return None

    def skills(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for f in self.facts:
            for s in f.skills:
                counts[s] = counts.get(s, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    def by_skill(self, skill: str) -> List[Fact]:
        return [f for f in self.facts if skill in f.skills]

    def evidence_index(self) -> Dict[str, Evidence]:
        return {e.eid: e for f in self.facts for e in f.evidence}

    def repos(self) -> List[str]:
        seen: List[str] = []
        for f in self.facts:
            for e in f.evidence:
                if e.repo and e.repo not in seen:
                    seen.append(e.repo)
        return seen

    # -- io -------------------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "person": self.person.to_dict(),
            "facts": [f.to_dict() for f in self.facts],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FactBase":
        return cls(
            person=Person.from_dict(d.get("person", {})),
            facts=[Fact.from_dict(f) for f in d.get("facts", [])],
            created_at=d.get("created_at", _now()),
            updated_at=d.get("updated_at", _now()),
            version=d.get("version", SCHEMA_VERSION),
        )

    def save(self, path: str) -> str:
        path = os.path.abspath(os.path.expanduser(path))
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
        return path

    @classmethod
    def load(cls, path: str) -> "FactBase":
        path = os.path.abspath(os.path.expanduser(path))
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))
