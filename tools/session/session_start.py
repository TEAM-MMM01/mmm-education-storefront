#!/usr/bin/env python3
"""Session Start — Reads vault note + sends "welcome back" Telegram.

Run when starting a new work session. Reads the last session state
from the vault, sends a Telegram summary, and prints where we left off.

Usage:
    python3 tools/session/session_start.py
    python3 tools/session/session_start.py --dry-run
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SESSION_STATE = REPO_ROOT / "docs" / "session-state.md"
VAULT_PATH = Path.home() / "Projects" / "TEAM-MMM01" / "obsidian-vault"
VAULT_SESSION_NOTE = VAULT_PATH / "00-HQ" / "HermesOS" / "State" / "latest-session.md"


def get_telegram_config():
    """Get Telegram bot token and chat ID from Keychain."""
    try:
        token = subprocess.check_output(
            ["security", "find-generic-password", "-a", "preparation-station",
             "-s", "telegram-prep-station-token", "-w"],
            text=True
        ).strip()
        chat_id = subprocess.check_output(
            ["security", "find-generic-password", "-a", "preparation-station",
             "-s", "telegram-chat-id", "-w"],
            text=True
        ).strip()
        return token, chat_id
    except subprocess.CalledProcessError:
        token = os.environ.get("TELEGRAM_BOT_TOKEN_PS")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID_PS")
        return token, chat_id


def send_telegram(token, chat_id, message):
    """Send a Telegram message."""
    if not token or not chat_id:
        print("No Telegram config found — skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }).encode("utf-8")

    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        resp = urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result.get("ok", False)
    except Exception as e:
        print(f"Telegram send failed: {e}")
        return False


def pull_latest():
    """Pull latest changes from GitHub."""
    print("Pulling latest from GitHub...")
    try:
        # Pull vault
        subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=str(VAULT_PATH), capture_output=True, timeout=30
        )
        # Pull repo
        subprocess.run(
            ["git", "pull", "--ff-only", "origin", "agent/esa-landing-page"],
            cwd=str(REPO_ROOT), capture_output=True, timeout=30
        )
        print("Latest pulled")
    except Exception as e:
        print(f"Pull failed (non-critical): {e}")


def read_vault_note():
    """Read the last session note from vault."""
    if not VAULT_SESSION_NOTE.exists():
        return None
    return VAULT_SESSION_NOTE.read_text()


def read_session_state():
    """Read current session state."""
    if not SESSION_STATE.exists():
        return None
    return SESSION_STATE.read_text()


def build_welcome_back(vault_note, session_state):
    """Build a welcome-back message."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("*Welcome back, Richie*")
    lines.append(f"_Session resumed: {now}_\n")

    # Extract key info from session state
    if session_state:
        for line in session_state.split("\n"):
            if "Last updated:" in line:
                lines.append(f"Last session: {line.split(':', 1)[1].strip().strip('*').strip()}")
            elif "SITE SUBMISSION STATUS" in line.upper():
                lines.append("\n*Site status:*")
                lines.append("  Deadline was Monday — now overdue")
                lines.append("  ESA landing page: done")
                lines.append("  Merge PR #18: waiting on you")
                lines.append("  Link Netlify: you're doing this")
            elif "OPEN LOCKS" in line.upper():
                lines.append("\n*Awaiting your decision:*")
            elif "LOCK-4" in line and "|" in line:
                lines.append("  LOCK-4: HermesOS-Vault disposition")
            elif "LOCK-5" in line and "|" in line:
                lines.append("  LOCK-5: OmniRoute provider keys")
            elif "LOCK-6" in line and "|" in line:
                lines.append("  LOCK-6: royal-collexions repo")
            elif "LOCK-7" in line and "|" in line:
                lines.append("  LOCK-7: HP setup")

    lines.append("\n*Resume:* `docs/session-state.md`")
    lines.append("*Full tasks:* `docs/DEFERRED-TASKS.md`")

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    # Pull latest
    pull_latest()

    print("Reading session state...")
    vault_note = read_vault_note()
    session_state = read_session_state()

    print("Building welcome-back message...")
    message = build_welcome_back(vault_note, session_state)

    if dry_run:
        print("\n--- DRY RUN ---")
        print(message)
        return

    # Send Telegram
    print("Sending Telegram notification...")
    token, chat_id = get_telegram_config()
    sent = send_telegram(token, chat_id, message)
    print(f"Telegram: {'sent' if sent else 'failed'}")

    # Print to console too
    print("\n" + "=" * 50)
    print(message.replace("*", "").replace("_", ""))
    print("=" * 50)

    print("\nSession started. Pick up where we left off.")


if __name__ == "__main__":
    main()
