#!/usr/bin/env python3
"""Generate the README's artwork.

Hand-written SVG, no build step and no external service: a hero banner, an
animated terminal cast of the real demo, and the pipeline diagram - each in a
light and a dark variant where the theme matters.

    python3 assets/make_assets.py

Every line of terminal output in here was copied from an actual run of
`examples/demo.sh`. Faking a screenshot in the README of a tool about not faking
things would be a poor start.
"""
from __future__ import annotations

import os

OUT = os.path.dirname(os.path.abspath(__file__))

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Inter, Roboto, Helvetica, Arial, sans-serif"

LIGHT = dict(
    bg="#ffffff", bg2="#f6f8fa", panel="#ffffff", border="#d8dee4", dots="#e4e8ed",
    text="#1f2328", muted="#636c76", bar="#d8dee4",
    green="#1a7f37", green_bg="#dafbe1", red="#cf222e", red_bg="#ffebe9",
    accent="#0969da",
)
DARK = dict(
    bg="#0d1117", bg2="#161b22", panel="#161b22", border="#30363d", dots="#1b2029",
    text="#e6edf3", muted="#8b949e", bar="#30363d",
    green="#3fb950", green_bg="#132d1c", red="#f85149", red_bg="#2d1618",
    accent="#58a6ff",
)


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- banner
def banner(p: dict) -> str:
    rows = [
        (218, "a1b2c3d", False),
        (186, "c9f62bf", False),
        (238, "7980eb4", False),
        (206, "", True),
    ]
    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 340" '
               'width="1200" height="340" role="img" '
               'aria-label="honestcv - a resume a recruiter can check, line by line">')
    out.append("<style>text{font-variant-ligatures:none}</style>")
    out.append("<defs>"
               '<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
               '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
               '<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">'
               '<circle cx="1.5" cy="1.5" r="1.5" fill="%s"/></pattern>'
               "</defs>" % (p["bg"], p["bg2"], p["dots"]))
    out.append('<rect width="1200" height="340" rx="14" fill="url(#g)"/>')
    out.append('<rect width="1200" height="340" rx="14" fill="url(#dots)"/>')
    out.append('<rect x="0.5" y="0.5" width="1199" height="339" rx="14" fill="none" stroke="%s"/>'
               % p["border"])

    # wordmark
    out.append('<text x="72" y="150" font-family="%s" font-size="78" font-weight="800" '
               'letter-spacing="-2" fill="%s">honest<tspan fill="%s">cv</tspan></text>'
               % (SANS, p["text"], p["green"]))
    out.append('<text x="76" y="192" font-family="%s" font-size="22" fill="%s">'
               'A resume a recruiter can check &#8212; line by line.</text>' % (SANS, p["muted"]))
    # command chip
    out.append('<rect x="74" y="222" width="402" height="40" rx="10" fill="%s" stroke="%s"/>'
               % (p["bg2"] if p is LIGHT else "#0d1117", p["border"]))
    out.append('<text x="92" y="248" font-family="%s" font-size="14" fill="%s">'
               '<tspan fill="%s">$</tspan> honestcv verify resume.md</text>'
               % (MONO, p["text"], p["green"]))
    out.append('<text x="330" y="248" font-family="%s" font-size="14" font-weight="700" fill="%s">'
               'PASS</text>' % (MONO, p["green"]))
    out.append('<text x="378" y="248" font-family="%s" font-size="14" fill="%s">21 claims</text>'
               % (MONO, p["muted"]))

    # the document card
    cx, cy, cw, ch = 672, 48, 456, 244
    out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="14" fill="%s" stroke="%s"/>'
               % (cx, cy, cw, ch, p["panel"], p["border"]))
    out.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s">resume.md</text>'
               % (cx + 22, cy + 32, MONO, p["muted"]))
    y = cy + 62
    for width, sha, rejected in rows:
        colour = p["red"] if rejected else p["bar"]
        out.append('<rect x="%d" y="%d" width="%d" height="11" rx="5.5" fill="%s" opacity="%s"/>'
                   % (cx + 22, y, width, colour, "0.45" if rejected else "1"))
        if rejected:
            out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="2"/>'
                       % (cx + 18, y + 5.5, cx + 26 + width, y + 5.5, p["red"]))
            out.append('<rect x="%d" y="%d" width="138" height="24" rx="12" fill="%s"/>'
                       % (cx + 296, y - 7, p["red_bg"]))
            out.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s">'
                       '&#10007; no evidence</text>' % (cx + 310, y + 9, MONO, p["red"]))
        else:
            out.append('<rect x="%d" y="%d" width="138" height="24" rx="12" fill="%s"/>'
                       % (cx + 296, y - 7, p["green_bg"]))
            out.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s">'
                       '&#10003; %s</text>' % (cx + 310, y + 9, MONO, p["green"], sha))
        y += 44
    out.append('<text x="%d" y="%d" font-family="%s" font-size="12" fill="%s">'
               'every line links to the commit behind it</text>'
               % (cx + 22, cy + ch - 20, SANS, p["muted"]))
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------- pipeline
COLUMNS = [
    ("EVIDENCE", [("git history", "commits you authored"),
                  ("guided interview", "what code cannot show")]),
    ("FACT BASE", [("facts + links", "counted, never estimated")]),
    ("TARGET", [("job description", "requirements, parsed"),
                ("match", "covered / gap / unread")]),
    ("OUTPUT", [("resume · cover letter", "ordered for this job"),
                ("two-week plan", "for every gap"),
                ("interview practice", "from your own commits")]),
    ("PROOF", [("verify", "document × trace × facts")]),
]


