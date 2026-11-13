"""Evidence-strength audit of a repository.

Junior candidates are now routinely suspected of having generated their portfolio.
This module does not try to detect that — it cannot, and claiming otherwise would
be dishonest. What it does is measure how *legible* a history is to a reviewer:
a repo built over three weeks of evenings, with fixes on top of its own features
and tests that came later, reads very differently from one commit that drops a
finished project.

A low score is not an accusation. It is a list of things that are currently
invisible to a reviewer, with honest suggestions for making real work visible.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from .git_miner import GENERIC_SUBJECTS, GitError, _git, classify, clean_subject, read_commits

def _plural(count: int, word: str) -> str:
    """"1 days" in a report about rigour is a bad look."""
    return "%d %s%s" % (count, word, "" if count == 1 else "s")


TEST_PATH = re.compile(r"(^|/)(tests?|spec|__tests__)/|_test\.|\.test\.|test_.*\.py$", re.IGNORECASE)


@dataclass
class Signal:
    key: str
    label_en: str
    label_zh: str
    value: str
    score: float          # 0..1
    weight: float
    advice_en: str = ""
    advice_zh: str = ""

    def label(self, lang: str) -> str:
        return self.label_zh if lang == "zh" else self.label_en

    def advice(self, lang: str) -> str:
        return self.advice_zh if lang == "zh" else self.advice_en


@dataclass
class AuditReport:
    repo: str
    author: str
    commits: int
    signals: List[Signal] = field(default_factory=list)
    flags: List[str] = field(default_factory=list)

    @property
    def score(self) -> int:
        total_w = sum(s.weight for s in self.signals)
        if not total_w:
            return 0
        return int(round(100 * sum(s.score * s.weight for s in self.signals) / total_w))

    def weak_signals(self) -> List[Signal]:
        return sorted([s for s in self.signals if s.score < 0.5], key=lambda s: s.score)

    def to_dict(self) -> Dict[str, object]:
        return {
            "repo": self.repo,
            "author": self.author,
            "commits": self.commits,
            "score": self.score,
            "signals": [
                {"key": s.key, "value": s.value, "score": round(s.score, 2), "weight": s.weight}
                for s in self.signals
            ],
            "flags": self.flags,
        }


def _commit_hours(repo: str, author: Optional[str]) -> List[int]:
    try:
        out = _git(repo, "log", "--no-merges", "--date=format:%H", "--pretty=format:%ad\x1f%an\x1f%ae")
    except GitError:  # pragma: no cover - defensive
        return []
    needle = (author or "").strip().lower()
    hours: List[int] = []
    for line in out.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        hour, name, email = parts
        if needle and needle not in name.lower() and needle not in email.lower():
            continue
        try:
            hours.append(int(hour))
        except ValueError:
            continue
    return hours


def audit_repo(repo: str, author: Optional[str] = None, since: Optional[str] = None) -> AuditReport:
    commits = read_commits(repo, author=author, since=since)
    commits.sort(key=lambda c: c.date)
    report = AuditReport(repo=repo, author=author or "(all authors)", commits=len(commits))
    if not commits:
        return report

    total_lines = sum(c.size for c in commits) or 1
    dates = [c.date for c in commits if c.date]
    active_days = len(set(dates))
    span = 0
    if len(dates) >= 2:
        try:
            span = (datetime.fromisoformat(dates[-1]) - datetime.fromisoformat(dates[0])).days
        except ValueError:  # pragma: no cover - defensive
            span = 0

    # --- shape of the history over time ---
    report.signals.append(Signal(
        "span", "Time span", "时间跨度", _plural(span, "day"),
        min(1.0, span / 21.0), 1.2,
        "Real work accumulates. Spread the remaining work over more sessions instead of one long sprint.",
        "真实的工作是攒出来的。把剩下的活分散到更多次坐下来做，而不是一口气冲完。",
    ))
    report.signals.append(Signal(
        "active_days", "Days with commits", "有提交的天数", _plural(active_days, "day"),
        min(1.0, active_days / 12.0), 1.5,
        "Commit at the end of each session, even when the work is unfinished.",
        "每次做完一段就提交，哪怕还没做完。",
    ))
    report.signals.append(Signal(
        "volume", "Commit count", "提交数量", _plural(len(commits), "commit"),
        min(1.0, len(commits) / 40.0), 1.0,
        "Smaller commits, one idea each, make the work readable.",
        "把提交拆小，一次一个意图，工作才读得出来。",
    ))

    # --- distribution of the work ---
    largest = max(c.size for c in commits)
    share = largest / total_lines
    report.signals.append(Signal(
        "distribution", "Largest commit share", "最大提交占比", "%.0f%% of all changed lines" % (share * 100),
        max(0.0, 1.0 - share), 1.2,
        "One commit holding most of the project is the single clearest sign of a dump.",
        "一个 commit 装下整个项目，是最明显的『一次性倒进来』的信号。",
    ))

    subjects = [clean_subject(c.subject) for c in commits]
    generic = sum(1 for s in subjects if not s or GENERIC_SUBJECTS.match(s))
    unique = len({s.lower() for s in subjects if s})
    quality = (1 - generic / len(commits)) * 0.6 + min(1.0, unique / max(1, len(commits))) * 0.4
    report.signals.append(Signal(
        "messages", "Commit message quality", "提交信息质量",
        "%d/%d generic, %d distinct" % (generic, len(commits), unique),
        max(0.0, min(1.0, quality)), 1.0,
        "Say what changed and why. 'update' tells a reviewer nothing.",
        "写清楚改了什么、为什么。『update』对读的人等于没说。",
    ))

    # --- signs of genuine iteration ---
    seen_files: set = set()
    revisits = 0
    for commit in commits:
        paths = set(commit.paths)
        if paths & seen_files:
            revisits += 1
        seen_files |= paths
    revisit_rate = revisits / len(commits)
    report.signals.append(Signal(
        "iteration", "Revisited own files", "回头改自己写过的文件", "%.0f%% of commits" % (revisit_rate * 100),
        min(1.0, revisit_rate / 0.5), 1.5,
        "Going back to change your own code is what real projects look like. Generated ones rarely do.",
        "回头改自己写过的代码，是真实项目的样子；生成出来的代码很少有这个痕迹。",
    ))

    kinds = Counter(classify(c) for c in commits)
    fix_ratio = (kinds["bugfix"] + kinds["perf"] + kinds["refactor"]) / len(commits)
    report.signals.append(Signal(
        "fixes", "Fixes and refactors", "修复与重构占比", "%.0f%% of commits" % (fix_ratio * 100),
        min(1.0, fix_ratio / 0.25), 1.2,
        "A project with no fixes in its history reads as a project that was never run.",
        "历史里一个修复都没有的项目，读起来像是从来没跑过。",
    ))

    test_commits = sum(1 for c in commits if any(TEST_PATH.search(p) for p in c.paths))
    report.signals.append(Signal(
        "tests", "Commits touching tests", "涉及测试的提交", "%d of %d" % (test_commits, len(commits)),
        min(1.0, (test_commits / len(commits)) / 0.2), 1.0,
        "Tests you wrote while building, committed as you went, are worth more than a tests/ folder added at the end.",
        "边做边写、随手提交的测试，比最后补一个 tests/ 目录有价值得多。",
    ))

    hours = _commit_hours(repo, author)
    if hours:
        spread = len(set(hours))
        report.signals.append(Signal(
            "rhythm", "Distinct commit hours", "提交时段分布", "%s" % _plural(spread, "distinct hour"),
            min(1.0, spread / 8.0), 0.6,
            "Everything landing inside one hour reads as a single session, whatever the dates say.",
            "全部集中在一个小时之内，不管日期怎么写，读起来都是一次性完成的。",
        ))

    # --- hard flags, stated plainly ---
    first = commits[0]
    all_files = {p for c in commits for p in c.paths}
    if all_files and len(set(first.paths)) / len(all_files) >= 0.6 and first.size / total_lines >= 0.5:
        report.flags.append("initial_dump")
    if span == 0 and len(commits) >= 5:
        report.flags.append("single_day")
    if revisit_rate < 0.1 and len(commits) >= 10:
        report.flags.append("no_iteration")
    if kinds["bugfix"] == 0 and len(commits) >= 15:
        report.flags.append("no_fixes")
    return report


FLAG_TEXT = {
    "initial_dump": (
        "The first commit contains most of the project. A reviewer reads this as code that arrived from somewhere else.",
        "第一个 commit 里装着项目的大部分内容。在审阅者眼里，这是代码从别处搬进来的样子。",
    ),
    "single_day": (
        "Every commit lands on the same day.",
        "所有提交都在同一天。",
    ),
    "no_iteration": (
        "Files are almost never touched twice: the history has no sign of rework.",
        "几乎没有文件被改过第二次：历史里看不到任何返工的痕迹。",
    ),
    "no_fixes": (
        "No commit fixes anything, across a sizeable history.",
        "历史不算短，却没有任何一次提交是在修东西。",
    ),
}


def render_audit(report: AuditReport, lang: str = "zh") -> str:
    zh = lang == "zh"
    lines: List[str] = []
    lines.append("# %s" % ("证据强度体检" if zh else "Evidence strength audit"))
    lines.append("")
    lines.append("**%s**: `%s`  " % ("仓库" if zh else "Repository", report.repo))
    lines.append("**%s**: %s  " % ("作者" if zh else "Author", report.author))
    lines.append("**%s**: %d/100 (%d %s)" % (
        "得分" if zh else "Score", report.score, report.commits,
        "次提交" if zh else ("commit" if report.commits == 1 else "commits")))
    lines.append("")
    if zh:
        lines.append("> 这个分数衡量的是**你的工作对审阅者有多可读**，不是你有没有作弊。")
        lines.append("> 它无法证明代码是谁写的，分数低也不代表你造假。它只告诉你：哪些东西现在看不见。")
    else:
        lines.append("> This score measures **how legible your work is to a reviewer**, not whether you cheated.")
        lines.append("> It cannot prove authorship, and a low score is not an accusation. It only says what is currently invisible.")
    lines.append("")
    lines.append("| %s | %s | %s |" % (
        "信号" if zh else "Signal", "观察值" if zh else "Observed", "评分" if zh else "Score"))
    lines.append("| --- | --- | ---: |")
    for s in report.signals:
        lines.append("| %s | %s | %.0f%% |" % (s.label(lang), s.value, s.score * 100))
    lines.append("")
    if report.flags:
        lines.append("## %s" % ("明显问题" if zh else "Clear problems"))
        lines.append("")
        for flag in report.flags:
            en, zh_text = FLAG_TEXT.get(flag, (flag, flag))
            lines.append("- %s" % (zh_text if zh else en))
        lines.append("")
    weak = report.weak_signals()
    if weak:
        lines.append("## %s" % ("怎么让真实的工作被看见" if zh else "How to make real work visible"))
        lines.append("")
        for s in weak:
            lines.append("- **%s** (%s: %s) — %s" % (
                s.label(lang), "当前" if zh else "now", s.value, s.advice(lang)))
        lines.append("")
    if zh:
        lines.append("这些建议都是让你**把本来就做过的事留下痕迹**，没有一条是教你伪造历史。")
        lines.append("改写已经发生的提交时间或作者信息，是另一回事，这个工具不做，也不建议你做。")
    else:
        lines.append("Every suggestion above is about leaving traces of work you actually do. None of it is about faking history.")
        lines.append("Rewriting commit dates or authorship is a different thing entirely: this tool will not do it and does not advise it.")
    return "\n".join(lines) + "\n"
