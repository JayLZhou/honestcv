"""Bilingual rendering.

Facts are stored as ``template`` + ``payload``. Changing language swaps the
template, never the payload: that is the structural version of the rule
"translate and reorder, never add".
"""
from __future__ import annotations

import json
import os
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


def render_fact(template: str, payload: Dict[str, Any], lang: str = DEFAULT_LANG) -> str:
    """Fill a fact template from its payload. Missing keys render as '?' rather
    than raising, so a malformed fact is visible instead of crashing a resume."""
    tpl = fact_template(template, lang)

    class _Safe(dict):
        def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
            return "?"

    try:
        return tpl.format_map(_Safe(payload))
    except Exception:  # pragma: no cover - defensive
        return str(payload)


def localise(entry: Any, lang: str = DEFAULT_LANG, **kwargs: Any) -> str:
    """Pick a language out of a {'en': ..., 'zh': ...} blob from a data file."""
    lang = normalise_lang(lang)
    if isinstance(entry, dict):
        text = entry.get(lang) or entry.get("en") or ""
    else:
        text = str(entry)
    return text.format(**kwargs) if kwargs else text
