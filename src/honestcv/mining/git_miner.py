"""Turn a git history into facts.

What goes in: the commits a person actually authored.
What comes out: facts whose payload contains only numbers and strings that came
out of those commits, each carrying links a recruiter can click.

The README's claim rests on this file: nothing here invents, estimates or
embellishes. If a number is in a fact, it was counted.
"""
from __future__ import annotations

import os
import re
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from ..models import Evidence, Fact
from ..taxonomy import load_skills, skills_for_dependency, skills_for_path, skills_in_text
from ..i18n import render_fact

REC = "\x01"
SEP = "\x1f"

MANIFESTS = (
    "requirements.txt", "pyproject.toml", "setup.py", "pipfile", "package.json",
    "go.mod", "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts",
    "gemfile", "composer.json", "environment.yml",
)

IGNORED_PATH_PARTS = (
    "node_modules/", "vendor/", "dist/", "build/", ".min.", "third_party/",
    "site-packages/", ".venv/", "venv/",
)
LOCK_FILES = ("package-lock.json", "yarn.lock", "poetry.lock", "cargo.lock", "pnpm-lock.yaml", "go.sum")

# Order matters: the first pattern that matches a subject wins.
KIND_PATTERNS: Sequence[Tuple[str, str]] = (
    ("bugfix", r"\b(fix(e[sd])?|bugfix|hotfix|patch(ed)?|resolve[sd]?|correct(ed)?)\b|修复|修正|解决"),
    ("perf", r"\b(perf|performance|optimi[sz]e[sd]?|speed ?up|faster|latency|cache)\b|性能|优化|提速"),
    ("test", r"\b(test(s|ing)?|spec|coverage|pytest|jest)\b|测试|用例"),
    ("refactor", r"\b(refactor|cleanup|clean up|tidy|rename|restructure|simplif(y|ied))\b|重构|整理|清理"),
    ("docs", r"\b(docs?|documentation|readme|comment(s|ed)?)\b|文档|注释|说明"),
    ("infra", r"\b(ci|cd|build|deploy|release|docker|k8s|kubernetes|pipeline|workflow|chore\(deps\))\b|部署|构建|发布|流水线"),
    ("feature", r"\b(feat(ure)?|add(ed|s)?|implement(ed|s)?|introduce[sd]?|support|new)\b|新增|实现|支持|引入"),
)

GENERIC_SUBJECTS = re.compile(
    r"^(update|updates|updated|fix|fixes|wip|tmp|temp|misc|minor|cleanup|init|initial commit|commit|change[sd]?|"
    r"更新|修改|提交|初始化|临时)\W*$",
    re.IGNORECASE,
)
CONVENTIONAL_PREFIX = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\([^)]*\))?!?:\s*", re.I)
ISSUE_REF = re.compile(r"#(\d{1,6})\b")
PR_MERGE = re.compile(r"Merge pull request #(\d+)", re.I)


class GitError(RuntimeError):
    pass


@dataclass
class Commit:
    sha: str
    name: str
    email: str
    date: str
    subject: str
    files: List[Tuple[int, int, str]] = field(default_factory=list)

    @property
    def additions(self) -> int:
        return sum(a for a, _, _ in self.files)

    @property
    def deletions(self) -> int:
        return sum(d for _, d, _ in self.files)

    @property
    def paths(self) -> List[str]:
        return [p for _, _, p in self.files]

    @property
    def size(self) -> int:
        return self.additions + self.deletions


def _git(repo: str, *args: str, check: bool = True) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True, text=True, errors="replace",
        )
    except FileNotFoundError as exc:  # pragma: no cover - environment dependent
        raise GitError("git is not installed or not on PATH") from exc
    if check and proc.returncode != 0:
        raise GitError((proc.stderr or proc.stdout).strip() or "git failed: %s" % " ".join(args))
    return proc.stdout


