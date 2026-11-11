"""honestcv — turn evidence you already have into a resume a recruiter can check.

Three rules the whole package exists to keep:

1. A claim without evidence is not written.
2. Translating and reordering facts is allowed; adding one is not.
3. Anything the person merely told us is labelled as such, every time.
"""
from __future__ import annotations

__version__ = "0.1.0"

from .models import Evidence, Fact, FactBase, Person  # noqa: F401

__all__ = ["Evidence", "Fact", "FactBase", "Person", "__version__"]
