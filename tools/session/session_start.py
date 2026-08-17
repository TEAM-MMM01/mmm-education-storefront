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
    """Get Telegram bot token and chat ID.

    Prefers environment variables (docs/workflow/NOTIFICATIONS.md Option A);
    falls back to Keychain using the documented service names (Option B).
    Previously used non-existent service names (telegram-prep-station-token,
    telegram-chat-id) that don't match what NOTIFICATIONS.md actually sets up,
    so this silently found nothing on a correctly-configured Mac.
    """
    env_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    env_chat = os.environ.get("TELEGRAM_CHAT_ID")
    if env_token and env_chat:
        return env_token, env_chat
    try:
        token = subprocess.check_output(
            ["security", "find-generic-password", "-a", "preparation-station",
             "-s", "telegram", "-w"],
            text=True
        ).strip()
        chat_id = subprocess.check_output(
            ["security", "find-generic-password", "-a", "preparation-station",
             "-s", "telegram-chat", "-w"],
            text=True
        ).strip()
        return token, chat_id
    except (subprocess.CalledProcessError, OSError):
        # CalledProcessError: keychain lookup failed.
        # OSError (incl. FileNotFoundError): `security` is unavailable (non-macOS).
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
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
        return result.get("ok", False)
    except Exception as e:
        # Some urllib errors render the full request URL, which embeds the bot
        # token; redact it before printing so it never lands in logs.
        print(f"Telegram send failed: {str(e).replace(token, '<redacted-token>')}")
        return False


def current_branch(repo):
    """Return the checked-out branch name for `repo`, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo), capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def pull_latest():
    """Fast-forward each repo's own checked-out branch from origin.

    Never merges a hard-coded feature branch into whatever is checked out;
    each repo pulls its own current branch so this keeps working after the
    landing-page branch merges and is deleted.
    """
    print("Pulling latest from GitHub...")
    for repo in (VAULT_PATH, REPO_ROOT):
        if not (repo / ".git").exists():
            print(f"Pull skipped: {repo} is not a git repository")
            continue
        branch = current_branch(repo)
        if not branch or branch == "HEAD":
            print(f"Pull skipped for {repo}: could not resolve current branch")
            continue
        try:
            result = subprocess.run(
                ["git", "pull", "--ff-only", "origin", branch],
                cwd=str(repo), capture_output=True, text=True, timeout=30
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            print(f"Pull failed for {repo} (non-critical): {e}")
            continue
        if result.returncode == 0:
            print(f"Pulled {repo} ({branch})")
        else:
            print(f"Pull failed for {repo} ({branch}): {result.stderr.strip()}")


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


def escape_markdown(text):
    """Escape characters Telegram's legacy Markdown parser treats as entities.

    The `Last updated:` value is copied verbatim from docs/session-state.md.
    A stray `_`, `*`, `` ` `` or `[` would make Telegram reject the whole
    message with HTTP 400, so escape dynamic text before interpolating it into
    an otherwise fixed template (mirrors tools/session/session_end.py).
    """
    for char in ("_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")
    return text


def build_welcome_back(vault_note, session_state):
    """Build a welcome-back message.

    Previously this hardcoded specific claims ("Deadline was Monday — now
    overdue", "Merge PR #18: waiting on you", literal LOCK-4..LOCK-7 text)
    that stayed fixed regardless of what session-state.md actually said, and
    accepted vault_note as a parameter without ever reading it. Both are
    fixed here: status/lock lines are now extracted from the real file
    content instead of being reprinted verbatim from memory, and a short
    excerpt from the vault note is included when present.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = []
    lines.append("*Welcome back, Richie*")
    lines.append(f"_Session resumed: {now}_\n")

    if session_state:
        state_lines = session_state.split("\n")
        in_status_block = False
        for line in state_lines:
            stripped = line.strip()
            if "Last updated:" in line:
                last = line.split(':', 1)[1].strip().strip('*').strip()
                lines.append(f"Last session: {escape_markdown(last)}")
            elif "SITE SUBMISSION STATUS" in line.upper():
                lines.append("\n*Site status:*")
                in_status_block = True
                continue
            elif "OPEN LOCKS" in line.upper():
                in_status_block = False
                lines.append("\n*Awaiting your decision:*")
                continue
            elif in_status_block and stripped and not stripped.startswith('#'):
                # Real current status text from the file, not a canned string
                lines.append(f"  {escape_markdown(stripped)}")
            elif stripped.startswith("LOCK-") and "|" in stripped:
                # Real lock line from the file, not a hardcoded rewrite
                lock_desc = stripped.split("|")[0].strip()
                lines.append(f"  {escape_markdown(lock_desc)}")
    elif vault_note:
        # No committed session-state (it's local-only now, see privacy
        # note in docs/) - fall back to the vault note's own summary
        # instead of showing nothing.
        excerpt = vault_note.strip().splitlines()[:5]
        if excerpt:
            lines.append("\n*From your last vault note:*")
            for l in excerpt:
                if l.strip():
                    lines.append(f"  {escape_markdown(l.strip())}")

    lines.append("\n*Resume:* `docs/session-state.md` (local, not committed)")
    lines.append("*Full tasks:* `docs/DEFERRED-TASKS.md`")

    return "\n".join(lines)


def main():
    dry_run = "--dry-run" in sys.argv

    # Pull latest (skipped entirely in dry-run — was previously running
    # unconditionally before the dry_run check, so a "print-only rehearsal"
    # was still doing real network fetches and could fast-forward both
    # working copies)
    if not dry_run:
        pull_latest()
    else:
        print("Dry run: skipping repository pull (no network/state changes)")

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
