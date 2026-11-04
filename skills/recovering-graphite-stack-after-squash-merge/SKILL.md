---
name: recovering-graphite-stack-after-squash-merge
description: Use when a Graphite stack looks broken or stuck after PRs below it squash-merged - symptoms include an upstack PR that conflicts with trunk or still contains already-merged commits, `gt log short` still showing merged branches, branches stuck on "needs restack", local branches reporting "ahead N behind N" of origin with equal counts, or a stack merge that stopped part-way.
---

# Recovering a Graphite stack after squash-merge

## Overview

Squash merging gives each merged PR a new commit on trunk. The branches above it still contain the original commits until something restacks them. Graphite does that restack, locally with `gt sync` or on the server during a stack merge, using its record of each branch's parent to drop exactly the commits that already merged.

**Core principle:** let Graphite do the restack. Find out what Graphite has already done, then either `gt sync` (it hasn't restacked yet) or adopt its server-side result (it has). Hand-rebasing with `git rebase --onto` works, but leaves Graphite's records stale and races any merge Graphite is running.

## Step 1: Check whether a Graphite merge is running

Graphite posts a "Merge activity" comment on each PR in a stack merge and updates it as the merge progresses:

```bash
gh api repos/<owner>/<repo>/issues/<lowest-open-pr>/comments \
  -q '.[]|select(.body|test("Merge activity"))|.body'
```

- **"couldn't merge … because a downstack PR failed to merge"**: the merge stopped and nothing is queued. Fix the blocking PR (Steps 2 to 4), then restart the merge with `gt merge` from the top branch, telling whoever started it.
- **"set to merge when ready"**: Graphite will merge each PR as soon as it can. Fix what blocks it and let it run. Don't merge the same PRs another way at the same time.

## Step 2: Has Graphite already restacked the branches?

```bash
git fetch origin
git log --oneline origin/<trunk>..origin/<lowest-open-branch>
```

- **Origin still contains the merged commits**, or the PR conflicts with trunk: Graphite hasn't restacked. Go to Step 3.
- **Origin contains only the branch's own commits**, and local branches show "ahead N behind N" with equal counts: Graphite restacked on the server. Go to Step 4.

## Step 3: Restack with `gt sync`

```bash
git checkout <trunk> && git pull --ff-only
gt sync --no-interactive
```

`gt sync` deletes branches whose PRs merged, then restacks the rest onto the latest trunk, keeping only each branch's own commits.

For conflicts, resolve the files, then commit with the original message and continue:

```bash
git add <files>
git commit -C REBASE_HEAD --cleanup=verbatim
gt continue
```

If commit subjects start with `#`, set `git config core.commentChar ';'` first. Otherwise git strips the subject as a comment and `gt continue` fails with an empty commit message.

Then push: `gt submit --no-edit --stack --force`.

## Step 4: Adopt Graphite's server-side restack

Local branches still point at the pre-restack commits. Verify you have no unpushed work (`git log <branch> ^origin/<branch>` should only show commits that merged or were restacked), then for each surviving branch, bottom to top:

```bash
git checkout <branch>
git reset --hard origin/<branch>
```

Delete merged local branches (`gt sync` does this), then check `gt log short`. If parents are wrong, `gt track <branch> --parent <parent>` bottom to top.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Hand-rebasing with `git rebase --onto` and re-tracking | `gt sync` does the same with the right parent records |
| Merging PRs with `gh` or the web UI while a Graphite merge is queued | Read the merge activity first; unblock the queued merge instead |
| `git pull` or `git merge` on a stack branch to "catch up" | Creates duplicate commits. Restack instead. |
| Resetting to origin when origin hasn't been restacked | Changes nothing. Check Step 2 first. |
| Resetting with unpushed local work | The reset destroys it. Push or back it up first. |
