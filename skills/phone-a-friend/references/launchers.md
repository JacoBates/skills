# Launchers

Read this file after selecting the complete model, effort, and capability route.

## Brief Safety

Write the bounded brief to a file with the normal file-editing tool. Do not interpolate brief contents into a shell command. Use the harness's existing permission policy and never add auto-approval or sandbox-bypass flags.

## OpenCode

OpenCode is the default launcher. It exposes every catalog model and an explicit per-run variant.

```bash
opencode run \
  'Complete the attached delegated brief and return its requested report.' \
  --model '<provider/model>' \
  --variant '<effort>' \
  --dir '<cwd>' \
  --format json \
  --file '<brief>'
```

Place the positional instruction before `--file`; the repeatable file option consumes following values. Use a fresh session. Do not pass `--continue` or `--session`. Keep the complete JSON event stream as evidence and extract the final text separately.

## Codex

Use Codex for a Codex-only capability, especially computer use.

```bash
codex exec \
  --model 'gpt-5.6-sol' \
  --config 'model_reasoning_effort="high"' \
  --cd '<cwd>' \
  --json \
  --output-last-message '<report>' \
  - < '<brief>'
```

For computer use, add `--enable computer_use`. Keep the JSON event stream and the final report. Use `--ephemeral` when the delegated session should not persist.

## Native Delegation

Use the current harness's native subagent tool only when it can preserve the selected model, effort, tools, permissions, fresh context, and return contract. Native convenience is not a reason to change the route.

## Failures

- Retry the same launcher once only when evidence shows a transient process or transport failure.
- Treat authentication, quota, missing model, and missing capability as availability failures and return to selection.
- Use another launcher only when it preserves model, effort, tools, and permissions.
- A Codex-only capability has no alternate launcher. Stop or narrow the task if Codex is unavailable.
