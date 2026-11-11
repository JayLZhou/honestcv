"""Bilingual rendering.

Facts are stored as ``template`` + ``payload``. Changing language swaps the
template, never the payload: that is the structural version of the rule
"translate and reorder, never add".
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
LANGS = ("zh", "en")
DEFAULT_LANG = "zh"


@lru_cache(maxsize=1)
def _bundle() -> Dict[str, Dict[str, Dict[str, str]]]:
    with open(os.path.join(DATA_DIR, "templates.json"), encoding="utf-8") as fh:
        return json.load(fh)


def normalise_lang(lang: str) -> str:
    lang = (lang or DEFAULT_LANG).lower()
    if lang.startswith("zh"):
        return "zh"
    if lang.startswith("en"):
        return "en"
    return DEFAULT_LANG


def ui(key: str, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    lang = normalise_lang(lang)
    entry = _bundle()["ui"].get(key)
    if not entry:
        return key
    text = entry.get(lang) or entry.get("en") or key
    return text.format(**kwargs) if kwargs else text


def fact_template(name: str, lang: str = DEFAULT_LANG) -> str:
    lang = normalise_lang(lang)
    entry = _bundle()["facts"].get(name)
    if not entry:
        return "{text}"
    return entry.get(lang) or entry.get("en") or "{text}"


# Counts come straight out of the evidence, so "1 commits" happens. Fixing it in
# the template is impossible (the number is not known when the template is written),
# and fixing it in the payload would mean storing prose instead of a count.
_COUNTED = ("commits", "files", "defects", "days", "tests", "issues", "lines",
            "requests", "weeks", "months")


def _singularise(text: str) -> str:
    for word in _COUNTED:
        # "1 commits" and "1 test files" both need fixing, so allow one modifier.
        text = re.sub(
            r"\b1 ((?:[A-Za-z]+ )?)%s\b" % word,
            lambda m, w=word: "1 %s%s" % (m.group(1), w[:-1]),
            text,
        )
    return text


def render_fact(template: str, payload: Dict[str, Any], lang: str = DEFAULT_LANG) -> str:
    """Fill a fact template from its payload. Missing keys render as '?' rather
    than raising, so a malformed fact is visible instead of crashing a resume."""
    tpl = fact_template(template, lang)

    class _Safe(dict):
        def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
            return "?"

    try:
        text = tpl.format_map(_Safe(payload))
    except Exception:  # pragma: no cover - defensive
        return str(payload)
    return _singularise(text) if normalise_lang(lang) == "en" else text


def localise(entry: Any, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Pick a language out of a {'en': ..., 'zh': ...} blob from a data file."""
    lang = normalise_lang(lang)
    if isinstance(entry, dict):
        text = entry.get(lang) or entry.get("en") or ""
    else:
        text = str(entry)
    return text.format(**kwargs) if kwargs else text
