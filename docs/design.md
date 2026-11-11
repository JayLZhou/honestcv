# Design notes

Three decisions carry the whole project. Everything else is plumbing.

## 1. A fact is a template plus a payload, never a sentence

```python
Fact(template="bugfix_work",
     payload={"repo": "demo/orders", "area": "src/dispatch", "commits": 2,
              "subject": "dispatch dropped orders when the queue was slow"},
     skills=["Python"],
     evidence=[Evidence(kind="commit", ref="c9f62bf", url="https://github.com/...")])
```

Renderers may pick facts, order them and choose a language. They cannot write a sentence,
because the sentences live in `data/templates.json`, one per template per language, and the
only values they can interpolate are the payload's — which came out of the evidence.

"Translate and reorder, never add" stops being a promise and becomes a property of the data
model. The test that holds it down renders the same fact base in both languages and asserts
the two documents contain exactly the same numbers.

## 2. Documents ship with a trace, and the trace is checked afterwards

`render_resume` returns `Rendered(text, trace)`. The trace records, for every bullet it
emitted: the exact line, the fact ids behind it, the evidence ids, and a `kind`
(`claim`, `self_reported`, `question`, `plan`, `hint`).

`verify` reads the document back, pulls out every bullet, and looks it up in the trace:

- not in the trace → the line was added or edited by hand; nothing backs it
- fact id missing from the fact base → stale document
- a number in the line that is in no payload, metric or date of its facts → unbacked
- a skill named in the line that none of its facts demonstrate → unbacked

This is why the tool survives being used by a human: people edit their resumes, and the
verifier is what tells them which edits they can defend in an interview.

Markdown links are stripped before the number check — a commit sha contains digits, and
reading `abc1234` as a claim of "1234 users" would make the checker useless.

## 3. The model is never trusted, and never required

`llm.py` is optional and bounded. It receives one sentence plus the numbers and technologies
that sentence is allowed to use. It never sees the evidence links, so it cannot produce one.
Every sentence it returns goes through `_violates()`: a new number, a dropped number, a new
skill or an attempted link means the rewrite is discarded and the deterministic wording is
kept. A failure of the API is a cosmetic downgrade, not an outage.

The same discipline applies to the audit in `mining/authenticity.py`. It would be easy to
claim it detects generated repositories. It cannot, so it says so in its own output, and every
piece of advice it gives is about leaving traces of real work rather than manufacturing them.

## Where the numbers come from

| Fact kind | Counted from |
| --- | --- |
| `sustained` | commit count, first/last date, distinct files, lines added/removed |
| `feature` / `bugfix` / `perf` / `refactor` / `test` / `infra` / `docs` | commits grouped by (area, kind); the subject shown is the most informative one in the group, never a synthesis |
| `adoption` | a dependency the person added themselves, read out of the manifest diff |
| `setup_tool` | the first commit that introduced a Dockerfile, a workflow file, a k8s manifest |
| `issue` | `#123` in a commit subject, linked to the issue |

`sustained` facts deliberately carry **no** skills. "I committed for 22 days" is not evidence
of Kafka, and when that fact carried skills it matched every requirement in a JD at once —
the exact over-claiming this project exists to prevent.
