# PR-Backed Review Loop Design

## Purpose

Capture the proven descriptive-comment PR workflow as a thin orchestration skill
above `review-loop`.

The skill accepts a GitHub PR whose unresolved review comments describe changes
already present in the PR. It repeatedly gives those claims to fresh reviewers,
revises the claims they reject, and uses GitHub threads as the persistent handoff
between iterations.

## Boundary

Create one model-invoked skill named `running-pr-backed-review-loops`.

It owns:

- fetching unresolved GitHub review threads and complete reply history;
- running each review-loop iteration with a fresh subagent;
- recording agreement or disagreement in the original thread;
- resolving accepted and superseded threads;
- revising rejected implementations and adding targeted tests;
- posting one replacement review comment per revision;
- repeating until a fresh iteration accepts every remaining comment;
- verifying zero unresolved loop threads, a pushed clean branch, mergeability,
  and applicable CI.

It does not own:

- finding the original descriptive comments;
- ordinary reviewer change requests;
- general review criteria;
- code style;
- pending GitHub review staging;
- generic convergence rules already owned by `review-loop`.

The user or originating workflow identifies the initial descriptive comments as
loop artifacts. Replacement comments carry an explicit marker.

## Composition

**REQUIRED SUB-SKILL:** Use `review-loop` for sequential fresh-review
convergence. One iteration may use any suitable review engine, including an
engine that fans out into parallel Standards and Spec reviews.

**REQUIRED SUB-SKILL:** Use `receiving-code-review` when judging whether a
descriptive claim and its implementation are technically sound.

Use repository and personal code-style skills when implementing revisions. Use
normal verification and git workflow skills before committing or claiming
completion.

The PR-backed skill is the only skill the user needs to invoke. It coordinates
the others internally rather than asking the user to orchestrate them.

## Iteration Protocol

Each iteration uses one fresh owner subagent. The same owner may review the
threads, implement that iteration's disagreements, and draft replacement
comments. A separate fresh cold reviewer checks any staged code revision before
commit.

### 1. Read the record

Fetch every review thread through GitHub GraphQL, including:

- `isResolved`;
- thread node ID;
- top-level comment database ID and URL;
- path and line;
- every comment and reply in chronological order.

Review only unresolved loop artifacts. Read the complete chain before judging a
revision. Inspect the current PR head and base, repository standards, linked
requirements, relevant current-base evolution, and the exact implementation.

### 2. Judge every artifact

Each comment documents a change already made. It is not a request to implement
the comment blindly.

For every artifact, decide whether both are correct:

1. The stated problem.
2. The implemented solution.

The owner returns `AGREE` or `DISAGREE`, technical rationale, IDs, and exact
proposed public reply for every unresolved artifact.

Agreement reply pattern:

```text
Reviewer loop iteration N. Agree with the problem and the solution. Resolved.
```

Add context only when it materially helps the next reader.

Disagreement replies state which part is valid, the exact technical defect in
the current solution, and what the next revision must preserve or change. They
must not claim unimplemented work is complete.

### 3. Approve and publish decisions

Public text requires approval by default. Batch the complete reply set for human
approval before posting. Explicit unattended authority may cover later writes in
the same session.

Post every approved reply in its existing thread.

- Resolve agreement threads immediately after successful reply readback.
- Leave disagreement threads open through implementation.

### 4. Revise disagreements

Resume the iteration owner to implement all disagreements. Reconcile current
base-branch changes first when the PR is stale or conflicting. Preserve both
intents where compatible.

For each disagreement:

- implement the smallest correct revision;
- add a targeted regression test;
- run relevant lint, typechecks, tests, and build checks;
- report exact verification evidence and candidate replacement anchors.

Dispatch a separate fresh cold reviewer over the staged revision. Fix and
re-review until it returns no actionable feedback.

Commit and push under the repository's normal approval policy.

### 5. Replace revised artifacts

Resume the iteration owner to draft one new top-level review comment per revised
disagreement. Anchor each comment to a valid added or modified right-side line in
the pushed PR diff.

Replacement comment pattern:

```text
Reviewer loop iteration N revision. The prior implementation [...]. This
revision [...]; [targeted test] covers [...].
```

Each replacement explains:

- what the prior implementation did;
- why the iteration disagreed;
- what the revision now does;
- which targeted test verifies it.

Obtain publication approval when required. Post and read back every replacement
before resolving its superseded thread. The replacements remain unresolved for
the next iteration.

### 6. Start a fresh iteration

Dispatch a new owner subagent. Never resume the previous iteration owner for the
next iteration. The new owner reads every unresolved replacement and its full
history, then repeats this protocol.

## Stop Conditions

The loop completes only when a fresh iteration agrees with every remaining loop
artifact and readback confirms:

- every approved agreement reply exists;
- zero unresolved loop-artifact threads remain;
- the intended commit is pushed;
- the worktree is clean and synchronized;
- the PR is mergeable;
- every applicable CI check passes.

If iteration four still produces substantive disagreements, stop and ask the
user to resolve the structural or requirements conflict.

After an ambiguous GitHub mutation, read back the exact state before any further
write. Never blindly retry a mutation whose outcome is unknown.

## Test Strategy

Skill creation follows RED-GREEN-REFACTOR.

Baseline scenarios run without the new skill and must expose failures such as:

- treating descriptive comments as instructions instead of claims;
- judging only the problem and not the implementation;
- ignoring predecessor replies;
- resolving disagreement threads before replacement comments exist;
- reusing one subagent across iterations;
- starting iterations in parallel;
- posting replacement comments before commit/push;
- claiming completion without GraphQL, git, mergeability, and CI readback.

The same scenarios run with the skill loaded. Success requires the approved
state transitions, public markers, fresh-subagent ownership, replacement order,
and completion evidence.

Pressure tests add many threads, mixed agreement, a stale/conflicting base,
publication approval, interrupted writes, and a fourth substantive iteration.

The implementation starts as one concise `SKILL.md`. Supporting scripts or
references are added only if tests show that prose cannot make the workflow
predictable.
