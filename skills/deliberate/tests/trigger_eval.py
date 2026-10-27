#!/usr/bin/env python3
"""Replay labelled historical prompts and measure whether a design skill loads.

Each run is an isolated `opencode run --standalone` with every action denied
except loading skills, so a run can only answer or load skills. Runs use their
own XDG data directory so eval sessions stay out of the user's session list.

Cases are private (real prompts), so they live outside the repository and are
passed in by path. Case file: JSON array of
  {sid, prompt, earlier?: [str], dir}
Labels file: JSON array of {sid, label: YES|NO|UNCLEAR, category}.
"""

import argparse
import collections
import concurrent.futures
import json
import os
import random
import re
import shutil
import subprocess
import tempfile

from replay_eval import isolated_env

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD_SKILL_REFERENCE = re.compile(r"brainstorm|superpowers", re.I)
ARMS = {
    "baseline": {"skill": "brainstorming", "deny": [], "package": False},
    "candidate": {"skill": "deliberate", "deny": ["brainstorming"], "package": True},
}


def existing_ancestor(path):
    while path and not os.path.isdir(path):
        path = os.path.dirname(path)
    return path or os.path.expanduser("~")


def build_message(case):
    earlier = [text[:1500] for text in (case.get("earlier") or [])[-3:]]
    if not earlier:
        return case["prompt"]
    quoted = "\n\n".join("> " + text.replace("\n", "\n> ") for text in earlier)
    return f"Earlier in this conversation I said:\n\n{quoted}\n\nNow:\n\n{case['prompt']}"


def select_cases(cases, labels, negatives, seed):
    eligible = []
    for case in cases:
        label = labels.get(case["sid"])
        if not label or label["label"] == "UNCLEAR":
            continue
        context = case["prompt"] + " ".join((case.get("earlier") or [])[-3:])
        if OLD_SKILL_REFERENCE.search(context):
            continue
        eligible.append(dict(case, expected=label["label"], category=label["category"]))

    positives = [case for case in eligible if case["expected"] == "YES"]
    by_category = collections.defaultdict(list)
    for case in eligible:
        if case["expected"] == "NO":
            by_category[case["category"]].append(case)
    total_no = sum(len(group) for group in by_category.values())
    rng = random.Random(seed)
    picked = []
    for group in by_category.values():
        quota = max(1, round(negatives * len(group) / total_no))
        picked += rng.sample(group, min(quota, len(group)))
    return positives + picked


def run_case(case, repetition, arm, args, package_dir):
    out_path = os.path.join(args.out, arm, f"{case['sid']}-{repetition}.jsonl")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
        return out_path
    permissions = [
        {"action": "*", "resource": "*", "effect": "deny"},
        {"action": "skill", "resource": "*", "effect": "allow"},
    ] + [{"action": "skill", "resource": skill, "effect": "deny"} for skill in ARMS[arm]["deny"]]
    config = {"permissions": permissions}
    if package_dir:
        config["skills"] = [package_dir]
    cwd = existing_ancestor(case["dir"])
    env = isolated_env(cwd, args.data_home, config)
    command = ["opencode", "run", "--standalone", "--model", args.model, "--format", "json", build_message(case)]
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, timeout=args.timeout)
        output = result.stdout
    except subprocess.TimeoutExpired as error:
        output = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as handle:
        handle.write(output)
    return out_path


def skills_loaded(path):
    loaded = []
    with open(path) as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except ValueError:
                continue
            part = event.get("part") or {}
            if part.get("type") == "tool" and part.get("tool") == "skill":
                loaded.append(((part.get("state") or {}).get("input") or {}).get("id"))
    return loaded


def score(cases, arm, args):
    target = ARMS[arm]["skill"]
    rows = []
    for case in cases:
        for repetition in range(1, args.reps + 1):
            path = os.path.join(args.out, arm, f"{case['sid']}-{repetition}.jsonl")
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                rows.append(dict(sid=case["sid"], expected=case["expected"], category=case["category"], loaded=None))
                continue
            loaded = skills_loaded(path)
            rows.append(
                dict(sid=case["sid"], expected=case["expected"], category=case["category"], loaded=target in loaded, skills=loaded)
            )
    valid = [row for row in rows if row["loaded"] is not None]
    positives = [row for row in valid if row["expected"] == "YES"]
    negatives = [row for row in valid if row["expected"] == "NO"]
    true_positive = sum(row["loaded"] for row in positives)
    false_positive = sum(row["loaded"] for row in negatives)
    summary = {
        "arm": arm,
        "runs": len(rows),
        "failed_runs": len(rows) - len(valid),
        "recall": f"{true_positive}/{len(positives)}",
        "false_positive_rate": f"{false_positive}/{len(negatives)}",
        "false_positives_by_category": collections.Counter(row["category"] for row in negatives if row["loaded"]),
        "missed": sorted({row["sid"] for row in positives if not row["loaded"]}),
        "false_positive_sids": sorted({row["sid"] for row in negatives if row["loaded"]}),
    }
    with open(os.path.join(args.out, f"score-{arm}.json"), "w") as handle:
        json.dump(dict(summary=summary, rows=rows), handle, indent=1, default=dict)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="+", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--arm", choices=sorted(ARMS), action="append", required=True)
    parser.add_argument("--reps", type=int, default=2)
    parser.add_argument("--negatives", type=int, default=60)
    parser.add_argument("--seed", type=int, default=20261027)
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--model", default="anthropic/claude-opus-5-5#high")
    parser.add_argument("--score-only", action="store_true")
    args = parser.parse_args()
    args.out = os.path.abspath(args.out)
    args.data_home = os.path.join(args.out, "xdg")

    cases = [case for path in args.cases for case in json.load(open(path))]
    labels = {label["sid"]: label for label in json.load(open(args.labels))}
    selected = select_cases(cases, labels, args.negatives, args.seed)
    print(f"{len(selected)} cases: {collections.Counter(case['expected'] for case in selected)}")

    for arm in args.arm:
        package_dir = None
        if ARMS[arm]["package"] and not args.score_only:
            package_dir = tempfile.mkdtemp(prefix="deliberate-pkg-")
            shutil.copytree(SKILL_DIR, os.path.join(package_dir, "deliberate"), ignore=shutil.ignore_patterns("tests"))
        if not args.score_only:
            jobs = [(case, repetition) for case in selected for repetition in range(1, args.reps + 1)]
            with concurrent.futures.ThreadPoolExecutor(args.concurrency) as pool:
                futures = [pool.submit(run_case, case, rep, arm, args, package_dir) for case, rep in jobs]
                for done, future in enumerate(concurrent.futures.as_completed(futures), 1):
                    future.result()
                    if done % 20 == 0:
                        print(f"{arm}: {done}/{len(jobs)}", flush=True)
        print(json.dumps(score(selected, arm, args), indent=1, default=dict))


if __name__ == "__main__":
    main()
