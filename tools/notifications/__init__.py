#!/usr/bin/env python3
"""Notification dispatchers with multi-bot Telegram + Slack routing.

Architecture: Hub-and-spoke. The main bot (@Hermes_OS1bot) receives all
events and routes to business-specific bots + Slack channels.

Telegram Bot Mapping:
    @Hermes_OS1bot    – HermesOS_Main (CFO/COO router, all events)
    @HermesOS2_Bot    – Preparation Station (education/TEFA)
    @RichieRichPF_Bot – PumpFun (crypto/trading)
    (TBD)             – Royal Collexions (commerce)
    (TBD)             – Oracle (trading signals)
    (TBD)             – HermesOS_Voice (voice input)

Slack Channel Mapping:
    #hermesos-ops        – agent orchestration, system health
    #preparation-station – education/TEFA updates
    #pumpfun             – trading activity
    #royal-collexions    – commerce/orders
    #oracle              – trading signals

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


# ── Business → Bot/Channel mapping ──────────────────────────────────

BUSINESS_CONFIG: dict[str, dict[str, str | None]] = {
    "preparation-station": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_PS",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_PS",
        "slack_channel": "#preparation-station",
        "label": "Preparation Station",
    },
    "royal-collexions": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_RC",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_RC",
        "slack_channel": "#royal-collexions",
        "label": "Royal Collexions",
    },
    "pumpfun": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_PF",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_PF",
        "slack_channel": "#pumpfun",
        "label": "PumpFun",
    },
    "oracle": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_ORACLE",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_ORACLE",
        "slack_channel": "#oracle",
        "label": "Oracle",
    },
    "hermesos": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN",
        "telegram_chat_env": "TELEGRAM_CHAT_ID",
        "slack_channel": "#hermesos-ops",
        "label": "HermesOS",
    },
}

# Event type → which routes should receive it
EVENT_ROUTING: dict[str, list[str]] = {
    "pr": ["business", "router"],
    "build": ["business", "router"],
    "task": ["business", "router"],
    "order": ["business", "router"],
    "request": ["business", "router"],
    "trade": ["business", "router"],
    "signal": ["business", "router"],
    "audit": ["router"],
    "huddle": ["router"],
    "blocker": ["business", "router"],
    "system": ["router"],
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

    bot="router"  → main CFO/COO bot (@Hermes_OS1bot)
    bot="ps"      → Preparation Station (@HermesOS2_Bot)
    bot="pf"      → PumpFun (@RichieRichPF_Bot)
    bot="rc"      → Royal Collexions (TBD)
    bot="oracle"  → Oracle (TBD)
    bot="voice"   → HermesOS_Voice (TBD)
    """
    if bot == "router":
        token = _env("TELEGRAM_BOT_TOKEN")
        chat_id = _env("TELEGRAM_CHAT_ID")
    elif bot == "ps":
        token = _env("TELEGRAM_BOT_TOKEN_PS")
        chat_id = _env("TELEGRAM_CHAT_ID_PS")
    elif bot == "pf":
        token = _env("TELEGRAM_BOT_TOKEN_PF")
        chat_id = _env("TELEGRAM_CHAT_ID_PF")
    elif bot == "rc":
        token = _env("TELEGRAM_BOT_TOKEN_RC")
        chat_id = _env("TELEGRAM_CHAT_ID_RC")
    elif bot == "oracle":
        token = _env("TELEGRAM_BOT_TOKEN_ORACLE")
        chat_id = _env("TELEGRAM_CHAT_ID_ORACLE")
    elif bot == "voice":
        token = _env("TELEGRAM_BOT_TOKEN_VOICE")
        chat_id = _env("TELEGRAM_CHAT_ID_VOICE")
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

    Routes to the correct Telegram bot + Slack channel based on business.
    Always sends to the router (main bot) for your visibility.

    Returns dict of {channel: success} for each target that was reached.
    """
    results: dict[str, bool] = {}
    targets = channels or ["telegram", "slack"]
    biz_config = BUSINESS_CONFIG.get(business, {})

    if "telegram" in targets:
        # Always send to router (main bot)
        results["telegram_router"] = send_telegram(text, bot="router")

        # Route to business-specific bot
        token_env = biz_config.get("telegram_token_env")
        chat_env = biz_config.get("telegram_chat_env")
        if token_env and chat_env:
            token = _env(token_env)
            chat_id = _env(chat_env)
            if token and chat_id:
                results["telegram_business"] = _send_telegram_raw(text, token, chat_id)
            else:
                results["telegram_business"] = False
        else:
            results["telegram_business"] = False

    if "slack" in targets:
        slack_channel = biz_config.get("slack_channel")
        if slack_channel:
            results["slack"] = send_slack(text, channel=slack_channel)
        else:
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

def fmt_trade(signal: str, pair: str, action: str) -> str:
    return f"Trade signal: {signal}\nPair: {pair}\nAction: {action}"

def fmt_order(order_id: str, status: str, total: str) -> str:
    return f"Order {order_id}: {status}\nTotal: {total}"
