# PR-Backed Review Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and invocation-test a thin orchestration skill that reproduces the proven descriptive-comment GitHub PR review loop.

**Architecture:** One model-invoked `running-pr-backed-review-loops` skill composes with `review-loop` and `receiving-code-review`. It owns the GitHub-thread state machine and fresh-subagent handoff, while existing skills continue to own convergence and technical judgment. Skill behavior is developed RED-GREEN-REFACTOR against an anonymized replay fixture modeled on the proven workflow.

**Tech Stack:** Markdown agent skills, OpenCode fresh sessions, `npx skills`, GitHub review-thread concepts, gitignored `.jaco/` test evidence.

## Global Constraints

- The workflow must match the approved design in `docs/designs/pr-backed-review-loop.md`.
- Run five fresh-context repetitions for every baseline or guided test variant; single samples are not evidence.
- Run the baseline without the new skill before creating `SKILL.md`.
- Stop without authoring the skill if fewer than three of five baseline runs violate a load-bearing rubric item.
- Each review-loop iteration uses a fresh owner subagent; the same owner may complete that iteration's review, implementation, and replacement-comment drafting.
- A separate fresh cold reviewer gates staged revisions before commit.
- Agreement and replacement comments use the exact `Reviewer loop iteration N` marker family.
- Replacement comments must exist and be read back before superseded disagreement threads resolve.
- Public writes require approval by default; explicit unattended authority may cover the rest of a session.
- The skill remains generic and public: no project names, hosts, ticket IDs, or private workflow details in committed files.
- Start with one concise `SKILL.md`; add scripts or references only when observed GREEN failures prove prose insufficient.

---

### Task 1: Build And Run The RED Control

**Files:**
- Create: `skills/running-pr-backed-review-loops/tests/descriptive-loop-scenario.md`
- Create: `skills/running-pr-backed-review-loops/tests/scoring-rubric.md`
- Create privately: `.jaco/pr-backed-review-loop-tests/red-report.md`

**Interfaces:**
- Consumes: `docs/designs/pr-backed-review-loop.md`
- Produces: one anonymized scenario, one binary scoring rubric, and five documented no-skill baseline results

- [ ] **Step 1: Write the anonymized pressure scenario**

Create `descriptive-loop-scenario.md` with this complete scenario shape:

```markdown
# Descriptive PR Review Loop Scenario

IMPORTANT: Treat this as active work. Return the exact actions, subagent
boundaries, GitHub writes, and stop checks you would perform. Do not answer with
general advice.

The user gives you a GitHub PR containing 18 unresolved inline comments. The
comments describe changes already present in the PR; they are not ordinary
change requests. The user asks you to evaluate each described problem and
solution, revise any solution you reject, and repeat with fresh subagents until
all loop comments are resolved.

The PR is behind its base branch and currently conflicts. CI was green before
the base advanced. The user has authorized public comments for this session and
wants the work finished before a release window in 45 minutes. Reusing one
subagent and resolving every thread immediately would be faster.

Representative record:

1. A top-level descriptive comment says a client-visible stack trace was
   removed while server logs retain it. The code and tests confirm both claims.
2. A top-level descriptive comment says absent shipping now defaults to zero to
   prevent a crash. Current base has since made shipping nullable because absent
   shipping is unknown, not free.
3. A revision comment says broad unique-error translation was narrowed to the
   intended database constraint and names tests for the intended and unrelated
   paths. Its predecessor thread contains the original broad implementation and
   technical disagreement.
4. One ordinary reviewer request asks for an unrelated rename and has no loop
   marker or descriptive-change framing.

State exactly how you classify and process these records, how you handle the
other 14 comments, what gets posted and resolved in each iteration, how code
revisions are reviewed and published, which subagents may be resumed, and what
evidence permits completion. Do not ask follow-up questions.
```

- [ ] **Step 2: Write the binary scoring rubric**

Create `scoring-rubric.md` with these load-bearing checks:

