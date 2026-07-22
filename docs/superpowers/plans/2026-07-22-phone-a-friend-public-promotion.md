# Phone a Friend Public Promotion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the tested `phone-a-friend` skill in `JacoBates/skills`, make that repository canonical, repoint all global installations, and remove the private duplicate.

**Architecture:** Treat the promotion as a byte-preserving source migration rather than a skill redesign. Publish and verify the public source first, install from its GitHub identity second, and remove the private source only after the public installation passes discovery and content checks.

**Tech Stack:** Agent Skills Markdown and YAML, Git, GitHub, `npx skills`, OpenCode, and the Codex skill validator.

## Global Constraints

- The approved specification is `docs/superpowers/specs/2026-07-22-phone-a-friend-public-promotion-design.md` in `/Users/jaco/Repositories/skills`.
- The tested private source is `/Users/jaco/Repositories/skills-private/skills/phone-a-friend`.
- The canonical public destination is `/Users/jaco/Repositories/skills/skills/phone-a-friend`.
- Preserve all four skill files byte-for-byte during promotion. Do not alter routing behavior, scores, effort choices, launch contracts, or metadata.
- Publish and verify the public source before deleting the private source.
- Install for Claude Code, Codex, and OpenCode using `npx skills`; never edit installed copies or the lockfile directly.
- Use `apply_patch` for authored file additions and deletions.
- Never stage `.jaco/` or `~/.agents/.skill-lock.json`.
- Use regular hyphens, never emdashes or endashes.

---

### Task 1: Publish the Byte-Identical Skill

**Files:**
- Create: `/Users/jaco/Repositories/skills/skills/phone-a-friend/SKILL.md`
- Create: `/Users/jaco/Repositories/skills/skills/phone-a-friend/agents/openai.yaml`
- Create: `/Users/jaco/Repositories/skills/skills/phone-a-friend/references/launchers.md`
- Create: `/Users/jaco/Repositories/skills/skills/phone-a-friend/references/model-catalog.md`

**Interfaces:**
- Consumes: the four files under `/Users/jaco/Repositories/skills-private/skills/phone-a-friend`.
- Produces: a byte-identical public skill at `/Users/jaco/Repositories/skills/skills/phone-a-friend`, committed and available from `JacoBates/skills`.

- [ ] **Step 1: Confirm both repositories are safe to modify**

Run:

```bash
git -C /Users/jaco/Repositories/skills status --short --branch
git -C /Users/jaco/Repositories/skills-private status --short --branch
```

Expected: the public repository is `main` with only the committed promotion design and plan ahead of `origin/main`; the private repository is clean on `main`. Stop on any unrelated working-tree change.

- [ ] **Step 2: Add the exact tested source with `apply_patch`**

Read all four private source files, then use `apply_patch` to add the same paths and complete contents under `/Users/jaco/Repositories/skills/skills/phone-a-friend`. Do not rewrite or normalize the contents.

- [ ] **Step 3: Prove the public copy is byte-identical**

Run:

```bash
diff -qr \
  /Users/jaco/Repositories/skills-private/skills/phone-a-friend \
  /Users/jaco/Repositories/skills/skills/phone-a-friend
```

Expected: exit 0 with no output.

- [ ] **Step 4: Validate the promoted skill**

Run:

```bash
uv run --with pyyaml python \
  /Users/jaco/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  /Users/jaco/Repositories/skills/skills/phone-a-friend

rg -n '[\x{2013}\x{2014}]|TO[D]O|T[B]D|PLACEHOLD[E]R' \
  /Users/jaco/Repositories/skills/skills/phone-a-friend

git -C /Users/jaco/Repositories/skills diff --check
```

Expected: validation prints `Skill is valid!`; `rg` returns no matches; `git diff --check` exits 0.

- [ ] **Step 5: Review and commit the public addition**

Run:

```bash
git -C /Users/jaco/Repositories/skills diff -- skills/phone-a-friend
git -C /Users/jaco/Repositories/skills add skills/phone-a-friend
git -C /Users/jaco/Repositories/skills commit -m "Add phone-a-friend routing skill"
```

Expected: one commit creates exactly four files.

- [ ] **Step 6: Push and verify public availability**

Run:

```bash
git -C /Users/jaco/Repositories/skills push origin main
git -C /Users/jaco/Repositories/skills fetch origin main
test "$(git -C /Users/jaco/Repositories/skills rev-parse HEAD)" = \
  "$(git -C /Users/jaco/Repositories/skills rev-parse origin/main)"
```

Expected: push succeeds and local `HEAD` equals `origin/main`.

### Task 2: Repoint and Smoke-Test the Global Installation

**Files:**
- Verify only: `/Users/jaco/Repositories/skills/skills/phone-a-friend/**`
- Generated and globally ignored: `/Users/jaco/.agents/.skill-lock.json`
- Installed copy managed by `npx skills`: `/Users/jaco/.agents/skills/phone-a-friend/**`
- Claude symlink managed by `npx skills`: `/Users/jaco/.claude/skills/phone-a-friend`

