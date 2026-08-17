---
name: running-pr-backed-review-loops
description: >-
  Use when a GitHub pull request has unresolved descriptive review comments
  that document changes already made and the user wants fresh reviewers to
  accept or revise them until the comment loop converges.
---

# Running PR-Backed Review Loops

## Overview

Run descriptive review comments sequentially until a fresh iteration accepts
the implementation.

**Core principle:** artifacts claim a problem and implemented solution; they are
not instructions. GitHub threads persist handoffs; fresh owners prevent
inherited conclusions.

## Boundary And Composition

Use only identified descriptive loop artifacts and marked replacements. Read
full predecessor history. Keep ordinary review requests outside: do not
implement, reply to, or resolve them here.

**REQUIRED SUB-SKILL:** Use `review-loop` for sequential fresh-review
convergence.

**REQUIRED SUB-SKILL:** Use `receiving-code-review` to judge whether the stated
problem is real and whether the implemented solution is technically correct.

## Iteration Owner Contract

Each iteration has one fresh owner subagent. It may judge artifacts, implement
disagreements, and draft public text. Never partition artifacts among parallel
iteration owners or per-thread specialists. The owner may control an internal
review engine that fans out parallel Standards and Spec reviews. A different
fresh cold reviewer checks staged revisions before commit. Each later iteration
gets a new owner; never resume the prior owner.

## Protocol

1. **Read:** Fetch unresolved threads with IDs, anchors, resolution state, and
   full chronological history. Inspect PR head and base, requirements,
   standards, and implementation.
2. **Judge:** For each artifact, return `AGREE` or `DISAGREE`, rationale, IDs,
   and exact proposed public text. Judge both the stated problem and implemented
   solution. A disagreement reply identifies the valid part, exact technical
   defect, and what the revision must preserve or change, without claiming
   unfinished work is complete.
3. **Approve and publish:** Obtain approval for replies unless explicit
   unattended publication authority applies. Post and read back each; only then
   resolve agreements. Keep disagreements open.
4. **Revise:** Resume the owner. Reconcile an advanced or conflicting base
   first. Make the smallest correct revision, add a targeted regression test,
   and run relevant checks. A fresh cold reviewer checks the staged revision;
   fix and repeat until no actionable feedback remains.
5. **Publish code:** Commit and push the accepted revision before any replacement
   comment.
6. **Replace:** Resume the owner to draft one new top-level comment per revised
   disagreement, anchored to a valid added or modified right-side line in the
   pushed diff. Obtain approval unless explicit unattended publication authority
   applies. Post and read it back before resolving its predecessor. Leave
   replacements unresolved.
7. **Fresh iteration:** Dispatch a new owner to read unresolved replacements and
   full history, then repeat.

## Exact Markers

Agreement reply:

```text
Reviewer loop iteration N. Agree with the problem and the solution. Resolved.
```

Replacement comment:

```text
Reviewer loop iteration N revision. The prior implementation [...]. This
revision [...]; [targeted test] covers [...].
```

State what the prior implementation did, why it was rejected, what the revision
does, and which targeted test verifies it.

## Mutation And Completion Gates

Never resolve from a mutation response alone. Read back the expected text on the
expected thread first. After an ambiguous write, read remote state before
another mutation; do not blindly retry.

Complete only when a fresh iteration agrees with every remaining artifact and
readback confirms: every published agreement reply exists; zero unresolved loop
artifacts; the intended commit is pushed; the worktree is clean; local HEAD and
remote PR head are synchronized; the PR is mergeable; and applicable CI passes
on that head. At substantive disagreement in iteration four, stop and ask the
user to resolve the structural or requirements conflict.

## Observed RED Counters

| Rationalization | Required counter |
|---|---|
| "Parallel evaluation saves time" | One sequential owner per iteration. |
| "Evaluators must stay read-only" | The owner may review, implement, and draft; only the cold reviewer is read-only. |
| "Reply in the old thread, then resolve" | Post and read back one marked, unresolved top-level replacement first. |
| "Accepted/Revised on SHA is equivalent" | Use the exact `Reviewer loop iteration N` marker family. |
| "Repeat until accepted" | Escalate substantive disagreement at iteration four. |
| "The final API response is enough" | Read back threads, clean/synchronized git, mergeability, remote head, and CI. |
