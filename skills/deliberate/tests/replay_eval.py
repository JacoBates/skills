#!/usr/bin/env python3
"""Replay historical design requests against a design skill with a simulated user.

Each run checks out the case's base commit in a fresh repository, sends the
original request, and lets a simulated user answer from the real conversation
history only. The run stops one turn after the simulated user approves a
design (to observe what the skill does next), when the agent starts
implementing, or at the turn limit.

Case directories are private and live outside the repository:
  case.json   {name, repo, base_commit, prompt, earlier}
  history.md  the user's real answers, verbatim
  outcome.md  what was agreed and shipped (used by the judge, never the agent)
"""

import argparse
import concurrent.futures
import json
import os
import re
import shutil
import signal
import subprocess
import tempfile
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = {
    "baseline": {"skill": "brainstorming", "deny": ["deliberate"], "package": False},
    "candidate": {"skill": "deliberate", "deny": ["brainstorming"], "package": True},
    "none": {"skill": None, "deny": ["brainstorming", "deliberate"], "package": False},
}
EDIT_TOOLS = {"edit", "write", "patch", "apply_patch"}
DOC_PATH = re.compile(r"(^|/)(docs|\.jaco|specs?|plans?)/|\.md$", re.I)
THROWAWAY_PATH = re.compile(r"scratch|prototype|mockup|sandbox|spike|/tmp/", re.I)
SIMULATOR_RULES = """You are role-playing Jaco, a senior engineer, replying to a coding agent.
You may only use what the real Jaco said in the attached history. Rules:
- If the agent asks something the history answers, answer the way Jaco did, in his terse style.
- If the history does not cover it, reply that you have no preference and the agent should decide.
- If the agent presents a complete design or plan and asks to proceed, approve it unless it contradicts
  a decision in the history; if it does, say what is wrong in one or two sentences, as Jaco would.
- If the agent asks to write, commit or review a spec or plan document, answer as Jaco did in the
  history; if the history says nothing, say "no need, just keep it in chat".
- Never reveal or invent requirements beyond the history. Never mention this role-play.
Return only JSON: {"reply": "<your message>", "status": "continue" | "approved"}
Use "approved" only when your reply approves a presented design or plan."""


