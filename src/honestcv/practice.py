"""Interview practice built from the person's own work.

The first question in a junior technical interview is "tell me about this
project". Generic question banks do not help with that. These questions are
generated from the candidate's own commits, so practising them means getting
better at explaining what they actually did.

The tool never writes the answers. An answer you did not write is one you cannot
defend when the follow-up comes.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from .grounding import Trace, normalise
from .i18n import normalise_lang, render_fact, ui
from .matcher import MatchReport
from .models import FactBase

QUESTIONS: Dict[str, List[Dict[str, str]]] = {
    "feature": [
        {"zh": "你在 {area} 里做的这个东西，当时还有别的做法吗？为什么选了这个？",
         "en": "What were the alternatives when you built this in {area}, and why this one?"},
        {"zh": "如果用量涨十倍，这段代码最先垮在哪里？",
         "en": "If traffic grew ten times, where does this break first?"},
        {"zh": "这块代码里你最不满意的一处是哪？为什么还没改？",
         "en": "Which part of this are you least happy with, and why is it still there?"},
    ],
    "bugfix": [
        {"zh": "讲一下这个 bug：{subject}。你是怎么定位到它的？",
         "en": "Walk me through this bug: {subject}. How did you track it down?"},
        {"zh": "你怎么确认它真的修好了，而不是被你盖住了？",
         "en": "How did you confirm it was actually fixed rather than hidden?"},
        {"zh": "这个问题当初是怎么被写进去的？以后怎么防？",
         "en": "How did this get introduced, and what stops it happening again?"},
    ],
    "perf": [
        {"zh": "优化之前你量了什么？数字是多少？",
         "en": "What did you measure before optimising, and what was the number?"},
        {"zh": "瓶颈最后在哪？你一开始猜的是哪？",
         "en": "Where was the bottleneck, and where did you first guess it was?"},
    ],
    "refactor": [
        {"zh": "重构之前的代码哪里让你受不了？不重构会怎样？",
         "en": "What made the old code unbearable, and what if you had left it?"},
        {"zh": "重构过程中你怎么保证没改坏？",
         "en": "How did you make sure the refactor did not break anything?"},
    ],
    "test": [
        {"zh": "这些测试拦住过什么真实的问题？",
         "en": "What real problem have these tests caught?"},
        {"zh": "哪一部分你故意没写测试？为什么？",
         "en": "What did you deliberately not test, and why?"},
    ],
    "infra": [
        {"zh": "这套构建/部署在什么情况下会失败？你见过吗？",
         "en": "When does this build or deployment fail? Have you seen it fail?"},
        {"zh": "新同事从零把它跑起来要多久？卡在哪？",
         "en": "How long does a new teammate need to run this from scratch, and where do they get stuck?"},
    ],
    "adoption": [
        {"zh": "你为什么引入 {tech}？不引入的话这件事怎么做？",
         "en": "Why did you bring in {tech}? How would you have done it without?"},
        {"zh": "{tech} 给你带来了什么代价——复杂度、运维、学习成本？",
         "en": "What did {tech} cost you — complexity, operations, learning time?"},
    ],
    "sustained": [
        {"zh": "这个项目做了 {days} 天，中间最大的一次返工是什么？",
         "en": "You worked on this for {days} days. What was the biggest piece of rework?"},
        {"zh": "如果现在重做一遍，你最早会改掉哪个决定？",
         "en": "Starting over today, which early decision would you change first?"},
    ],
}

GENERIC = {
    "zh": [
        "现场打开你的仓库，随便挑一个文件，解释它为什么存在。",
        "面试官会默认你的项目是 AI 生成的。你准备怎么让他改变看法？（提示：讲你踩过的坑，生成的代码没有坑。）",
        "你这个项目里，哪一行代码你现在还解释不清？（先自己找出来，别等面试官找。）",
    ],
    "en": [
        "Open your repository live, pick a file at random, and explain why it exists.",
        "The interviewer will assume your project was generated. How do you change their mind? (Hint: talk about what went wrong. Generated code has no scars.)",
        "Which line in this project can you still not explain? Find it yourself before an interviewer does.",
    ],
}


def _questions_for(fact, lang: str) -> List[str]:
    bank = QUESTIONS.get(fact.kind, QUESTIONS["feature"])
    out: List[str] = []
    payload = dict(fact.payload)
    payload.setdefault("area", payload.get("repo", "this project"))
    payload.setdefault("subject", payload.get("repo", "this change"))
    payload.setdefault("tech", ", ".join(fact.skills[:2]) or payload.get("repo", ""))
    payload.setdefault("days", fact.metrics.get("days", 0))
    for question in bank:
        text = question.get(lang) or question["en"]
        try:
            out.append(text.format(**payload))
        except (KeyError, IndexError):  # pragma: no cover - defensive
            out.append(text)
    return out


def render_practice(
    factbase: FactBase,
    report: Optional[MatchReport] = None,
    lang: str = "zh",
    max_facts: int = 6,
) -> "object":
    from .render import Rendered

    lang = normalise_lang(lang)
    zh = lang == "zh"
    trace = Trace()
    out: List[str] = []

    out.append("# %s" % ui("practice_title", lang))
    out.append("")
    out.append("> %s" % ui("star_prompt", lang))
    out.append("")

    facts = report.ranked_facts() if report is not None else sorted(
        factbase.facts, key=lambda f: -f.confidence)
    facts = [f for f in facts if f.source != "interview"][:max_facts]

    for i, fact in enumerate(facts, start=1):
        out.append("## %d." % i)
        out.append("")
        sentence = render_fact(fact.template, fact.payload, lang)
        links = " ".join(e.link() for e in fact.evidence[:3])
        line = "- %s %s" % (sentence, links) if links else "- %s" % sentence
        out.append(line)
        trace.add(normalise(line), fact_ids=[fact.id], evidence=fact.evidence_ids()[:3])
        if links:
            hint = "- *%s*: %s" % (ui("evidence_to_reread", lang), links)
            out.append(hint)
            trace.add(normalise(hint), fact_ids=[fact.id], evidence=fact.evidence_ids()[:3], kind="hint")
        out.append("")
        for question in _questions_for(fact, lang):
            line = "- ❓ %s" % question
            out.append(line)
            trace.add(normalise(line), kind="question")
        out.append("")
        out.append("```")
        out.append("S (%s):" % ("背景" if zh else "Situation"))
        out.append("T (%s):" % ("任务" if zh else "Task"))
        out.append("A (%s):" % ("你做了什么" if zh else "Action"))
        out.append("R (%s):" % ("结果，带上你量到的数字" if zh else "Result, with the number you measured"))
        out.append("```")
        out.append("")

    out.append("## %s" % ("不管聊哪个项目都会被问到的" if zh else "Asked about any project"))
    out.append("")
    for question in GENERIC[lang]:
        line = "- ❓ %s" % question
        out.append(line)
        trace.add(normalise(line), kind="question")
    out.append("")
    return Rendered(text="\n".join(out) + "\n", trace=trace)