def pipeline(p: dict) -> str:
    col_w, gap, x0, top = 196, 52, 36, 66
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1240 320" width="1240" '
           'height="320" role="img" aria-label="honestcv pipeline: evidence to fact base to '
           'match to output to proof">',
           "<style>text{font-variant-ligatures:none}</style>"]
    out.append('<rect width="1240" height="320" rx="14" fill="%s" stroke="%s"/>'
               % (p["bg"], p["border"]))
    for i, (header, cards) in enumerate(COLUMNS):
        x = x0 + i * (col_w + gap)
        out.append('<text x="%d" y="%d" font-family="%s" font-size="11" font-weight="700" '
                   'letter-spacing="2" fill="%s">%s</text>' % (x, 42, SANS, p["muted"], header))
        y = top
        for title, note in cards:
            accent = header in ("FACT BASE", "PROOF")
            out.append('<rect x="%d" y="%d" width="%d" height="60" rx="12" fill="%s" stroke="%s" '
                       'stroke-width="%s"/>'
                       % (x, y, col_w, p["bg2"], p["green"] if accent else p["border"],
                          "1.5" if accent else "1"))
            out.append('<text x="%d" y="%d" font-family="%s" font-size="14" font-weight="600" '
                       'fill="%s">%s</text>' % (x + 16, y + 26, SANS, p["text"], esc(title)))
            out.append('<text x="%d" y="%d" font-family="%s" font-size="11" fill="%s">%s</text>'
                       % (x + 16, y + 44, SANS, p["muted"], esc(note)))
            y += 76
        if i < len(COLUMNS) - 1:
            cxx = x + col_w + gap / 2
            out.append('<path d="M %.1f 150 l 11 11 l -11 11" fill="none" stroke="%s" '
                       'stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>'
                       % (cxx - 5, p["muted"]))
    # the two outcomes under "verify"
    x = x0 + 4 * (col_w + gap)
    for j, (glyph, label, colour, bg) in enumerate(
            [("✓", "every line traced", p["green"], p["green_bg"]),
             ("✗", "rejected", p["red"], p["red_bg"])]):
        y = top + 76 + j * 44
        out.append('<rect x="%d" y="%d" width="%d" height="34" rx="10" fill="%s"/>'
                   % (x, y, col_w, bg))
        out.append('<text x="%d" y="%d" font-family="%s" font-size="13" fill="%s">%s %s</text>'
                   % (x + 16, y + 22, MONO, colour, glyph, esc(label)))
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------- terminal cast
# Copied verbatim from a real run; see examples/demo.sh.
CAST = [
    ("cmd", "honestcv mine ~/code/orders"),
    ("out", "Mined 13 facts from orders, 13 new."),
    ("out", "Skills with evidence: Python, REST API, CI/CD, Docker, FastAPI, Kafka,"),
    ("out", "                      PostgreSQL, Redis, Testing"),
    ("gap", ""),
    ("cmd", "honestcv match --jd jd.txt"),
    ("out", "Must-have coverage: 100% (backed by evidence)"),
    ("ok", "  ✓ Experience with Kafka or another message queue"),
    ("dim", "      Introduced Kafka into demo/orders (visible in requirements.txt)  c7f2ca4"),
    ("bad", "  ✗ Kubernetes"),
    ("dim", "      missing: Kubernetes  →  honestcv plan writes a two-week project instead"),
    ("gap", ""),
    ("cmd", "honestcv resume --jd jd.txt -o resume.md"),
    ("out", "Wrote resume.md (trace: resume.trace.json)"),
    ("ok", "resume.md: PASS (21 claims checked, 0 errors, 0 warnings)"),
    ("dim", "  Every claim traces back to evidence."),
    ("gap", ""),
    ("cmd", "echo '- Led a team of 12 engineers, cut p99 latency by 90%' >> resume.md"),
    ("cmd", "honestcv verify resume.md"),
    ("bad", "resume.md: FAIL (22 claims checked, 1 errors, 0 warnings)"),
    ("bad", "  ✗ [untraced_claim] - Led a team of 12 engineers, cut p99 latency by 90%"),
    ("dim", "      This line is not in the trace: it was added or edited after"),
    ("dim", "      generation, so nothing backs it."),
    ("gap", ""),
    ("cmd", "echo $?"),
    ("out", "1"),
]


