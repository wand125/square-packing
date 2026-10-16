#!/usr/bin/env python3
"""Check the run logs of both checkers for coverage and accounting (standard library only).

Usage: python3 verify_logs.py LOGDIR
LOGDIR is the unpacked release asset logs/ (checker/full.jsonl, checker2/full.jsonl, checker2/retry/*.jsonl).

First system (checker/): every task id 0..4095 appears exactly once, every task has fails == 0, and
boxes == 2 * leaves - 1 per task (leaves = infeasible + near + closed_g + closed_f).

Second system (checker2/): the full run covers 0..65535 exactly once. Tasks with fails > 0 in the full run
(they hit the per-task time cap) must be exactly the tasks of the retry run, each retried once with fails == 0.
Per task boxes == 2 * leaves - 1 (leaves = discarded + near + closed + fails). Totals are taken over the accepted
records (full-run records with fails == 0, plus the retry records)."""
import json, sys
from pathlib import Path


def load(path):
    out = []
    for ln in Path(path).read_text().splitlines():
        if ln.strip():
            out.append(json.loads(ln))
    return out


def first(d):
    recs = load(d / "checker" / "full.jsonl")
    ids = [r["id"] for r in recs]
    assert sorted(ids) == list(range(4096)), "checker: task ids are not exactly 0..4095"
    tot = {"tasks": 0, "boxes": 0, "leaves": 0, "max_depth": 0}
    for r in recs:
        leaves = r["infeasible"] + r["near"] + r["closed_g"] + r["closed_f"]
        assert r["fails"] == 0, f"checker: task {r['id']} has fails"
        assert r["boxes"] == 2 * leaves - 1, f"checker: tree identity fails in task {r['id']}"
        tot["tasks"] += 1; tot["boxes"] += r["boxes"]; tot["leaves"] += leaves
        tot["max_depth"] = max(tot["max_depth"], r["max_depth"])
    assert tot["boxes"] == 2 * tot["leaves"] - tot["tasks"]
    return tot


def second(d):
    full = load(d / "checker2" / "full.jsonl")
    ids = [r["task"] for r in full]
    assert sorted(ids) == list(range(65536)), "checker2: full run does not cover 0..65535 exactly once"
    capped = {r["task"] for r in full if r["fails"] > 0}
    retry = []
    for f in sorted((d / "checker2" / "retry").glob("*.jsonl")):
        retry += load(f)
    rids = [r["task"] for r in retry]
    assert len(rids) == len(set(rids)), "checker2: a task was retried twice"
    assert set(rids) == capped, "checker2: retried tasks differ from the capped tasks of the full run"
    for r in full:
        if r["fails"] > 0:
            assert all(b.get("reason") == "time_limit" for b in r["fail_boxes"]), \
                f"checker2: task {r['task']} failed for a reason other than the time cap"
    accepted = [r for r in full if r["fails"] == 0] + retry
    assert sorted(r["task"] for r in accepted) == list(range(65536))
    tot = {"tasks": 0, "boxes": 0, "leaves": 0, "max_depth": 0, "capped_in_full_run": len(capped)}
    for r in accepted:
        leaves = r["discarded"] + r["near"] + r["closed"] + r["fails"]
        assert r["fails"] == 0, f"checker2: task {r['task']} has fails"
        assert r["boxes"] == 2 * leaves - 1, f"checker2: tree identity fails in task {r['task']}"
        tot["tasks"] += 1; tot["boxes"] += r["boxes"]; tot["leaves"] += leaves
        tot["max_depth"] = max(tot["max_depth"], r["max_depth"])
    assert tot["boxes"] == 2 * tot["leaves"] - tot["tasks"]
    return tot


if __name__ == "__main__":
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "logs")
    res = {"checker": first(d), "checker2": second(d), "ok": True}
    print(json.dumps(res, indent=1))
