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
# VAULT_PATH was previously hardcoded to one operator's exact folder layout
# (~/Projects/TEAM-MMM01/obsidian-vault), so on any other machine this
# script would silently create a new, empty directory tree at that fixed
# path rather than finding the real vault. HERMES_VAULT_PATH lets each
# machine point at its actual vault location; the old path remains the
# default so existing setups keep working unchanged.
VAULT_PATH = Path(os.environ.get("HERMES_VAULT_PATH",
                                  str(Path.home() / "Projects" / "TEAM-MMM01" / "obsidian-vault")))
VAULT_SESSION_NOTE = VAULT_PATH / "00-HQ" / "HermesOS" / "State" / "latest-session.md"


def get_telegram_config():
    """Get Telegram bot token and chat ID.

    Prefers environment variables (docs/workflow/NOTIFICATIONS.md Option A);
    falls back to Keychain using the documented service names (Option B).
    Previously used non-existent Keychain service names and a non-standard
    env var suffix (_PS) that don't match NOTIFICATIONS.md.
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
        return None, None


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
    """Write a vault note for the next session to read.

    Verifies VAULT_PATH is an existing git repository first. Previously this
    would silently create the entire directory tree via mkdir(parents=True)
    even when the vault hadn't been cloned yet (e.g. a freshly set up HP),
    leaving a non-repository directory sitting at the clone destination -
    a later `git clone` into that same path then fails because the
    destination is non-empty. Returns None instead of fabricating a vault.
    """
    if not (VAULT_PATH / ".git").exists():
        print(f"Vault note skipped: {VAULT_PATH} is not an existing git "
              f"repository. Clone it first: git clone <vault-url> {VAULT_PATH}")
        return None

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


def checkout_session_branch():
    """Create and check out a dedicated session branch in the vault.

    Must be called BEFORE write_vault_note() - previously the note was
    written first, on whatever branch the vault happened to be on
    (potentially main), and the session branch was only created afterward
    inside push_vault_note(). That left the vault's current branch dirty
    on every normal run, even without --push.

    Returns (original_branch, session_branch). session_branch is None if
    the vault isn't a git repo or branch creation failed - callers should
    skip the write in that case rather than dirty an unknown branch.
    """
    if not (VAULT_PATH / ".git").exists():
        print(f"Vault git skipped: {VAULT_PATH} is not a git repository")
        return None, None

    origin = _git(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if origin is None or origin.returncode != 0:
        print("Vault git skipped: could not resolve current branch")
        return None, None
    original_branch = origin.stdout.strip()

    branch = f"session/end-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    checkout = _git(["git", "checkout", "-b", branch])
    if checkout is None or checkout.returncode != 0:
        print(f"Vault git skipped: could not create branch '{branch}': "
              f"{checkout.stderr.strip() if checkout else 'command error'}")
        return original_branch, None

    return original_branch, branch


def commit_and_push_vault_note(session_branch, do_push):
    """Commit the vault note on session_branch, and push if do_push.

    Assumes checkout_session_branch() already succeeded and the vault is
    currently checked out on session_branch. Returns True only if every
    attempted git step succeeded.
    """
    add = _git(["git", "add", "00-HQ/HermesOS/State/latest-session.md"])
    if add is None or add.returncode != 0:
        print(f"Vault commit failed (git add): "
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
            print("Vault note unchanged — nothing to commit")
            return True
        print(f"Vault commit failed: {commit.stderr.strip()}")
        return False

    if not do_push:
        print(f"Vault note committed locally on branch '{session_branch}' "
              f"(not pushed; pass --push to push)")
        return True

    push = _git(["git", "push", "origin", session_branch])
    if push is None or push.returncode != 0:
        print(f"Vault push failed (git push): "
              f"{push.stderr.strip() if push else 'command error'}")
        return False

    print(f"Vault note pushed to branch '{session_branch}' — open a PR to land it on main")
    return True


def restore_original_branch(original_branch):
    """Return the vault to original_branch. Returns True only if it actually succeeded.

    Previously a failed restore only printed a warning while the caller's
    return value stayed True - callers were told every git step succeeded
    even when the vault was left stranded on the session branch, which
    directly violated the "always returns to original branch" contract.
    """
    if original_branch is None:
        return True
    restore = _git(["git", "checkout", original_branch])
    if restore is None or restore.returncode != 0:
        print(f"WARNING: could not restore vault to '{original_branch}' — "
              f"it is still on a session branch. Check manually before your "
              f"next pull.")
        return False
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

    # Check out a dedicated session branch BEFORE writing anything, so the
    # write lands on an attributable branch instead of dirtying whatever
    # branch the vault happened to be on (potentially main).
    print("Checking out vault session branch...")
    original_branch, session_branch = checkout_session_branch()

    try:
        # Write vault note
        print("Writing vault note...")
        note_path = write_vault_note(info, summary)
        if note_path:
            print(f"Vault note: {note_path}")

        # Commit (and optionally push) on the session branch
        if session_branch and note_path:
            commit_and_push_vault_note(session_branch, do_push)
        elif not do_push:
            print(f"Vault note written to {note_path} but not committed "
                  f"(no session branch available)" if note_path else
                  "Vault note not written (see message above)")
    finally:
        restored = restore_original_branch(original_branch)
        if not restored:
            print("Session end completed with a vault branch warning above — check manually.")

    print("\nSession end complete.")


if __name__ == "__main__":
    main()
