"""Deterministic graders for Gate 1 utility WAVE results.json.

This scores task-success strings only. It does not attest USD 0, freshness,
or that producers were live RepoForge/Engram. CONTROL is recorded, not used
for the D vs max(B, C) lift.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "D_SHADOW")
TASKS = ("locate", "decision", "mismatch")
GOLD_PATH = (
    Path(__file__).resolve().parents[1]
    / "tests/fixtures/context_broker/gate1_utility/gold.json"
)


def _first_token(answer: str) -> str:
    stripped = answer.strip()
    if not stripped:
        return ""
    return stripped.split()[0].strip(",.;:")


def _load_gold() -> dict[str, Any]:
    payload = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("gold.json must be an object")
    return payload


def grade_answer(task: str, answer: str, arm: str) -> bool:
    spec = _load_gold().get(task, {}).get(arm)
    if not isinstance(spec, dict):
        return False
    contains = spec.get("contains")
    if isinstance(contains, str):
        return contains in answer
    expected = spec.get("first_token")
    if isinstance(expected, str):
        return _first_token(answer) == expected
    return False


def grade_results(payload: dict[str, Any]) -> dict[str, Any]:
    cells = payload.get("cells")
    if not isinstance(cells, list):
        raise ValueError("results.json cells must be a list")
    per_task: dict[str, dict[str, list[bool]]] = {
        task: {arm: [] for arm in ARMS} for task in TASKS
    }
    scored = 0
    for cell in cells:
        if not isinstance(cell, dict) or cell.get("status") != "complete":
            continue
        task = cell.get("task")
        arm = cell.get("arm")
        answer = cell.get("answer")
        if task not in TASKS or arm not in ARMS or not isinstance(answer, str):
            continue
        per_task[task][arm].append(grade_answer(task, answer, arm))
        scored += 1
    rates: dict[str, dict[str, float | None]] = {}
    wins: list[str] = []
    for task in TASKS:
        rates[task] = {}
        for arm in ARMS:
            values = per_task[task][arm]
            rates[task][arm] = (sum(values) / len(values)) if values else None
        d = rates[task]["D_SHADOW"]
        b = rates[task]["B_STRUCTURE"]
        c = rates[task]["C_MEMORY"]
        present = [x for x in (b, c) if x is not None]
        best_single = max(present) if present else None
        if d is not None and best_single is not None and d > best_single:
            wins.append(task)
    d_mean = _mean([rates[task]["D_SHADOW"] for task in TASKS])
    single_mean = _mean(
        [
            max(
                x
                for x in (rates[task]["B_STRUCTURE"], rates[task]["C_MEMORY"])
                if x is not None
            )
            for task in TASKS
            if rates[task]["B_STRUCTURE"] is not None or rates[task]["C_MEMORY"] is not None
        ]
    )
    lift = bool(d_mean is not None and single_mean is not None and d_mean > single_mean)
    return {
        "scored_cells": scored,
        "rates": rates,
        "d_beats_best_single_tasks": wins,
        "d_mean": d_mean,
        "best_single_mean": single_mean,
        "hypothesis_lift": lift,
        "utility_verdict": "continue" if lift else "stop",
        "caveat": "transport+producer answers only; billing unverified; not a broker authorization",
    }


def _mean(values: list[float | None]) -> float | None:
    present = [value for value in values if value is not None]
    if not present:
        return None
    return sum(present) / len(present)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Grade a Gate 1 utility results.json")
    parser.add_argument("results", type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.results.read_text(encoding="utf-8"))
    print(json.dumps(grade_results(payload), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