def is_git_repo(path: str) -> bool:
    try:
        return _git(path, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except GitError:
        return False


def repo_identity(repo: str) -> Tuple[str, str]:
    """Return (slug, web_base). Falls back to the directory name with no URL."""
    try:
        url = _git(repo, "remote", "get-url", "origin").strip()
    except GitError:
        url = ""
    if not url:
        return os.path.basename(os.path.abspath(repo)), ""
    cleaned = url
    if cleaned.startswith("git@"):
        cleaned = cleaned.replace(":", "/", 1).replace("git@", "https://", 1)
    cleaned = re.sub(r"\.git$", "", cleaned)
    m = re.match(r"https?://(?:[^@/]+@)?([^/]+)/(.+)$", cleaned)
    if not m:
        return os.path.basename(os.path.abspath(repo)), ""
    host, path = m.group(1), m.group(2).strip("/")
    slug = path
    if host.endswith("github.com") or host.endswith("gitlab.com") or "git" in host:
        return slug, "https://%s/%s" % (host, path)
    return slug, ""


def _commit_url(base: str, sha: str) -> str:
    if not base:
        return ""
    if "gitlab" in base:
        return "%s/-/commit/%s" % (base, sha)
    return "%s/commit/%s" % (base, sha)


def _issue_url(base: str, number: str) -> str:
    if not base:
        return ""
    if "gitlab" in base:
        return "%s/-/issues/%s" % (base, number)
    return "%s/issues/%s" % (base, number)


def list_authors(repo: str) -> List[Tuple[str, str, int]]:
    """Every author in the history, most commits first."""
    out = _git(repo, "log", "--no-merges", "--pretty=format:%an" + SEP + "%ae")
    counter: Counter = Counter()
    for line in out.splitlines():
        if SEP not in line:
            continue
        name, email = line.split(SEP, 1)
        counter[(name.strip(), email.strip().lower())] += 1
    return [(n, e, c) for (n, e), c in counter.most_common()]


def read_commits(
    repo: str,
    author: Optional[str] = None,
    since: Optional[str] = None,
    max_commits: int = 5000,
) -> List[Commit]:
    """Read commits with per-file line counts. ``author`` matches name or email."""
    if not is_git_repo(repo):
        raise GitError("%s is not a git repository" % repo)
    args = [
        "log", "--no-merges", "--date=short", "--numstat",
        "--pretty=format:%s%%H%s%%an%s%%ae%s%%ad%s%%s" % (REC, SEP, SEP, SEP, SEP),
        "-n", str(max_commits),
    ]
    if since:
        args.append("--since=%s" % since)
    raw = _git(repo, *args)

    commits: List[Commit] = []
    needle = (author or "").strip().lower()
    for block in raw.split(REC):
        block = block.strip("\n")
        if not block:
            continue
        head, _, rest = block.partition("\n")
        parts = head.split(SEP)
        if len(parts) < 5:
            continue
        sha, name, email, date, subject = parts[0], parts[1], parts[2], parts[3], SEP.join(parts[4:])
        if needle and needle not in name.lower() and needle not in email.lower():
            continue
        files: List[Tuple[int, int, str]] = []
        for line in rest.splitlines():
            cols = line.split("\t")
            if len(cols) != 3:
                continue
            add, dele, path = cols
            if any(part in path.lower() for part in IGNORED_PATH_PARTS):
                continue
            if os.path.basename(path).lower() in LOCK_FILES:
                continue
            files.append((_int(add), _int(dele), path))
        commits.append(Commit(sha=sha, name=name, email=email, date=date, subject=subject.strip(), files=files))
    return commits


def _int(value: str) -> int:
    try:
        return int(value)
    except ValueError:  # binary files show as "-"
        return 0


def classify(commit: Commit) -> str:
    subject = commit.subject
    for kind, pattern in KIND_PATTERNS:
        if re.search(pattern, subject, re.IGNORECASE):
            return kind
    paths = [p.lower() for p in commit.paths]
    if paths and all(("test" in p or "spec" in p) for p in paths):
        return "test"
    if paths and all(
        any(h in p for h in (".github/workflows", "dockerfile", "docker-compose", ".gitlab-ci", "jenkinsfile", "makefile"))
        for p in paths
    ):
        return "infra"
    return "feature"


def area_of(commit: Commit) -> str:
    """The part of the tree a commit touched, as a short human-readable label."""
    segments: Counter = Counter()
    nested = [p for p in commit.paths if "/" in p.replace("\\", "/")]
    for path in (nested or commit.paths):
        parts = [p for p in path.replace("\\", "/").split("/") if p]
        if len(parts) == 1:
            segments["(root)"] += 1
            continue
        head = parts[0].lower()
        if head in ("src", "lib", "app", "pkg", "internal", "packages", "cmd") and len(parts) > 2:
            segments["%s/%s" % (parts[0], parts[1])] += 1
        else:
            segments[parts[0]] += 1
    if not segments:
        return "(root)"
    return segments.most_common(1)[0][0]


def clean_subject(subject: str) -> str:
    text = CONVENTIONAL_PREFIX.sub("", subject).strip()
    text = re.sub(r"\s*\(#\d+\)\s*$", "", text).rstrip(".。 ")
    return text


def pick_subject(commits: Sequence[Commit]) -> str:
    """The most informative subject in a group, ignoring 'update' style noise."""
    candidates = []
    for c in commits:
        text = clean_subject(c.subject)
        if not text or GENERIC_SUBJECTS.match(text):
            continue
        candidates.append((len(text.split()), c.size, text))
    if not candidates:
        return ""
    candidates.sort(key=lambda t: (-t[0], -t[1]))
    return candidates[0][2]


def _skills_for_commits(commits: Iterable[Commit]) -> List[str]:
    counter: Counter = Counter()
    for c in commits:
        for path in c.paths:
            for skill in skills_for_path(path):
                counter[skill] += 1
        for skill in skills_in_text(c.subject):
            counter[skill] += 2
    return [s for s, _ in counter.most_common(8)]


def _evidence_for(commits: Sequence[Commit], slug: str, base: str, limit: int = 8) -> List[Evidence]:
    ranked = sorted(commits, key=lambda c: -c.size)[:limit]
    ranked.sort(key=lambda c: c.date)
    return [
        Evidence(
            kind="commit",
            ref=c.sha,
            repo=slug,
            url=_commit_url(base, c.sha),
            date=c.date,
            summary=clean_subject(c.subject)[:200],
            stats={"files": len(c.files), "additions": c.additions, "deletions": c.deletions},
        )
        for c in ranked
    ]


def _days_between(first: str, last: str) -> int:
    from datetime import date

    try:
        a = date.fromisoformat(first)
        b = date.fromisoformat(last)
    except ValueError:  # pragma: no cover - defensive
        return 0
    return abs((b - a).days)


def _manifest_adoptions(repo: str, commits: Sequence[Commit], slug: str, base: str, budget: int = 60) -> List[Fact]:
    """Dependencies the person added themselves — strong evidence of real adoption."""
    seen_tech: Dict[str, Commit] = {}
    manifest_of: Dict[str, str] = {}
    spent = 0
    for commit in sorted(commits, key=lambda c: c.date):
        manifests = [p for p in commit.paths if os.path.basename(p).lower() in MANIFESTS]
        if not manifests or spent >= budget:
            continue
        spent += 1
        try:
            diff = _git(repo, "show", "--unified=0", "--no-color", commit.sha, "--", *manifests)
        except GitError:  # pragma: no cover - defensive
            continue
        for line in diff.splitlines():
            if not line.startswith("+") or line.startswith("+++"):
                continue
            for token in re.findall(r"[A-Za-z][A-Za-z0-9_.\-/]{2,}", line[1:]):
                for skill in skills_for_dependency(token):
                    if skill not in seen_tech:
                        seen_tech[skill] = commit
                        manifest_of[skill] = os.path.basename(manifests[0])
    facts: List[Fact] = []
    for skill, commit in seen_tech.items():
        payload = {"repo": slug, "tech": skill, "manifest": manifest_of[skill]}
        facts.append(
            Fact(
                template="adopted_tech",
                payload=payload,
                text=render_fact("adopted_tech", payload, "en"),
                skills=[skill],
                evidence=_evidence_for([commit], slug, base, limit=1),
                source="git",
                kind="adoption",
                period=[commit.date, commit.date],
                metrics={},
            )
        )
    return facts


def _issue_facts(commits: Sequence[Commit], slug: str, base: str, limit: int = 6) -> List[Fact]:
    facts: List[Fact] = []
    picked = []
    for commit in commits:
        if PR_MERGE.search(commit.subject):
            continue
        refs = ISSUE_REF.findall(commit.subject)
        subject = clean_subject(commit.subject)
        if refs and subject and not GENERIC_SUBJECTS.match(subject):
            picked.append((commit, refs[0]))
    picked.sort(key=lambda t: -t[0].size)
    for commit, number in picked[:limit]:
        payload = {"repo": slug, "issue": "#%s" % number, "subject": clean_subject(commit.subject)}
        evidence = _evidence_for([commit], slug, base, limit=1)
        if base:
            evidence.append(
                Evidence(kind="issue", ref="#%s" % number, repo=slug, url=_issue_url(base, number), date=commit.date)
            )
        facts.append(
            Fact(
                template="issue_closed",
                payload=payload,
                text=render_fact("issue_closed", payload, "en"),
                skills=_skills_for_commits([commit]),
                evidence=evidence,
                source="git",
                kind="bugfix",
                period=[commit.date, commit.date],
                metrics={},
            )
        )
    return facts


def _path_hint_skills(path: str) -> List[str]:
    """Skills a path proves on its own: a Dockerfile means Docker, a workflow file
    means CI. Extensions are excluded here - one .py file is not "introduced Python"."""
    low = path.lower().replace("\\", "/")
    base = os.path.basename(low)
    out = set()
    for name, spec in load_skills().items():
        for hint in spec.get("paths", []):
            if hint in low or base == hint:
                out.add(name)
    if low.endswith((".yml", ".yaml")) and any(
            k in low for k in ("k8s/", "kubernetes/", "charts/", "manifests/")):
        out.add("Kubernetes")
    return sorted(out)


def _tool_setups(commits: Sequence[Commit], slug: str, base: str, covered: Sequence[str],
                 limit: int = 6) -> List[Fact]:
    """Infrastructure a person set up themselves, which is usually one small commit
    and would otherwise be dropped for being too small to group."""
    seen: Dict[str, Tuple[Commit, str]] = {}
    for commit in sorted(commits, key=lambda c: c.date):
        for path in commit.paths:
            for skill in _path_hint_skills(path):
                if skill in covered or skill in seen:
                    continue
                seen[skill] = (commit, os.path.basename(path) or path)
    facts: List[Fact] = []
    for skill, (commit, filename) in list(seen.items())[:limit]:
        payload = {"repo": slug, "tech": skill, "manifest": filename}
        facts.append(Fact(
            template="setup_tool",
            payload=payload,
            text=render_fact("setup_tool", payload, "en"),
            skills=[skill],
            evidence=_evidence_for([commit], slug, base, limit=1),
            source="git",
            kind="adoption",
            period=[commit.date, commit.date],
            metrics={},
        ))
    return facts


TEMPLATE_FOR_KIND = {
    "feature": "feature_work",
    "bugfix": "bugfix_work",
    "perf": "perf_work",
    "refactor": "refactor_work",
    "test": "test_work",
    "infra": "infra_work",
    "docs": "docs_work",
}


def mine_repo(
    repo: str,
    author: Optional[str] = None,
    since: Optional[str] = None,
    lang: str = "en",
    min_commits_per_group: int = 2,
    max_facts: int = 40,
) -> List[Fact]:
    """Mine one repository into facts for a single author."""
    repo = os.path.abspath(os.path.expanduser(repo))
    slug, base = repo_identity(repo)
    commits = read_commits(repo, author=author, since=since)
    if not commits:
        return []

    dates = sorted(c.date for c in commits if c.date)
    first, last = (dates[0], dates[-1]) if dates else ("", "")
    facts: List[Fact] = []

    # 1. The shape of the contribution as a whole.
    if len(commits) >= 3 and first and last:
        payload = {
            "repo": slug,
            "commits": len(commits),
            "days": _days_between(first, last),
            "first": first,
            "last": last,
        }
        facts.append(
            Fact(
                template="sustained_contribution",
                payload=payload,
                text=render_fact("sustained_contribution", payload, lang),
                # Deliberately no skills: "committed for 22 days" says nothing about
                # Kafka. Attaching skills here made this one fact match every
                # requirement in a JD, which is exactly the over-claiming this tool exists
                # to prevent. Skills come from the work facts below.
                skills=[],
                evidence=_evidence_for(commits, slug, base, limit=8),
                source="git",
                kind="sustained",
                period=[first, last],
                metrics={
                    "commits": len(commits),
                    "days": _days_between(first, last),
                    "files": len({p for c in commits for p in c.paths}),
                    "additions": sum(c.additions for c in commits),
                    "deletions": sum(c.deletions for c in commits),
                },
            )
        )

    # 2. What was done, grouped by area and kind.
    groups: Dict[Tuple[str, str], List[Commit]] = defaultdict(list)
    for commit in commits:
        if not commit.files:
            continue
        groups[(area_of(commit), classify(commit))].append(commit)

    ranked = sorted(groups.items(), key=lambda kv: (-len(kv[1]), -sum(c.size for c in kv[1])))
    for (area, kind), group in ranked:
        significant = len(group) >= min_commits_per_group or sum(c.size for c in group) >= 50
        if not significant:
            continue
        template = TEMPLATE_FOR_KIND.get(kind)
        if not template:
            continue
        subject = pick_subject(group)
        if template in ("feature_work", "bugfix_work", "perf_work") and not subject:
            # Without a readable subject the sentence would say nothing; skip it
            # rather than pad it out.
            continue
        gdates = sorted(c.date for c in group if c.date)
        payload = {
            "repo": slug,
            "area": area,
            "commits": len(group),
            "files": len({p for c in group for p in c.paths}),
            "additions": sum(c.additions for c in group),
            "deletions": sum(c.deletions for c in group),
            "subject": subject,
        }
        facts.append(
            Fact(
                template=template,
                payload=payload,
                text=render_fact(template, payload, lang),
                skills=_skills_for_commits(group),
                evidence=_evidence_for(group, slug, base),
                source="git",
                kind=kind,
                period=[gdates[0], gdates[-1]] if gdates else None,
                metrics={
                    "commits": len(group),
                    "files": payload["files"],
                    "additions": payload["additions"],
                    "deletions": payload["deletions"],
                    "days": _days_between(gdates[0], gdates[-1]) if gdates else 0,
                },
            )
        )
        if len(facts) >= max_facts:
            break

    facts.extend(_manifest_adoptions(repo, commits, slug, base))
    facts.extend(_issue_facts(commits, slug, base))
    covered = {skill for f in facts for skill in f.skills}
    facts.extend(_tool_setups(commits, slug, base, sorted(covered)))
    return facts[: max_facts + 20]
