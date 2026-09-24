# Evidence Harness

`run-evidence.sh` is the source of truth for reproducing the skill evidence. It
creates a production-only temporary skill package, a neutral working directory,
and complete session exports under `.jaco/pr-backed-review-loop-tests/`.

## Prerequisites

- `bash`, `git`, `jq`, and `opencode` v2
- OpenCode authentication for `openai/gpt-5.6-sol`
- No live GitHub target is required; scenarios are hypothetical active-work cases

## Run

```bash
skills/running-pr-backed-review-loops/tests/run-evidence.sh all
```

Run one suite with `guided`, `recovery`, `authority`, or `trigger`. Override the
model with `MODEL` and `VARIANT`; reports must record any override.

If authority behavior exports completed but scoring was interrupted, resume with
`authority-score`; it validates and scores the existing twenty exports.
Use `authority-behavior` to regenerate and validate those exports without
starting a scorer.

## Isolation And Oracles

- Tested agents run from a fresh temporary directory and cannot discover sibling
  rubrics or repository tests. Each run gets its own `--standalone` server so the
  inline `OPENCODE_CONFIG_CONTENT` applies. Every tool except `skill` is denied,
  and the skill permission only allows the temporary package's production and
  dependency skills, which hides every globally installed skill.
- Guided and recovery runs rely on automatic discovery.
- Authority files test behavior, not discovery. The harness copies them to
  neutral paths and explicitly preloads the production skill.
- Trigger prompts have no attachment. Each of five qualified prompts and six
  near misses runs five times, for 55 fresh sessions.
- A trigger load means invoking the production skill or attempting to obtain its
  body by another tool. Negative runs fail on either action.
- Guided, recovery, and authority runs fail if any tool input names the source
  checkout; protected files are also inaccessible through OpenCode permissions.
- Session exports are written through a validated temporary file, so a failed
  run cannot replace prior evidence with an empty export.

## Scoring

The guided, recovery, and authority suites each dispatch a separate scorer after
all behavior runs finish. The scorer receives only the applicable rubric and
complete exports in a temporary scoring directory. Scorers may read those files,
but all other tools remain denied. The harness converts JSON to wrapped text so
long lines remain readable and rejects any non-read scorer tool call. Scorer
sessions are preserved as `final-*-score.json`.

Rubric totals are:

| Suite | Expected checks |
|---|---:|
| Guided | 110 load-bearing plus 5 pressure |
| Recovery | 35 |
| Authority | 45 applicable checks across 20 independent runs |
| Trigger | 25 qualified loads plus 30 near-miss exclusions |

Read every scorer result before updating a report. Semantic scoring remains a
review judgment; the harness guarantees provenance, isolation, repetitions, and
tool-call oracles rather than replacing that judgment with keyword matching.

No-guidance authority controls are globally confounded in the current harness
and cannot establish causal RED evidence. They may document the confound but
must not be presented as proof that the production skill alone taught the rule.
