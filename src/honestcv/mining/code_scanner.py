"""Facts from source code, for people whose work has no git history behind it.

A bootcamp project handed over as a zip. Coursework. A repository someone else
initialised with one "initial commit". The evidence is there - it just has no
timeline, no authorship and nothing to click.

So this module reads the code itself and counts what is actually in it:
endpoints, data models, tests, the technologies the imports prove, how much of
each language. Every number is counted from a file that is named in the
evidence, with a line number where there is one.

What it deliberately does not do is pretend this is as good as a commit.
Evidence here is of kind ``file`` - half the strength of a commit in the model -
facts carry ``source="code"``, the resume renders them in their own section, and
``verify`` warns on every line that rests on files alone. A folder of code
cannot show who wrote it, when, or in what order, and this tool will not imply
otherwise.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from ..i18n import render_fact
from ..models import Evidence, Fact
from ..taxonomy import path_hint_skills, skills_for_dependency, skills_for_path

IGNORE_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "bower_components", "vendor", "dist", "build",
    "out", "target", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "venv", ".venv", "env", ".env", "site-packages", ".next", ".nuxt", ".cache",
    "coverage", "htmlcov", ".idea", ".vscode", ".terraform", "Pods", ".gradle",
}
IGNORE_SUFFIXES = (
    ".min.js", ".min.css", ".lock", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".ico", ".pdf", ".zip", ".tar", ".gz", ".whl", ".so", ".dylib", ".dll", ".class",
    ".pyc", ".jar", ".woff", ".woff2", ".ttf", ".mp4", ".mp3", ".csv", ".parquet",
)
MAX_FILE_BYTES = 400_000
MAX_FILES = 4000

MANIFESTS = ("requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py",
             "package.json", "go.mod", "cargo.toml", "pom.xml", "build.gradle",
             "gemfile", "composer.json", "environment.yml", "pipfile")

TEST_PATH = re.compile(r"(^|/)(tests?|spec|__tests__)/|_test\.|\.test\.|\.spec\.|test_[^/]*\.py$",
                       re.IGNORECASE)

ROUTE = re.compile(
    r"@(?:app|router|api|bp|blueprint|\w+_bp)\.(?:get|post|put|patch|delete|route)\s*\("
    r"|\b(?:app|router|api|server)\.(?:get|post|put|patch|delete)\s*\(\s*[\"'`]"
    r"|@(?:Get|Post|Put|Patch|Delete|Request)Mapping\b"
    r"|\b(?:mux|r|router|http)\.(?:HandleFunc|Handle|GET|POST|PUT|DELETE)\s*\("
    r"|^\s*path\s*\(\s*[\"']"
    r"|^\s*export\s+(?:async\s+)?function\s+(?:GET|POST|PUT|PATCH|DELETE)\b",
    re.MULTILINE)

MODEL = re.compile(
    r"class\s+\w+\s*\(\s*(?:models\.Model|Base|db\.Model|SQLModel)"
    r"|__tablename__\s*="
    r"|CREATE\s+TABLE"
    r"|@Entity\b|@Table\b"
    r"|^\s*model\s+\w+\s*\{",
    re.IGNORECASE | re.MULTILINE)

TEST_FN = re.compile(
    r"^\s*def\s+test_\w+|^\s*(?:async\s+)?func\s+Test\w+|@Test\b"
    r"|\b(?:it|test)\s*\(\s*[\"'`]",
    re.MULTILINE)

FUNC = {
    "Python": re.compile(r"^\s*(?:async\s+)?def\s+\w+", re.MULTILINE),
    "Go": re.compile(r"^\s*func\s+", re.MULTILINE),
    "Rust": re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+\w+", re.MULTILINE),
    "_js": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+\w+"
                      r"|^\s*(?:export\s+)?const\s+\w+\s*=\s*(?:async\s*)?\([^)]*\)\s*=>",
                      re.MULTILINE),
    "_jvm": re.compile(r"^\s*(?:public|private|protected)\s+[\w<>\[\],\s]+\s+\w+\s*\(",
                       re.MULTILINE),
}
CLASS = re.compile(r"^\s*(?:export\s+)?(?:public\s+)?(?:abstract\s+)?(?:class|interface|struct)\s+\w+",
                   re.MULTILINE)

IMPORTS = (
    re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][\w\.]*)", re.MULTILINE),          # python
    re.compile(r"""(?:from|require\()\s*["']([^"'./][^"']*)["']""", re.MULTILINE),  # js / ts
    re.compile(r"""^\s*import\s+(?:[\w\.]+\s+)?["']([^"']+)["']""", re.MULTILINE),  # go
    re.compile(r"^\s*import\s+([a-z][\w\.]+)\s*;", re.MULTILINE),                   # java
    re.compile(r"^\s*use\s+([a-z][\w:]+)", re.MULTILINE),                           # rust
)


