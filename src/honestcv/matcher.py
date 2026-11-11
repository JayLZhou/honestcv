"""Match a fact base against a job description.

Three outcomes per requirement, and the third one matters most:
  covered   - at least one fact backs it
  gap       - the requirement is readable and nothing backs it
  unread    - the parser could not pin the requirement to any skill

Calling an unread requirement "covered" is how resume tools quietly lie. They
stay separate here, and the gap list is what feeds the two-week plans.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .jd import JD, Requirement
from .models import Fact, FactBase


@dataclass
class Coverage:
    requirement: Requirement
    facts: List[Fact] = field(default_factory=list)

    @property
    def covered(self) -> bool:
        return bool(self.facts)

    @property
    def strength(self) -> float:
        if not self.facts:
            return 0.0
        return round(min(1.0, sum(f.confidence for f in self.facts) / 1.5), 3)

    @property
    def missing_skills(self) -> List[str]:
        have = {s for f in self.facts for s in f.skills}
        return [s for s in self.requirement.skills if s not in have]


@dataclass
class MatchReport:
    jd: JD
    coverages: List[Coverage] = field(default_factory=list)

    def by_kind(self, kind: str) -> List[Coverage]:
        return [c for c in self.coverages if c.requirement.kind == kind]

    def covered(self, kinds=("must", "nice", "duty")) -> List[Coverage]:
        return [c for c in self.coverages if c.covered and c.requirement.kind in kinds]

    def gaps(self, kinds=("must", "nice")) -> List[Coverage]:
        return [c for c in self.coverages
                if not c.covered and c.requirement.readable and c.requirement.kind in kinds]

    def unread(self) -> List[Requirement]:
        return [c.requirement for c in self.coverages if not c.requirement.readable]

    def gap_skills(self, kinds=("must", "nice")) -> List[str]:
        out: List[str] = []
        for c in self.coverages:
            if c.requirement.kind not in kinds or c.covered:
                continue   # "FastAPI or Django" with FastAPI in hand is not a Django gap
            for s in c.missing_skills:
                if s not in out:
                    out.append(s)
        return out

    def coverage_ratio(self, kind: str = "must") -> float:
        readable = [c for c in self.by_kind(kind) if c.requirement.readable]
        if not readable:
            return 0.0
        return round(sum(1 for c in readable if c.covered) / len(readable), 3)

    def ranked_facts(self) -> List[Fact]:
        """Facts that support this JD, strongest and most relevant first."""
        score: Dict[str, float] = {}
        holder: Dict[str, Fact] = {}
        weight = {"must": 1.0, "nice": 0.6, "duty": 0.4}
        for cov in self.coverages:
            w = weight.get(cov.requirement.kind, 0.4)
            for fact in cov.facts:
                score[fact.id] = score.get(fact.id, 0.0) + w * (0.5 + fact.confidence)
                holder[fact.id] = fact
        ordered = sorted(score.items(), key=lambda kv: -kv[1])
        return [holder[fid] for fid, _ in ordered]


def match(factbase: FactBase, jd: JD) -> MatchReport:
    report = MatchReport(jd=jd)
    for req in jd.requirements:
        supporting = []
        if req.skills:
            for fact in factbase.facts:
                if any(s in fact.skills for s in req.skills):
                    supporting.append(fact)
            supporting.sort(key=lambda f: -f.confidence)
        report.coverages.append(Coverage(requirement=req, facts=supporting[:4]))
    return report


def render_match(report: MatchReport, lang: str = "zh") -> str:
    zh = lang == "zh"
    jd = report.jd
    lines: List[str] = []
    lines.append("# %s%s" % ("岗位匹配报告" if zh else "Match report", (": %s" % jd.title) if jd.title else ""))
    lines.append("")
    must_ratio = report.coverage_ratio("must")
    lines.append("**%s**: %.0f%% %s" % (
        "硬性要求覆盖率" if zh else "Must-have coverage", must_ratio * 100,
        "（有证据支撑的比例）" if zh else "(backed by evidence)"))
    lines.append("")

    for kind, header in (("must", "硬性要求" if zh else "Must have"),
                         ("nice", "加分项" if zh else "Nice to have")):
        covs = [c for c in report.by_kind(kind) if c.requirement.readable]
        if not covs:
            continue
        lines.append("## %s" % header)
        lines.append("")
        for cov in covs:
            mark = "✅" if cov.covered else "❌"
            lines.append("- %s %s" % (mark, cov.requirement.text))
            for fact in cov.facts[:2]:
                links = " ".join(e.link() for e in fact.evidence[:3])
                lines.append("    - %s %s" % (fact.text, links))
            if not cov.covered:
                missing = "、".join(cov.missing_skills) if zh else ", ".join(cov.missing_skills)
                if missing:
                    lines.append("    - %s %s" % ("缺口技能：" if zh else "missing:", missing))
        lines.append("")

    unread = report.unread()
    if unread:
        lines.append("## %s" % ("工具读不懂的要求" if zh else "Requirements the parser could not read"))
        lines.append("")
        if zh:
            lines.append("这些要求没有被判定为匹配或不匹配——请你自己看一遍。")
        else:
            lines.append("These were neither matched nor counted as gaps. Read them yourself.")
        lines.append("")
        for req in unread[:12]:
            lines.append("- %s" % req.text)
        lines.append("")
    return "\n".join(lines) + "\n"
