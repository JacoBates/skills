---
name: resolving-pr-merge-conflicts
description: Use when resolving a pull request whose head conflicts with its base, especially when an orchestrator supplies exact refs, verification requirements, and conditional push authority. Merges rather than rebases, requires an isolated checkout, and pushes only a fully understood verified result with unchanged remote refs.
---

# Resolving PR merge conflicts

## Core principle

No doubt means no push. A conflict-free index is necessary but not sufficient:
understand both sides, verify affected behavior, inspect against both parents,
and revalidate remote refs immediately before committing.

## Required inputs

Require every field. Missing repository or ref identity is a failed precondition.
`cwd: null` means `repositoryPath`. `commitSubject` is the exact commit subject
when authorized and null otherwise. `pushAuthorized: false` or a null or empty
subject removes commit and push authority, but does not prevent analysis.

### `VerificationRequirement`

| Field | Type | Meaning |
| --- | --- | --- |
| `command` | `string` | Exact command to run and repeat in the result. |
| `cwd` | `string \| null` | Working directory, or `repositoryPath` when null. |
| `required` | `boolean` | Whether failure or non-execution blocks confidence. |

### `ResolverInput`

| Field | Type |
| --- | --- |
| `repositoryPath` | `string` |
| `forbiddenGitCommonDirs` | `string[]` |
| `prUrl` | `string` |
| `headRepository` | `string` |
| `baseRepository` | `string` |
| `headRemote` | `string` |
| `baseRemote` | `string` |
| `headFetchUrl` | `string` |
| `headPushUrl` | `string` |
| `baseFetchUrl` | `string` |
| `headSha` | `string` |
| `baseSha` | `string` |
| `headRefName` | `string` |
| `baseRefName` | `string` |
| `verificationRequirements` | `VerificationRequirement[]` |
| `pushAuthorized` | `boolean` |
| `commitSubject` | `string \| null` |

### `ResolverResult`

| Field | Type |
| --- | --- |
| `outcome` | `"resolved" \| "needs_attention" \| "stale" \| "failed"` |
| `prUrl` | `string` |
| `headRepository` | `string` |
| `baseRepository` | `string` |
| `headSha` | `string` |
| `baseSha` | `string` |
| `headRefName` | `string` |
| `baseRefName` | `string` |
| `files` | `Array<{ path: string; resolution: string }>` |
| `verification` | `Array<{ command: string; outcome: "passed" \| "failed" \| "not_run"; detail: string }>` |
| `commitSha` | `string \| null` |
| `blockers` | `string[]` |
| `error` | `string \| null` |
| `retainedWorktreePath` | `string \| null` |
| `retainedWorktreeReason` | `string \| null` |
| `at` | `number` (epoch milliseconds) |

## Output contract

Return exactly one `ResolverResult`, not free-form prose. Preserve the supplied
PR and ref identity. Include every conflicting file with concise resolution
reasoning and every supplied verification command with its result. Every array
is present even when empty, every absent nullable value is explicitly null, and
`at` is the epoch-millisecond time when the result is produced.

`commitSha` is the pushed merge commit SHA only when `outcome` is `resolved`.
It is null for every `needs_attention`, `stale`, and `failed` result, including
when a local commit exists but a post-commit ref check or push fails. In that
case, return the isolated checkout in `retainedWorktreePath` and identify the
unpushed local commit in `retainedWorktreeReason`; do not expose it as the
result's `commitSha`. Put decision or confidence impediments in `blockers`. Put
an operational failure in `error`; otherwise `error` is null.

## Workflow

1. Canonicalize `repositoryPath` and the result of
   `git rev-parse --git-common-dir`. Before merge mutation, fail if the checkout
   is dirty, `HEAD` differs from `headSha`, or the canonical common directory
   equals any canonical `forbiddenGitCommonDirs` entry.
2. Verify `headRemote` and `baseRemote` exist. For each applicable remote, read
   `git remote get-url --all` and `git remote get-url --push --all`. Require
   exactly one head fetch URL, one head push URL, and one base fetch URL, exactly
   equal to `headFetchUrl`, `headPushUrl`, and `baseFetchUrl`. Missing,
   mismatched, or additional URLs are `failed` before mutation. Compare literal
   configured strings: never normalize or guess SSH/HTTPS equivalence.
