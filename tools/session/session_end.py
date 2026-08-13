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


def escape_markdown(text):
    """Escape characters that Telegram's legacy Markdown parser treats as entities.

    The summary body is copied verbatim from docs/session-state.md, which
    contains stray `_`, `*`, `` ` `` and `[` characters. Unbalanced markers make
    Telegram reject the whole message with HTTP 400, so escape dynamic text
    before interpolating it into an otherwise fixed template.
    """
    for char in ("_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")
    return text


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
            lines.append(f"  {escape_markdown(item)}")
        if len(info["completed"]) > 10:
            lines.append(f"  _...and {len(info['completed']) - 10} more_")
        lines.append("")

    # Pending locks
    if info and info["locks"]:
        lines.append("*Awaiting your decision:*")
        for lock in info["locks"][:5]:
            lines.append(f"  {escape_markdown(lock)}")
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


def _git(step):
    """Run a git command in the vault, returning the CompletedProcess or None."""
    try:
        return subprocess.run(
            step, cwd=str(VAULT_PATH), capture_output=True, text=True, timeout=30
        )
    except Exception as e:
        print(f"Vault git command failed ({' '.join(step)}): {e}")
        return None


def push_vault_note():
    """Commit the vault note to a session branch and push it.

    Never pushes to main directly (see AGENTS.md git workflow); every
    automated write goes to a dedicated branch so it stays attributable
    and reviewable. Returns True only if every git step succeeds. The vault
    is always returned to its original branch, even on failure, so later
    edits and pulls do not silently happen on a throwaway session branch.
    """
    if not (VAULT_PATH / ".git").exists():
        print(f"Vault push skipped: {VAULT_PATH} is not a git repository")
        return False

    origin = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if origin is None or origin.returncode != 0:
        print("Vault push skipped: could not resolve current branch")
        return False
    original_branch = origin.stdout.strip()

    branch = f"session/end-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    try:
        checkout = _git(["git", "checkout", "-b", branch])
        if checkout is None or checkout.returncode != 0:
            print(f"Vault push failed (git checkout -b {branch}): "
                  f"{checkout.stderr.strip() if checkout else 'command error'}")
            return False

        add = _git(["git", "add", "00-HQ/HermesOS/State/latest-session.md"])
        if add is None or add.returncode != 0:
            print(f"Vault push failed (git add): "
                  f"{add.stderr.strip() if add else 'command error'}")
            return False

        commit = _git(
            ["git", "commit", "-m", f"Session end: {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
        )
        if commit is None:
            return False
        if commit.returncode != 0:
            # "nothing to commit" is a benign no-op, not a failure.
            if "nothing to commit" in (commit.stdout + commit.stderr).lower():
                print("Vault note unchanged — nothing to push")
                return True
            print(f"Vault push failed (git commit): {commit.stderr.strip()}")
            return False

        push = _git(["git", "push", "origin", branch])
        if push is None or push.returncode != 0:
            print(f"Vault push failed (git push): "
                  f"{push.stderr.strip() if push else 'command error'}")
            return False

        print(f"Vault note pushed to branch '{branch}' — open a PR to land it on main")
        return True
    finally:
        restore = _git(["git", "checkout", original_branch])
        if restore is None or restore.returncode != 0:
            print(f"Warning: vault left on branch '{branch}'; "
                  f"could not restore '{original_branch}'")


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
