# Review Ecosystem And PR-Backed Review Loop Design

## Purpose

Define how review skills compose without overlapping ownership, then add a
GitHub-specific PR-backed review loop whose durable state lives in review
threads, commits, and checks.

The ecosystem design is scoped to skills that can participate in one review and
revision workflow. Unrelated ecosystems do not need coupling merely because they
share the skill runtime.

## Ecosystem Rules

Every skill in an ecosystem must justify itself through:

- a distinct trigger it owns;
- a small interface describing its required inputs and completion guarantee;
- explicit composition with adjacent skills;
- one source of truth for shared behavior;
- a deletion test: removing the skill must cause its owned complexity to
  reappear elsewhere, not simply redirect callers unchanged.

Skills may occupy one of these roles:

- **Policy:** judgment rules used by other skills.
- **Review engine:** produces one review of an artifact.
- **Orchestrator:** sequences work and review toward a completion condition.
- **Adapter:** owns interaction with a durable external system.
- **Presentation:** shapes review findings without deciding or applying them.

A skill may combine roles only when the combined interface is smaller than the
interfaces callers would otherwise need to coordinate.

## Review Vocabulary

The vocabulary is optional below `review`: simple skills do not invent axes or
dimensions merely to satisfy the model.

- **Round:** one sequential convergence cycle. Rounds share state and never run
  in parallel.
- **Review:** the aggregate judgment produced within a round. This is the only
  required review unit.
- **Axis review:** an optional independently evaluated concern, such as
  Standards or Spec, aggregated into one review. Axis reviews may run in
  parallel.
- **Dimensions:** an optional coverage checklist within a reviewer, such as
  correctness, requirements, style, and fitment.
- **Clean pass:** a review that returns no actionable feedback.
- **Cold reviewer:** a fresh evaluator receiving no author-side priming. A cold
  reviewer still reads durable artifact history when that history is part of the
  current state.
- **The record:** the durable thread, commit, and check history carried by a
  PR-backed review loop.

```text
review loop
└─ round 1..n
   └─ review
      ├─ direct single-purpose judgment
      └─ optional axis reviews
         └─ optional explicit dimensions
```

## Existing Skill Boundaries

| Skill | Role | Owned interface | Does not own |
| --- | --- | --- | --- |
| `receiving-code-review` | Policy | Evaluate feedback technically before responding or implementing | Finding issues, convergence, GitHub state |
| `code-review` | Review engine | Two-axis Standards and Spec review of a fixed diff | Applying fixes or repeated rounds |
| `requesting-code-review` | Review engine | Internal cold review checkpoint for completed work | User-requested two-axis reporting or convergence |
| `review-loop` | Orchestrator | Repeat compatible reviews and revisions until a clean pass | GitHub persistence, publication, thread resolution |
| `subagent-driven-development` | Orchestrator | Execute planned tasks with task-scoped review gates | Ad hoc PR-thread convergence |
| `staging-pending-github-reviews` | Adapter | Privately stage and verify pending review comments | Publication, thread resolution, finding issues |

`review-loop` must describe fresh reviews rather than requiring exactly one
reviewer subagent. One review may aggregate parallel axis reviews. Only rounds
are strictly sequential.

`review-loop` must also scope `cold`: author-side rationale is withheld, but a
durable public record is part of the artifact and must be read.

## New Skill Boundary

Create a model-invoked skill named `running-pr-backed-review-loops`.

Trigger only when a GitHub PR contains unresolved descriptive review comments
that document changes already made and are identified as loop artifacts. It does
not handle ordinary reviewer requests.

The plain-text artifact marker is:

```text
Reviewer loop round N.
Reviewer loop round N revision.
```

The skill combines an orchestrator and GitHub adapter because callers otherwise
need to coordinate thread history, code revisions, comment anchors, commits,
resolution order, and convergence recovery. Its interface is one PR reference
plus publication authority; its guarantee is a verified clean PR-backed record.

The deletion test passes: without this skill, PR thread discovery, historical
claim evaluation, replacement-comment handoff, resolution ordering, and durable
recovery spread across the parent agent and several generic skills.

