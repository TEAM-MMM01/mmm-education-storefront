#!/usr/bin/env python3
"""Notification dispatchers for Telegram and Slack.

Reads tokens from environment variables (never from files or hard-coded).
All functions are pure local — they make HTTP requests only to the
configured messaging API and never touch the repository filesystem.

Environment variables:
    TELEGRAM_BOT_TOKEN   – BotFather token for the Preparation Station bot
    TELEGRAM_CHAT_ID     – Target chat/channel ID
    SLACK_WEBHOOK_URL    – Incoming webhook URL for the Slack workspace
    SLACK_BOT_TOKEN      – Bot token for Slack API (optional, for richer messages)

Usage:
    from tools.notifications.sender import send_telegram, send_slack
    send_telegram("PR #16 opened: baby-agent harness")
    send_slack("Build failed on agent/fix-typo")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError


def _env(name: str) -> str | None:
    return os.environ.get(name) or None


def send_telegram(text: str, *, silent: bool = False) -> bool:
    """Send a message via Telegram Bot API. Returns True on success."""
    token = _env("TELEGRAM_BOT_TOKEN")
    chat_id = _env("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("WARN: Telegram not configured (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)", file=sys.stderr)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": silent,
    }).encode()
    req = Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except (URLError, OSError) as exc:
        print(f"ERROR: Telegram send failed: {exc}", file=sys.stderr)
        return False


def send_slack(text: str, *, channel: str | None = None) -> bool:
    """Send a message via Slack. Prefers webhook, falls back to API.

    Returns True on success.
    """
    webhook_url = _env("SLACK_WEBHOOK_URL")
    if webhook_url:
        payload = json.dumps({"text": text}).encode()
        req = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except (URLError, OSError) as exc:
            print(f"ERROR: Slack webhook send failed: {exc}", file=sys.stderr)
            return False

    # Fallback to Slack API with bot token.
    token = _env("SLACK_BOT_TOKEN")
    if not token:
        print("WARN: Slack not configured (missing SLACK_WEBHOOK_URL or SLACK_BOT_TOKEN)", file=sys.stderr)
        return False
    target = channel or _env("SLACK_CHANNEL") or "general"
    url = "https://slack.com/api/chat.postMessage"
    payload = json.dumps({
        "channel": target,
        "text": text,
    }).encode()
    req = Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("ok", False)
    except (URLError, OSError) as exc:
        print(f"ERROR: Slack API send failed: {exc}", file=sys.stderr)
        return False


def notify(text: str, *, channels: list[str] | None = None) -> dict[str, bool]:
    """Send to all configured channels. Returns {channel: success}."""
    targets = channels or ["telegram", "slack"]
    results: dict[str, bool] = {}
    for ch in targets:
        if ch == "telegram":
            results["telegram"] = send_telegram(text)
        elif ch == "slack":
            results["slack"] = send_slack(text)
    return results


# ── Formatting helpers ──────────────────────────────────────────────

def fmt_pr_opened(pr_number: int, branch: str, title: str) -> str:
    return f"PR #{pr_number} opened: {title}\nBranch: `{branch}`"

def fmt_pr_merged(pr_number: int, branch: str) -> str:
    return f"PR #{pr_number} merged: `{branch}` → `main`"

def fmt_build_failed(branch: str, check: str) -> str:
    return f"Build failed on `{branch}`\nCheck: {check}"

def fmt_task_failed(task_name: str, error: str) -> str:
    return f"Task failed: {task_name}\nError: {error}"

def fmt_state_change(workflow_id: str, old_state: str, new_state: str) -> str:
    return f"Workflow {workflow_id}: {old_state} → {new_state}"

def fmt_blocker_added(blocker: str) -> str:
    return f"Blocker added: {blocker}"
