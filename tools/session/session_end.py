#!/usr/bin/env python3
"""Session End — Sends Telegram summary + updates vault note.

Run when wrapping up a work session. Reads the current session state,
generates a summary, sends it to Telegram, and writes a vault note
so the next session can pick up seamlessly.

Usage:
    python3 tools/session/session_end.py
    python3 tools/session/session_end.py --dry-run
    python3 tools/session/session_end.py --push  # opt-in: commit + push vault note
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
        elif "COMPLETED" in line.upper() and line.lstrip().startswith("#"):
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


def _current_branch(repo):
    """Return the checked-out branch name for `repo`, or None if unavailable."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo), capture_output=True, text=True, timeout=10
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def _run_git(step, cwd):
    """Run a git step; return CompletedProcess or raise OSError on spawn failure."""
    try:
        return subprocess.run(
            step, cwd=str(cwd), capture_output=True, text=True, timeout=30
        )
    except OSError as e:
        print(f"Vault push failed ({' '.join(step)}): {e}")
        raise


def push_vault_note():
    """Commit the vault note to a session branch and push it.

    Never pushes to main directly (see AGENTS.md git workflow); every
    automated write goes to a dedicated branch so it stays attributable
    and reviewable. Always restores the previously checked-out branch
    via finally-style cleanup so the vault never gets parked on a
    one-off branch. An empty commit ('nothing to commit') is treated
    as a benign no-op rather than a hard failure. Returns True only
    if the push (or the no-op) completed.
    """
    if not (VAULT_PATH / ".git").exists():
        print(f"Vault push skipped: {VAULT_PATH} is not a git repository")
        return False

    start_branch = _current_branch(VAULT_PATH)
    if not start_branch or start_branch == "HEAD":
        print(
            f"Vault push skipped: could not resolve current branch "
            f"in {VAULT_PATH} (got {start_branch!r})"
        )
        return False

    branch = f"session/end-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    pushed = False
    try:
        result = _run_git(["git", "checkout", "-b", branch], VAULT_PATH)
        if result.returncode != 0:
            print(f"Vault push failed (checkout -b {branch}): {result.stderr.strip()}")
            return False

        result = _run_git(
            ["git", "add", "00-HQ/HermesOS/State/latest-session.md"], VAULT_PATH
        )
        if result.returncode != 0:
            print(f"Vault push failed (git add): {result.stderr.strip()}")
            return False

        result = _run_git(
            ["git", "commit", "-m", f"Session end: {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            VAULT_PATH,
        )
        if result.returncode != 0:
            combined = (result.stdout + result.stderr).lower()
            if "nothing to commit" in combined:
                print(
                    f"Vault push: no changes to commit on {branch} (benign no-op)"
                )
            else:
                print(f"Vault push failed (git commit): {result.stderr.strip()}")
                return False
        else:
            result = _run_git(["git", "push", "origin", branch], VAULT_PATH)
            if result.returncode != 0:
                print(f"Vault push failed (git push): {result.stderr.strip()}")
                return False
            pushed = True
    finally:
        # Always restore the original branch so session_start.py's
        # `git pull --ff-only` continues to target the user's branch,
        # not the one-off session branch we just created.
        result = _run_git(["git", "checkout", start_branch], VAULT_PATH)
        if result.returncode != 0:
            print(
                f"Vault push warning: could not restore branch '{start_branch}' "
                f"in {VAULT_PATH}: {result.stderr.strip()}"
            )

    if pushed:
        print(f"Vault note pushed to branch '{branch}' — open a PR to land it on main")
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    do_push = "--push" in sys.argv

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

    # Git push vault (opt-in; never touches main directly)
    if do_push:
        print("Pushing vault note to a session branch...")
        push_vault_note()
    else:
        print(f"Vault note written to {note_path} (not pushed; pass --push to commit + push)")

    print("\nSession end complete.")


if __name__ == "__main__":
    main()
