# Deferred Tasks — Preparation Station

**Last updated:** 2026-08-11
**Source:** Session state, project-state.json, AGENTS.md, architecture review

---

## LOCKS (require Richie decision)

| Lock | Item | Status | Decision Needed | Priority |
|---|---|---|---|---|
| LOCK-2 | Telegram bot token | **Fixed** — new Prep Station bot stored | None — done | ✅ |
| LOCK-4 | HermesOS-Vault (3 GiB) | No remote, live token in vault | Tarball+rotate, push-to-private-repo, or status quo | High |
| LOCK-5 | OmniRoute wiring | Unknown which provider keys loaded | Confirm which keys are active | Medium |
| LOCK-6 | royal-collexions-commerce repo | 404 on GitHub | Create or delete? | Medium |
| LOCK-7 | HP visibility | Zero from Mac | Wipe + re-clone, or leave offline | Low — HP not required for Mac to function |

---

## BLOCKED (waiting on external action)

| Task | Blocker | What's Needed |
|---|---|---|
| Merge PRs 14-17 | CodeQL false positive on PR #15 | Dismiss in GitHub Security tab |
| Merge PR #18 (ESA landing page) | Draft status | Review + merge |
| Telegram notifications | Token fixed ✅ | Wire into notification module |
| Hermes Voice bot | Not created via BotFather | Create @HermesVoice_bot, paste token |
| Slack channels | Only #hermesos-ops active | Create #preparation-station, #pumpfun, #royal-collexions, #oracle |
| Netlify deploy | netlify.toml pushed ✅ | Link project to main branch in dashboard |
| Claude/Devin GitHub access | Issue #5 | Set up separate GitHub Apps |

---

## IN PROGRESS

| Task | Status | Next Step |
|---|---|---|
| ESA landing page (PR #18) | Draft, catalog integrated | Review + merge |
| Bot descriptions | All 6 updated ✅ | Done |
| Branch protection | enforce_admins enabled ✅ | Done |
| netlify.toml | Created + pushed ✅ | Link in Netlify dashboard |
| Notification module | Built + wired | Test with new Prep Station bot |
| Codex/Devin access policy | Reviewed + approved | Enable on remaining repos |

---

## QUEUED (after blockers clear)

### Immediate (this session)
1. ~~Store new Prep Station bot token~~ ✅
2. ~~Update all bot descriptions~~ ✅
3. ~~Enable branch protection enforcement~~ ✅
4. ~~Create netlify.toml~~ ✅
5. Wire new Prep Station bot into notification module
6. Update notification module to support voice bot
7. Merge PR #18 (ESA landing page)

### Next (after PRs merge)
1. Design full ESA landing page (Outschool reference)
2. Wire Telegram notifications with new bot
3. Create remaining Slack channels
4. Set up Netlify deploy gating from main
5. Add AGENTS.md to repos where agents write code (not all repos)

### Medium-term
1. Resolve HermesOS-Vault disposition (LOCK-4)
2. Resolve royal-collexions-commerce repo (LOCK-6)
3. Confirm OmniRoute provider keys (LOCK-5)
4. Set up HP as secondary executor (when ready)
5. Voice bot integration (Hermes Voice)
6. Build the HermesOS Operating Contract doc structure

### Long-term
1. OpenCode agent configs (`.opencode/agents/`, `.opencode/commands/`)
2. Device conflict prevention (writer leasing)
3. Full COO workflow lifecycle (14-step)
4. Automation (manual sync → limited automation)
5. Netlify production deploy verification flow

---

## COMPLETED THIS SESSION

- [x] PR #13 merged (gitignore guard + check_untracked)
- [x] PR #14 opened (sync runbook)
- [x] PR #15 opened (orchestration tools)
- [x] PR #16 opened (baby-agent harness + notifications)
- [x] PR #17 opened (README ESA-only)
- [x] Telegram + Slack notification module built and wired
- [x] Keychain credentials stored for Telegram + Slack
- [x] Slack notifications working
- [x] Storage cleanup: 5 GiB → 16 GiB free
- [x] Facebook Marketplace listing created
- [x] Full audit of PRs 14-17
- [x] Critical fixes pushed to PRs #15 and #16
- [x] Outschool TEFA page fetched as ESA reference
- [x] New Prep Station bot token stored + tested
- [x] All 6 bot descriptions updated
- [x] Branch protection enforcement enabled
- [x] netlify.toml created + pushed
- [x] Codex/Devin access policy reviewed

---

## AUDIT FINDINGS (deferred, lower priority)

| Finding | PR | Reason |
|---|---|---|
| No state transition validation | #15 | Requires design decision — which transitions are valid? |
| "Pure local" claim false for connectivity.py | #15 | Already documented as opt-in |
| `retry_count` increments on any set to "Remote Attempted" | #15 | Needs policy decision |
| No concurrency guard | #16 | Low risk — agents use separate branches |
| `send_telegram()` embeds token in URL | #16 | Standard URL construction; logging middleware is real risk |
| Notification failures silently swallowed | #16 | "Best-effort" is intentional |

---

## REFERENCE: ARCHITECTURE LAYERS

```
HERMESOS OPERATING CONTRACT
├── 01 Governance     — authority, risk tiers, approvals, completion rules
├── 02 Identity       — HermesOS, COO, specialist agents, canonical names
├── 03 Routing        — Slack channels, Telegram bots, webhooks
├── 04 Execution      — Mac, HP/NemoClaw, models, agent boundaries
├── 05 Repository     — Codex/Devin policy, branching, PRs, merge restrictions
└── 06 Secrets        — named secret references only; no values in docs/git
```

## REFERENCE: DEVICE PROFILES

| Device | Model | Role | Best Tasks | Avoid |
|---|---|---|---|---|
| Mac | MiMo V2 | Control plane | Repo changes, approvals, config, deploy prep, docs | Noisy background jobs, long monitoring |
| HP | NemoClaw | Worker plane | Monitoring, research, batch ops, signal support, voice | Final production truth, secrets-heavy governance |

## REFERENCE: BOT MAPPING

| Bot | Username | Purpose | Channel |
|---|---|---|---|
| Hermes COO | @Hermes_OS1bot | Task routing, audit, orchestration | All businesses |
| Prep Station | @HermesPrepStation_Bot | Education/TEFA operations | Preparation Station |
| Hermes Voice | @HermesOS2_Bot | Voice input | HermesOS |
| Hermes PF | @RichieRichPF_bot | PumpFun trading | Hermes PF |
| Royal Collexions | @RoyalCXL_Bot | Shopify commerce | Royal Collexions |
| The Oracle | @OracleSignalsProphet_Bot | Trading signals | The Oracle |

## REFERENCE: WORKFLOW STATES (8)

1. `DRAFT`
2. `QUEUED`
3. `PLANNING`
4. `APPROVED`
5. `IMPLEMENTING`
6. `VALIDATING`
7. `READY_FOR_PR`
8. `COMPLETE_VERIFIED`

Additional terminal states: `BLOCKED`, `FAILED_WITH_EVIDENCE`, `CANCELLED`
