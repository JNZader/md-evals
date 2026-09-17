"""Fail-closed Gate 1 utility preregister. This is NOT smoke-dev.

Smoke cannot decide Gate 1. Live execute is not implemented. This module only
prints the locked 24-cell plan (3 tasks × 4 arms × 2 repetitions).
It never calls a model, a gateway, or a memory/graph producer.
"""

from __future__ import annotations

import argparse
import json
import sys

PROVIDER = "opencode-cli"
MODEL = "gemini-3.7-flash-medium"
GATEWAY = "http://127.0.0.1:3456/v1/generate"
ARMS = ("CONTROL", "B_STRUCTURE", "C_MEMORY", "D_SHADOW")
TASKS = ("conflict", "stale_dirty", "locate")
N = 2
TIMEOUT_SECONDS = 300
BUDGET_TOKENS = 4000
SPEND_CAP_USD = 0
RETRY = 0
FALLBACK = "forbidden"
TEMPERATURE = 0
TOOLS = ["Read", "rg/Grep"]
CANONICAL_STATUS = "utility-preregister/not-executed"
PRODUCERS = {
    "B_STRUCTURE": "repoforge graph -w . --v2 --format json",
    "C_MEMORY": "Engram search+get",
    "D_SHADOW": "smart-context skill",
}
BLOCKED_REASON = (
    "live execute is not implemented; this is a utility preregister, not smoke-dev"
)


def build_plan() -> dict[str, object]:
    """Return the locked 24-cell preregister. Never authorizes execution."""
    cells: list[dict[str, object]] = []
    for repetition in range(1, N + 1):
        for task in TASKS:
            for arm in ARMS:
                cell: dict[str, object] = {
                    "task": task,
                    "arm": arm,
                    "repetition": repetition,
                    "timeout": TIMEOUT_SECONDS,
                    "model": MODEL,
                    "provider": PROVIDER,
                    "budget_tokens": None if arm == "CONTROL" else BUDGET_TOKENS,
                }
                if arm != "CONTROL":
                    cell["producer"] = PRODUCERS[arm]
                cells.append(cell)
    return {
        "canonical_status": CANONICAL_STATUS,
        "execution_authorized": False,
        "provider": PROVIDER,
        "model": MODEL,
        "gateway": GATEWAY,
        "n": N,
        "arms": list(ARMS),
        "tasks": list(TASKS),
        "timeout_seconds": TIMEOUT_SECONDS,
        "spend_cap_usd": SPEND_CAP_USD,
        "retry": RETRY,
        "fallback": FALLBACK,
        "temperature": TEMPERATURE,
        "tools": list(TOOLS),
        "cells": cells,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print the Gate 1 utility preregister; live execute is not implemented"
    )
    parser.add_argument("--plan", action="store_true", help="print the JSON plan (default)")
    parser.add_argument(
        "--live", action="store_true", help="rejected: live execute is not implemented"
    )
    parser.add_argument(
        "--execute", action="store_true", help="rejected: live execute is not implemented"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.live or args.execute:
        print(json.dumps({"status": "blocked", "reason": BLOCKED_REASON}))
        return 2
    print(json.dumps(build_plan(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