def terminal() -> str:
    p = DARK
    line_h, top, left = 21, 76, 26
    body = [l for l in CAST]
    height = top + line_h * len(body) + 34
    width = 940
    # It plays once and holds the finished screen. A looping cast means anyone who
    # lands mid-cycle sees an empty black rectangle, which is a bad first frame for
    # the thing the README is built around.
    step = 0.4           # seconds between lines
    total = round(0.6 + step * len(body), 2)

    colours = {"cmd": p["text"], "out": p["muted"], "ok": p["green"],
               "bad": p["red"], "dim": p["muted"], "gap": p["muted"]}

    css = ["text{font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0}",
           ".l{opacity:0}"]
    for i in range(len(body)):
        start = (0.6 + i * step) / total * 100
        css.append("@keyframes a%d{0%%,%.3f%%{opacity:0;transform:translateY(3px)}"
                   "%.3f%%,100%%{opacity:1;transform:translateY(0)}}"
                   % (i, start, min(start + 1.6, 100)))
        css.append(".l%d{animation:a%d %ss linear 1 forwards}" % (i, i, total))
    css.append("@keyframes blink{0%,45%{opacity:1}50%,100%{opacity:0}}")
    css.append(".cur{animation:blink 1s steps(1) infinite}")

    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'role="img" aria-label="terminal recording of honestcv rejecting an invented resume '
           'line">' % (width, height, width, height)]
    out.append("<style>%s</style>" % "".join(css))
    out.append('<rect width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>'
               % (width, height, p["bg"], p["border"]))
    out.append('<rect width="%d" height="38" rx="12" fill="%s"/>' % (width, p["bg2"]))
    out.append('<rect y="26" width="%d" height="12" fill="%s"/>' % (width, p["bg2"]))
    out.append('<line x1="0" y1="38" x2="%d" y2="38" stroke="%s"/>' % (width, p["border"]))
    for k, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        out.append('<circle cx="%d" cy="19" r="6" fill="%s"/>' % (24 + k * 20, colour))
    out.append('<text x="%d" y="24" text-anchor="middle" font-family="%s" font-size="12" '
               'fill="%s">honestcv</text>' % (width // 2, MONO, p["muted"]))

    y = top
    for i, (kind, text) in enumerate(body):
        if kind == "gap":
            y += line_h
            continue
        out.append('<g class="l l%d">' % i)
        if kind == "cmd":
            out.append('<text x="%d" y="%d" font-family="%s" font-size="13" fill="%s">$</text>'
                       % (left, y, MONO, p["green"]))
            out.append('<text x="%d" y="%d" font-family="%s" font-size="13" letter-spacing="0.4" '
                       'fill="%s">%s</text>'
                       % (left + 16, y, MONO, colours[kind], esc(text)))
        else:
            out.append('<text x="%d" y="%d" font-family="%s" font-size="13" letter-spacing="0.4" '
                       'fill="%s" xml:space="preserve">%s</text>'
                       % (left, y, MONO, colours[kind], esc(text)))
        out.append("</g>")
        y += line_h
    out.append('<rect class="cur" x="%d" y="%d" width="8" height="15" fill="%s"/>'
               % (left, y - 12, p["green"]))
    out.append("</svg>")
    return "\n".join(out)



# --------------------------------------------------------------------------- feature cards
# Six illustrations, 440x300, one pair per theme. They use only code-shaped text
# (shas, commit subjects, flags), so the same images serve the English and the
# Chinese README without a word needing translation.
CARD_W, CARD_H = 440, 300


def _open_card(p: dict, label: str) -> list:
    return ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'role="img" aria-label="%s">' % (CARD_W, CARD_H, CARD_W, CARD_H, label),
            "<style>text{font-variant-ligatures:none}</style>",
            '<rect x="1" y="1" width="%d" height="%d" rx="16" fill="%s" stroke="%s"/>'
            % (CARD_W - 2, CARD_H - 2, p["bg"], p["border"])]


def _box(x, y, w, h, p, stroke=None, dash=False, r=12):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" '
            'stroke-width="%s"%s/>' % (x, y, w, h, r, p["bg2"], stroke or p["border"],
                                       "1.5" if stroke else "1",
                                       ' stroke-dasharray="5 4"' if dash else ""))


