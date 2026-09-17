"""Deterministic Gate 1 utility graders. No live models."""

from __future__ import annotations

from md_evals.gate1_utility_grade import grade_answer, grade_results, main


def test_locate_requires_fixture_path():
    assert grade_answer("locate", "see src/consumer.ts") is True
    assert grade_answer("locate", "I mapped the workspace") is False


def test_conflict_requires_first_token():
    assert grade_answer("conflict", "NO_CONFLICT nothing in producer_output") is True
    assert grade_answer("conflict", "conflict / CONTROL verification") is False


def test_stale_dirty_requires_first_token():
    assert grade_answer("stale_dirty", "UNKNOWN") is True
    assert grade_answer("stale_dirty", "index is stale") is False


def test_lift_when_d_beats_best_single(tmp_path, capsys):
    payload = {
        "status": "complete",
        "cells": [
            _cell("locate", "B_STRUCTURE", "nope"),
            _cell("locate", "C_MEMORY", "nope"),
            _cell("locate", "D_SHADOW", "src/base.ts"),
            _cell("conflict", "B_STRUCTURE", "nope"),
            _cell("conflict", "C_MEMORY", "nope"),
            _cell("conflict", "D_SHADOW", "CONFLICT two observations disagree"),
            _cell("stale_dirty", "B_STRUCTURE", "nope"),
            _cell("stale_dirty", "C_MEMORY", "nope"),
            _cell("stale_dirty", "D_SHADOW", "DIRTY"),
        ],
    }
    result = grade_results(payload)
    assert result["hypothesis_lift"] is True
    assert result["utility_verdict"] == "continue"
    path = tmp_path / "results.json"
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    assert main([str(path)]) == 0
    assert "continue" in capsys.readouterr().out


def test_stop_when_d_does_not_beat_single():
    payload = {
        "status": "complete",
        "cells": [
            _cell("locate", "B_STRUCTURE", "src/entry.js"),
            _cell("locate", "D_SHADOW", "mapped the repo"),
            _cell("conflict", "C_MEMORY", "NO_CONFLICT"),
            _cell("conflict", "D_SHADOW", "conflict / CONTROL"),
        ],
    }
    result = grade_results(payload)
    assert result["hypothesis_lift"] is False
    assert result["utility_verdict"] == "stop"


def _cell(task: str, arm: str, answer: str) -> dict[str, str]:
    return {"task": task, "arm": arm, "status": "complete", "answer": answer, "repetition": 1}
