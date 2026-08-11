# Notification Setup

Preparation Station sends notifications to Telegram and Slack when:

- A baby-agent opens a draft PR (success).
- A baby-agent task fails (build, push, or PR creation).
- State changes in the orchestration queue (future: PR 15 merge).

Notifications are **best-effort** — they never block or crash the main workflow.

## Required credentials

All tokens are read from environment variables. **Never commit tokens to git.**

| Variable | Purpose | Source |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | BotFather token for the Preparation Station bot | BotFather / Telegram |
| `TELEGRAM_CHAT_ID` | Target chat or channel ID | @userinfobot or channel info |
| `SLACK_WEBHOOK_URL` | Incoming webhook URL for the workspace | Slack App settings |
| `SLACK_BOT_TOKEN` | Bot token (optional, for richer API messages) | Slack App settings |
| `SLACK_CHANNEL` | Target channel name (optional, defaults to `general`) | Slack workspace |

## Setting credentials

### Option A: Shell profile (recommended for local dev)

```bash
# In ~/.zshrc or ~/.bashrc — NEVER commit this file
export TELEGRAM_BOT_TOKEN="your-token-here"
export TELEGRAM_CHAT_ID="your-chat-id"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
```

### Option B: Keychain (macOS)

```bash
security add-generic-password -a "preparation-station" -s "telegram" -w "YOUR_TOKEN"
security add-generic-password -a "preparation-station" -s "telegram-chat" -w "YOUR_CHAT_ID"
security add-generic-password -a "preparation-station" -s "slack-webhook" -w "YOUR_WEBHOOK_URL"
```

Then export them in your shell profile:

```bash
export TELEGRAM_BOT_TOKEN=$(security find-generic-password -a "preparation-station" -s "telegram" -w)
export TELEGRAM_CHAT_ID=$(security find-generic-password -a "preparation-station" -s "telegram-chat" -w)
export SLACK_WEBHOOK_URL=$(security find-generic-password -a "preparation-station" -s "slack-webhook" -w)
```

### Option C: .env file (not committed)

Create a local `.env` file at the repo root. It is already in `.gitignore`.

```bash
# .env (DO NOT COMMIT)
TELEGRAM_BOT_TOKEN=your-token-here
TELEGRAM_CHAT_ID=your-chat-id
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
```

## Testing

```bash
# Test Telegram
python3 tools/notifications/send.py --channel telegram "Test from Preparation Station"

# Test Slack
python3 tools/notifications/send.py --channel slack "Test from Preparation Station"

# Test both
python3 tools/notifications/send.py "Test from Preparation Station"
```

## CLI usage

```bash
# Raw message
python3 tools/notifications/send.py "Hello from Preparation Station"

# Event-driven
python3 tools/notifications/send.py --event pr-opened --pr 16 --branch agent/fix-typo
python3 tools/notifications/send.py --event build-failed --branch agent/fix-typo --check ci/build
python3 tools/notifications/send.py --event task-failed --task agent/fix-typo --error "lint failed"
```

## Integration points

| Trigger | Source | Event |
|---|---|---|
| PR opened | `tools/agent_loop/baby_agent.py` | `pr-opened` |
| Task failed | `tools/agent_loop/baby_agent.py` | `task-failed` |
| State change | `tools/orchestration/queue.py` (future) | `state-change` |
| Blocker added | `tools/orchestration/queue.py` (future) | `blocker-added` |

## Security

- Tokens are never logged, printed, or committed.
- The `send.py` CLI never prints token values.
- `.env` is in `.gitignore`.
- `check_untracked.py` will flag `.env` if it somehow appears in the working tree.