def _mono(x, y, text, size, fill, weight=400, anchor="start"):
    return ('<text x="%s" y="%s" font-family="%s" font-size="%s" font-weight="%s" '
            'text-anchor="%s" fill="%s" xml:space="preserve">%s</text>'
            % (x, y, MONO, size, weight, anchor, fill, esc(text)))


def _bar(x, y, w, p, colour=None, h=10):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (
        x, y, w, h, h / 2, colour or p["bar"])


def _chip(x, y, w, text, fg, bg, size=11, h=24):
    return ('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="%s"/>' % (x, y, w, h, h / 2, bg)
            + _mono(x + 12, y + h / 2 + 4, text, size, fg))


def _chevron(cx, cy, colour):
    return ('<path d="M %s %s l 12 12 l 12 -12" fill="none" stroke="%s" stroke-width="3" '
            'stroke-linecap="round" stroke-linejoin="round"/>' % (cx - 12, cy - 6, colour))


def card_mine(p):
    o = _open_card(p, "commits turning into facts")
    o.append(_box(28, 26, 384, 108, p))
    for i, (sha, msg) in enumerate([("2002261", "feat: validate order payloads"),
                                    ("c9f62bf", "fix: dispatch dropped orders"),
                                    ("7c50441", "test: duplicate ids are rejected")]):
        y = 54 + i * 28
        o.append(_mono(48, y, sha, 12, p["accent"]))
        o.append(_mono(118, y, msg, 12, p["muted"]))
    o.append(_chevron(220, 156, p["muted"]))
    o.append(_box(28, 180, 384, 92, p, stroke=p["green"]))
    o.append(_bar(50, 206, 230, p))
    o.append(_chip(300, 196, 92, "\u2713 c9f62bf", p["green"], p["green_bg"]))
    o.append(_bar(50, 236, 164, p))
    o.append(_chip(300, 228, 92, "\u2713 2002261", p["green"], p["green_bg"]))
    o.append("</svg>")
    return "\n".join(o)


