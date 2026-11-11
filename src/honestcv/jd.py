"""Parse a job description into requirements.

Plain pattern matching, no model. A requirement the parser cannot read is
reported as unread rather than silently dropped — a missed requirement that
looks like a match is the one failure mode that actually hurts the candidate.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from .taxonomy import skills_in_text

BULLET = re.compile(r"^\s*(?:[-*•·‣◦>]|\d{1,2}[.)、]|[（(]\d{1,2}[）)])\s*")
HEADER = re.compile(r"^\s*#{1,6}\s*|[:：]\s*$")

MUST_HEADERS = (
    "requirement", "qualification", "what you", "you have", "you should", "must have",
    "we are looking for", "skills", "experience", "任职要求", "岗位要求", "职位要求",
    "技能要求", "任职资格", "我们希望你", "基本要求",
)
NICE_HEADERS = (
    "nice to have", "preferred", "bonus", "plus", "desirable", "a plus",
    "加分", "优先", "亮点", "锦上添花",
)
DUTY_HEADERS = (
    "responsibilit", "what you'll do", "what you will do", "the role", "about the role",
    "工作职责", "岗位职责", "你将", "工作内容",
)
NOISE_HEADERS = (
    "benefit", "perks", "about us", "equal opportunity", "how to apply", "salary",
    "福利", "关于我们", "投递方式", "薪资",
)
TITLE_HINT = re.compile(r"^(job title|position|role|title|职位|岗位)\s*[:：]\s*(.+)$", re.IGNORECASE)
COMPANY_HINT = re.compile(r"^(company|employer|公司)\s*[:：]\s*(.+)$", re.IGNORECASE)
NICE_INLINE = re.compile(r"(nice to have|preferred|a plus|bonus|加分|优先)", re.IGNORECASE)


@dataclass
class Requirement:
    text: str
    skills: List[str] = field(default_factory=list)
    kind: str = "must"        # must | nice | duty
    line_no: int = 0

    @property
    def readable(self) -> bool:
        """True when the parser found something concrete to match against."""
        return bool(self.skills)


@dataclass
class JD:
    title: str = ""
    company: str = ""
    requirements: List[Requirement] = field(default_factory=list)
    raw: str = ""

    def must_haves(self) -> List[Requirement]:
        return [r for r in self.requirements if r.kind == "must"]

    def nice_to_haves(self) -> List[Requirement]:
        return [r for r in self.requirements if r.kind == "nice"]

    def duties(self) -> List[Requirement]:
        return [r for r in self.requirements if r.kind == "duty"]

    def skills(self, kinds=("must", "nice", "duty")) -> List[str]:
        out: List[str] = []
        for r in self.requirements:
            if r.kind not in kinds:
                continue
            for s in r.skills:
                if s not in out:
                    out.append(s)
        return out


def _section_of(line: str, current: str) -> str:
    low = line.strip().lower().lstrip("#").strip().rstrip(":：").strip()
    if not low or len(low) > 60:
        return current
    for needle in NOISE_HEADERS:
        if low.startswith(needle):
            return "noise"
    for needle in NICE_HEADERS:
        if needle in low:
            return "nice"
    for needle in DUTY_HEADERS:
        if needle in low:
            return "duty"
    for needle in MUST_HEADERS:
        if needle in low:
            return "must"
    return current


def parse_jd(text: str, title: Optional[str] = None) -> JD:
    jd = JD(raw=text, title=title or "")
    lines = text.splitlines()
    section = ""
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        m = TITLE_HINT.match(stripped)
        if m and not title:
            jd.title = m.group(2).strip()
            continue
        m = COMPANY_HINT.match(stripped)
        if m:
            jd.company = m.group(2).strip()
            continue

        is_bullet = bool(BULLET.match(line))
        new_section = _section_of(stripped, section)
        if new_section != section and not is_bullet:
            section = new_section
            continue
        if section in ("", "noise"):
            continue
        if section == "duty" and not is_bullet:
            continue   # prose describing the team is not a requirement

        body = BULLET.sub("", stripped).strip()
        if not body or len(body) < 3:
            continue
        if HEADER.search(stripped) and not is_bullet and len(body) < 40:
            continue

        kind = section
        if kind == "must" and NICE_INLINE.search(body):
            kind = "nice"
        jd.requirements.append(Requirement(text=body, skills=skills_in_text(body), kind=kind, line_no=i))

    if not jd.title:
        for line in lines:
            if line.strip():
                jd.title = line.strip().lstrip("# ").strip()
                break
    if not jd.requirements:
        # No recognisable sections: treat every bullet in the document as a requirement.
        for i, raw_line in enumerate(lines, start=1):
            if BULLET.match(raw_line):
                body = BULLET.sub("", raw_line.strip()).strip()
                if len(body) >= 3:
                    jd.requirements.append(
                        Requirement(text=body, skills=skills_in_text(body), kind="must", line_no=i))
    return jd


def load_jd(path: str, title: Optional[str] = None) -> JD:
    with open(path, encoding="utf-8") as fh:
        return parse_jd(fh.read(), title=title)
