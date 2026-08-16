---
name: running-pr-backed-review-loops
description: >-
  Use when a GitHub pull request has unresolved descriptive review comments
  that document changes already made and the user wants fresh reviewers to
  accept or revise them until the comment loop converges.
---

# Running PR-Backed Review Loops

## Overview

Run unresolved descriptive review comments as a sequential record until a fresh
iteration accepts the implementation.

**Core principle:** each loop artifact is a claim about both a problem and its
implemented solution, not an instruction. GitHub threads preserve the handoff;
fresh iteration owners prevent inherited conclusions.

## Boundary And Composition

Use this only for identified descriptive loop artifacts and their marked
replacements. Read complete predecessor history. Ordinary review requests stay
outside the loop: do not implement, reply to, or resolve them through it.

**REQUIRED SUB-SKILL:** Use `review-loop` for sequential fresh-review
convergence.

**REQUIRED SUB-SKILL:** Use `receiving-code-review` to judge whether the stated
problem is real and whether the implemented solution is technically correct.

## Iteration Owner Contract

Run one iteration at a time with one fresh owner subagent. That owner may judge
artifacts, implement disagreements, and draft its public text. Do not replace it
with parallel, per-thread, or read-only specialists. A different fresh cold
reviewer must check staged revisions before commit. Give each later iteration a
new owner; never resume the prior owner.

## Protocol

1. **Read:** Fetch unresolved loop threads, IDs, anchors, resolution state, and
   all comments and replies chronologically. Inspect the current PR head, base,
   requirements, standards, and implementation.
2. **Judge:** For each artifact, return `AGREE` or `DISAGREE`, rationale, IDs,
   and exact proposed public text. Judge both the stated problem and implemented
   solution.
3. **Approve and publish:** Obtain approval for all replies unless explicit
   unattended publication authority applies. Post and read back each reply.
   Only then resolve agreements. Keep disagreements open.
4. **Revise:** Resume the owner. Reconcile an advanced or conflicting base
   first. Make the smallest correct revision, add a targeted regression test,
   and run relevant checks. A separate fresh cold reviewer checks the staged
   revision; fix and repeat until no actionable feedback remains.
5. **Publish code:** Commit and push the accepted revision before any replacement
   comment.
6. **Replace:** Resume the owner to draft one new top-level comment per revision,
   anchored to an added or modified right-side line in the pushed diff. Approve,
   post, and read it back before resolving its predecessor. Leave replacements
   unresolved.
7. **Fresh iteration:** Dispatch a new owner to read the unresolved replacements
   and full history, then repeat.

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
readback confirms: all agreement replies exist; zero unresolved loop artifacts;
the intended commit is pushed; the worktree is clean; local HEAD and remote PR
head are synchronized; the PR is mergeable; and applicable CI passes on that
head. If iteration four still produces substantive disagreement, stop and ask
the user to resolve the structural or requirements conflict.

## Observed RED Counters

| Rationalization | Required counter |
|---|---|
| "Parallel evaluation saves time" | One sequential owner per iteration. |
| "Evaluators must stay read-only" | The owner may review, implement, and draft; only the cold reviewer is read-only. |
| "Reply in the old thread, then resolve" | Post and read back one marked, unresolved top-level replacement first. |
| "Accepted/Revised on SHA is equivalent" | Use the exact `Reviewer loop iteration N` marker family. |
| "Repeat until accepted" | Escalate substantive disagreement at iteration four. |
| "The final API response is enough" | Read back threads, clean/synchronized git, mergeability, remote head, and CI. |
