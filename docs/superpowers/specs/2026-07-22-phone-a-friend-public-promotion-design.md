# Phone a Friend Public Promotion Design

## Goal

Promote `phone-a-friend` from `JacoBates/skills-private` to `JacoBates/skills`, make the public repository its only authored source, and repoint the global installation without changing routing behavior.

## Public Content

Publish the existing skill unchanged:

- `SKILL.md` contains the routing workflow, receipt, delegation boundary, and failure recovery rules.
- `references/model-catalog.md` contains Jaco's opinionated model scores, direct routes, effort choices, and weighted fallback.
- `references/launchers.md` contains the tested OpenCode and Codex launch contracts.
- `agents/openai.yaml` contains cosmetic Codex metadata.

The catalog already identifies its scores as personal working judgments rather than benchmark claims. That is sufficient disclosure. Users who disagree with the defaults are expected to fork or modify the skill.

No project, employer, credential, or private repository detail may appear in the published skill.

## Source Ownership

`JacoBates/skills` becomes the canonical authored source. After public publication and installation verification, remove `skills/phone-a-friend` from `JacoBates/skills-private` so the copies cannot drift.

The public promotion starts with a normal add commit. Cross-repository history rewriting is unnecessary because the private design and implementation history is not part of the reusable skill artifact.

## Migration Sequence

1. Copy the complete private skill directory into the public repository.
2. Confirm the public copy is byte-identical to the tested private source.
3. Run skill validation and hygiene checks from the public repository.
4. Commit and push the public addition on `main`.
5. Install `phone-a-friend` globally from `JacoBates/skills` for OpenCode, Codex, and Claude Code.
6. Verify the installed directory matches the public source and Claude's link resolves to the canonical installed copy.
7. Run a fresh explicit-discovery smoke test against the installed skill.
8. Remove the private authored copy, commit, and push the removal on `main`.
9. Verify both repositories are clean and synchronized with their remotes.

The public addition must be pushed and globally verified before removing the private source. If publication or installation fails, retain the private source and leave the current installation intact.

## Verification

- The skill validator reports success against the public directory.
- Placeholder and non-ASCII dash scans return no matches.
- The pre-removal public and private directories compare byte-for-byte.
- The installed directory compares byte-for-byte with the public directory.
- `npx skills list -g` lists `phone-a-friend` for OpenCode, Codex, and Claude Code.
- A fresh harness session explicitly invokes `$phone-a-friend` and returns the expected route.
- Neither repository contains unintended tracked changes.

The existing no-skill baseline, 9/9 guided routing result, and real delegated CSV smoke test remain valid because the promoted skill content is unchanged.