@dataclass
class FileFacts:
    path: str
    lang: str = ""
    lines: int = 0
    is_test: bool = False
    functions: int = 0
    classes: int = 0
    routes: List[int] = field(default_factory=list)   # line numbers
    models: List[int] = field(default_factory=list)
    tests: int = 0
    test_lines: List[int] = field(default_factory=list)
    techs: Set[str] = field(default_factory=set)


@dataclass
class ScanResult:
    project: str
    root: str
    files: List[FileFacts] = field(default_factory=list)
    skipped: int = 0

    @property
    def source_files(self) -> List[FileFacts]:
        return [f for f in self.files if f.lang]

    @property
    def lines(self) -> int:
        return sum(f.lines for f in self.files)

    def languages(self) -> List[Tuple[str, int]]:
        counts: Dict[str, int] = {}
        for f in self.source_files:
            counts[f.lang] = counts.get(f.lang, 0) + f.lines
        return sorted(counts.items(), key=lambda kv: -kv[1])

    def techs(self) -> Dict[str, str]:
        """tech -> the first file that shows it."""
        out: Dict[str, str] = {}
        for f in sorted(self.files, key=lambda f: f.path):
            for tech in sorted(f.techs):
                out.setdefault(tech, f.path)
        return out


def _line_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _lang_of(path: str) -> str:
    for skill in skills_for_path(path):
        # Only count a file as "written in X" for languages, not for frameworks
        # that merely happen to share a path hint.
        from ..taxonomy import category
        if category(skill) == "language":
            return skill
    return ""


REGEXY = re.compile(r"""re\.compile|r["']|\\s|\\w|\\b|\|\s*\^""")


def _line_numbers(pattern: re.Pattern, text: str) -> List[int]:
    """Line numbers of real matches. A line that is itself a regular expression -
    this module's own source, a linter config, documentation of a framework - is
    not evidence that the project uses the thing it describes."""
    out: List[int] = []
    lines = text.splitlines()
    for m in pattern.finditer(text):
        no = text.count("\n", 0, m.start()) + 1
        line = lines[no - 1] if no <= len(lines) else ""
        if REGEXY.search(line):
            continue
        out.append(no)
    return out


def _imported_techs(text: str) -> Set[str]:
    found: Set[str] = set()
    for pattern in IMPORTS:
        for module in pattern.findall(text)[:400]:
            head = module.split(".")[0].split("/")[0].strip()
            if not head or len(head) < 2:
                continue
            for skill in skills_for_dependency(head):
                found.add(skill)
            for skill in skills_for_dependency(module):
                found.add(skill)
    return found


def _manifest_techs(path: str, text: str) -> Set[str]:
    name = os.path.basename(path).lower()
    tokens: List[str] = []
    if name == "package.json":
        try:
            data = json.loads(text)
            for key in ("dependencies", "devDependencies", "peerDependencies"):
                tokens.extend(data.get(key, {}).keys())
        except (ValueError, AttributeError):
            pass
    elif name == "pom.xml":
        tokens = re.findall(r"<artifactId>([^<]+)</artifactId>", text)
    elif name == "go.mod":
        tokens = re.findall(r"^\s+([\w\.\-/]+)\s+v", text, re.MULTILINE)
    else:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "[", "-r ", "//")):
                continue
            token = re.split(r"[<>=!~\[\s;,:\"']", line)[0].strip('",\'')
            if token:
                tokens.append(token)
    found: Set[str] = set()
    for token in tokens[:300]:
        for skill in skills_for_dependency(token):
            found.add(skill)
    return found


