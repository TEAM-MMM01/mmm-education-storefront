#!/usr/bin/env python3
"""Print the task spec for a given baby-agent task name.

Used by parent agents to display the task summary and the allowlisted
paths before invoking `baby_agent.py`. Pure read-only; does not mutate
the working tree.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "tools" / "agent_loop" / "tasks"

TASK_NAME_RE = re.compile(r"^[a-zA-Z0-9._/-]+$")
ALLOWED_BRANCH_PREFIXES = ("agent/",)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a baby-agent task spec.")
    parser.add_argument("task_name")
    args = parser.parse_args()

    if not TASK_NAME_RE.match(args.task_name):
        print(f"ERROR: task name contains unsafe characters: {args.task_name!r}", file=sys.stderr)
        return 2
    if not any(args.task_name.startswith(p) for p in ALLOWED_BRANCH_PREFIXES):
        print(
            "ERROR: task name must start with one of "
            + ", ".join(ALLOWED_BRANCH_PREFIXES),
            file=sys.stderr,
        )
        return 2

    # Prevent directory traversal.
    spec_path = (TASKS_DIR / f"{args.task_name}.md").resolve()
    if not str(spec_path).startswith(str(TASKS_DIR.resolve()) + "/"):
        print(f"ERROR: task name escapes the tasks directory", file=sys.stderr)
        return 2
    if not spec_path.exists():
        print(f"ERROR: no task spec at {spec_path.relative_to(ROOT)}", file=sys.stderr)
        return 1
    print(spec_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())