# Session Notification System

Auto-notifies via Telegram when sessions start/end, and writes vault notes
for seamless resumption.

## How it works

1. **Session end** — run `session_end.py` to send a summary to Telegram + write a vault note
2. **Session start** — run `session_start.py` to pull latest + send "welcome back" to Telegram
3. **Auto-trigger** — launchd agent runs `session_start.py` on Mac login

## Manual usage

```bash
# End a session (sends Telegram + writes vault note)
python3 tools/session/session_end.py

# Start a session (pulls latest + sends Telegram)
python3 tools/session/session_start.py

# Dry run (no Telegram, just prints)
python3 tools/session/session_end.py --dry-run
python3 tools/session/session_start.py --dry-run
```

## Shell aliases (add to ~/.zshrc)

```bash
# Session shortcuts
alias session-end="python3 ~/Projects/TEAM-MMM01/mmm-education-storefront/tools/session/session_end.py"
alias session-start="python3 ~/Projects/TEAM-MMM01/mmm-education-storefront/tools/session/session_start.py"
```

## Auto-trigger (launchd)

The launchd agent `com.hermes.session-start.plist` runs `session_start.py`
on Mac login. To install:

```bash
cp tools/session/com.hermes.session-start.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.hermes.session-start.plist
```

To uninstall:

```bash
launchctl unload ~/Library/LaunchAgents/com.hermes.session-start.plist
rm ~/Library/LaunchAgents/com.hermes.session-start.plist
```

## What gets sent

### Session end
- Completed tasks this session
- Pending locks awaiting decision
- Next actions
- Link to full state docs

### Session start
- Last session timestamp
- Site submission status
- Locks awaiting decision
- Links to resume files

## Vault note location

After each session end, a note is written to:
```
obsidian-vault/00-HQ/HermesOS/State/latest-session.md
```

This is pushed to GitHub so the HP can also read it.
