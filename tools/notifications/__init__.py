#!/usr/bin/env python3
"""Notification dispatchers with multi-bot Telegram routing.

Architecture: Hub-and-spoke. The main bot (@Hermes_OS1bot) receives all
events and routes to business-specific bots based on the `business` tag.

Bot mapping (stored in Keychain, read via shell profile exports):
    @Hermes_OS1bot   – CFO/COO router (all events, always notified)
    @HermesOS2_Bot   – Preparation Station (ops/education)
    @RichieRichPF_Bot – Revenue/Product (future: Royal Collexions)

Environment variables:
    TELEGRAM_BOT_TOKEN        – Main router bot token
    TELEGRAM_CHAT_ID          – Your chat ID (for router)
    TELEGRAM_BOT_TOKEN_PS     – Preparation Station bot token
    TELEGRAM_CHAT_ID_PS       – PS bot chat ID (usually same as main)
    TELEGRAM_BOT_TOKEN_RC     – Royal Collexions bot token (future)
    TELEGRAM_CHAT_ID_RC       – RC bot chat ID (future)
    SLACK_WEBHOOK_URL         – Slack webhook URL
    SLACK_BOT_TOKEN           – Slack API token (optional)

Usage:
    from tools.notifications import notify_routed
    notify_routed("PR #16 opened", business="preparation-station", event_type="pr")
"""

from __future__ import annotations

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError


# ── Business → Bot mapping ─────────────────────────────────────────

BUSINESS_BOTS: dict[str, dict[str, str | None]] = {
    "preparation-station": {
        "token_env": "TELEGRAM_BOT_TOKEN_PS",
        "chat_env": "TELEGRAM_CHAT_ID_PS",
        "label": "Preparation Station",
    },
    "royal-collexions": {
        "token_env": "TELEGRAM_BOT_TOKEN_RC",
        "chat_env": "TELEGRAM_CHAT_ID_RC",
        "label": "Royal Collexions",
    },
}

# Event type → which bots should receive it
EVENT_ROUTING: dict[str, list[str]] = {
    # PR and build events go to the business bot + always to router
    "pr": ["business", "router"],
    "build": ["business", "router"],
    "task": ["business", "router"],
    # Revenue events go to revenue bot + router
    "order": ["revenue", "router"],
    "request": ["revenue", "router"],
    # Audit/log events only go to router
    "audit": ["router"],
    "huddle": ["router"],
    # Blockers always go everywhere
    "blocker": ["business", "revenue", "router"],
}


def _env(name: str) -> str | None:
    return os.environ.get(name) or None


def _send_telegram_raw(text: str, token: str, chat_id: str, *, silent: bool = False) -> bool:
    """Send to a specific Telegram bot+chat. Returns True on success."""
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


def send_telegram(text: str, *, silent: bool = False, bot: str = "router") -> bool:
    """Send via Telegram. `bot` selects which token/chat to use.

    bot="router"  → main CFO/COO bot
    bot="ps"      → Preparation Station bot
    bot="rc"      → Royal Collexions bot
    """
    if bot == "router":
        token = _env("TELEGRAM_BOT_TOKEN")
        chat_id = _env("TELEGRAM_CHAT_ID")
    elif bot == "ps":
        token = _env("TELEGRAM_BOT_TOKEN_PS")
        chat_id = _env("TELEGRAM_CHAT_ID_PS")
    elif bot == "rc":
        token = _env("TELEGRAM_BOT_TOKEN_RC")
        chat_id = _env("TELEGRAM_CHAT_ID_RC")
    else:
        print(f"WARN: unknown bot {bot!r}", file=sys.stderr)
        return False

    if not token or not chat_id:
        print(f"WARN: Telegram bot {bot!r} not configured", file=sys.stderr)
        return False

    return _send_telegram_raw(text, token, chat_id, silent=silent)


def send_slack(text: str, *, channel: str | None = None) -> bool:
    """Send via Slack. Prefers webhook, falls back to API."""
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

    token = _env("SLACK_BOT_TOKEN")
    if not token:
        print("WARN: Slack not configured", file=sys.stderr)
        return False
    target = channel or _env("SLACK_CHANNEL") or "general"
    url = "https://slack.com/api/chat.postMessage"
    payload = json.dumps({"channel": target, "text": text}).encode()
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


# ── Routed notification (main entry point) ──────────────────────────

def notify_routed(
    text: str,
    *,
    business: str = "preparation-station",
    event_type: str = "task",
    channels: list[str] | None = None,
) -> dict[str, bool]:
    """Send notification with business routing.

    Routes to the correct Telegram bot based on business + event_type.
    Also sends to Slack if configured.

    Returns {"telegram_router": bool, "telegram_business": bool, "slack": bool}
    """
    results: dict[str, bool] = {}
    targets = channels or ["telegram", "slack"]

    if "telegram" in targets:
        # Always send to router (main bot)
        results["telegram_router"] = send_telegram(text, bot="router")

        # Route to business-specific bot
        bot_map = BUSINESS_BOTS.get(business)
        if bot_map:
            token = _env(bot_map["token_env"])
            chat_id = _env(bot_map["chat_env"])
            if token and chat_id:
                results["telegram_business"] = _send_telegram_raw(text, token, chat_id)
            else:
                results["telegram_business"] = False
        else:
            results["telegram_business"] = False

    if "slack" in targets:
        results["slack"] = send_slack(text)

    return results


# Legacy alias
def notify(text: str, *, channels: list[str] | None = None) -> dict[str, bool]:
    """Send to router only. Use notify_routed() for business routing."""
    results: dict[str, bool] = {}
    targets = channels or ["telegram", "slack"]
    for ch in targets:
        if ch == "telegram":
            results["telegram"] = send_telegram(text, bot="router")
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