def analyse_file(root: str, rel_path: str) -> Optional[FileFacts]:
    full = os.path.join(root, rel_path)
    try:
        if os.path.getsize(full) > MAX_FILE_BYTES:
            return None
        with open(full, encoding="utf-8", errors="ignore") as fh:
            text = fh.read()
    except (OSError, ValueError):
        return None
    if "\x00" in text[:2048]:
        return None

    info = FileFacts(path=rel_path, lang=_lang_of(rel_path), lines=_line_count(text))
    info.is_test = bool(TEST_PATH.search("/" + rel_path))
    info.techs |= set(path_hint_skills(rel_path))
    if os.path.basename(rel_path).lower() in MANIFESTS:
        info.techs |= _manifest_techs(rel_path, text)
        return info
    if not info.lang:
        return info

    info.techs |= _imported_techs(text)
    info.routes = _line_numbers(ROUTE, text)
    info.models = _line_numbers(MODEL, text)
    if info.is_test:
        info.test_lines = _line_numbers(TEST_FN, text)
        info.tests = len(info.test_lines)
    pattern = FUNC.get(info.lang)
    if pattern is None:
        pattern = FUNC["_jvm"] if info.lang in ("Java", "Kotlin", "C#") else FUNC["_js"]
    info.functions = len(pattern.findall(text))
    info.classes = len(CLASS.findall(text))
    return info


def scan_tree(root: str, max_files: int = MAX_FILES) -> ScanResult:
    root = os.path.abspath(os.path.expanduser(root))
    if not os.path.isdir(root):
        raise NotADirectoryError("%s is not a directory" % root)
    base = os.path.basename(root.rstrip("/")) or root
    if base.lower() in ("src", "lib", "app", "source", "sources", "code"):
        parent = os.path.basename(os.path.dirname(root.rstrip("/")))
        base = parent or base
    result = ScanResult(project=base, root=root)
    for dirpath, dirnames, filenames in os.walk(root):
        # ".git" is in IGNORE_DIRS; a prefix test would also throw away ".github",
        # which is where the CI evidence lives.
        dirnames[:] = sorted(d for d in dirnames if d not in IGNORE_DIRS)
        for name in sorted(filenames):
            if name.lower().endswith(IGNORE_SUFFIXES):
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), root)
            if len(result.files) >= max_files:
                result.skipped += 1
                continue
            info = analyse_file(root, rel)
            if info is None:
                result.skipped += 1
                continue
            if info.lang or info.techs:
                result.files.append(info)
    return result


def area_of_path(path: str) -> str:
    parts = [p for p in path.replace("\\", "/").split("/") if p]
    if len(parts) == 1:
        return "(root)"
    head = parts[0].lower()
    if head in ("src", "lib", "app", "pkg", "internal", "packages", "cmd") and len(parts) > 2:
        return "%s/%s" % (parts[0], parts[1])
    return parts[0]


def _evidence(files: Sequence[FileFacts], project: str, base_url: str, branch: str,
              lines: Optional[Dict[str, int]] = None, limit: int = 4) -> List[Evidence]:
    out: List[Evidence] = []
    for info in list(files)[:limit]:
        line = (lines or {}).get(info.path)
        ref = "%s:%d" % (info.path, line) if line else info.path
        url = ""
        if base_url:
            url = "%s/blob/%s/%s" % (base_url.rstrip("/"), branch, info.path)
            if line:
                url += "#L%d" % line
        out.append(Evidence(kind="file", ref=ref, repo=project, url=url,
                            summary=info.path, stats={"lines": info.lines}))
    return out


