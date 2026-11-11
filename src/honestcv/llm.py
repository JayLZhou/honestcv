"""Optional LLM polish — strictly bounded, never trusted.

Everything in honestcv works without this module. It exists for one narrow job:
making a mined sentence read like a human wrote it, in the person's second
language, without changing what it says.

The model is given one sentence and the exact facts behind it, and is allowed to
rephrase. It never sees the evidence links (we re-attach those ourselves, so it
cannot invent one), and every sentence it returns is re-checked against the same
rules the deterministic renderer obeys: no new number, no new skill, no new
claim. A sentence that fails goes in the bin and the original is kept.

If ``anthropic`` is not installed or no credentials are configured, the tool
behaves exactly as before. Nothing degrades.
"""
from __future__ import annotations

import json
import os
import re
from typing import List, Optional, Sequence, Tuple

from .models import Fact
from .taxonomy import skills_in_text

DEFAULT_MODEL = os.environ.get("HONESTCV_MODEL", "claude-opus-5-5")
NUMBER = re.compile(r"\d+(?:[.,]\d+)*%?")

SYSTEM = """You rewrite one resume bullet at a time for a junior engineer.

Rules, in order of importance:
1. Never add a fact. No numbers, technologies, job titles, team sizes, impact or
   outcomes that are not in the input. If the input does not say it, it does not exist.
2. Never remove a number or a technology that is in the input.
3. Rewrite only for readability and natural phrasing in the target language.
4. No superlatives, no "expert", no "spearheaded", no impact you were not given.
5. Return JSON only: {"bullets": ["...", ...]} with exactly as many items as you were given,
   in the same order.

The person reading this resume will click through to the commits. A sentence
that overstates what the commits show costs them the interview."""


class LLMUnavailable(RuntimeError):
    pass


def available() -> Tuple[bool, str]:
    """(usable, reason). Never raises; the CLI prints the reason and carries on."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False, "the `anthropic` package is not installed (pip install honestcv[llm])"
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return False, "no ANTHROPIC_API_KEY in the environment"
    return True, ""


def _violates(original: str, rewritten: str, fact: Fact) -> str:
    """Return a reason the rewrite must be rejected, or '' if it is clean."""
    if not rewritten.strip():
        return "empty"
    if len(rewritten) > max(240, len(original) * 2):
        return "too long"
    allowed_numbers = set()
    for value in fact.numeric_claims():
        allowed_numbers.update(NUMBER.findall(str(value)))
    for number in NUMBER.findall(rewritten):
        if number not in allowed_numbers:
            return "introduced the number %s" % number
    for number in NUMBER.findall(original):
        if number not in NUMBER.findall(rewritten):
            return "dropped the number %s" % number
    allowed_skills = set(fact.skills) | set(skills_in_text(fact.text)) | set(skills_in_text(original))
    for skill in skills_in_text(rewritten):
        if skill not in allowed_skills:
            return "introduced %s" % skill
    if "](" in rewritten or "http" in rewritten:
        return "tried to write a link"
    return ""


def polish(
    sentences: Sequence[str],
    facts: Sequence[Fact],
    lang: str = "zh",
    model: Optional[str] = None,
    max_tokens: int = 4096,
) -> Tuple[List[str], List[str]]:
    """Rephrase sentences. Returns (sentences, notes) — rejected rewrites are
    silently replaced by the original and explained in notes."""
    usable, reason = available()
    if not usable:
        raise LLMUnavailable(reason)
    if len(sentences) != len(facts):
        raise ValueError("sentences and facts must line up")
    import anthropic

    client = anthropic.Anthropic()
    payload = {
        "language": "Chinese" if lang.startswith("zh") else "English",
        "bullets": [
            {
                "text": sentence,
                "numbers_you_may_use": sorted({n for v in fact.numeric_claims()
                                               for n in NUMBER.findall(str(v))}),
                "technologies_you_may_name": fact.skills,
            }
            for sentence, fact in zip(sentences, facts)
        ],
    }
    response = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise LLMUnavailable("the model did not return JSON")
    try:
        rewritten = json.loads(match.group(0)).get("bullets", [])
    except json.JSONDecodeError as exc:
        raise LLMUnavailable("could not parse the model's JSON: %s" % exc)

    out: List[str] = []
    notes: List[str] = []
    for i, original in enumerate(sentences):
        candidate = rewritten[i] if i < len(rewritten) else ""
        if not isinstance(candidate, str):
            candidate = ""
        reason = _violates(original, candidate, facts[i])
        if reason:
            notes.append("kept the original bullet %d: the rewrite %s" % (i + 1, reason))
            out.append(original)
        else:
            out.append(candidate.strip())
    return out, notes
