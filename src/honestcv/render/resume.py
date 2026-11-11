"""Render a resume from the fact base.

The renderer may choose which facts to show, in what order, and in which
language. It may not write a sentence that is not a fact template filled from a
fact's own payload. Every bullet it emits is recorded in the trace, so
``honestcv verify`` can prove that afterwards.
"""
from __future__ import annotations

from typing import List, Optional

from ..grounding import Trace, normalise
from ..i18n import render_fact, ui
from ..matcher import MatchReport
from ..models import FactBase, Fact


def _contact_line(person) -> str:
    bits = [b for b in (person.headline, person.location, person.email, person.phone) if b]
    for label, url in (person.links or {}).items():
        bits.append("[%s](%s)" % (label, url))
    return " · ".join(bits)


def order_facts(factbase: FactBase, report: Optional[MatchReport]) -> List[Fact]:
    if report is None:
        return sorted(factbase.facts, key=lambda f: (-f.confidence, f.id))
    ranked = report.ranked_facts()
    seen = {f.id for f in ranked}
    rest = sorted((f for f in factbase.facts if f.id not in seen),
                  key=lambda f: (-f.confidence, f.id))
    return ranked + rest


def render_resume(
    factbase: FactBase,
    report: Optional[MatchReport] = None,
    lang: str = "zh",
    max_bullets: int = 12,
    max_links: int = 3,
    overrides: Optional[dict] = None,
) -> "object":
    from . import Rendered

    trace = Trace()
    person = factbase.person
    out: List[str] = []

    out.append("# %s" % (person.name or ui("resume_title", lang)))
    contact = _contact_line(person)
    if contact:
        out.append("")
        out.append(contact)
    if report is not None and report.jd.title:
        out.append("")
        target = report.jd.title
        if report.jd.company:
            target = "%s @ %s" % (target, report.jd.company)
        out.append("**%s**: %s" % (ui("tailored_for", lang), target))
    out.append("")

    # --- evidence-backed work ---
    out.append("## %s" % ui("evidence_section", lang))
    out.append("")
    shown: List[Fact] = []
    for fact in order_facts(factbase, report):
        if fact.source == "interview":
            continue
        if len(shown) >= max_bullets:
            break
        sentence = (overrides or {}).get(fact.id) or render_fact(fact.template, fact.payload, lang)
        links = " ".join(e.link() for e in fact.evidence[:max_links])
        line = "- %s %s" % (sentence, links) if links else "- %s" % sentence
        out.append(line)
        trace.add(normalise(line), fact_ids=[fact.id], evidence=fact.evidence_ids()[:max_links])
        shown.append(fact)
    out.append("")

    # --- skills, each one pointing at the work that shows it ---
    skill_counts = factbase.skills()
    wanted = report.jd.skills() if report is not None else []
    ordered_skills = [s for s in wanted if s in skill_counts]
    ordered_skills += [s for s in skill_counts if s not in ordered_skills]
    if ordered_skills:
        out.append("## %s" % ui("skills_section", lang))
        out.append("")
        for skill in ordered_skills[:14]:
            supporting = sorted(factbase.by_skill(skill), key=lambda f: -f.confidence)[:max_links]
            if not supporting:
                continue
            links = " ".join(
                e.link() for f in supporting for e in f.evidence[:1] if e.link()
            )
            line = "- **%s** — %s" % (skill, links) if links else "- **%s**" % skill
            out.append(line)
            trace.add(
                normalise(line),
                fact_ids=[f.id for f in supporting],
                evidence=[e.eid for f in supporting for e in f.evidence[:1]],
            )
        out.append("")

    # --- what the person told us, clearly separated ---
    self_reported = [f for f in factbase.facts if f.source == "interview"]
    extras = list(person.education) + list(person.languages)
    if self_reported or extras:
        out.append("## %s" % ui("self_reported", lang))
        out.append("")
        for fact in self_reported[:6]:
            line = "- %s" % render_fact(fact.template, fact.payload, lang)
            out.append(line)
            trace.add(normalise(line), fact_ids=[fact.id], evidence=fact.evidence_ids(), kind="self_reported")
        for item in extras:
            line = "- %s" % item
            out.append(line)
            trace.add(normalise(line), kind="self_reported")
        out.append("")

    out.append("---")
    out.append("")
    out.append("*%s*" % ui("footer", lang))
    return Rendered(text="\n".join(out) + "\n", trace=trace)
