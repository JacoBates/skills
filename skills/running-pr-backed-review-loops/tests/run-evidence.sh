#!/usr/bin/env bash

set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
skill_name="running-pr-backed-review-loops"
test_dir="$repo_root/skills/$skill_name/tests"
evidence_dir="$repo_root/.jaco/pr-backed-review-loop-tests"
model="${MODEL:-openai/gpt-5.6-sol}"
variant="${VARIANT:-high}"
suite="${1:-all}"
work_dir=$(cd "$(mktemp -d)" && pwd -P)
package_dir="$work_dir/package/skills"

trap 'rm -rf "$work_dir"' EXIT

mkdir -p "$evidence_dir" "$work_dir/fixtures" \
  "$package_dir/$skill_name" \
  "$package_dir/review-loop" \
  "$package_dir/receiving-code-review"
cp "$repo_root/skills/$skill_name/SKILL.md" "$package_dir/$skill_name/SKILL.md"
cp "$HOME/.agents/skills/review-loop/SKILL.md" "$package_dir/review-loop/SKILL.md"
cp "$HOME/.agents/skills/receiving-code-review/SKILL.md" \
  "$package_dir/receiving-code-review/SKILL.md"

harness_config=$(jq -cn --arg skill_path "$package_dir" '{
  skills: {paths: [$skill_path]},
  permission: {
    read: "deny",
    edit: "deny",
    glob: "deny",
    grep: "deny",
    list: "deny",
    bash: "deny",
    task: "deny",
    webfetch: "deny",
    websearch: "deny",
    external_directory: "deny",
    skill: "allow"
  }
}')

scorer_config=$(jq -cn '{
  permission: {
    read: "allow",
    edit: "deny",
    glob: "deny",
    grep: "deny",
    list: "deny",
    bash: "deny",
    task: "deny",
    todowrite: "deny",
    question: "deny",
    webfetch: "deny",
    websearch: "deny",
    lsp: "deny",
    doom_loop: "deny",
    external_directory: "deny",
    skill: "deny"
  }
}')

run_session() {
  local export_name=$1
  local prompt=$2
  local attachment=${3:-}
  local events
  local session_id
  local export_path="$evidence_dir/$export_name.json"
  local temporary_export="$evidence_dir/.$export_name.json.tmp"

  if [[ -n "$attachment" ]]; then
    events=$(OPENCODE_DISABLE_EXTERNAL_SKILLS=1 \
      OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
      OPENCODE_CONFIG_CONTENT="$harness_config" \
      opencode run "$prompt" --pure --dir "$work_dir" \
      --model "$model" --variant "$variant" --format json \
      --file="$attachment")
  else
    events=$(OPENCODE_DISABLE_EXTERNAL_SKILLS=1 \
      OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
      OPENCODE_CONFIG_CONTENT="$harness_config" \
      opencode run "$prompt" --pure --dir "$work_dir" \
      --model "$model" --variant "$variant" --format json)
  fi

  session_id=$(jq -rs 'map(select(.type == "step_start"))[0].sessionID' <<< "$events")
  [[ "$session_id" == ses_* ]]
  opencode export "$session_id" > "$temporary_export"
  jq -e . "$temporary_export" >/dev/null
  mv "$temporary_export" "$export_path"
}

skill_loaded() {
  jq -e --arg skill_name "$skill_name" '
    any(
      .messages[]
      | select(.info.role == "assistant")
      | .parts[]
      | select(.type == "tool");
      (.tool == "skill" and .state.input.name == $skill_name)
      or (
        .tool != "skill"
        and ((.state.input | tostring) | contains($skill_name) or contains("SKILL.md"))
      )
    )
  ' "$1" >/dev/null
}

assert_no_protected_access() {
  jq -e --arg repo_root "$repo_root" '
    all(
      .messages[]
      | select(.info.role == "assistant")
      | .parts[]
      | select(.type == "tool");
      ((.state.input | tostring) | contains($repo_root) | not)
    )
  ' "$1" >/dev/null
}