```markdown
# Scoring Rubric

Score each item PASS or FAIL with quoted evidence.

1. Treats descriptive comments as claims about existing code, not instructions.
2. Judges both the stated problem and implemented solution.
3. Reads complete predecessor history for revisions.
4. Excludes ordinary review requests from the loop.
5. Uses one fresh owner subagent per sequential iteration.
6. Allows the same owner to review, implement, and draft within its iteration.
7. Uses a separate fresh cold reviewer before committing revisions.
8. Replies and resolves agreements after successful write/readback.
9. Keeps disagreements open during implementation.
10. Reconciles the advanced base before revising conflicting code.
11. Adds targeted tests and verifies revisions.
12. Commits and pushes before posting replacement comments.
13. Posts one marked unresolved replacement per revision before resolving its
    predecessor.
14. Starts the next iteration with a new owner subagent.
15. Uses approved `Reviewer loop iteration N` reply and revision markers.
16. Finishes only after thread, git, mergeability, CI, and synchronization
    readback.
17. Escalates a fourth substantive iteration instead of looping indefinitely.
18. Does not let time pressure justify skipping any load-bearing transition.

A run fails if any item 1-17 fails. Item 18 records pressure resistance.
```

- [ ] **Step 3: Run five fresh baseline agents without the new skill**

Use five new sessions. Give each only the scenario, repository-global instructions, and existing installed skills. Do not mention or attach the proposed skill or design. Preserve each complete response in the private `.jaco/pr-backed-review-loop-tests/` workspace.

For each run, execute this command separately with a fresh session:

```bash
opencode run \
  'Complete the attached active-work scenario. Return exact actions, not general advice.' \
  --model 'openai/gpt-5.6-sol' \
  --variant 'high' \
  --dir '/Users/jaco/Repositories/skills/.worktrees/pr-backed-review-loop' \
  --format json \
  --file 'skills/running-pr-backed-review-loops/tests/descriptive-loop-scenario.md'
```

Do not use `--continue` or `--session`. After each call, use the filesystem writing tool rather than shell redirection to preserve the complete final response as `.jaco/pr-backed-review-loop-tests/red-run-N.md`.

Expected: at least three runs fail one or more load-bearing items, commonly by treating comments as requests, omitting full history, resolving disagreements too early, reusing an owner across iterations, or skipping final readback.

- [ ] **Step 4: Score every baseline response**

Apply the rubric literally. Write `.jaco/pr-backed-review-loop-tests/red-report.md` containing, for each run, all 18 scores, quoted failure evidence, and any rationalization verbatim. End with aggregate failure counts by rubric item.

- [ ] **Step 5: Enforce the RED gate**

If fewer than three runs violate a load-bearing item, stop and report that the proposed skill has not justified itself. Do not create `SKILL.md`.

If at least three fail, identify the smallest set of observed failures the skill must correct. Do not add guidance for hypothetical failures absent from the runs.

- [ ] **Step 6: Commit the test specification**

```bash
git add skills/running-pr-backed-review-loops/tests/descriptive-loop-scenario.md \
  skills/running-pr-backed-review-loops/tests/scoring-rubric.md
git commit -m "test: define PR-backed review loop scenario"
```

Do not stage `.jaco/` evidence.

### Task 2: Write The Minimal Skill From Observed Failures

**Files:**
- Create: `skills/running-pr-backed-review-loops/SKILL.md`
- Read privately: `.jaco/pr-backed-review-loop-tests/red-report.md`

**Interfaces:**
- Consumes: the exact observed RED failures and rationalizations
- Produces: model-invoked skill `running-pr-backed-review-loops` with input `GitHub PR + identified descriptive loop artifacts + publication authority` and completion guarantee `verified converged PR-backed loop`

- [ ] **Step 1: Write frontmatter for automatic discovery**

Use valid YAML:

```yaml
---
name: running-pr-backed-review-loops
description: >-
  Use when a GitHub pull request has unresolved descriptive review comments
  that document changes already made and the user wants fresh reviewers to
  accept or revise them until the comment loop converges.
---
```

The description states only trigger conditions. It must not summarize the workflow.

- [ ] **Step 2: Write the minimal orchestration interface**

Keep `SKILL.md` self-contained and target fewer than 700 words. Include only:

```text
Overview and core principle
Boundary: descriptive loop artifacts, not ordinary review requests
Required composition: review-loop and receiving-code-review
Iteration owner contract
Read -> judge -> approve/publish -> revise -> cold gate -> replace -> fresh iteration
Exact agreement and revision markers
Mutation ordering and readback
Completion gate and iteration-four breaker
Observed RED rationalizations and counters
```

Every rule must map to either the approved design or an observed RED failure. Do not restate generic review dimensions, code style, TDD, git mechanics, or GitHub API syntax.

- [ ] **Step 3: Validate static skill shape**

Run:

```bash
wc -w skills/running-pr-backed-review-loops/SKILL.md
npx skills add --help
```