3. Fetch `refs/heads/<headRefName>` from `headRemote` and
   `refs/heads/<baseRefName>` from `baseRemote` without switching branches. If
   either live SHA differs from its supplied SHA, return `stale` before mutation.
4. Run `git merge --no-commit --no-ff` against the exact fetched base commit. If
   Git reports no conflicts, abort the uncommitted merge and return `stale`.
   This resolver resolves a reported conflict; it does not silently update a
   branch that no longer conflicts.
5. Enumerate unmerged paths. Read both parents, relevant commits, tests, and
   repository instructions before choosing a resolution.
6. Resolve each path according to understood intent. Never default blindly to
   ours or theirs. Record concise per-file reasoning while context is fresh.
7. Reject remaining unmerged entries and conflict markers. Inspect the complete
   merge diff against both parents and reject unrelated edits.
8. Account for every caller-supplied verification requirement, in input order,
   from its requested directory. Run each applicable command and record the
   exact command, `passed`/`failed`, and concise detail. Record `not_run` and why
   when a command is inapplicable or an earlier prerequisite prevents it. A
   required command may never be silently omitted.
9. Apply the confidence gate. Any semantic uncertainty, unclear generated or
   lockfile output, failed or not-run required verification, unrelated diff, or
   material doubt means `needs_attention` and no commit.
10. Fetch both exact refs from their supplied remotes again. Any movement means
    `stale` and no commit. Do not merge, rebase, or otherwise absorb movement.
11. Only when `pushAuthorized` is true, `commitSubject` is non-null and non-empty,
    and every gate passed, create one local merge commit with exactly
    `commitSubject` and no body. Without that authority, return
    `needs_attention` with the verified candidate uncommitted and unpushed.
12. Fetch and validate both exact refs once more after commit creation and
    immediately before push. If either moved, return `stale`; leave the local
    commit unpushed for caller cleanup. Do not create another commit.
13. Push `HEAD` to `refs/heads/<headRefName>` through the validated
    `headRemote`/`headPushUrl`, without force.
14. If push is rejected, fetch and check both exact remote refs again. Ref
    movement is `stale`; authentication, transport, or another operational
    failure is `failed`. In either result, `commitSha` is null and the unpushed
    local commit is described only through the retained-worktree fields. Never
    merge, rebase, retry with force, or create a replacement commit.
15. Return the complete result. Abort an in-progress merge before cleanup unless
    retaining a useful `needs_attention` candidate under the Cleanup boundary.

## Confidence gate

All conditions are mandatory: both sides' intent is explainable; the resolution
preserves or deliberately supersedes that intent; no product behavior is
guessed; no unresolved review decision is invented; no unmerged entries or
markers remain; the result is coherent against both parents; all required
verification passes; both remote refs are unchanged; and there is no material
doubt.

## Cleanup boundary

The caller owns repository and environment cleanup. This skill aborts an
in-progress merge when no candidate should be retained. For a useful
`needs_attention` candidate, leave the isolated path intact and return that path
and reason. A `stale` or `failed` result after local commit creation also returns
the retained path and reason so the caller can find the unpushed commit, while
`commitSha` remains null. A `resolved` result returns null retained fields. The
caller may add cleanup-failure detail without changing `resolved` or
`commitSha`.

## Prohibited actions

Never mutate a shared checkout, rebase, amend, force-push, post PR text, resolve
review threads, change tracker state, dismiss a failed check as unrelated without
evidence, or commit merely because Git accepts the merge.

## Outcome rules

| Outcome | Use when |
| --- | --- |
| `resolved` | The authorized merge commit was pushed; `commitSha` is its SHA. |
| `needs_attention` | A person must decide semantics, verification did not establish confidence, or a verified candidate lacks push authority. |
| `stale` | The reported conflict disappeared or either exact ref moved. |
| `failed` | Tooling, checkout, authentication, remote identity, or another operational prerequisite failed. |

Every non-`resolved` outcome has `commitSha: null`.

## Red flags

| Thought | Stop reason |
| --- | --- |
| "Git accepted it" | A clean index does not establish semantic correctness. |
| "Tests mostly pass" | Every required verification must pass. |
| "Ours looks newer" | Recency is not evidence of intended behavior. |
| "The ref only moved a little" | Any movement invalidates the supplied snapshot. |
| "Force-with-lease is safe" | Force is prohibited; return `stale`. |
| "The caller probably intended push authority" | Only explicit `pushAuthorized: true` plus an exact non-empty subject grants authority. |