def card_links(p):
    o = _open_card(p, "a resume line opening the commit behind it")
    o.append(_box(28, 28, 384, 56, p, stroke=p["green"]))
    o.append(_bar(50, 50, 212, p))
    o.append(_chip(286, 44, 106, "\u2713 c9f62bf", p["green"], p["green_bg"]))
    o.append('<path d="M 330 92 q 0 24 -40 28" fill="none" stroke="%s" stroke-width="2" '
             'stroke-dasharray="4 4"/>' % p["muted"])
    o.append(_box(70, 118, 300, 152, p, r=10))
    o.append('<rect x="70" y="118" width="300" height="28" rx="10" fill="%s"/>' % p["border"])
    o.append('<rect x="70" y="136" width="300" height="10" fill="%s"/>' % p["border"])
    for k, colour in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        o.append('<circle cx="%d" cy="132" r="4" fill="%s"/>' % (86 + k * 14, colour))
    o.append(_mono(220, 136, "github.com/\u2026/commit/c9f62bf", 9, p["muted"], anchor="middle"))
    o.append('<rect x="86" y="162" width="268" height="20" rx="4" fill="%s"/>' % p["green_bg"])
    o.append(_mono(96, 176, "+    for _ in range(retries):", 11, p["green"]))
    o.append('<rect x="86" y="188" width="268" height="20" rx="4" fill="%s"/>' % p["red_bg"])
    o.append(_mono(96, 202, "-    publish(order)", 11, p["red"]))
    o.append(_mono(96, 232, "src/dispatch/queue.py", 11, p["muted"]))
    o.append(_mono(96, 252, "2026-03-10", 11, p["muted"]))
    o.append("</svg>")
    return "\n".join(o)


def card_self_report(p):
    o = _open_card(p, "verifiable evidence kept separate from self-reported answers")
    o.append(_box(28, 52, 180, 218, p, stroke=p["green"]))
    o.append(_mono(44, 40, "evidence", 12, p["green"], weight=600))
    for i in range(3):
        y = 78 + i * 46
        o.append(_bar(48, y, 110, p))
        o.append(_chip(48, y + 16, 96, "\u2713 commit", p["green"], p["green_bg"], size=10, h=20))
    o.append(_box(232, 52, 180, 218, p, dash=True))
    o.append(_mono(248, 40, "self-reported", 12, p["muted"], weight=600))
    for i in range(3):
        y = 78 + i * 46
        o.append(_bar(252, y, 120, p))
        o.append(_chip(252, y + 16, 110, "~ you told us", p["muted"], p["bg"], size=10, h=20))
    o.append("</svg>")
    return "\n".join(o)


def card_verify(p):
    o = _open_card(p, "document, trace and fact base reconciled by verify")
    for i, label in enumerate(("resume.md", "resume.trace.json", "honestcv.json")):
        y = 40 + i * 62
        o.append(_box(26, y, 150, 48, p, r=10))
        o.append(_mono(40, y + 29, label, 11, p["text"]))
        o.append('<path d="M 182 %d L 228 150" fill="none" stroke="%s" stroke-width="1.5"/>'
                 % (y + 24, p["muted"]))
    o.append('<path d="M 232 112 h 72 l 24 38 l -24 38 h -72 l -24 -38 z" fill="%s" stroke="%s" '
             'stroke-width="2"/>' % (p["bg2"], p["green"]))
    o.append(_mono(268, 155, "verify", 13, p["text"], weight=700, anchor="middle"))
    o.append('<path d="M 328 140 l 36 -32" fill="none" stroke="%s" stroke-width="1.5"/>' % p["green"])
    o.append('<path d="M 328 160 l 36 32" fill="none" stroke="%s" stroke-width="1.5"/>' % p["red"])
    o.append(_chip(338, 86, 76, "\u2713 pass", p["green"], p["green_bg"]))
    o.append(_chip(338, 190, 76, "\u2717 fail", p["red"], p["red_bg"]))
    o.append("</svg>")
    return "\n".join(o)