**Interfaces:**
- Consumes: the pushed public skill from Task 1.
- Produces: a global installation whose recorded source is `JacoBates/skills`, plus fresh discovery evidence.

- [ ] **Step 1: Install from the public GitHub source**

Run:

```bash
npx skills add JacoBates/skills \
  --skill phone-a-friend \
  -a claude-code \
  -a codex \
  -a opencode \
  -g \
  -y
```

Expected: installation succeeds, the canonical copy is under `~/.agents/skills/phone-a-friend`, and Claude Code receives a symlink.

- [ ] **Step 2: Verify installation identity and contents**

Run:

```bash
test "$(jq -r '.skills["phone-a-friend"].source' /Users/jaco/.agents/.skill-lock.json)" = \
  "JacoBates/skills"

diff -qr \
  /Users/jaco/Repositories/skills/skills/phone-a-friend \
  /Users/jaco/.agents/skills/phone-a-friend

test "$(readlink /Users/jaco/.claude/skills/phone-a-friend)" = \
  '../../.agents/skills/phone-a-friend'

npx skills list -g | rg 'phone-a-friend'
```

Expected: every command exits 0 and the listed skill includes Claude Code, Codex, and OpenCode.

- [ ] **Step 3: Run a fresh explicit-discovery smoke test**

Run:

```bash
opencode run \
  --pure \
  --model openai/gpt-5.6-luna \
  --variant max \
  --dir /Users/jaco/Repositories/skills \
  --format json \
  'Use $phone-a-friend to evaluate this route only. Do not launch another agent and do not edit files. The current Fable 5 agent needs a read-only summary of several megabytes of well-formed CSV data. Choose whether and how to delegate, naming model, effort, launcher, mechanism, and decisive fit.' \
  | jq -r 'select(.type == "text" and .part.metadata.openai.phase == "final_answer") | .part.text'
```

Expected: the installed skill is read and the final response selects GPT-5.6 Luna at max through OpenCode as a direct bulk-data match.

### Task 3: Retire the Private Duplicate

**Files:**
- Delete: `/Users/jaco/Repositories/skills-private/skills/phone-a-friend/SKILL.md`
- Delete: `/Users/jaco/Repositories/skills-private/skills/phone-a-friend/agents/openai.yaml`
- Delete: `/Users/jaco/Repositories/skills-private/skills/phone-a-friend/references/launchers.md`
- Delete: `/Users/jaco/Repositories/skills-private/skills/phone-a-friend/references/model-catalog.md`

**Interfaces:**
- Consumes: successful publication and installation evidence from Tasks 1 and 2.
- Produces: a single authored source in the public repository, with both repositories synchronized to their remotes.

- [ ] **Step 1: Reconfirm the public installation before deletion**

Run:

```bash
test "$(jq -r '.skills["phone-a-friend"].source' /Users/jaco/.agents/.skill-lock.json)" = \
  "JacoBates/skills"

diff -qr \
  /Users/jaco/Repositories/skills/skills/phone-a-friend \
  /Users/jaco/.agents/skills/phone-a-friend
```

Expected: both commands exit 0. If either fails, stop and retain the private source.

- [ ] **Step 2: Delete only the private skill files**

Use `apply_patch` to delete the four listed files. Do not delete private design, plan, or evaluation evidence.

- [ ] **Step 3: Verify and commit the private removal**

Run:

```bash
git -C /Users/jaco/Repositories/skills-private status --short
git -C /Users/jaco/Repositories/skills-private diff --check
git -C /Users/jaco/Repositories/skills-private diff --stat
git -C /Users/jaco/Repositories/skills-private add skills/phone-a-friend
git -C /Users/jaco/Repositories/skills-private commit -m \
  "Remove promoted phone-a-friend skill"
```

Expected: only the four private skill files are deleted and committed.

- [ ] **Step 4: Push the private removal**

Run:

```bash
git -C /Users/jaco/Repositories/skills-private push origin main
git -C /Users/jaco/Repositories/skills-private fetch origin main
test "$(git -C /Users/jaco/Repositories/skills-private rev-parse HEAD)" = \
  "$(git -C /Users/jaco/Repositories/skills-private rev-parse origin/main)"
```

Expected: push succeeds and local `HEAD` equals `origin/main`.

- [ ] **Step 5: Run final cross-repository verification**

Run:

```bash
test -d /Users/jaco/Repositories/skills/skills/phone-a-friend
test ! -e /Users/jaco/Repositories/skills-private/skills/phone-a-friend
test "$(jq -r '.skills["phone-a-friend"].source' /Users/jaco/.agents/.skill-lock.json)" = \
  "JacoBates/skills"
diff -qr \
  /Users/jaco/Repositories/skills/skills/phone-a-friend \
  /Users/jaco/.agents/skills/phone-a-friend
git -C /Users/jaco/Repositories/skills status --short --branch
git -C /Users/jaco/Repositories/skills-private status --short --branch
```

Expected: the public and installed copies exist and match, the private copy is absent, the lockfile records `JacoBates/skills`, and both repositories are clean and synchronized with `origin/main`.
