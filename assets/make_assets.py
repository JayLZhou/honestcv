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
    step = 0.46          # seconds between lines
    hold = 4.0           # seconds the finished screen stays up
    total = round(0.6 + step * len(body) + hold, 2)

    colours = {"cmd": p["text"], "out": p["muted"], "ok": p["green"],
               "bad": p["red"], "dim": p["muted"], "gap": p["muted"]}

    css = ["text{font-variant-ligatures:none;font-feature-settings:'liga' 0,'calt' 0}",
           ".l{opacity:0}"]
    for i in range(len(body)):
        start = (0.6 + i * step) / total * 100
        css.append("@keyframes a%d{0%%,%.3f%%{opacity:0;transform:translateY(3px)}"
                   "%.3f%%,96%%{opacity:1;transform:translateY(0)}100%%{opacity:0}}"
                   % (i, start, min(start + 1.2, 96)))
        css.append(".l%d{animation:a%d %ss linear infinite}" % (i, i, total))
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


def main() -> None:
    files = {
        "banner-light.svg": banner(LIGHT),
        "banner-dark.svg": banner(DARK),
        "pipeline-light.svg": pipeline(LIGHT),
        "pipeline-dark.svg": pipeline(DARK),
        "demo.svg": terminal(),
    }
    for name, content in files.items():
        path = os.path.join(OUT, name)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content + "\n")
        print("%-22s %6.1f KB" % (name, len(content) / 1024))


if __name__ == "__main__":
    main()
