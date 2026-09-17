"""Deterministic Gate 1 utility graders. No live models."""

from __future__ import annotations

import json
from pathlib import Path

from md_evals.gate1_utility_grade import grade_answer, grade_results, main

GOLD_PATH = (
    Path(__file__).resolve().parent
    / "fixtures/context_broker/gate1_utility/gold.json"
)
ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "D_SHADOW")


def test_gold_fixture_exists_before_producers():
    assert GOLD_PATH.is_file()
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    assert set(gold) == {"locate", "decision", "mismatch"}
    for task in gold:
        assert tuple(gold[task]) == ARMS


def test_locate_each_arm_gold():
    assert grade_answer("locate", "src/consumer.ts", "CONTROL") is True
    assert grade_answer("locate", "src/consumer.ts", "B_STRUCTURE") is True
    assert grade_answer("locate", "src/consumer.ts", "C_MEMORY") is True
    assert grade_answer("locate", "src/consumer.ts", "D_SHADOW") is True
    assert grade_answer("locate", "src/base.ts", "B_STRUCTURE") is False
    assert grade_answer("locate", "I mapped the workspace", "C_MEMORY") is False


def test_decision_each_arm_gold():
    title = "consumer must import VALUE from base"
    assert grade_answer("decision", "NONE", "CONTROL") is True
    assert grade_answer("decision", "NONE", "B_STRUCTURE") is True
    assert grade_answer("decision", title, "C_MEMORY") is True
    assert grade_answer("decision", title, "D_SHADOW") is True
    assert grade_answer("decision", title, "CONTROL") is False
    assert grade_answer("decision", "NONE", "C_MEMORY") is False


def test_mismatch_each_arm_gold():
    assert grade_answer("mismatch", "NO_CONFLICT", "CONTROL") is True
    assert grade_answer("mismatch", "NO_CONFLICT", "B_STRUCTURE") is True
    assert grade_answer("mismatch", "UNKNOWN", "C_MEMORY") is True
    assert grade_answer("mismatch", "CONFLICT", "D_SHADOW") is True
    assert grade_answer("mismatch", "CONFLICT", "B_STRUCTURE") is False
    assert grade_answer("mismatch", "NO_CONFLICT", "C_MEMORY") is False
    assert grade_answer("mismatch", "UNKNOWN", "D_SHADOW") is False


def test_lift_d_beats_max_bc_on_mismatch_while_locate_b_equals_d(tmp_path, capsys):
    payload = {
        "status": "complete",
        "cells": [
            _cell("locate", "B_STRUCTURE", "src/consumer.ts"),
            _cell("locate", "C_MEMORY", "nope"),
            _cell("locate", "D_SHADOW", "src/consumer.ts"),
            _cell("decision", "B_STRUCTURE", "NONE"),
            _cell("decision", "C_MEMORY", "consumer must import VALUE from base"),
            _cell("decision", "D_SHADOW", "consumer must import VALUE from base"),
            _cell("mismatch", "B_STRUCTURE", "CONFLICT"),
            _cell("mismatch", "C_MEMORY", "CONFLICT"),
            _cell("mismatch", "D_SHADOW", "CONFLICT"),
        ],
    }
    result = grade_results(payload)
    assert result["rates"]["locate"]["B_STRUCTURE"] == result["rates"]["locate"]["D_SHADOW"]
    assert "mismatch" in result["d_beats_best_single_tasks"]
    assert "locate" not in result["d_beats_best_single_tasks"]
    assert result["hypothesis_lift"] is True
    assert result["utility_verdict"] == "continue"
    path = tmp_path / "results.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert main([str(path)]) == 0
    assert "continue" in capsys.readouterr().out


def test_stop_when_d_does_not_beat_single():
    payload = {
        "status": "complete",
        "cells": [
            _cell("locate", "B_STRUCTURE", "src/consumer.ts"),
            _cell("locate", "D_SHADOW", "src/consumer.ts"),
            _cell("mismatch", "B_STRUCTURE", "NO_CONFLICT"),
            _cell("mismatch", "C_MEMORY", "UNKNOWN"),
            _cell("mismatch", "D_SHADOW", "NO_CONFLICT"),
        ],
    }
    result = grade_results(payload)
    assert result["hypothesis_lift"] is False
    assert result["utility_verdict"] == "stop"


def _cell(task: str, arm: str, answer: str) -> dict[str, str]:
    return {"task": task, "arm": arm, "status": "complete", "answer": answer, "repetition": 1}
