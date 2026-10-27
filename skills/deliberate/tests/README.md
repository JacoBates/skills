# deliberate evals

These replay real, previously solved requests against the skill and compare it with other arms. Case data is real user prompts, so it lives outside the repository and is passed in by path.

Every run is an isolated `opencode run --standalone` with its own `XDG_DATA_HOME`, so eval sessions stay out of the normal session list. `opencode run` takes its location from `$PWD`, not the process working directory, so the scripts set `PWD` for each run.

| Script | What it measures |
|---|---|
| `trigger_eval.py` | Whether the skill loads on labelled prompts. Every action except loading skills is denied. |
| `replay_eval.py` | A design conversation with a simulated user who may only answer from the real conversation history. Stops one capped turn after approval, when implementation starts, or at the turn limit. |
| `judge_eval.py` | Blind, shuffled scoring of replay transcripts against what actually shipped. |

Replays run in a fresh repository that holds history only up to the base commit, in the system temp directory. A worktree would share the real repository's refs, and the real checkout already contains the shipped work, so the sandbox also denies outside directories, shell commands that mention `Repositories`, Code Mode (`execute`, which can move the session), and applies the same rules to subagents. `leaks` in each result lists any tool input that referenced the real repository; check that all of them errored.

Case directory layout:

```text
<case>/
  case.json    name, repo, base_commit, prompt, earlier
  history.md   the user's real replies, verbatim
  outcome.md   what was agreed and shipped (judge only)
```

Trigger cases are a JSON array of `{sid, prompt, earlier, dir}` with a labels file of `{sid, label: YES|NO|UNCLEAR, category}`.
