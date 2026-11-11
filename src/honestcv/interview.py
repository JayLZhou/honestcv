"""The guided interview: the half of the evidence that code cannot show.

A git history shows what changed. It does not show that you were the only person
on the project, that the first design failed, that you shipped it while working
nights. Those are facts too, and they are what an interviewer actually asks
about — but they can only come from the person.

Answers are stored as facts with ``source="interview"`` and self-report
evidence, so they are always rendered as self-reported and never dressed up as
verifiable. Nothing here is generated: an unanswered question stays unanswered.
"""
from __future__ import annotations

import json
import sys
from typing import Dict, List, Optional

from .i18n import normalise_lang
from .models import Evidence, Fact
from .taxonomy import skills_in_text

QUESTIONS: List[Dict[str, str]] = [
    {"id": "role",
     "zh": "这个项目你是一个人做的，还是和别人一起？你具体负责哪一部分？",
     "en": "Did you build this alone or with others? Which part was yours?"},
    {"id": "why_built",
     "zh": "你为什么要做这个项目？是作业、工作需要，还是你自己想解决什么问题？",
     "en": "Why did you build it — coursework, a job, or a problem of your own?"},
    {"id": "decision",
     "zh": "挑一个你做过的技术决定（选了某个库、某种结构）。当时还有什么别的选法？为什么没选？",
     "en": "Pick one technical decision you made. What were the alternatives, and why did you rule them out?"},
    {"id": "first_version_failed",
     "zh": "第一版跑起来之后，最大的问题是什么？你是怎么发现的？",
     "en": "What went wrong with the first working version, and how did you find out?"},
    {"id": "hardest",
     "zh": "整个过程里你卡得最久的是哪一步？卡了多久？最后怎么过去的？",
     "en": "Where were you stuck longest? How long, and what got you unstuck?"},
    {"id": "constraint",
     "zh": "做这个项目时最大的限制是什么（时间、机器、不会的东西、英文文档）？",
     "en": "What constrained you most — time, hardware, something you did not know yet?"},
    {"id": "redo",
     "zh": "如果现在重做一遍，你会改掉哪个决定？",
     "en": "What would you do differently if you started again?"},
    {"id": "non_code_evidence",
     "zh": "除了代码，你还有什么可以拿出来的证据？（结业证书、培训记录、推荐信、线上课程、比赛名次、给开源项目提的 issue）",
     "en": "What evidence do you have besides code? Certificates, training records, references, course completions, contest results, issues you filed on other projects."},
    {"id": "non_tech_experience",
     "zh": "转行之前你做过什么工作？那份工作里你每天要处理什么？（餐饮、仓储、客服、销售都算——排班、库存、客诉处理在技术岗里都有对应的东西）",
     "en": "What did you do before this? What did a normal day involve? Scheduling, stock, customer complaints and shift handovers all have counterparts in engineering work."},
    {"id": "availability",
     "zh": "你每周能投入多少小时继续学/做项目？（写实数，这决定补齐计划现不现实）",
     "en": "How many hours a week can you put into this? Be realistic — the gap plans depend on it."},
]

GAP_QUESTION = {
    "zh": "JD 要求 {skill}，你的提交记录里看不到。你在工作、课程或自学里碰过它吗？做过什么？（没碰过就直接写『没有』，这不丢人，工具会给你一个两周补齐计划。）",
    "en": "The JD asks for {skill} and your commits do not show it. Have you touched it in work, a course or on your own? If not, write 'no' — that is fine, and the tool will give you a two-week plan.",
}

NO_ANSWER = {"", "-", "n/a", "na", "none", "skip", "无", "没有", "跳过"}


def questions(lang: str = "zh", gaps: Optional[List[str]] = None) -> List[Dict[str, str]]:
    lang = normalise_lang(lang)
    out = [{"id": q["id"], "text": q.get(lang) or q["en"]} for q in QUESTIONS]
    for skill in gaps or []:
        out.append({
            "id": "gap:%s" % skill,
            "text": (GAP_QUESTION.get(lang) or GAP_QUESTION["en"]).format(skill=skill),
        })
    return out


def answer_template(lang: str = "zh", gaps: Optional[List[str]] = None) -> Dict[str, str]:
    """A blank answers file. Fill it in a text editor instead of a terminal."""
    return {q["id"]: "" for q in questions(lang, gaps)}


def write_template(path: str, lang: str = "zh", gaps: Optional[List[str]] = None) -> str:
    payload = {
        "_help": ("每个 key 对应一个问题，运行 `honestcv questions` 可以看到问题原文。"
                  "留空表示跳过；不会有任何内容被自动填充。"
                  if normalise_lang(lang) == "zh" else
                  "Each key is a question; run `honestcv questions` to see them. "
                  "Leave a value empty to skip it. Nothing is ever filled in for you."),
        "_questions": {q["id"]: q["text"] for q in questions(lang, gaps)},
        "answers": answer_template(lang, gaps),
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return path


def load_answers(path: str) -> Dict[str, str]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict) and "answers" in data:
        data = data["answers"]
    return {str(k): str(v) for k, v in data.items() if str(v).strip()}


def facts_from_answers(answers: Dict[str, str], lang: str = "zh") -> List[Fact]:
    lang = normalise_lang(lang)
    prompts = {q["id"]: q["text"] for q in questions(lang)}
    facts: List[Fact] = []
    for qid, answer in answers.items():
        text = (answer or "").strip()
        if not text or text.lower() in NO_ANSWER:
            continue
        prompt = prompts.get(qid, "")
        skills = skills_in_text(text)
        if qid.startswith("gap:"):
            skill = qid.split(":", 1)[1]
            prompt = (GAP_QUESTION.get(lang) or GAP_QUESTION["en"]).format(skill=skill)
            if skill not in skills:
                skills = skills + [skill]
        payload = {"answer": text}
        facts.append(Fact(
            template="self_report",
            payload=payload,
            text=text,
            skills=skills,
            evidence=[Evidence(kind="self_report", ref=qid, summary=prompt)],
            source="interview",
            kind="self_report",
            metrics={},
            notes=prompt,
        ))
    return facts


def run_interactive(lang: str = "zh", gaps: Optional[List[str]] = None,
                    stream=None) -> Dict[str, str]:  # pragma: no cover - needs a tty
    """Ask the questions one at a time. Enter alone skips a question."""
    out = stream or sys.stdout
    lang = normalise_lang(lang)
    zh = lang == "zh"
    answers: Dict[str, str] = {}
    qs = questions(lang, gaps)
    out.write(("一共 %d 个问题，回车跳过，Ctrl-C 随时退出（已答的会保留）。\n\n" if zh
               else "%d questions. Press Enter to skip, Ctrl-C to stop (answers so far are kept).\n\n") % len(qs))
    for i, q in enumerate(qs, start=1):
        out.write("[%d/%d] %s\n" % (i, len(qs), q["text"]))
        out.flush()
        try:
            answer = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            out.write("\n" + ("已停止。\n" if zh else "Stopped.\n"))
            break
        if answer:
            answers[q["id"]] = answer
        out.write("\n")
    return answers
