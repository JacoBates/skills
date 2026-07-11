---
name: setting-up-worktree-docker-env
description: Use when a git worktree already exists and the user wants that worktree to run its own local Docker stack alongside another checkout, using Docker Compose env overrides rather than editing tracked config.
---

# Setting Up Worktree Docker Env

## Overview

This skill sets up a per-worktree Docker environment for a repo that already supports env-driven port overrides.

**Core principle:** inspect the actual `docker-compose.yml` first, then use exported env vars and `COMPOSE_PROJECT_NAME` to isolate the stack. Do not invent services, ports, or helper files.

**Related skills** (invoke when the situation matches):

- `using-git-worktrees` — when the worktree does not exist yet.
- `verification-before-completion` — before claiming the worktree stack is ready.

## When to Use

Use this when:

- the user already has a worktree
- the user wants to run that worktree beside another checkout
- the repo uses Docker Compose for local development
- the user wants exact env vars and commands, or wants you to start the stack

Do not use this when:

- the worktree still needs to be created first
- the repo does not use Docker Compose
- the repo hardcodes ports and does not support env overrides yet

## Workflow

1. **Confirm the repo supports env-driven Docker setup.** Inspect `docker-compose.yml` and any Vite/dev-server config before proposing commands.
2. **Identify the required variables.** Only use variables that actually exist in the repo.
3. **Choose a unique project name and free host ports.** Prefer a predictable block tied to the worktree or branch name.
4. **Use exported env vars, not tracked file edits.** Do not edit `docker-compose.yml` just to switch ports.
5. **Show the exact commands.** If the user asked you to start the stack, run them. Otherwise stop at the export block and command.
6. **Verify with `docker compose config` or equivalent.** Confirm the rendered ports and project namespace match what you intended.

## Required Handoff

When the skill finishes, the final user-facing output must include a copy-pasteable shell block with the real verified values, not placeholders.

Minimum handoff shape:

```bash
export COMPOSE_PROJECT_NAME=<real-project-name>
export <REAL_PORT_VAR>=<real-port>
export <REAL_PORT_VAR>=<real-port>
docker compose config
```

If the stack was started, also include:

```bash
docker compose up
```

If useful, include the matching follow-up commands that rely on the same exported environment:

```bash
docker compose logs -f
docker compose exec <service> <shell-or-command>
docker compose down
```

Do not end with only a prose summary. The export block is required.

## Port Selection

Inspect what host ports the repo already parameterizes. Only use variables that are actually present in the repo.

Typical examples might include:

- `COMPOSE_PROJECT_NAME`
- app port variables
- dev-server or HMR port variables
- component-explorer / Storybook / Histoire port variables (e.g. `HISTOIRE_PORT`)
- local database or backing-service port variables

Choose a full non-conflicting block after inspecting every parameterized published port in the compose file. Before using a block, check whether those ports are already in use.

Allocate **every** parameterized published port the compose file exposes, not just the obvious app/dev-server ones. If the compose file publishes a component-explorer port (Histoire/Storybook), include it in the block so the worktree can run it without clashing with another checkout.

## Command Pattern

Preferred shell setup:

```bash
export COMPOSE_PROJECT_NAME=<project-worktree-name>
export APP_PORT=<free-app-port>
export VITE_PORT=<free-dev-server-port>
export HISTOIRE_PORT=<free-histoire-port>
```

Then either:

```bash
docker compose config
```

or, if the user asked to run it:

```bash
docker compose up
```

If you need one-shot commands instead of exports, use the same variables inline. Prefer exports when the user will also run `docker compose logs`, `docker compose exec`, or `docker compose down` afterward.

## Red Flags

Stop and correct course if you catch yourself doing any of these:

- inventing services or variables not present in the repo, such as `REDIS_PORT`
- assuming `.env`, `.envrc`, or helper files are required
- editing tracked Compose files just to change ports
- choosing only the app port and forgetting related ports like Vite or local backing services
- giving `docker compose up` without the matching `COMPOSE_PROJECT_NAME`
- claiming the setup is ready without rendering the final Compose config
- ending without a copy-pasteable export block containing the real values you chose

## Quick Reference

| Need | Action |
| --- | --- |
| Worktree missing | Use `using-git-worktrees` first |
| Need ports | Inspect `docker-compose.yml`, then check for free host ports |
| Need isolation | Set `COMPOSE_PROJECT_NAME` |
| Need repeatable commands | Use `export ...` in the current shell |
| Need proof | Run `docker compose config` and confirm rendered values |