def scan_code(
    path: str,
    project: Optional[str] = None,
    lang: str = "en",
    repo_url: str = "",
    branch: str = "main",
    max_facts: int = 24,
) -> List[Fact]:
    """Read a directory of source code and return facts, all of them file-backed."""
    result = scan_tree(path)
    if project:
        result.project = project
    if not result.source_files:
        return []

    name = result.project
    facts: List[Fact] = []
    by_lines = sorted(result.source_files, key=lambda f: -f.lines)
    languages = [l for l, _ in result.languages()[:3]]

    # 1. the project as a whole
    payload = {
        "project": name,
        "files": len(result.source_files),
        "lines": result.lines,
        "languages": ", ".join(languages) if lang == "en" else "、".join(languages),
    }
    facts.append(Fact(
        template="code_project", payload=payload,
        text=render_fact("code_project", payload, lang),
        skills=languages,
        evidence=_evidence(by_lines, name, repo_url, branch),
        source="code", kind="codebase",
        metrics={"files": len(result.source_files), "lines": result.lines},
    ))

    # 2. the modules it is made of
    areas: Dict[str, List[FileFacts]] = {}
    for info in result.source_files:
        areas.setdefault(area_of_path(info.path), []).append(info)
    for area, files in sorted(areas.items(), key=lambda kv: -sum(f.lines for f in kv[1])):
        if area == "(root)" or len(files) < 3:
            continue
        if len(areas) < 2 or area.lower() == name.lower():
            continue   # "built the X module of X" says nothing the project fact did not
        if all(f.is_test for f in files):
            continue   # the tests get their own fact, with a count in it
        skills = sorted({f.lang for f in files if f.lang} |
                        {s for f in files for s in f.techs})[:6]
        payload = {"project": name, "area": area, "files": len(files),
                   "lines": sum(f.lines for f in files)}
        facts.append(Fact(
            template="code_module", payload=payload,
            text=render_fact("code_module", payload, lang), skills=skills,
            evidence=_evidence(sorted(files, key=lambda f: -f.lines), name, repo_url, branch),
            source="code", kind="codebase",
            metrics={"files": payload["files"], "lines": payload["lines"]},
        ))
        if len(facts) >= max_facts:
            break

    # 3. things that are countable and that an interviewer asks about
    routed = [f for f in result.files if f.routes]
    if sum(len(f.routes) for f in routed) >= 2:
        payload = {"project": name, "count": sum(len(f.routes) for f in routed),
                   "files": len(routed)}
        facts.append(Fact(
            template="code_endpoints", payload=payload,
            text=render_fact("code_endpoints", payload, lang),
            skills=sorted({"REST API"} | {f.lang for f in routed if f.lang})[:4],
            evidence=_evidence(routed, name, repo_url, branch,
                               lines={f.path: f.routes[0] for f in routed}),
            source="code", kind="codebase", metrics=dict(payload),
        ))

    modelled = [f for f in result.files if f.models]
    if modelled:
        payload = {"project": name, "count": sum(len(f.models) for f in modelled),
                   "files": len(modelled)}
        facts.append(Fact(
            template="code_models", payload=payload,
            text=render_fact("code_models", payload, lang),
            skills=sorted({s for f in modelled for s in f.techs} |
                          {f.lang for f in modelled if f.lang})[:4],
            evidence=_evidence(modelled, name, repo_url, branch,
                               lines={f.path: f.models[0] for f in modelled}),
            source="code", kind="codebase", metrics=dict(payload),
        ))

    tested = [f for f in result.files if f.tests]
    if tested:
        payload = {"project": name, "count": sum(f.tests for f in tested),
                   "files": len(tested)}
        facts.append(Fact(
            template="code_tests", payload=payload,
            text=render_fact("code_tests", payload, lang),
            skills=["Testing"] + [f.lang for f in tested[:1] if f.lang],
            evidence=_evidence(tested, name, repo_url, branch,
                               lines={f.path: f.test_lines[0] for f in tested if f.test_lines}),
            source="code", kind="codebase", metrics=dict(payload),
        ))

    # 4. technologies the code itself proves, one fact each
    covered = {s for f in facts for s in f.skills}
    by_path = {f.path: f for f in result.files}
    for tech, where in result.techs().items():
        if tech in covered or len(facts) >= max_facts:
            continue
        payload = {"project": name, "tech": tech, "file": where}
        facts.append(Fact(
            template="code_tech", payload=payload,
            text=render_fact("code_tech", payload, lang), skills=[tech],
            evidence=_evidence([by_path[where]], name, repo_url, branch),
            source="code", kind="codebase",
        ))
    return facts


def summarise(result: ScanResult, lang: str = "en") -> str:
    zh = lang == "zh"
    langs = ", ".join("%s %d" % (l, n) for l, n in result.languages()[:4])
    if zh:
        return "%d 个源文件、%d 行代码（%s）" % (len(result.source_files), result.lines, langs)
    return "%d source files, %d lines (%s)" % (len(result.source_files), result.lines, langs)
