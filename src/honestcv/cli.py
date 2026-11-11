"""honestcv command line.

    honestcv init                      start a fact base
    honestcv mine <repo>               git history  -> facts
    honestcv audit <repo>              how legible is this history to a reviewer
    honestcv questions                 what the code cannot tell us
    honestcv interview                 answers -> facts (clearly self-reported)
    honestcv facts                     what we have on you
    honestcv match --jd jd.txt         covered / gap / unread, per requirement
    honestcv resume --jd jd.txt        tailored resume, every line linked
    honestcv letter --jd jd.txt        cover letter with the gaps stated
    honestcv plan --jd jd.txt          two-week projects for the gaps
    honestcv practice                  interview questions from your own work
    honestcv verify resume.md          prove every claim still traces to evidence
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .grounding import render_report, verify_files
from .i18n import normalise_lang
from .interview import (facts_from_answers, load_answers, questions, run_interactive,
                        write_template)
from .jd import load_jd
from .matcher import match, render_match
from .mining import GitError, list_authors, mine_repo
from .mining.authenticity import audit_repo, render_audit
from .models import FactBase, Person
from .practice import render_practice
from .render import render_cover_letter, render_plan, render_resume

DEFAULT_FILE = os.environ.get("HONESTCV_FILE", "honestcv.json")


def _load(path: str) -> FactBase:
    if not os.path.exists(path):
        raise SystemExit("No fact base at %s. Run `honestcv init` first." % path)
    return FactBase.load(path)


def _jd_or_none(path: Optional[str]):
    return load_jd(path) if path else None


def _report_for(factbase: FactBase, jd_path: Optional[str]):
    jd = _jd_or_none(jd_path)
    return match(factbase, jd) if jd is not None else None


def _default_author(repo: str, given: Optional[str]) -> Optional[str]:
    if given:
        return given
    try:
        import subprocess
        email = subprocess.run(["git", "-C", repo, "config", "user.email"],
                               capture_output=True, text=True).stdout.strip()
        return email or None
    except Exception:  # pragma: no cover - defensive
        return None


# --------------------------------------------------------------------------- commands
def cmd_init(args: argparse.Namespace) -> int:
    path = args.file
    if os.path.exists(path) and not args.force:
        print("%s already exists (use --force to overwrite)" % path)
        return 1
    fb = FactBase(person=Person(
        name=args.name or "", email=args.email or "", location=args.location or ""))
    fb.save(path)
    print("Created %s" % path)
    print("Next: honestcv mine <path-to-your-repo>")
    return 0


def cmd_mine(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    author = _default_author(args.repo, args.author)
    if args.list_authors:
        for name, email, count in list_authors(args.repo):
            print("%5d  %s <%s>" % (count, name, email))
        return 0
    try:
        facts = mine_repo(args.repo, author=author, since=args.since, lang=args.lang)
    except GitError as exc:
        print("git: %s" % exc, file=sys.stderr)
        return 2
    if not facts:
        print("No commits found for author %r in %s." % (author, args.repo))
        print("Run with --list-authors to see who is in this history.")
        return 1
    repos = {e.repo for f in facts for e in f.evidence}
    for repo in repos:
        fb.drop_source("git", repo=repo)   # re-mining the same repo replaces, never duplicates
    added = fb.extend(facts)
    fb.save(args.file)
    print("Mined %d facts from %s (author: %s), %d new." % (len(facts), args.repo, author, added))
    skills = fb.skills()
    if skills:
        print("Skills with evidence: %s" % ", ".join(list(skills)[:12]))
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    author = _default_author(args.repo, args.author)
    try:
        report = audit_repo(args.repo, author=author, since=args.since)
    except GitError as exc:
        print("git: %s" % exc, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
        return 0
    print(render_audit(report, args.lang))
    return 0


def cmd_facts(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    facts = fb.by_skill(args.skill) if args.skill else fb.facts
    if args.json:
        print(json.dumps([f.to_dict() for f in facts], indent=2, ensure_ascii=False))
        return 0
    if not facts:
        print("No facts yet. Run `honestcv mine <repo>`.")
        return 1
    for fact in sorted(facts, key=lambda f: -f.confidence):
        marker = "~" if fact.source == "interview" else "+"
        print("%s %s  [%s %.2f]" % (marker, fact.text, fact.source, fact.confidence))
        if fact.skills:
            print("    skills: %s" % ", ".join(fact.skills))
        if fact.evidence:
            print("    evidence: %s" % " ".join(e.label for e in fact.evidence[:4]))
    print("\n%d facts, %d skills" % (len(facts), len(fb.skills())))
    return 0


def cmd_questions(args: argparse.Namespace) -> int:
    gaps: List[str] = []
    if args.jd:
        fb = _load(args.file)
        report = _report_for(fb, args.jd)
        if report is not None:
            gaps = report.gap_skills(("must", "nice"))[:5]
    if args.template:
        write_template(args.template, args.lang, gaps)
        print("Wrote %s — fill in the answers, then run `honestcv interview --answers %s`"
              % (args.template, args.template))
        return 0
    for q in questions(args.lang, gaps):
        print("- [%s] %s" % (q["id"], q["text"]))
    return 0


def cmd_interview(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    gaps: List[str] = []
    if args.jd:
        report = _report_for(fb, args.jd)
        if report is not None:
            gaps = report.gap_skills(("must", "nice"))[:5]
    if args.answers:
        answers = load_answers(args.answers)
    else:
        answers = run_interactive(args.lang, gaps)
    facts = facts_from_answers(answers, args.lang)
    if not facts:
        print("No answers recorded; nothing added.")
        return 1
    fb.drop_source("interview")
    added = fb.extend(facts)
    fb.save(args.file)
    print("Added %d self-reported facts." % added)
    return 0


def cmd_match(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    report = _report_for(fb, args.jd)
    text = render_match(report, args.lang)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("Wrote %s" % args.out)
    else:
        print(text)
    return 0


def _finish(rendered, out_path: str, factbase_path: str, lang: str, quiet: bool = False) -> int:
    doc, trace = rendered.save(out_path)
    rendered.trace.factbase = os.path.abspath(factbase_path)
    rendered.trace.save(trace)
    report = verify_files(doc, factbase_path, trace)
    if not quiet:
        print("Wrote %s (trace: %s)" % (doc, os.path.basename(trace)))
        print(render_report(report, lang), end="")
    return 0 if report.ok() else 1


def cmd_resume(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    report = _report_for(fb, args.jd)
    overrides = None
    if args.polish:
        from . import llm
        from .i18n import render_fact
        from .render.resume import order_facts
        usable, reason = llm.available()
        if not usable:
            print("--polish is off: %s" % reason, file=sys.stderr)
        else:
            facts = [f for f in order_facts(fb, report) if f.source != "interview"][:args.max_bullets]
            sentences = [render_fact(f.template, f.payload, args.lang) for f in facts]
            try:
                polished, notes = llm.polish(sentences, facts, args.lang, model=args.model)
                overrides = {f.id: s for f, s in zip(facts, polished)}
                for note in notes:
                    print("note: %s" % note, file=sys.stderr)
            except Exception as exc:  # the tool must still produce a resume
                print("--polish failed (%s); using the plain wording." % exc, file=sys.stderr)
    rendered = render_resume(fb, report, lang=args.lang, max_bullets=args.max_bullets,
                             overrides=overrides)
    return _finish(rendered, args.out, args.file, args.lang)


def cmd_letter(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    report = _report_for(fb, args.jd)
    rendered = render_cover_letter(fb, report, lang=args.lang)
    return _finish(rendered, args.out, args.file, args.lang)


def cmd_plan(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    skills = list(args.skill or [])
    if not skills and args.jd:
        report = _report_for(fb, args.jd)
        if report is not None:
            skills = report.gap_skills(("must", "nice"))
    if not skills:
        print("No gaps to plan for. Pass --jd or --skill.")
        return 1
    rendered = render_plan(skills, lang=args.lang, max_plans=args.max_plans)
    return _finish(rendered, args.out, args.file, args.lang)


def cmd_practice(args: argparse.Namespace) -> int:
    fb = _load(args.file)
    report = _report_for(fb, args.jd)
    rendered = render_practice(fb, report, lang=args.lang, max_facts=args.max_facts)
    return _finish(rendered, args.out, args.file, args.lang)


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_files(args.document, args.file, args.trace)
    print(render_report(report, args.lang), end="")
    return 0 if report.ok(strict=args.strict) else 1


# --------------------------------------------------------------------------- parser
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="honestcv",
        description="Build a resume out of evidence you already have, and verify every line of it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version="honestcv %s" % __version__)
    parser.add_argument("-f", "--file", default=DEFAULT_FILE, help="fact base (default: %(default)s)")
    parser.add_argument("--lang", default="zh", type=normalise_lang, choices=["zh", "en"],
                        help="output language (default: zh)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="create an empty fact base")
    p.add_argument("--name"); p.add_argument("--email"); p.add_argument("--location")
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("mine", help="turn a git history into facts")
    p.add_argument("repo")
    p.add_argument("--author", help="name or email; defaults to the repo's git user.email")
    p.add_argument("--since", help="e.g. 2024-01-01")
    p.add_argument("--list-authors", action="store_true")
    p.set_defaults(func=cmd_mine)

    p = sub.add_parser("audit", help="how legible is this history to a reviewer")
    p.add_argument("repo")
    p.add_argument("--author"); p.add_argument("--since")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_audit)

    p = sub.add_parser("facts", help="list what the fact base holds")
    p.add_argument("--skill"); p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_facts)

    p = sub.add_parser("questions", help="the questions code cannot answer")
    p.add_argument("--jd", help="target the questions at this JD's gaps")
    p.add_argument("--template", help="write a blank answers file here")
    p.set_defaults(func=cmd_questions)

    p = sub.add_parser("interview", help="record answers as self-reported facts")
    p.add_argument("--answers", help="a filled-in answers file; omit to be asked interactively")
    p.add_argument("--jd")
    p.set_defaults(func=cmd_interview)

    p = sub.add_parser("match", help="requirement-by-requirement coverage")
    p.add_argument("--jd", required=True); p.add_argument("-o", "--out")
    p.set_defaults(func=cmd_match)

    p = sub.add_parser("resume", help="render a tailored resume")
    p.add_argument("--jd"); p.add_argument("-o", "--out", default="resume.md")
    p.add_argument("--max-bullets", type=int, default=12)
    p.add_argument("--polish", action="store_true",
                   help="let Claude rephrase the bullets; every rewrite is re-checked")
    p.add_argument("--model", help="model id for --polish")
    p.set_defaults(func=cmd_resume)

    p = sub.add_parser("letter", help="render a cover letter")
    p.add_argument("--jd"); p.add_argument("-o", "--out", default="letter.md")
    p.set_defaults(func=cmd_letter)

    p = sub.add_parser("plan", help="two-week projects for the gaps")
    p.add_argument("--jd"); p.add_argument("--skill", action="append")
    p.add_argument("-o", "--out", default="plan.md")
    p.add_argument("--max-plans", type=int, default=3)
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("practice", help="interview questions from your own work")
    p.add_argument("--jd"); p.add_argument("-o", "--out", default="practice.md")
    p.add_argument("--max-facts", type=int, default=6)
    p.set_defaults(func=cmd_practice)

    p = sub.add_parser("verify", help="check a generated document against the fact base")
    p.add_argument("document")
    p.add_argument("--trace", help="trace file (default: <document>.trace.json)")
    p.add_argument("--strict", action="store_true", help="treat warnings as failures")
    p.set_defaults(func=cmd_verify)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:  # pragma: no cover
        return 130
    except SystemExit:
        raise
    except FileNotFoundError as exc:
        print("not found: %s" % exc, file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
