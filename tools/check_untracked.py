#!/usr/bin/env python3
"""Fail if forbidden local-only directories exist in the working tree.

This guard is paired with `.gitignore` so the rules in AGENTS.md (no session
memory, no snapshot directories, no editor scratch) cannot be bypassed by a
future `git add -f` mistake. The patterns below must stay aligned with
`.gitignore`.

Why we scan the filesystem (not `git status`): `.gitignore` excludes paths
from `git status`, which is exactly what we want for normal operation, but it
also hides them from any naive guard. A directory sitting on disk under a
forbidden name is still a leak risk even if Git is silent about it.

Scope rules:
- We only scan the repository root and its top-level subdirectories.
- We never descend into anything tracked as a regular file or symlink.
- We never report a forbidden path that lives inside `.git/`.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# (regex matched against a POSIX-style relative path, reason)
FORBIDDEN: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(^|.*/)\.claude(/|$)"), "Claude session memory (local-only)"),
    (re.compile(r"(^|.*/)_org-backup(/|$)"), "Local snapshot directory (never commit)"),
    (re.compile(r"(^|.*/)_audits(/|$)"), "Local audit run directory (never commit)"),
    (re.compile(r"(^|.*/)\.hermes-mac(/|$)"), "Orchestration runtime output (local-only)"),
    (re.compile(r".*/?\.DS_Store$"), "macOS Finder metadata"),
    (re.compile(r".*\.log$"), "Log file (likely local scratch)"),
    (re.compile(r".*\.(swp|swo)$|.*~$", re.IGNORECASE), "Editor swap/backup file"),
    (re.compile(r"(^|.*/)\.env$"), "Environment token file (NEVER commit)"),
    (re.compile(r"(^|.*/)\.env\.(?!example$)[^/]+$"), "Environment token file (NEVER commit)"),
    (re.compile(r"(^|.*/)\.mcp\.json$"), "Local MCP config (credentials; never commit)"),
    (re.compile(r"(^|.*/)\.hermes-mac(/|$)"), "HermesOS local queue state (never commit)"),
]

# Top-level entries we never descend into, even if they exist on disk.
SKIP_TOP_LEVEL = {".git", "node_modules", ".venv", "venv"}


def relative_posix(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def scan() -> list[str]:
    violations: list[str] = []
    for entry in sorted(ROOT.iterdir()):
        if entry.name in SKIP_TOP_LEVEL:
            continue
        rel = relative_posix(entry)
        for pattern, reason in FORBIDDEN:
            if pattern.match(rel):
                violations.append(f"{rel}  ({reason})")
                break
        else:
            # Recurse one level into non-ignored directories so we can catch
            # forbidden files like .DS_Store buried inside tracked subtrees.
            if entry.is_dir():
                for child in entry.rglob("*"):
                    if not child.is_file():
                        continue
                    child_rel = relative_posix(child)
                    for pattern, reason in FORBIDDEN:
                        if pattern.match(child_rel):
                            violations.append(f"{child_rel}  ({reason})")
                            break
    return violations


def main() -> int:
    violations = scan()
    if violations:
        print("Forbidden local-only paths exist in the working tree:", file=sys.stderr)
        for line in violations:
            print(f"  - {line}", file=sys.stderr)
        print(
            "\nThese paths must not be present in the repository (see .gitignore"
            " and AGENTS.md). Delete them locally or move them outside this"
            " repository before continuing.",
            file=sys.stderr,
        )
        return 1

    print("No forbidden local-only paths detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())