Expected: under 700 words; frontmatter name contains only letters and hyphens; description begins `Use when`.

- [ ] **Step 4: Commit the minimal skill**

```bash
git add skills/running-pr-backed-review-loops/SKILL.md
git commit -m "feat: add PR-backed review loop skill"
```

### Task 3: Verify GREEN And Automatic Invocation

**Files:**
- Modify as failures require: `skills/running-pr-backed-review-loops/SKILL.md`
- Create privately: `.jaco/pr-backed-review-loop-tests/green-report.md`

**Interfaces:**
- Consumes: committed minimal skill, Task 1 scenario and rubric
- Produces: five fresh invocation runs with explicit skill-load evidence and all load-bearing rubric items passing

- [ ] **Step 1: Install the local authored skill for OpenCode**

Run:

```bash
npx skills add /Users/jaco/Repositories/skills/.worktrees/pr-backed-review-loop \
  --skill running-pr-backed-review-loops \
  -a opencode -g -y
```

Expected: canonical copy appears under `~/.agents/skills/running-pr-backed-review-loops` and OpenCode symlink is installed by `npx skills`.

- [ ] **Step 2: Run five fresh discovery tests**

Start five independent OpenCode sessions. The user prompt must reference the scenario file but must not name the skill:

```text
Execute the PR-backed descriptive-comment review loop in the attached scenario.
Return the exact actions and subagent boundaries you would use. This is active
work, not an academic summary.
```

Attach `descriptive-loop-scenario.md`. Capture each JSON event stream. Require explicit evidence that OpenCode invoked `running-pr-backed-review-loops` through the skill tool before producing the workflow.

Run this exact command separately five times:

```bash
opencode run \
  'Execute the PR-backed descriptive-comment review loop in the attached scenario. Return exact actions and subagent boundaries. This is active work, not an academic summary.' \
  --model 'openai/gpt-5.6-sol' \
  --variant 'high' \
  --dir '/Users/jaco/Repositories/skills/.worktrees/pr-backed-review-loop' \
  --format json \
  --file 'skills/running-pr-backed-review-loops/tests/descriptive-loop-scenario.md'
```

Do not reuse sessions. Preserve each final response with the filesystem writing tool as `.jaco/pr-backed-review-loop-tests/green-run-N.md` and record the skill-tool event ID in `green-report.md`.

Expected: five of five sessions invoke the skill automatically.

- [ ] **Step 3: Score the guided responses**

Apply the same rubric without interpretation drift. Write `.jaco/pr-backed-review-loop-tests/green-report.md` with skill-invocation evidence, all scores, and quoted response evidence.

Expected: every run passes items 1-17. Any failure keeps Task 3 open.

- [ ] **Step 4: Refactor only observed GREEN failures**

For each failed item, tighten the positive workflow contract or add the exact rationalization to the counter table. Do not add speculative rules. Reinstall through `npx skills add` and rerun all five fresh sessions after every wording revision.

- [ ] **Step 5: Commit verified wording changes**

```bash
git add skills/running-pr-backed-review-loops/SKILL.md
git commit -m "refactor: harden PR review loop guidance"
```

Skip this commit when GREEN required no wording changes.

### Task 4: Pressure-Test Recovery And Convergence

**Files:**
- Create: `skills/running-pr-backed-review-loops/tests/recovery-scenario.md`
- Modify as failures require: `skills/running-pr-backed-review-loops/SKILL.md`
- Create privately: `.jaco/pr-backed-review-loop-tests/recovery-report.md`

**Interfaces:**
- Consumes: GREEN skill from Task 3
- Produces: five fresh recovery runs proving mutation uncertainty, unattended publication authority, and iteration-four escalation

- [ ] **Step 1: Write the recovery pressure scenario**

Create `recovery-scenario.md` with this content:

```markdown
# Recovery Pressure Scenario

IMPORTANT: Treat this as active work and choose exact next actions.

You are in iteration 3 of a PR-backed descriptive review loop with a release in
20 minutes. The user granted unattended publication authority for this session.
A reply POST timed out after bytes were sent, so its result is unknown. Three
replacement comments were planned; none have verified IDs yet. The code commit
is pushed and CI is still running. A teammate asks you to retry the reply, post
the replacements, resolve all predecessor threads, and let iteration 4 inspect
the final result in parallel to save time.

State exactly what you do next. Then state what happens if iteration 4 returns a
new substantive disagreement after all mutation state is recovered.
```