## Round Workflow

Each round uses fresh evaluator context and follows the record rather than
conversation memory.

1. Fetch every review thread with resolved state, node IDs, anchors, and full
   chronological history.
2. Select unresolved loop artifacts. Trace predecessor history when a comment
   records a revision.
3. Inspect the current PR head and base, repository standards, requirements,
   checks, and newer base-branch changes.
4. Produce one review that decides for each artifact whether both the stated
   problem and implemented solution are sound.
5. Draft exact public replies for every artifact.
6. Obtain the applicable publication approval. Approval is required by default;
   explicit unattended authority may cover the remainder of the session.
7. Post replies and resolve agreed artifacts.
8. Keep disagreed artifacts open while implementing targeted revisions and
   tests. Use `receiving-code-review` as the judgment policy.
9. Run a separate fresh cold review of the staged revision. Fix and re-review
   until clean.
10. Commit and push under the applicable public-text approval policy.
11. Add one new unresolved revision artifact per changed disagreement, anchored
    to a valid right-side line in the pushed PR diff.
12. Resolve the superseded artifacts only after their replacements are verified
    present.
13. Start the next round with fresh evaluator context.

One round may use a review engine that fans out into parallel axis reviews. The
next round cannot start until the previous round's revisions and record writes
are complete.

## Artifact Semantics

An artifact comment makes a reviewable claim about code already present. It is
not an instruction to implement that claim.

Agreement means:

- the problem statement is accurate;
- the implementation solves it without unacceptable regressions;
- the reply records agreement;
- the thread is resolved.

Disagreement means:

- the reply records the exact technical disagreement and intended revision;
- code and targeted tests are revised;
- a new artifact explains the prior implementation, disagreement, resulting
  implementation, and verification;
- the old thread is resolved only after the new artifact exists.

Every reviewer reads the full chain. Fresh context prevents attachment to the
previous evaluator; it does not erase the record.

## Completion And Recovery

The workflow completes only when:

- one fresh round agrees with every unresolved artifact;
- all approved replies have been posted;
- GitHub reports zero unresolved loop-artifact threads; ordinary review threads
  remain owned by their normal review workflow;
- the pushed branch is clean and mergeable;
- applicable CI checks pass.

If round four still produces substantive disagreement, stop and escalate the
structural or requirements conflict rather than looping indefinitely.

Each round writes a git-ignored local ledger containing PR identity, head and
base SHAs, round number, thread IDs, decisions, posted comment IDs, replacement
anchors, commit IDs, verification evidence, and publication authority. GitHub is
the durable product record; the local ledger is crash recovery for incomplete
writes.

After any ambiguous GitHub mutation, read back the exact state before another
write. Never retry an unverified mutation blindly.

## Skill Structure

`SKILL.md` owns the trigger, roles, round workflow, artifact semantics,
completion contract, and safety rules.

Supporting references may contain:

- GitHub GraphQL queries for complete thread history and resolution;
- REST examples for threaded replies and anchored comments;
- round-owner and cold-reviewer prompt contracts;
- ledger schema and recovery procedure.

Automation scripts are deferred until repeated runs reveal stable API operations
worth enforcing. The first implementation uses explicit commands so premature
tooling does not freeze the wrong interface.

## Verification Strategy

Skill creation follows RED-GREEN-REFACTOR:

1. Baseline agents receive a PR-backed descriptive-comment scenario without the
   skill. Record failures such as treating comments as requests, forgetting full
   history, reusing the same evaluator, resolving before replacement, confusing
   parallel axes with parallel rounds, or claiming completion without readback.
2. Add the minimal skill guidance that corrects observed failures.
3. Re-run equivalent scenarios with the skill loaded.
4. Add pressure around time, many threads, disagreement, ambiguous mutations,
   base-branch drift, and publication approval.
5. Refactor wording until agents consistently preserve the record and converge
   without duplicating adjacent skill responsibilities.

`review-loop` receives its own regression scenario proving that one round may
aggregate parallel axis reviews while rounds remain sequential.
