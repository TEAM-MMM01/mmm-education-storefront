#!/usr/bin/env python3
"""Notification dispatchers with multi-bot Telegram + Slack routing."""

from __future__ import annotations

import json
import os
import sys
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

BUSINESS_CONFIG: dict[str, dict[str, Optional[str]]] = {
    "preparation-station": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_PREP_STATION",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_PREP_STATION",
        "slack_webhook_env": "SLACK_WEBHOOK_PREPARATION_STATION",
    },
    "hermesos": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_HERMES_COO",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_HERMES_COO",
        "slack_webhook_env": "SLACK_WEBHOOK_HERMESOS_OPS",
    },
    "royal-collexions": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_ROYAL_COLLEXIONS",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_ROYAL_COLLEXIONS",
        "slack_webhook_env": "SLACK_WEBHOOK_ROYAL_COLLEXIONS",
    },
    "pumpfun": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_HERMES_PF",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_HERMES_PF",
        "slack_webhook_env": "SLACK_WEBHOOK_PUMPFUN",
    },
    "oracle": {
        "telegram_token_env": "TELEGRAM_BOT_TOKEN_ORACLE",
        "telegram_chat_env": "TELEGRAM_CHAT_ID_ORACLE",
        "slack_webhook_env": "SLACK_WEBHOOK_ORACLE",
    },
}

DEFAULT_BUSINESS = "hermesos"


def _post_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> None:
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=body,
        headers={"content-type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        status = getattr(response, "status", 200)
        if status >= 400:
            raise RuntimeError(f"notification_http_{status}")


def _send_telegram(message: str, token: str, chat_id: str) -> None:
    _post_json(
        f"https://api.telegram.org/bot{token}/sendMessage",
        {"chat_id": chat_id, "text": message},
    )


def _send_slack(message: str, webhook_url: str) -> None:
    _post_json(webhook_url, {"text": message})


def notify_routed(message: str, business: str = DEFAULT_BUSINESS, event_type: str = "event") -> None:
    config = BUSINESS_CONFIG.get(business, BUSINESS_CONFIG[DEFAULT_BUSINESS])

    telegram_token = os.getenv(config["telegram_token_env"] or "")
    telegram_chat_id = os.getenv(config["telegram_chat_env"] or "")
    slack_webhook = os.getenv(config["slack_webhook_env"] or "")

    prefix = f"[{business}/{event_type}] "
    full_message = prefix + message

    errors: list[str] = []

    if telegram_token and telegram_chat_id:
        try:
            _send_telegram(full_message, telegram_token, telegram_chat_id)
        except (URLError, RuntimeError) as exc:
            errors.append(f"telegram:{exc}")

    if slack_webhook:
        try:
            _send_slack(full_message, slack_webhook)
        except (URLError, RuntimeError) as exc:
            errors.append(f"slack:{exc}")

    if errors:
        raise RuntimeError("; ".join(errors))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: python -m tools.notifications 'message' [business] [event_type]")

    notify_routed(
        sys.argv[1],
        business=sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BUSINESS,
        event_type=sys.argv[3] if len(sys.argv) > 3 else "event",
    )
