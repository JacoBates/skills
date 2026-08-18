# Trigger Discovery Scenario

Run each prompt five times in fresh sessions from an isolated directory where
repository source and test files are inaccessible. Record a load if the agent
invokes `running-pr-backed-review-loops`, directly reads its files, or otherwise
obtains its body. A negative case fails on any such access, not only a skill-tool
call.

## Qualified Execution Prompts

1. Execute the PR-backed review loop for identified unresolved descriptive
   artifacts that claim already-present changes on a GitHub PR.
2. Continue an existing GitHub PR loop for identified unresolved comments that
   describe problems and solutions already present.
3. Recover an interrupted PR-backed loop for identified unresolved descriptive
   change claims whose solutions are already in the PR.
4. Run fresh iterations over identified unresolved artifacts that each claim a
   problem and an implemented solution already in the branch.
5. Resume a GitHub PR loop for identified unresolved revision markers and
   descriptive comments claiming existing code changes.

Expected: **5/5 load** `running-pr-backed-review-loops`.

## Required-Predicate Near Misses

1. Explain the workflow without executing, continuing, or recovering it.
2. Perform an ordinary PR review for bugs and missing tests.
3. Run a loop over requests for future changes, not changes already present.
4. Summarize qualifying descriptive comments without running their loop.
5. Run a local fresh-review loop with no GitHub PR or descriptive artifacts.

Expected: **0/5 load** `running-pr-backed-review-loops`.

## Authority-Only Near Miss

Decide whether an unapproved public reply batch may be posted when no publication
authority exists. Answer the policy question only; do not execute a PR review
loop.

Expected: **0/5 load** `running-pr-backed-review-loops`.