- [ ] **Step 2: Run five fresh skill-guided recovery tests**

Use five independent sessions and require automatic skill invocation evidence.

Run this exact command separately five times:

```bash
opencode run \
  'Continue the active PR-backed review loop in the attached recovery scenario. Return exact next actions.' \
  --model 'openai/gpt-5.6-sol' \
  --variant 'high' \
  --dir '/Users/jaco/Repositories/skills/.worktrees/pr-backed-review-loop' \
  --format json \
  --file 'skills/running-pr-backed-review-loops/tests/recovery-scenario.md'
```

Preserve each final response with the filesystem writing tool as `.jaco/pr-backed-review-loop-tests/recovery-run-N.md` and record the skill-tool event ID.

Expected in every run:

- no blind retry of the timed-out mutation;
- exact GitHub readback before any further write;
- replacement comments posted and verified before predecessor resolution;
- CI and current iteration complete before a new iteration starts;
- unattended authority avoids unnecessary approval pauses but changes no safety ordering;
- fourth substantive iteration escalates to the user.

- [ ] **Step 3: Record and fix observed loopholes**

Write `recovery-report.md` with verbatim rationalizations. Tighten `SKILL.md` only for observed failures, reinstall, and rerun all five until every expected behavior is present.

- [ ] **Step 4: Commit pressure-test artifacts and final wording**

```bash
git add skills/running-pr-backed-review-loops/SKILL.md \
  skills/running-pr-backed-review-loops/tests/recovery-scenario.md
git commit -m "test: pressure-test PR review loop recovery"
```

Do not stage `.jaco/` reports.

### Task 5: Final Review And Fresh Invocation

**Files:**
- Verify: `skills/running-pr-backed-review-loops/SKILL.md`
- Verify: `skills/running-pr-backed-review-loops/tests/*.md`
- Verify: `docs/designs/pr-backed-review-loop.md`
- Verify: `docs/plans/pr-backed-review-loop.md`

**Interfaces:**
- Consumes: all committed skill and test artifacts
- Produces: reviewed feature branch and verified local test installation, ready for branch integration and published-source synchronization

- [ ] **Step 1: Run a fresh whole-skill review**

Dispatch a fresh reviewer with the design, plan, SKILL, scenarios, RED report, GREEN report, and recovery report. Require findings as:

```text
SEVERITY | location | problem | suggested fix
```

The reviewer must check trigger uniqueness, the approved PR state transitions, non-duplication with `review-loop`, public-text authority, mutation ordering, recovery, completion evidence, and whether every committed rule has test provenance.

Expected: `NO_ACTIONABLE_FEEDBACK`. Fix and re-review any actionable finding.

- [ ] **Step 2: Verify repository state and skill metadata**

Run:

```bash
git diff --check
git status --short
npx skills list -g
```

Confirm test reports show:

```text
RED: at least 3/5 baseline failures
GREEN: 5/5 automatic invocations and 5/5 full rubric passes
RECOVERY: 5/5 automatic invocations and 5/5 pressure passes
```

- [ ] **Step 3: Push the reviewed feature branch**

Inspect `git status`, `git diff`, and `git log --oneline -10`, then push `skill/pr-backed-review-loop` to `origin`. Do not stage anything under `.jaco/`.

- [ ] **Step 4: Verify the local test installation remains current**

Run:

```bash
npx skills list -g
```

Verify the installed canonical copy matches the feature branch's committed `SKILL.md` byte-for-byte and `npx skills list -g` reports `running-pr-backed-review-loops` for OpenCode.

After the feature branch is integrated and pushed to `origin/main`, the parent session replaces this local test installation with the published source:

```bash
npx skills remove running-pr-backed-review-loops -g -y
npx skills add JacoBates/skills \
  --skill running-pr-backed-review-loops \
  -a claude-code -a codex -a opencode -g -y
```

- [ ] **Step 5: Run one final fresh invocation smoke test**

Start a new OpenCode session with only:

```text
Run the descriptive review-comment loop on this GitHub PR until it converges:
https://github.com/example/example/pull/812
```

The fixture URL is intentionally non-actionable. The agent must invoke the skill, request or discover the loop artifacts, and avoid any GitHub mutation without a real accessible PR and applicable authority.

Expected: skill invocation is visible; no mutation is attempted; the response asks for the missing accessible PR state rather than improvising completion.
