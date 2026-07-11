---
name: recovering-graphite-stack-after-squash-merge
description: Use when Graphite's stack visualisation looks broken or stale after PRs have squash-merged - symptoms include `gt log short` still showing merged branches, branches stuck on "needs restack", local branches reporting "ahead N behind N" of origin with equal counts, or `gt restack` triggering an interactive rebase that wants to replay 20+ already-merged commits.
---

# Recovering a Graphite stack after squash-merge

## Overview

Squash-merging gives each merged commit a new SHA on trunk. Local branches still reference the pre-rebase parent SHA, and Graphite's metadata in `.git/.graphite_metadata.db` points at the old parents. Result: a stack that looks broken from Graphite's view even though every PR's content is already in trunk.

**Core principle:** the post-rebase remote tip of each surviving branch is the truth. Reset locals to origin, prune merged branches, re-tell Graphite about the parent-child structure. Don't try to interactive-rebase your way out - that replays commits already in trunk and you'll conflict on each one.

## When to Use

- `gt log short` still shows merged branches in the tree after a stack-merge.
- Local stack branches show "ahead N behind N" of origin with matching counts (squash-merge signature).
- `gt sync` warns "merged commits are not contained in the latest trunk" but you've verified they are (under different SHAs).
- `gt restack` starts an interactive rebase wanting to replay 10+ commits.

**Don't use when:** you have unpushed local commits on a stack branch - the reset destroys them. Push or stash first. Run `git log <branch> ^origin/<branch>` to check.

## Workflow

1. **Sync trunk:**
   ```bash
   git checkout <trunk>          # e.g. main, staging
   git pull --ff-only
   gt sync --no-interactive
   ```
   `gt sync` identifies merged branches but won't try to restack them.

2. **Delete merged local branches.** For each one `gt sync` reported as merged:
   ```bash
   git branch -D <merged-branch>
   ```
   Do all of these before touching survivors - Graphite's metadata gets confused otherwise.

3. **Reset each surviving branch to its origin head.** For each survivor, bottom-to-top:
   ```bash
   git checkout <branch>
   git reset --hard origin/<branch>
   ```
   **Destructive.** Verify no unpushed work first.

4. **Re-track the stack.** Graphite probably lost parent metadata when the merged branches went away:
   ```bash
   stack=(branch-1 branch-2 branch-3 ...)   # bottom to top
   parent="<trunk>"
   for b in "${stack[@]}"; do
     git checkout "$b"
     gt track --parent "$parent"
     parent="$b"
   done
   ```

5. **Verify.** `gt log short` should now show a clean stack on trunk with no "(needs restack)" annotations.

6. **Re-push to sync Graphite's remote view:**
   ```bash
   gt submit --no-edit --stack --draft --force
   ```
   Content is a no-op; this updates Graphite's remote metadata.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| `git pull` or `git merge` on a stack branch to "catch up" | Use `git reset --hard origin/<branch>` instead - creates no duplicate commits |
| Run `gt restack` and let it start an interactive rebase | `git rebase --abort`, use this skill's reset approach |
| Re-track before deleting merged branches | Delete merged branches first, then re-track survivors |
| Skip the final `gt submit --force` | Local Graphite metadata correct but remote stale - re-push to sync |

## Why This Works

Two pieces of state were stale: the local branch tips (pre-rebase commits) and the local Graphite metadata (parent SHAs pointing at deleted commits). Resetting to origin adopts the rebased state Graphite already produced server-side. Re-tracking tells local metadata about the new structure. Final force-push keeps remote Graphite metadata aligned.