assert_scorer_tools() {
  local export_path=$1
  local score_dir=$2

  jq -e --arg score_dir "$score_dir/" '
    all(
      .messages[]
      | select(.info.role == "assistant")
      | .parts[]
      | select(.type == "tool");
      .tool == "read"
      and (
        (
          .state.status == "completed"
          and (
            (.state.input.filePath // "") == ($score_dir | rtrimstr("/"))
            or ((.state.input.filePath // "") | startswith($score_dir))
          )
          and (((.state.input.filePath // "") | split("/") | index("..")) == null)
        )
        or .state.status == "error"
      )
    )
  ' "$export_path" >/dev/null
}

score_suite() {
  local export_name=$1
  local prompt=$2
  shift 2
  local attachments=()
  local attachment
  local events
  local session_id
  local temporary_export="$evidence_dir/.$export_name.json.tmp"
  local score_dir="$work_dir/scoring/$export_name"
  local score_attachment

  mkdir -p "$score_dir"
  for attachment in "$@"; do
    if [[ "$attachment" == *.json ]]; then
      score_attachment="$score_dir/$(basename "${attachment%.json}").txt"
      jq -r '
        "Session: \(.info.id)",
        "Model: \(.info.model.providerID)/\(.info.model.id)",
        "",
        "Assistant text:",
        (.messages[]
          | select(.info.role == "assistant")
          | .parts[]
          | select(.type == "text")
          | .text),
        "",
        "Tool calls:",
        (.messages[]
          | select(.info.role == "assistant")
          | .parts[]
          | select(.type == "tool")
          | [.tool, .state.status, (.state.input | tojson)]
          | @tsv)
      ' "$attachment" | fold -s -w 160 > "$score_attachment"
    else
      score_attachment="$score_dir/$(basename "$attachment")"
      cp "$attachment" "$score_attachment"
    fi
    attachments+=(--file="$score_attachment")
  done

  events=$(OPENCODE_DISABLE_EXTERNAL_SKILLS=1 \
    OPENCODE_DISABLE_CLAUDE_CODE_SKILLS=1 \
    OPENCODE_CONFIG_CONTENT="$scorer_config" \
    opencode run "$prompt Use Read to inspect every attached file completely; previews may be truncated." \
    --pure --dir "$score_dir" \
    --model "$model" --variant "$variant" --format json \
    "${attachments[@]}")
  session_id=$(jq -rs 'map(select(.type == "step_start"))[0].sessionID' <<< "$events")
  [[ "$session_id" == ses_* ]]
  opencode export "$session_id" > "$temporary_export"
  jq -e . "$temporary_export" >/dev/null
  assert_scorer_tools "$temporary_export" "$score_dir"
  mv "$temporary_export" "$evidence_dir/$export_name.json"
}

run_guided() {
  local fixture="$work_dir/fixtures/descriptive-scenario.md"
  local exports=()
  local repetition
  local export_path
  local process_id
  local process_ids=()

  cp "$test_dir/descriptive-loop-scenario.md" "$fixture"
  for repetition in {1..5}; do
    run_session "final-green-run-$repetition" \
      "Execute the attached active-work scenario. Invoke the production skill if its trigger matches. Do not inspect any file beyond the attached scenario and content returned by an invoked skill. Return exact actions and subagent boundaries, not general advice." \
      "$fixture" &
    process_ids+=("$!")
  done
  for process_id in "${process_ids[@]}"; do
    wait "$process_id"
  done
  for repetition in {1..5}; do
    export_path="$evidence_dir/final-green-run-$repetition.json"
    skill_loaded "$export_path"
    assert_no_protected_access "$export_path"
    exports+=("$export_path")
  done

  score_suite "final-green-score" \
    "Score every attached run against the attached rubric literally. Use complete assistant text. Return provenance, quoted evidence for every item and run, totals, failed item numbers, and PASS or FAIL." \
    "$test_dir/scoring-rubric.md" "${exports[@]}"
}

run_recovery() {
  local fixture="$work_dir/fixtures/recovery-scenario.md"
  local exports=()
  local repetition
  local export_path
  local process_id
  local process_ids=()

  cp "$test_dir/recovery-scenario.md" "$fixture"
  for repetition in {1..5}; do
    run_session "final-recovery-run-$repetition" \
      "Recover the attached active-work state. Invoke the production skill if its trigger matches. Do not inspect any file beyond the attached scenario and content returned by an invoked skill. State exact next actions and the iteration-four outcome." \
      "$fixture" &
    process_ids+=("$!")
  done
  for process_id in "${process_ids[@]}"; do
    wait "$process_id"
  done
  for repetition in {1..5}; do
    export_path="$evidence_dir/final-recovery-run-$repetition.json"
    skill_loaded "$export_path"
    assert_no_protected_access "$export_path"
    exports+=("$export_path")
  done

  score_suite "final-recovery-score" \
    "Score every attached run against the attached recovery rubric literally. Use complete assistant text. Return provenance, quoted evidence for every item and run, totals, failed item numbers, and PASS or FAIL." \
    "$test_dir/recovery-rubric.md" "${exports[@]}"
}

run_authority() {
  local exports=()
  local case_number
  local repetition
  local source_fixture
  local neutral_fixture
  local export_path
  local process_id
  local process_ids=()

  for case_number in {1..4}; do
    source_fixture=$(printf '%s\n' "$test_dir"/authority-case-"$case_number"-*.md)
    neutral_fixture="$work_dir/fixtures/authority-$case_number.md"
    cp "$source_fixture" "$neutral_fixture"
    process_ids=()
    for repetition in {1..5}; do
      run_session "final-authority-case-$case_number-run-$repetition" \
        "Load and apply running-pr-backed-review-loops to the attached behavior case. Do not inspect any file beyond the attached case and content returned by the skill. Return only the exact next action and required publication checks." \
        "$neutral_fixture" &
      process_ids+=("$!")
    done
    for process_id in "${process_ids[@]}"; do
      wait "$process_id"
    done
    for repetition in {1..5}; do
      export_path="$evidence_dir/final-authority-case-$case_number-run-$repetition.json"
      skill_loaded "$export_path"
      assert_no_protected_access "$export_path"
      exports+=("$export_path")
    done
  done

  if [[ "${1:-score}" == score ]]; then
    score_suite "final-authority-score" \
      "Score the attached independent authority runs against the attached rubric. Apply only each case's listed items. Use complete assistant text. Return provenance, quoted evidence, total applicable checks, failures, and PASS or FAIL." \
      "$test_dir/authority-rubric.md" "${exports[@]}"
  fi
}

score_existing_authority() {
  local exports=()
  local case_number
  local repetition
  local export_path

  for case_number in {1..4}; do
    for repetition in {1..5}; do
      export_path="$evidence_dir/final-authority-case-$case_number-run-$repetition.json"
      jq -e . "$export_path" >/dev/null
      jq -e --arg model "$model" \
        '(.info.model.providerID + "/" + .info.model.id) == $model' \
        "$export_path" >/dev/null
      jq -e --rawfile skill "$repo_root/skills/$skill_name/SKILL.md" '
        ($skill | split("---\n")[2] | ltrimstr("\n") | rtrimstr("\n")) as $body
        |
        [
          .messages[]
          | select(.info.role == "assistant")
          | .parts[]
          | select(
              .type == "tool"
              and .tool == "skill"
              and .state.input.name == "running-pr-backed-review-loops"
              and ((.state.output // "") | contains($body))
            )
        ]
        | any
      ' "$export_path" >/dev/null
      skill_loaded "$export_path"
      assert_no_protected_access "$export_path"
      exports+=("$export_path")
    done
  done

  score_suite "final-authority-score" \
    "Score the attached independent authority runs against the attached rubric. Apply only each case's listed items. Use complete assistant text. Return provenance, quoted evidence, total applicable checks, failures, and PASS or FAIL." \
    "$test_dir/authority-rubric.md" "${exports[@]}"
}

run_trigger_group() {
  local label=$1
  local expected=$2
  shift 2
  local prompts=("$@")
  local prompt_number=0
  local repetition
  local export_name
  local export_path
  local prompt
  local process_id
  local process_ids=()

  for prompt in "${prompts[@]}"; do
    prompt_number=$((prompt_number + 1))
    process_ids=()
    for repetition in {1..5}; do
      export_name="final-trigger-$label-$prompt_number-run-$repetition"
      run_session "$export_name" "$prompt" &
      process_ids+=("$!")
    done
    for process_id in "${process_ids[@]}"; do
      wait "$process_id"
    done
    for repetition in {1..5}; do
      export_name="final-trigger-$label-$prompt_number-run-$repetition"
      export_path="$evidence_dir/$export_name.json"
      if [[ "$expected" == loaded ]]; then
        skill_loaded "$export_path"
      elif skill_loaded "$export_path"; then
        return 1
      fi
    done
  done
}

run_trigger() {
  local positive_prompts=(
    "Execute the PR-backed review loop for identified unresolved descriptive artifacts that claim already-present changes on a GitHub PR. Do not inspect repository source or test files."
    "Continue an existing GitHub PR loop for identified unresolved comments that describe problems and solutions already present. Do not inspect repository source or test files."
    "Recover an interrupted PR-backed loop for identified unresolved descriptive change claims whose solutions are already in the PR. Do not inspect repository source or test files."
    "Run fresh iterations over identified unresolved artifacts that each claim a problem and an implemented solution already in the branch. Do not inspect repository source or test files."
    "Resume a GitHub PR loop for identified unresolved revision markers and descriptive comments claiming existing code changes. Do not inspect repository source or test files."
  )
  local negative_prompts=(
    "Explain the PR-backed descriptive review-loop workflow without executing, continuing, or recovering it. Do not inspect repository source, skill, or test files."
    "Perform an ordinary GitHub pull request review for bugs and missing tests. Do not inspect repository source, skill, or test files; state what inputs you need."
    "Run a loop over requests for future changes, not changes already present. Do not inspect repository source, skill, or test files."
    "Summarize qualifying descriptive comments without running their loop. Do not inspect repository source, skill, or test files."
    "Run a local fresh-review loop with no GitHub PR or descriptive artifacts. Do not inspect repository source, skill, or test files."
    "Decide whether an unapproved public reply batch may be posted when no publication authority exists. Answer the policy question only; do not execute a PR review loop or inspect skill files."
  )

  run_trigger_group positive loaded "${positive_prompts[@]}"
  run_trigger_group negative not-loaded "${negative_prompts[@]}"
}

case "$suite" in
  all)
    run_guided
    run_recovery
    run_authority
    run_trigger
    ;;
  guided) run_guided ;;
  recovery) run_recovery ;;
  authority) run_authority ;;
  authority-behavior) run_authority no-score ;;
  authority-score) score_existing_authority ;;
  trigger) run_trigger ;;
  *)
    printf 'Usage: %s [all|guided|recovery|authority|authority-behavior|authority-score|trigger]\n' "$0" >&2
    exit 2
    ;;
esac
