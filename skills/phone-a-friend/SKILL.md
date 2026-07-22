---
name: phone-a-friend
description: Use when a task or subtask may benefit from a better-fit model, requires tools unavailable to the current agent, involves unusually large input, or repeated failed attempts suggest specialist delegation or escalation.
---

# Phone a Friend

## Overview

Delegate only when a fresh specialist context materially improves the expected result. Choose the least overpowered model that comfortably clears every material task requirement.

## Route the Task

**REQUIRED:** Read [references/model-catalog.md](references/model-catalog.md) before selecting a model.

1. Profile the bounded subtask: required tools, input volume, relevant quality demands, prior failures, verification, and mutation scope.
2. Keep the task when delegation overhead exceeds the benefit or the current route is already the best fit. Localized scope alone does not make a poorly matched model suitable.
3. Apply hard capability gates, then high-confidence direct rules.
4. When no direct rule cleanly fits, run the catalog's weighted fallback. Do not replace the calculation with intuition.
5. Select model, effort, and launcher as one route. Respect an explicit user choice unless it is unavailable or lacks a required capability.

## Explain the Choice

Before dispatch, emit exactly one concise routing receipt:

> Delegating `<subtask>` to `<model>` at `<effort>` through `<launcher>`: `<mechanism and decisive fit>`.

Name the mechanism: hard capability, direct match, weighted fallback, failure escalation, availability fallback, or efficiency tie-break. A mechanism label without the decisive task-to-model fit is incomplete.

## Dispatch

Delegates are report-only by default. An implementation brief must name every writable file or directory, including inside a worktree. Never allow overlapping delegates to mutate shared state.

The brief contains:

- One bounded objective
- Working directory and relevant artifacts
- Necessary context, constraints, and prior evidence
- Allowed tools and mutation boundaries
- Required verification
- Exact return contract

The return contract requests outcome, evidence, changed files, verification, uncertainty, and recommended next action.

**REQUIRED:** Read [references/launchers.md](references/launchers.md) before dispatch. Pass the brief as a file rather than interpolating untrusted text into a shell command.

## Validate and Recover

The parent reviews evidence, integrates authorized changes, and owns final verification.

- Capability, quota, authentication, or launcher mismatch: update availability and reroute without consuming a reasoning retry.
- First failed result: classify missing context, underestimated effort, poor specialization, or bad verification.
- Second materially similar failure: reroute to a better-fitted or more capable model.
- No valid route remains: stop, report accumulated evidence, and ask the user to narrow, decompose, or accept the limitation.

Every reroute gets a new receipt and a fresh context containing prior evidence and failed approaches, not the full conversation transcript.

## Common Mistakes

- Keeping taste-sensitive work because it is localized
- Choosing a generic subagent without model, effort, or launcher
- Assuming the current harness defines all available capabilities
- Repeating a failed route after the second similar verification failure
- Dumping score arithmetic into the receipt