def isolated_env(cwd, data_home, config):
    """opencode run takes its location from $PWD, not the process working directory."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("OPENCODE_")}
    return dict(env, PWD=cwd, XDG_DATA_HOME=data_home, OPENCODE_CONFIG_CONTENT=json.dumps(config))


def opencode(message, cwd, config, data_home, model, session=None, timeout=900):
    env = isolated_env(cwd, data_home, config)
    command = ["opencode", "run", "--standalone", "--model", model, "--format", "json"]
    if session:
        command += ["--session", session]
    started = time.time()
    process = subprocess.Popen(command + [message], cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL, text=True, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        output, _ = process.communicate()
    events = []
    for line in output.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return events, time.time() - started


def summarize_turn(events):
    texts, tools, tokens, cost, session = [], [], 0, 0.0, None
    for event in events:
        session = session or event.get("sessionID")
        part = event.get("part") or {}
        if event.get("type") == "text":
            texts.append(part.get("text", ""))
        elif part.get("type") == "tool":
            state = part.get("state") or {}
            tools.append(dict(tool=part.get("tool"), input=state.get("input") or {}, status=state.get("status")))
        elif event.get("type") == "step_finish":
            usage = part.get("tokens") or {}
            tokens += usage.get("input", 0) + usage.get("output", 0) + (usage.get("cache") or {}).get("read", 0)
            tokens += (usage.get("cache") or {}).get("write", 0)
            cost += part.get("cost") or 0
    return dict(text="\n\n".join(texts), tools=tools, tokens=tokens, cost=cost, session=session)


def edited_paths(tools):
    paths = []
    for tool in tools:
        if tool["tool"] in EDIT_TOOLS:
            paths.append(tool["input"].get("filePath") or tool["input"].get("path") or json.dumps(tool["input"])[:120])
    return paths


def simulate_user(case_dir, transcript, args):
    history = open(os.path.join(case_dir, "history.md")).read()
    recent = "\n\n".join(f"{who.upper()}:\n{text}" for who, text in transcript[-4:])
    message = f"{SIMULATOR_RULES}\n\n# History (the real Jaco)\n\n{history}\n\n# Conversation so far (most recent last)\n\n{recent}"
    config = {"permissions": [{"action": "*", "resource": "*", "effect": "deny"}]}
    events, _ = opencode(message, args.scratch, config, args.data_home, args.model, timeout=300)
    text = summarize_turn(events)["text"]
    match = re.search(r"\{.*\}", text, re.S)
    try:
        parsed = json.loads(match.group(0)) if match else {}
    except ValueError:
        parsed = {}
    return parsed.get("reply") or "No preference, your call.", parsed.get("status", "continue")


def checkout_base(case, parent):
    """Fresh repository holding history only up to the base commit.

    A worktree would share the real repository's refs, and `git log --all` would show the shipped work.
    """
    checkout = os.path.join(parent, os.path.basename(case["repo"].rstrip("/")))
    commit = subprocess.run(["git", "-C", case["repo"], "rev-parse", case["base_commit"]],
                            check=True, capture_output=True, text=True).stdout.strip()
    os.makedirs(checkout)
    for command in (["init", "-q"], ["fetch", "-q", "--no-tags", case["repo"], commit],
                    ["checkout", "-q", "-b", "main", "FETCH_HEAD"]):
        subprocess.run(["git", "-C", checkout] + command, check=True, capture_output=True)
    return checkout


def sandbox_config(arm, package_dir, deny_skills=None):
    """Keep the run inside its checkout, including subagents, which carry their own permissions.

    The real checkout already contains the shipped work, so any read of it leaks the answer.
    """
    rules = [
        {"action": "*", "resource": "*", "effect": "allow"},
        {"action": "question", "resource": "*", "effect": "deny"},
        {"action": "execute", "resource": "*", "effect": "deny"},
        {"action": "external_directory", "resource": "*", "effect": "deny"},
        {"action": "external_directory", "resource": os.path.expanduser("~/.agents/skills/*"), "effect": "allow"},
        {"action": "shell", "resource": "*Repositories*", "effect": "deny"},
        {"action": "shell", "resource": "git push *", "effect": "deny"},
        {"action": "shell", "resource": "gh *", "effect": "deny"},
        {"action": "shell", "resource": "docker *", "effect": "deny"},
        {"action": "shell", "resource": "opencode *", "effect": "deny"},
        {"action": "clickup_*", "resource": "*", "effect": "deny"},
    ]
    if package_dir:
        rules.append({"action": "external_directory", "resource": package_dir + "/*", "effect": "allow"})
    denied = ARMS[arm]["deny"] if deny_skills is None else deny_skills
    rules += [{"action": "skill", "resource": skill, "effect": "deny"} for skill in denied]
    subagent_rules = [rule for rule in rules[1:] if rule["action"] != "question"]
    config = {
        "permissions": rules,
        "agents": {name: {"permissions": subagent_rules} for name in ("explore", "general")},
    }
    if package_dir:
        config["skills"] = [package_dir]
    return config


def leaked_paths(turns, repo):
    return [
        json.dumps(tool["input"])[:200]
        for turn in turns for tool in turn["tools"]
        if repo.rstrip("/") in json.dumps(tool["input"])
    ]


def first_message(case, arm):
    message = case["prompt"]
    earlier = [text[:1500] for text in (case.get("earlier") or [])[-3:]]
    if earlier:
        quoted = "\n\n".join("> " + text.replace("\n", "\n> ") for text in earlier)
        message = f"Earlier in this conversation I said:\n\n{quoted}\n\nNow:\n\n{message}"
    skill = ARMS[arm]["skill"]
    return f"{message}\n\n(Use the {skill} skill.)" if skill else message


def replay(case_dir, arm, repetition, args, package_dir):
    case = json.load(open(os.path.join(case_dir, "case.json")))
    run_id = f"{case['name']}-{arm}-{repetition}"
    result_path = os.path.join(args.out, "runs", f"{run_id}.json")
    if os.path.exists(result_path):
        return result_path
    checkout = checkout_base(case, os.path.join(args.checkouts, run_id))
    config = sandbox_config(arm, package_dir)

    transcript, turns, session, approved_at, stop = [], [], None, None, "turn-limit"
    message = first_message(case, arm)
    try:
        for turn_number in range(1, args.max_turns + 1):
            timeout = args.post_approval_timeout if approved_at is not None else 900
            events, seconds = opencode(message, checkout, config, args.data_home, args.model, session=session,
                                       timeout=timeout)
            turn = summarize_turn(events)
            session = session or turn["session"]
            turn.update(number=turn_number, seconds=round(seconds, 1), user=message, edits=edited_paths(turn["tools"]))
            turns.append(turn)
            transcript += [("user", message), ("agent", turn["text"])]
            code_edits = [path for path in turn["edits"] if not DOC_PATH.search(path) and not THROWAWAY_PATH.search(path)]
            if approved_at is not None:
                stop = "post-approval-turn-observed"
                break
            if code_edits:
                stop = "implementation-started"
                break
            if not turn["text"].strip():
                message, status = "Continue.", "continue"
            else:
                message, status = simulate_user(case_dir, transcript, args)
            if status == "approved":
                approved_at = turn_number
    finally:
        status = subprocess.run(["git", "-C", checkout, "status", "--porcelain"], capture_output=True, text=True).stdout
        commits = subprocess.run(["git", "-C", checkout, "log", "--oneline", f"{case['base_commit']}..HEAD"],
                                 capture_output=True, text=True).stdout
        shutil.rmtree(os.path.dirname(checkout), ignore_errors=True)

    result = dict(
        run=run_id, case=case["name"], arm=arm, repetition=repetition, stop=stop, approved_at=approved_at,
        agent_turns=len(turns), tokens=sum(t["tokens"] for t in turns), cost=round(sum(t["cost"] for t in turns), 3),
        seconds=round(sum(t["seconds"] for t in turns)), skills=[t["input"].get("id") for turn in turns
                                                                for t in turn["tools"] if t["tool"] == "skill"],
        doc_writes=[p for turn in turns for p in turn["edits"] if DOC_PATH.search(p)],
        code_writes=[p for turn in turns for p in turn["edits"] if not DOC_PATH.search(p) and not THROWAWAY_PATH.search(p)],
        throwaway_writes=[p for turn in turns for p in turn["edits"] if THROWAWAY_PATH.search(p)],
        reads=sum(1 for turn in turns for t in turn["tools"] if t["tool"] in {"read", "grep", "glob"}),
        commits=commits.splitlines(), uncommitted=status.splitlines(), leaks=leaked_paths(turns, case["repo"]),
        turns=turns,
    )
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    json.dump(result, open(result_path, "w"), indent=1)
    with open(os.path.join(args.out, "runs", f"{run_id}.md"), "w") as handle:
        for turn in turns:
            handle.write(f"## Turn {turn['number']}\n\n### User\n\n{turn['user']}\n\n### Agent\n\n{turn['text']}\n\n")
            if turn["edits"]:
                handle.write("Files written: " + ", ".join(turn["edits"]) + "\n\n")
    return result_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="+", required=True, help="case directories")
    parser.add_argument("--out", required=True)
    parser.add_argument("--arm", choices=sorted(ARMS), action="append", required=True)
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--post-approval-timeout", type=int, default=240,
                        help="seconds to observe the turn after approval; enough to see spec, plan or build")
    parser.add_argument("--concurrency", type=int, default=3)
    parser.add_argument("--model", default="anthropic/claude-opus-5-5#high")
    args = parser.parse_args()
    args.out = os.path.abspath(args.out)
    args.data_home = os.path.join(args.out, "xdg")
    args.checkouts = os.path.join(tempfile.gettempdir(), "deliberate-replays")
    args.scratch = os.path.join(args.out, "scratch")
    for path in (args.checkouts, args.scratch):
        os.makedirs(path, exist_ok=True)

    package_dir = None
    if "candidate" in args.arm:
        package_dir = tempfile.mkdtemp(prefix="deliberate-pkg-")
        shutil.copytree(SKILL_DIR, os.path.join(package_dir, "deliberate"), ignore=shutil.ignore_patterns("tests"))
    jobs = [(case, arm, rep) for case in args.cases for arm in args.arm for rep in range(1, args.reps + 1)]
    with concurrent.futures.ThreadPoolExecutor(args.concurrency) as pool:
        futures = {pool.submit(replay, case, arm, rep, args, package_dir): (case, arm, rep) for case, arm, rep in jobs}
        for future in concurrent.futures.as_completed(futures):
            case, arm, rep = futures[future]
            try:
                print("done", future.result(), flush=True)
            except Exception as error:
                print("FAILED", os.path.basename(case), arm, rep, repr(error), flush=True)


if __name__ == "__main__":
    main()
