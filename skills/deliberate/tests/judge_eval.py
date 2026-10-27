#!/usr/bin/env python3
"""Blind-judge replay transcripts for each case against what actually shipped.

Transcripts are shuffled and relabelled per case so the judge cannot tell
which arm produced them. Scores are mapped back to arms afterwards.
"""

import argparse
import collections
import json
import os
import random
import re
import shutil
import string

from replay_eval import opencode, summarize_turn

RUBRIC = """Score every transcript in this directory. Each transcript is a coding agent working out a design with
a user before building. outcome.md is what was actually agreed and shipped; history.md is what the user said
in the original conversation. Read every file completely.

For each transcript return:
- fit (1-5): how well the design the agent reached matches the agreed and shipped outcome. 5 = same shape and
  decisions; 1 = wrong direction. A transcript that never reached a design scores at most 2.
- questions_asked: number of distinct questions put to the user.
- questions_observable: how many of those the agent could have answered itself by reading code, running
  something, or a quick prototype.
- ceremony (0-3): process the user did not ask for and the task did not need - approval gates on small steps,
  section-by-section approval, writing, committing or reviewing spec documents, announcing process. 0 = none.
- anticipated_later_issue (true/false): the design addresses something outcome.md lists as a later fix,
  divergence or rework.
- rank: 1 = the session this user would most want to have had, given their pushback in history.md (terse,
  dislikes ceremony, values real options and questions about intent). Ranks are unique within this directory.
- why: at most 25 words.

Return only JSON: {"<transcript label>": {fit, questions_asked, questions_observable, ceremony,
anticipated_later_issue, rank, why}, ...}"""
JUDGE_PERMISSIONS = {"permissions": [
    {"action": "*", "resource": "*", "effect": "deny"},
    {"action": "read", "resource": "*", "effect": "allow"},
    {"action": "glob", "resource": "*", "effect": "allow"},
]}


def prepare_blind_directory(case_dir, case, out, rng):
    runs_dir = os.path.join(out, "runs")
    runs = sorted(p for p in os.listdir(runs_dir) if p.startswith(case["name"] + "-") and p.endswith(".json"))
    judge_dir = os.path.join(out, "judge", case["name"])
    shutil.rmtree(judge_dir, ignore_errors=True)
    os.makedirs(judge_dir)
    for name in ("outcome.md", "history.md"):
        shutil.copy(os.path.join(case_dir, name), judge_dir)
    rng.shuffle(runs)
    runs_by_label = {}
    for label, run in zip(string.ascii_uppercase, runs):
        runs_by_label[label] = json.load(open(os.path.join(runs_dir, run)))
        shutil.copy(os.path.join(runs_dir, run[:-5] + ".md"), os.path.join(judge_dir, f"transcript-{label}.md"))
    return judge_dir, runs_by_label


def judge(judge_dir, out, model):
    events, _ = opencode(RUBRIC, judge_dir, JUDGE_PERMISSIONS, os.path.join(out, "xdg"), model, timeout=1800)
    match = re.search(r"\{.*\}", summarize_turn(events)["text"], re.S)
    return json.loads(match.group(0)) if match else {}


def unblind(case, runs_by_label, verdicts):
    for label, run in runs_by_label.items():
        verdict = verdicts.get(label) or verdicts.get(f"transcript-{label}") or {}
        yield dict(case=case["name"], arm=run["arm"], run=run["run"], label=label,
                   agent_turns=run["agent_turns"], tokens=run["tokens"], cost=run["cost"],
                   approved_at=run["approved_at"], stop=run["stop"], doc_writes=len(run["doc_writes"]),
                   commits=len(run["commits"]), **verdict)


def print_summary_by_arm(scores):
    by_arm = collections.defaultdict(list)
    for row in scores:
        by_arm[row["arm"]].append(row)
    for arm, rows in sorted(by_arm.items()):
        def mean(key):
            values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
            return round(sum(values) / len(values), 2) if values else None
        print(arm, dict(n=len(rows), fit=mean("fit"), rank=mean("rank"), ceremony=mean("ceremony"),
                        questions=mean("questions_asked"), observable_questions=mean("questions_observable"),
                        turns=mean("agent_turns"), tokens=mean("tokens"), cost=mean("cost"),
                        approved=sum(1 for row in rows if row["approved_at"]),
                        doc_writes=mean("doc_writes"), commits=mean("commits"),
                        anticipated=sum(1 for row in rows if row.get("anticipated_later_issue") is True)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model", default="anthropic/claude-opus-5-5#high")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    out = os.path.abspath(args.out)
    rng = random.Random(args.seed)
    scores = []
    for case_dir in args.cases:
        case = json.load(open(os.path.join(case_dir, "case.json")))
        judge_dir, runs_by_label = prepare_blind_directory(case_dir, case, out, rng)
        if runs_by_label:
            scores += unblind(case, runs_by_label, judge(judge_dir, out, args.model))
    json.dump(scores, open(os.path.join(out, "judge-scores.json"), "w"), indent=1)
    print_summary_by_arm(scores)


if __name__ == "__main__":
    main()
