---
name: deliberate
description: "Use when the user asks to think through how something should work or be built before building it, and the approach is not settled - phrasings like \"how should this work\", \"what are our options\", \"design this\", \"let's plan this feature\", \"thoughts on X vs Y\", \"ideas?\". Not when the user gives a direct instruction to build or change something, even a large one, and not for bugs, reviews, dependency updates, merges, status or research questions, or continuing agreed work."
---

# Deliberate

Work out how something should work before it is built. You do the finding out; the user makes only the calls that are theirs to make.

## 1. Ground in what exists

Read the code, docs and recent history the change touches before proposing anything. Name the existing patterns, constraints and the data the change works with. A design that ignores the surrounding system gets redone.

If the request bundles several independent pieces, say so and agree which piece to deliberate first.

## 2. Sort every open question

| The question is about | Do this |
|---|---|
| A fact you can observe: what the code does, behaviour, timing, layout, performance, whether something is possible | Find out. Read, run, or build a throwaway prototype in a scratch directory. Report what you saw. |
| Intent, preference, priority or scope: what should happen for the user, what matters more, what is out | Ask the user. |

Ask in rounds. Put related questions in one structured-question call (or one numbered message), each with concrete options and your recommendation listed first. Ask only what changes the design.

## 3. Lay out the options

Present two or three structurally different approaches - different shapes, not variations of one. For each: how it works, what it costs, what it rules out. Recommend one and say why. Prefer the approach that hides more behind a smaller interface. Cut anything the stated goal does not need.

When a choice is visual, build a quick mockup (a throwaway HTML file is enough) and show it instead of describing it.

## 4. Present one design

Once the direction is chosen, present the design in one message, scaled to the task:

- the data shape and where it lives
- the units, their boundaries and interfaces (for code crossing module boundaries, sketch the types and signatures)
- the flow, including errors
- how it will be verified
- what is out of scope
- the riskiest assumption, and the question: "Anything we're missing?"

## 5. Hand off

The user's go-ahead on the design ends deliberation. Then:

- If the work is a single change with an obvious sequence, build it test-first, using the `test-driven-development` skill if it is available.
- If it spans several steps or PRs, write an implementation plan first, with a planning skill if one is available.

Do not write or commit a spec file unless the user asks. If the design needs to survive the session, save it where the user's instructions say working notes go.

If the user says to just build it at any point, stop deliberating and build with the best current design, stating the assumptions you made.

## Reopening a design

If implementation keeps producing the same kind of workaround, special case or type escape hatch, the design is wrong. Stop, say so, and return to step 3 with what you learned, rather than patching around it.
