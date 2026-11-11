"""The invariant: every claim traces back to evidence.

Renderers emit a document plus a sidecar trace. This module reads both back and
checks, line by line, that:

  * every claim line in the document is in the trace
  * every traced fact still exists in the fact base
  * every number in a line came out of that fact
  * every skill named in a line is one that fact actually demonstrates
  * every claim carries a link, or is explicitly marked self-reported

It runs after rendering, and it runs again after an LLM has rephrased anything.
If a claim cannot be traced, the document fails — that is the whole point.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import FactBase
from .taxonomy import skills_in_text

MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
INLINE_CODE = re.compile(r"`[^`]*`")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")
BULLET_LINE = re.compile(r"^\s*[-*]\s+\S")
FENCE = re.compile(r"^\s*```")

UNVERIFIABLE = [
    "expert", "guru", "ninja", "rockstar", "world-class", "world class", "best-in-class",
    "10x", "single-handedly", "singlehandedly", "visionary", "seamlessly", "cutting-edge",
    "精通", "顶尖", "业界领先", "行业领先", "独立完成全部", "完美", "极致",
]


@dataclass
class Violation:
    severity: str      # error | warning
    code: str
    line: str
    detail: str = ""
    fact_id: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "severity": self.severity, "code": self.code, "line": self.line,
            "detail": self.detail, "fact_id": self.fact_id,
        }


@dataclass
class Report:
    document: str = ""
    checked_lines: int = 0
    violations: List[Violation] = field(default_factory=list)

    @property
    def errors(self) -> List[Violation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> List[Violation]:
        return [v for v in self.violations if v.severity == "warning"]

    def ok(self, strict: bool = False) -> bool:
        return not self.errors and (not strict or not self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document,
            "checked_lines": self.checked_lines,
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class Trace:
    """What a renderer claims it wrote, and on what basis."""

    document: str = ""
    factbase: str = ""
    lines: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, line: str, fact_ids: Optional[List[str]] = None,
            evidence: Optional[List[str]] = None, kind: str = "claim") -> None:
        self.lines.append({
            "line": line, "fact_ids": list(fact_ids or []),
            "evidence": list(evidence or []), "kind": kind,
        })

    def index(self) -> Dict[str, Dict[str, Any]]:
        return {normalise(entry["line"]): entry for entry in self.lines}

    def to_dict(self) -> Dict[str, Any]:
        return {"document": self.document, "factbase": self.factbase, "lines": self.lines}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Trace":
        return cls(document=d.get("document", ""), factbase=d.get("factbase", ""),
                   lines=list(d.get("lines", [])))

    def save(self, path: str) -> str:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.to_dict(), fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        return path

    @classmethod
    def load(cls, path: str) -> "Trace":
        with open(path, encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))


def trace_path_for(doc_path: str) -> str:
    stem, _ = os.path.splitext(doc_path)
    return stem + ".trace.json"


def normalise(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def strip_markup(line: str) -> str:
    """Remove links and inline code so evidence refs are not read as claims."""
    text = MD_LINK.sub(" ", line)
    text = INLINE_CODE.sub(" ", text)
    return text


def claim_lines(document: str) -> List[str]:
    out, in_fence = [], False
    for line in document.splitlines():
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if BULLET_LINE.match(line):
            out.append(line)
    return out


def _allowed_numbers(fact) -> List[str]:
    allowed: List[str] = []
    for value in fact.numeric_claims():
        allowed.extend(NUMBER.findall(str(value)))
    return allowed


def _allowed_skills(fact) -> set:
    allowed = set(fact.skills)
    allowed |= set(skills_in_text(fact.text))
    for value in fact.payload.values():
        if isinstance(value, str):
            allowed |= set(skills_in_text(value))
    for ev in fact.evidence:
        allowed |= set(skills_in_text(ev.summary))
        allowed |= set(skills_in_text(ev.repo))
    return allowed


def verify(document: str, trace: Trace, factbase: FactBase, doc_name: str = "") -> Report:
    report = Report(document=doc_name or trace.document)
    index = trace.index()
    evidence_index = factbase.evidence_index()

    for raw in claim_lines(document):
        line = normalise(raw)
        report.checked_lines += 1
        entry = index.get(line)
        if entry is None:
            report.violations.append(Violation(
                "error", "untraced_claim", line,
                "This line is not in the trace: it was added or edited after generation, "
                "so nothing backs it."))
            continue
        kind = entry.get("kind", "claim")
        if kind != "claim":
            continue  # quoted JD text, headings, instructions to the candidate

        fact_ids = list(entry.get("fact_ids") or ([entry["fact_id"]] if entry.get("fact_id") else []))
        facts = []
        for fid in fact_ids:
            fact = factbase.get(fid)
            if fact is None:
                report.violations.append(Violation(
                    "error", "unknown_fact", line,
                    "Traced to %s, which is not in the fact base." % fid, fid))
            else:
                facts.append(fact)
        if not facts:
            if not fact_ids:
                report.violations.append(Violation(
                    "error", "unknown_fact", line, "This claim names no fact."))
            continue
        primary = facts[0]

        for eid in entry.get("evidence", []):
            if eid not in evidence_index:
                report.violations.append(Violation(
                    "error", "unknown_evidence", line,
                    "Evidence %s is not in the fact base." % eid, primary.id))

        bare = strip_markup(raw)
        allowed_numbers = []
        allowed_skills = set()
        for fact in facts:
            allowed_numbers.extend(_allowed_numbers(fact))
            allowed_skills |= _allowed_skills(fact)

        for number in NUMBER.findall(bare):
            if number not in allowed_numbers:
                report.violations.append(Violation(
                    "error", "unbacked_number", line,
                    "The number %s does not appear in the evidence for this fact." % number, primary.id))

        for skill in skills_in_text(bare):
            if skill not in allowed_skills:
                report.violations.append(Violation(
                    "error", "unbacked_skill", line,
                    "%s is claimed here but this fact does not demonstrate it." % skill, primary.id))

        has_link = bool(MD_LINK.search(raw))
        if not has_link and primary.source != "interview" and primary.evidence:
            report.violations.append(Violation(
                "warning", "missing_link", line,
                "This claim has evidence but no clickable link; a reviewer cannot check it.", primary.id))
        if primary.source == "interview" and kind == "claim":
            if "self_report" not in [e.kind for e in primary.evidence]:
                report.violations.append(Violation(
                    "warning", "unmarked_self_report", line,
                    "This came from the interview and should be shown as self-reported.", primary.id))

        low = bare.lower()
        for word in UNVERIFIABLE:
            if word in low:
                report.violations.append(Violation(
                    "warning", "unverifiable_language", line,
                    "'%s' cannot be checked by anyone. Say what you did instead." % word, primary.id))
    return report


def verify_files(doc_path: str, factbase_path: str, trace_path: Optional[str] = None) -> Report:
    with open(doc_path, encoding="utf-8") as fh:
        document = fh.read()
    factbase = FactBase.load(factbase_path)
    trace_file = trace_path or trace_path_for(doc_path)
    if not os.path.exists(trace_file):
        report = Report(document=doc_path)
        report.violations.append(Violation(
            "error", "missing_trace", "",
            "No trace file at %s. A document without a trace cannot be verified." % trace_file))
        return report
    trace = Trace.load(trace_file)
    return verify(document, trace, factbase, doc_name=doc_path)


def render_report(report: Report, lang: str = "zh") -> str:
    zh = lang == "zh"
    lines: List[str] = []
    status = "通过" if zh else "PASS"
    if report.errors:
        status = "未通过" if zh else "FAIL"
    lines.append("%s: %s (%d %s, %d %s, %d %s)" % (
        report.document, status,
        report.checked_lines, "条声明" if zh else "claims checked",
        len(report.errors), "个错误" if zh else "errors",
        len(report.warnings), "个警告" if zh else "warnings"))
    for v in report.violations:
        marker = "✗" if v.severity == "error" else "!"
        lines.append("  %s [%s] %s" % (marker, v.code, v.line[:100]))
        if v.detail:
            lines.append("      %s" % v.detail)
    if not report.violations:
        lines.append("  " + ("每一条都能追溯到证据。" if zh else "Every claim traces back to evidence."))
    return "\n".join(lines) + "\n"
