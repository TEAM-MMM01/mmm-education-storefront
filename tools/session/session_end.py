#!/usr/bin/env python3
"""Session End — Sends Telegram summary + updates vault note.

Run when wrapping up a work session. Reads the current session state,
generates a summary, sends it to Telegram, and writes a vault note
so the next session can pick up seamlessly.

Usage:
    python3 tools/session/session_end.py
    python3 tools/session/session_end.py --dry-run
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
DEFERRED_TASKS = REPO_ROOT / "docs" / "DEFERRED-TASKS.md"
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
        # Fallback to env vars
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


def read_session_state():
    """Read the session state file and extract key info."""
    if not SESSION_STATE.exists():
        return None

    content = SESSION_STATE.read_text()

    # Extract key sections
    info = {
        "last_updated": "",
        "completed": [],
        "pending": [],
        "locks": [],
    }

    lines = content.split("\n")
    current_section = None

    for line in lines:
        if "Last updated:" in line:
            info["last_updated"] = line.split(":", 1)[1].strip()
        elif "COMPLETED THIS SESSION" in line.upper():
            current_section = "completed"
        elif "OPEN LOCKS" in line.upper():
            current_section = "locks"
        elif "WHAT'S NEXT" in line.upper() or "IMMEDIATE" in line.upper():
            current_section = "pending"
        elif current_section and line.startswith("- [x]"):
            info["completed"].append(line.replace("- [x]", "").strip())
        elif current_section and line.startswith("| LOCK-"):
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 3:
                info["locks"].append(f"{parts[0]}: {parts[1]} — {parts[2]}")

    return info


def build_summary(info):
    """Build a concise session summary for Telegram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("*Session Summary*")
    lines.append(f"_Updated: {now}_\n")

    # Completed
    if info and info["completed"]:
        lines.append("*Completed:*")
        for item in info["completed"][:10]:  # Cap at 10
            lines.append(f"  {item}")
        if len(info["completed"]) > 10:
            lines.append(f"  _...and {len(info['completed']) - 10} more_")
        lines.append("")

    # Pending locks
    if info and info["locks"]:
        lines.append("*Awaiting your decision:*")
        for lock in info["locks"][:5]:
            lines.append(f"  {lock}")
        lines.append("")

    # Next actions
    lines.append("*Next actions:*")
    lines.append("  1. Merge PR #18 (ESA landing page)")
    lines.append("  2. Link Netlify to main branch")
    lines.append("  3. Resolve LOCK-4 through LOCK-7")
    lines.append("")
    lines.append("_Full state: docs/session-state.md_")

    return "\n".join(lines)


def write_vault_note(info, summary):
    """Write a vault note for the next session to read."""
    VAULT_SESSION_NOTE.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    content = f"""# Latest Session

**Saved:** {now}
**Resume point:** docs/session-state.md

## Summary

{summary}

## What was shipped this session

"""
    if info and info["completed"]:
        for item in info["completed"]:
            content += f"- {item}\n"
    else:
        content += "- (no items recorded)\n"

    content += "\n## What's still pending\n\n"
    content += "See docs/DEFERRED-TASKS.md for full list.\n"
    content += "See docs/session-state.md for current state.\n"

    VAULT_SESSION_NOTE.write_text(content)
    return VAULT_SESSION_NOTE


def main():
    dry_run = "--dry-run" in sys.argv

    print("Reading session state...")
    info = read_session_state()

    print("Building summary...")
    summary = build_summary(info)

    if dry_run:
        print("\n--- DRY RUN ---")
        print(summary)
        return

    # Send Telegram
    print("Sending Telegram notification...")
    token, chat_id = get_telegram_config()
    sent = send_telegram(token, chat_id, summary)
    print(f"Telegram: {'sent' if sent else 'failed'}")

    # Write vault note
    print("Writing vault note...")
    note_path = write_vault_note(info, summary)
    print(f"Vault note: {note_path}")

    # Git push vault
    print("Pushing vault to GitHub...")
    try:
        subprocess.run(
            ["git", "add", "00-HQ/HermesOS/State/latest-session.md"],
            cwd=str(VAULT_PATH), capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", f"Session end: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=str(VAULT_PATH), capture_output=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=str(VAULT_PATH), capture_output=True, timeout=30
        )
        print("Vault pushed")
    except Exception as e:
        print(f"Vault push failed (non-critical): {e}")

    print("\nSession end complete.")


if __name__ == "__main__":
    main()
