#!/usr/bin/env python3
"""CLI for sending notifications to Telegram and Slack.

Usage:
    python3 tools/notifications/send.py "Hello from Preparation Station"
    python3 tools/notifications/send.py --channel telegram "Private message"
    python3 tools/notifications/send.py --channel slack "Team update"
    python3 tools/notifications/send.py --event pr-opened --pr 16 --branch agent/fix-typo

Reads tokens from environment variables. Never commits or logs credentials.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.notifications import (
    notify,
    send_telegram,
    send_slack,
    fmt_pr_opened,
    fmt_pr_merged,
    fmt_build_failed,
    fmt_task_failed,
    fmt_state_change,
)


EVENT_FORMATTERS = {
    "pr-opened": lambda **kw: fmt_pr_opened(kw["pr"], kw["branch"], kw.get("title", "")),
    "pr-merged": lambda **kw: fmt_pr_merged(kw["pr"], kw["branch"]),
    "build-failed": lambda **kw: fmt_build_failed(kw["branch"], kw.get("check", "unknown")),
    "task-failed": lambda **kw: fmt_task_failed(kw["task"], kw.get("error", "unknown")),
    "state-change": lambda **kw: fmt_state_change(kw["workflow"], kw["old"], kw["new"]),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a notification")
    parser.add_argument("message", nargs="?", help="Raw message text")
    parser.add_argument("--channel", choices=["telegram", "slack", "all"], default="all")
    parser.add_argument("--event", choices=list(EVENT_FORMATTERS.keys()),
                        help="Use a pre-defined event formatter")
    parser.add_argument("--pr", type=int, help="PR number (for event formatters)")
    parser.add_argument("--branch", help="Branch name (for event formatters)")
    parser.add_argument("--title", default="", help="PR title (for pr-opened)")
    parser.add_argument("--check", default="", help="Check name (for build-failed)")
    parser.add_argument("--task", help="Task name (for task-failed)")
    parser.add_argument("--error", default="", help="Error message (for task-failed)")
    parser.add_argument("--workflow", help="Workflow ID (for state-change)")
    parser.add_argument("--old", help="Old state (for state-change)")
    parser.add_argument("--new", help="New state (for state-change)")
    args = parser.parse_args()

    if args.event:
        kwargs = {k: v for k, v in vars(args).items()
                  if v is not None and k not in ("event", "channel", "message")}
        try:
            text = EVENT_FORMATTERS[args.event](**kwargs)
        except KeyError as exc:
            print(f"ERROR: missing required argument for event {args.event}: {exc}", file=sys.stderr)
            return 2
    elif args.message:
        text = args.message
    else:
        parser.error("either MESSAGE or --event is required")

    channels = None if args.channel == "all" else [args.channel]
    results = notify(text, channels=channels)
    for ch, ok in results.items():
        status = "sent" if ok else "FAILED"
        print(f"  {ch}: {status}")
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
