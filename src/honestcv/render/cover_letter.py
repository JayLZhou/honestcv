"""Render a cover letter.

Every sentence about the person is a bullet drawn from a fact, so the verifier
can check it. Everything the tool does not know - why this company, when they
can start - is left as an explicit TODO rather than invented. A letter with
three TODOs in it is more useful than a fluent letter that says something untrue
in an interview three weeks later.
"""
from __future__ import annotations

from typing import List, Optional

from ..grounding import Trace, normalise
from ..i18n import render_fact, ui
from ..matcher import MatchReport
from ..models import FactBase

BODY = {
    "zh": {
        "salutation": "尊敬的招聘负责人：",
        "opening": "我申请贵司的 **{title}** 岗位。[TODO：一句话写你是从哪里看到这个岗位的，以及为什么是这家公司——这句必须你自己写，工具不知道。]",
        "evidence_lead": "和这个岗位最相关的，是我做过的这几件事，每条后面的链接都能点开看到原始提交：",
        "gap_lead": "有一项要求我目前还没有可展示的证据：{gaps}。我正在用两周时间补这个缺口，计划写在 {plan_hint}。",
        "closing": "随信附上简历，里面每一条都能追溯到公开的提交记录。期待有机会聊聊。\n\n此致\n\n{name}",
        "no_gap": "岗位列出的硬性要求，我目前都有对应的工作可以展示。",
    },
    "en": {
        "salutation": "Dear Hiring Team,",
        "opening": "I am applying for the **{title}** role. [TODO: one sentence on where you saw this role and why this company — write this yourself; the tool does not know.]",
        "evidence_lead": "The work most relevant to this role is below. Every link opens the commit it came from:",
        "gap_lead": "One requirement I cannot yet show evidence for: {gaps}. I am spending two weeks closing that gap; the plan is in {plan_hint}.",
        "closing": "My resume is attached; every line in it traces back to a public commit. I would welcome a conversation.\n\nBest regards,\n\n{name}",
        "no_gap": "I can point to work behind each of the must-have requirements listed.",
    },
}


def render_cover_letter(
    factbase: FactBase,
    report: Optional[MatchReport] = None,
    lang: str = "zh",
    max_bullets: int = 3,
    plan_hint: str = "plan.md",
) -> "object":
    from . import Rendered

    lang = "zh" if lang.startswith("zh") else "en"
    body = BODY[lang]
    trace = Trace()
    out: List[str] = []
    title = report.jd.title if report is not None and report.jd.title else "[TODO: job title]"

    out.append("# %s" % ui("letter_subject", lang, title=title))
    out.append("")
    out.append(body["salutation"])
    out.append("")
    out.append(body["opening"].format(title=title))
    out.append("")
    out.append(body["evidence_lead"])
    out.append("")

    facts = report.ranked_facts() if report is not None else sorted(
        factbase.facts, key=lambda f: -f.confidence)
    count = 0
    for fact in facts:
        if fact.source == "interview" or count >= max_bullets:
            continue
        sentence = render_fact(fact.template, fact.payload, lang)
        links = " ".join(e.link() for e in fact.evidence[:2])
        line = "- %s %s" % (sentence, links) if links else "- %s" % sentence
        out.append(line)
        trace.add(normalise(line), fact_ids=[fact.id], evidence=fact.evidence_ids()[:2])
        count += 1
    out.append("")

    gaps = report.gap_skills(("must",)) if report is not None else []
    if gaps:
        joined = "、".join(gaps[:3]) if lang == "zh" else ", ".join(gaps[:3])
        out.append(body["gap_lead"].format(gaps=joined, plan_hint=plan_hint))
    elif report is not None:
        out.append(body["no_gap"])
    out.append("")
    out.append(body["closing"].format(name=factbase.person.name or "[TODO: your name]"))
    out.append("")
    return Rendered(text="\n".join(out) + "\n", trace=trace)