def card_plan(p):
    o = _open_card(p, "two weeks of evenings, commits spread across the days")
    o.append(_mono(28, 42, "gap: Kafka", 13, p["red"], weight=700))
    o.append(_mono(412, 42, "14 days", 12, p["muted"], anchor="end"))
    dots = [1, 2, 0, 1, 3, 0, 0, 2, 1, 1, 0, 2, 3, 1]
    for i, n in enumerate(dots):
        col, row = i % 7, i // 7
        x, y = 28 + col * 56, 62 + row * 68
        o.append('<rect x="%d" y="%d" width="48" height="56" rx="10" fill="%s" stroke="%s"/>'
                 % (x, y, p["bg2"], p["border"]))
        o.append(_mono(x + 8, y + 18, str(i + 1), 10, p["muted"]))
        for d in range(n):
            o.append('<circle cx="%d" cy="%d" r="4.5" fill="%s"/>'
                     % (x + 14 + d * 12, y + 38, p["green"]))
    o.append(_box(28, 212, 384, 58, p, stroke=p["green"]))
    o.append(_mono(48, 238, "the history itself is the evidence", 13, p["text"]))
    o.append(_mono(48, 258, "plans only \u2014 it never writes the code", 11, p["muted"]))
    o.append("</svg>")
    return "\n".join(o)


def card_practice(p):
    o = _open_card(p, "interview questions generated from your own commit")
    o.append(_box(28, 28, 384, 52, p, stroke=p["green"]))
    o.append(_chip(44, 42, 92, "\u2713 c9f62bf", p["green"], p["green_bg"]))
    o.append(_mono(148, 60, "fix: dispatch dropped orders", 12, p["text"]))
    questions = ["How did you track it down?",
                 "How did you confirm the fix?",
                 "What stops it happening again?"]
    for i, q in enumerate(questions):
        y = 100 + i * 62
        o.append('<rect x="%d" y="%d" width="%d" height="48" rx="12" fill="%s" stroke="%s"/>'
                 % (52, y, 360, p["bg2"], p["border"]))
        o.append('<path d="M 52 %d l -14 10 l 14 10 z" fill="%s"/>' % (y + 14, p["bg2"]))
        o.append(_mono(28, y + 32, "?", 20, p["accent"], weight=700))
        o.append(_mono(70, y + 29, q, 13, p["text"]))
    o.append("</svg>")
    return "\n".join(o)


CARDS = {
    "card-mine": card_mine,
    "card-links": card_links,
    "card-self-report": card_self_report,
    "card-verify": card_verify,
    "card-plan": card_plan,
    "card-practice": card_practice,
}


def main() -> None:
    files = {
        "banner-light.svg": banner(LIGHT),
        "banner-dark.svg": banner(DARK),
        "pipeline-light.svg": pipeline(LIGHT),
        "pipeline-dark.svg": pipeline(DARK),
        "demo.svg": terminal(),
    }
    for name, fn in CARDS.items():
        files["%s-light.svg" % name] = fn(LIGHT)
        files["%s-dark.svg" % name] = fn(DARK)
    for name, content in files.items():
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content + "\n")
        print("%-22s %6.1f KB" % (name, len(content) / 1024))


if __name__ == "__main__":
    main()
