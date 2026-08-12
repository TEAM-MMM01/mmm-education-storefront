# Session State — Preparation Station

**Last updated:** 2026-08-11T21:00:00Z
**Session:** mmm-education-storefront

---

## Current Branch State

| Branch | PR | Status | Last Action |
|---|---|---|---|
| `agent/esa-landing-page` | #18 | DRAFT | netlify.toml + operating contract + deferred tasks pushed |
| `agent/agent-loop` | #16 | MERGED | Audit fixes pushed |
| `agent/orchestration-bootstrap` | #15 | MERGED | Audit fixes pushed |
| `agent/sync-bootstrap` | #14 | MERGED | No changes needed |
| `agent/readme-esa-only-clarification` | #17 | MERGED | Clean — no changes needed |
| `main` | — | — | All PRs merged |

## Open Locks (require Richie decision)

| Lock | Item | Status | Decision Needed |
|---|---|---|---|
| LOCK-4 | HermesOS-Vault (3 GiB) | No remote, live token | Tarball+rotate, push-to-private-repo, or status quo |
| LOCK-5 | OmniRoute wiring | Unknown | Which provider keys loaded? |
| LOCK-6 | royal-collexions-commerce repo | 404 | Create or delete? |
| LOCK-7 | HP visibility | Zero from Mac | Wipe + re-clone, or leave offline |

## Completed This Session

- [x] PR #13 merged (gitignore guard + check_untracked)
- [x] PRs #14-17 merged (sync, orchestration, agent-loop, README)
- [x] PR #18 opened (ESA landing page + netlify.toml + catalog)
- [x] Telegram + Slack notification module built and wired
- [x] Keychain credentials stored for all 6 Telegram bots + Slack
- [x] Slack notifications working
- [x] Storage cleanup: 5 GiB → 16 GiB free (11 GiB recovered)
- [x] Facebook Marketplace listing created
- [x] Full audit of PRs 14-17
- [x] Critical fixes pushed to PRs #15 and #16
- [x] Outschool TEFA page fetched as ESA reference
- [x] New Prep Station bot token stored + tested
- [x] All 6 bot descriptions updated
- [x] Branch protection enforcement enabled (enforce_admins: true)
- [x] netlify.toml created + pushed
- [x] Codex/Devin access policy reviewed + approved
- [x] Deferred tasks mapped to docs/DEFERRED-TASKS.md
- [x] HermesOS Operating Contract created at docs/HERMESOS-OPERATING-CONTRACT.md

## Bot Mapping (final)

| Bot | Username | Display Name | Purpose |
|---|---|---|---|
| Hermes COO | @Hermes_OS1bot | Hermes COO | Task routing, audit, orchestration |
| Prep Station | @HermesPrepStation_Bot | Prep Station | Education/TEFA operations |
| Hermes Voice | @HermesOS2_Bot | Hermes Voice | Voice input |
| Hermes PF | @RichieRichPF_bot | Hermes PF | PumpFun trading |
| Royal Collexions | @RoyalCXL_Bot | Royal Collexions | Shopify commerce |
| The Oracle | @OracleSignalsProphet_Bot | The Oracle | Trading signals |

All bots route to chat ID: 7584154252 (Richie Rich)

## Pending Tasks (next session)

### Immediate
1. Wire new Prep Station bot into notification module
2. Update notification module to support voice bot
3. Merge PR #18 (ESA landing page)
4. Link Netlify project to main branch in dashboard

### Medium-term
1. Resolve HermesOS-Vault disposition (LOCK-4)
2. Resolve royal-collexions-commerce repo (LOCK-6)
3. Confirm OmniRoute provider keys (LOCK-5)
4. Set up HP as secondary executor (when ready)
5. Voice bot integration (Hermes Voice)
6. Create remaining Slack channels

### Long-term
1. OpenCode agent configs
2. Device conflict prevention (writer leasing)
3. Full COO workflow lifecycle
4. Automation (manual sync → limited)

## Key Files

| File | Purpose |
|---|---|
| `config/project-state.json` | Canonical business state |
| `catalog/books.json` | Product catalog (4 items) |
| `catalog/products.json` | Product catalog (14 items, 6 categories) |
| `AGENTS.md` | Agent instructions |
| `docs/DEFERRED-TASKS.md` | All deferred tasks mapped |
| `docs/HERMESOS-OPERATING-CONTRACT.md` | Operating contract |
| `docs/workflow/SYNC_RUNBOOK.md` | Device sync recipe |
| `docs/workflow/NOTIFICATIONS.md` | Notification setup |
| `docs/workflow/DEVICE_SYNC.md` | Source-of-truth table |
| `tools/agent_loop/baby_agent.py` | Baby-agent orchestrator |
| `tools/orchestration/queue.py` | 8-state workflow queue |
| `tools/notifications/__init__.py` | Telegram + Slack senders |
| `netlify.toml` | Netlify deploy config |

## Disk State

- **Available:** ~16 GiB (50% used)
- **Ollama models:** Cleared (8.1G recovered)
- **Keychain:** All 6 Telegram bot tokens + chat ID + Slack bot token + webhook URL
- **Shell exports:** Added to `~/.zshrc` from Keychain

## CodeQL Status

- **PR #15**: False positive on `HERMES_MAC_QUEUE_ROOT` env var path injection
- **Status**: Resolved via admin merge — dismissed
