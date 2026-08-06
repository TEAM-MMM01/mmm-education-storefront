#!/usr/bin/env python3
"""Create the TEAM-MMM01 Obsidian operations vault scaffold.

This script intentionally generates a local vault at a caller-provided path instead of
committing a real Obsidian vault into this storefront repository. The vault should be
synced with Obsidian Sync or another owner-approved private sync method.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

VAULT_DIRS = [
    "00-Inbox",
    "01-Companies",
    "02-Projects",
    "03-Products",
    "04-SOPs",
    "05-Meetings",
    "06-Finance",
    "07-Legal-Admin",
    "08-Dashboards",
    "09-Archive",
]

STARTER_NOTES = {
    "01-Companies/Preparation Station.md": """# Preparation Station

## Current status

## Confirmed facts

## Open decisions

## Links

## Next actions
""",
    "02-Projects/Preparation Station Storefront.md": """# Preparation Station Storefront

## Goal

## Current branch / PR

## Launch status

## Blockers

## Next actions
""",
    "02-Projects/OmniRoute Dashboard.md": """# OmniRoute Dashboard

## Goal

## Current status

OmniRoute is not connected to the storefront repository yet.

## Needed to wire routing

- OmniRoute repository, endpoint, schema, or dashboard codebase.
- Authentication approach.
- First events to route.

## Next actions
""",
    "02-Projects/Hermes Agent.md": """# Hermes Agent

## Goal

## Current status

## Related repositories

## Next actions
""",
    "03-Products/ESA Product Ideas.md": """# ESA Product Ideas

## Confirmed product facts

## Assumptions to verify

## Pricing basis

## ESA/funding considerations

## Launch blockers
""",
    "03-Products/High Ticket Bundles.md": """# High Ticket Bundles

## Confirmed facts

## Product concepts

## Supplier costs to verify

## Pricing basis

## Fulfillment considerations

## Launch blockers
""",
    "04-SOPs/GitHub PR Workflow.md": """# GitHub PR Workflow

## Standard flow

1. Start from `main`.
2. Create a focused branch.
3. Make source changes.
4. Run required checks.
5. Commit.
6. Open a draft PR.
7. Wait for owner approval before merge or deployment.

## Safety rules

- Do not paste tokens into notes, chat, screenshots, or committed files.
- Do not merge directly to `main`.
""",
    "04-SOPs/Codex Cloud Workflow.md": """# Codex Cloud Workflow

## Before editing

## During editing

## After editing

## Required checks
""",
    "04-SOPs/Launch Checklist.md": """# Launch Checklist

## Customer-facing readiness

## Operational readiness

## Compliance readiness

## Remaining blockers
""",
    "08-Dashboards/Launch Status Dashboard.md": """# Launch Status Dashboard

## Status cards

- Open PRs
- Latest build result
- Launch blockers
- ESA product readiness
- General Store preview status
- Next owner action
- OmniRoute assignment queue
""",
}

README = """# TEAM-MMM01 Operations Vault

This vault is for business memory, decisions, product thinking, SOPs, project notes, and
launch planning. It is not a secrets store.

## Rules

- Do not store GitHub tokens, passwords, API keys, private customer data, or personal mail.
- Keep the daily Obsidian vault separate from storefront source code.
- Promote only reviewed operating docs into GitHub when agents or dashboards need to read them.
- Use GitHub pull requests for code and reviewed markdown docs.

## Suggested sync

Use Obsidian Sync for daily notes across Mac and HP. If a private GitHub vault repo is used,
expect normal Git conflict handling when the same note is edited on multiple devices.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create the TEAM-MMM01 Obsidian operations vault scaffold."
    )
    parser.add_argument(
        "target",
        type=Path,
        help="Directory where the vault should be created, for example ~/Obsidian/TEAM-MMM01 Operations Vault.",
    )
    parser.add_argument(
        "--allow-inside-repo",
        action="store_true",
        help="Allow creating the vault inside the current repository. Not recommended.",
    )
    return parser.parse_args()


def is_inside_repo(target: Path) -> bool:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        target.resolve().relative_to(repo_root)
    except ValueError:
        return False
    return True


def write_file(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    target = args.target.expanduser()

    if is_inside_repo(target) and not args.allow_inside_repo:
        print(
            "Refusing to create a daily Obsidian vault inside this storefront repository. "
            "Choose a path such as ~/Obsidian/TEAM-MMM01 Operations Vault, or pass "
            "--allow-inside-repo for a deliberate test fixture.",
            file=sys.stderr,
        )
        return 2

    target.mkdir(parents=True, exist_ok=True)
    for directory in VAULT_DIRS:
        (target / directory).mkdir(parents=True, exist_ok=True)

    write_file(target / "README.md", README)
    for relative_path, content in STARTER_NOTES.items():
        write_file(target / relative_path, content)

    print(f"Created Obsidian operations vault scaffold at: {target}")
    print("Next: open this folder in Obsidian and enable your chosen sync method.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
