"""Gap -> a two-week project the person actually builds themselves.

The JD asks for Kafka and there is no Kafka in the history. The dishonest fix is
a line on the resume. The honest fix is two weeks of evenings and a commit
history that is spread across them, because that history is itself the evidence.

These are plans, not code. The tool does not write the project.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Dict, List

from ..grounding import Trace, normalise
from ..i18n import localise, normalise_lang, ui

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


@lru_cache(maxsize=1)
def _blueprints() -> Dict[str, dict]:
    with open(os.path.join(DATA, "gap_projects.json"), encoding="utf-8") as fh:
        return json.load(fh)


def blueprint_for(skill: str) -> dict:
    """An exact blueprint when we have one, otherwise the generic shape."""
    data = _blueprints()
    for name, blueprint in data.items():
        if name.lower() == skill.lower():
            return blueprint
    return data["_generic"]


def has_blueprint(skill: str) -> bool:
    return any(name.lower() == skill.lower() for name in _blueprints())


def render_plan(skills: List[str], lang: str = "zh", max_plans: int = 3) -> "object":
    from . import Rendered

    lang = normalise_lang(lang)
    zh = lang == "zh"
    trace = Trace()
    out: List[str] = []

    out.append("# %s" % ("补齐计划" if zh else "Gap-closing plans"))
    out.append("")
    if not skills:
        out.append("没有发现硬性缺口。" if zh else "No must-have gaps found.")
        return Rendered(text="\n".join(out) + "\n", trace=trace)

    if zh:
        out.append("> 这里只有计划，没有代码。代码必须你自己写——面试官问的是你写代码时在想什么，")
        out.append("> 那件事没人能替你经历。两周里分散开的提交记录，本身就是你真做了的证据。")
    else:
        out.append("> These are plans, not code. You write the code: an interviewer asks what you were")
        out.append("> thinking while you wrote it, and nobody can have that experience for you. A commit")
        out.append("> history spread across two weeks is itself the evidence that you did.")
    out.append("")

    for skill in skills[:max_plans]:
        bp = blueprint_for(skill)
        out.append("## %s" % ui("plan_title", lang, skill=skill))
        out.append("")
        out.append("**%s** %s" % ("项目：" if zh else "Project:", localise(bp["title"], lang, skill=skill)))
        out.append("")
        out.append("**%s** %s" % ("目标：" if zh else "Goal:", localise(bp["goal"], lang, skill=skill)))
        out.append("")
        out.append("**%s** %s" % ("为什么这能证明你会：" if zh else "Why this proves it:",
                                  localise(bp["why_it_proves"], lang, skill=skill)))
        out.append("")
        out.append("**%s** %s" % ("不要做的事：" if zh else "Out of scope:",
                                  localise(bp["scope_guard"], lang, skill=skill)))
        out.append("")
        out.append("| %s | %s | %s |" % ("天" if zh else "Days", "做什么" if zh else "Focus",
                                         "交付物" if zh else "Deliverable"))
        out.append("| --- | --- | --- |")
        for milestone in bp["milestones"]:
            out.append("| %s | %s | %s |" % (
                milestone["days"],
                localise(milestone["focus"], lang, skill=skill),
                localise(milestone["deliverable"], lang, skill=skill)))
        out.append("")
        line = "- **%s** %s" % ("提交节奏：" if zh else "Commit rhythm:",
                                localise(bp["commit_rhythm"], lang, skill=skill))
        out.append(line)
        trace.add(normalise(line), kind="plan")
        out.append("")
        out.append("**%s**" % ("做完之后，你必须答得上来这几个问题：" if zh
                               else "When you are done, you must be able to answer:"))
        out.append("")
        for question in bp["interview_questions"]:
            line = "- %s" % localise(question, lang, skill=skill)
            out.append(line)
            trace.add(normalise(line), kind="plan")
        out.append("")
    return Rendered(text="\n".join(out) + "\n", trace=trace)
