# Model Catalog

Read this file before every route selection. Scores are personal working judgments on a 1-10 scale, not benchmark claims.

## Scores

| Model | Intelligence | Exploratory | Debugging | Surgical | Taste | Bulk data | Efficiency |
|---|---:|---:|---:|---:|---:|---:|---:|
| Claude Fable 5 | 9 | 10 | 8 | 8 | 10 | 8 | 4 |
| Claude Opus 4.8 | 7 | 6 | 7 | 6 | 8 | 7 | 5 |
| GPT-5.6 Sol | 9 | 8 | 9 | 9 | 4 | 8 | 7 |
| GPT-5.6 Luna | 5 | 5 | 6 | 8 | 1 | 9 | 10 |

Quality dimensions:

- Intelligence: problem interpretation and unsupervised autonomy
- Exploratory: open-space engineering, codebase discovery, and approach selection
- Debugging: hypothesis formation, evidence use, recovery, and root-cause analysis
- Surgical: precise bounded implementation and constraint-following
- Taste: visual, interaction, frontend, and product judgment
- Bulk data: large-input extraction, classification, aggregation, and transformation

Efficiency combines speed, subscription pressure, and cost efficiency. Exclude it from quality eligibility. Use it only for close fits.

## Model IDs and Effort

| Model | OpenCode ID | Effort |
|---|---|---|
| Fable | `anthropic/claude-fable-5` | Always `high` |
| Opus | `anthropic/claude-opus-4-8` | Always `high` |
| Sol | `openai/gpt-5.6-sol` | `medium`, or `high` for persistence |
| Luna | `openai/gpt-5.6-luna` | Always `max` |

Sol persistence signals include multi-step tool use, computer use, ambiguous debugging, recovery after a failed attempt, and repeated verification. Never lower effort merely to save usage.

## Availability

Assess availability per routing episode from explicit user context or a fresh launch result. A quota or missing-model failure removes that route for the episode but does not consume a reasoning retry.

Anthropic limits Fable to at most half of the weekly Anthropic allowance. This is a ceiling, not a target ratio. Use Opus when it comfortably meets an Anthropic-shaped task. Reserve Fable for complexity, ambiguity, exploration, or taste that exceeds Opus's comfortable range.

## Direct Rules

A direct route must still clear every material quality requirement. Conflicting direct rules fall through to the weighted calculation.

- Computer use: Sol at `high` through Codex.
- Large, well-scoped structured data: Luna at `max` through OpenCode.
- Taste-sensitive frontend work: use Anthropic. Choose Opus for localized improvements and Fable for large, ambiguous, architectural, or exploratory work.
- Persistent tool-heavy coding, debugging, recovery, or exact technical work: Sol, using `high` when persistence is material.
- Well-specified surgical or mechanical work: Luna at `max` when it clears every requirement; otherwise Sol.

## Weighted Fallback

Use only when no direct rule cleanly applies:

1. Give every relevant quality dimension a required score from 1-10. Every scored dimension is a material minimum.
2. Give each scored dimension an importance weight from 1-3.
3. Mark any critical dimension that needs one point of uncertainty headroom.
4. Eliminate a model below any requirement or required critical headroom.
5. For each eligible model calculate `sum((model score - requirement) * weight)`.
6. Find the minimum unused-capability total. Candidates no more than one point above that minimum are close fits.
7. Among close fits choose higher efficiency, then stable order: Luna, Sol, Opus, Fable.

If no model qualifies, keep the work with a better-suited parent, narrow or decompose the delegated objective, or report the capability gap. Never dispatch a knowingly underqualified route.
