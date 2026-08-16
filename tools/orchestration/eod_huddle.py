#!/usr/bin/env python3
"""EOD Huddle agenda printer.

Reads the open-questions file and pending-locks file from the configured
Obsidian vault path and prints a structured EOD Huddle agenda to stdout.

Pure local. No remote calls. Will not modify any files.

The two inputs live at:
  <vault>/00-HQ/EOD-Huddle/EOD-Huddle-Open-Questions.md
  <vault>/00-HQ/EOD-Huddle/EOD-Huddle-Pending-Locks.md

Override with --vault /path/to/obsidian-vault.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def parse_huddle_sections(text: str) -> list[dict]:
    """Extract each `## HUDDLE-...` section as a dict with id, status, and body."""
    sections: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        header = re.match(r"^##\s+(HUDDLE-[A-Za-z0-9_-]+)\s*(?:—|-)?\s*(.*)$", line)
        if header:
            if current is not None:
                sections.append(current)
            current = {"id": header.group(1), "title": header.group(2).strip(), "body": []}
            continue
        if current is not None:
            current["body"].append(line)
    if current is not None:
        sections.append(current)
    return sections


def status_for(section: dict) -> str:
    body = "\n".join(section["body"])
    match = re.search(r"\*\*State:\*\*\s*([^\n]+)", body)
    return match.group(1).strip() if match else "Unknown"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Print EOD Huddle agenda")
    parser.add_argument(
        "--vault",
        default=str(Path.home() / "Projects" / "TEAM-MMM01" / "obsidian-vault"),
        help="Path to the obsidian-vault repo (default: ~/Projects/TEAM-MMM01/obsidian-vault)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    vault = Path(args.vault)
    open_path = vault / "00-HQ" / "EOD-Huddle" / "EOD-Huddle-Open-Questions.md"
    pending_path = vault / "00-HQ" / "EOD-Huddle" / "EOD-Huddle-Pending-Locks.md"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    sections: list[tuple[str, dict]] = []
    for label, path in (("OPEN-QUESTIONS", open_path), ("PENDING-LOCKS", pending_path)):
        if not path.exists():
            print(f"# WARNING: {label} file missing: {path}", file=sys.stderr)
            continue
        for section in parse_huddle_sections(path.read_text(encoding="utf-8")):
            sections.append((label, section))

    print(f"# EOD Huddle Agenda — generated {now}\n")
    for label, section in sections:
        print(f"## {section['id']} ({label}) — {status_for(section)}")
        print(section["title"])
        body = "\n".join(section["body"]).strip()
        # Trim the **State:** line from the body since we already printed it.
        body = re.sub(r"\*\*State:\*\*[^\n]*\n", "", body, count=1)
        if body:
            print(body)
        print()
    if not sections:
        print("(no huddle sections found)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())