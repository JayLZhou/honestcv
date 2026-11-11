"""Document renderers. Every one of them returns a document *and* its trace."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from ..grounding import Trace, trace_path_for


@dataclass
class Rendered:
    text: str
    trace: Trace

    def save(self, path: str) -> Tuple[str, str]:
        path = os.path.abspath(os.path.expanduser(path))
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(self.text)
        self.trace.document = path
        tpath = trace_path_for(path)
        self.trace.save(tpath)
        return path, tpath


from .resume import render_resume  # noqa: E402,F401
from .cover_letter import render_cover_letter  # noqa: E402,F401
from .project_plan import render_plan, blueprint_for  # noqa: E402,F401
