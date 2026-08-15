# Session State — Preparation Station

**Last updated:** 2026-08-12T01:00:00Z
**Session:** mmm-education-storefront
**Resumption point:** Continue from here on next session

---

## SITE SUBMISSION STATUS

**Deadline:** Monday Aug 11 — now overdue (Wednesday Aug 12)
**What's done:** ESA landing page with hero, how-it-works, catalog (18 products), important dates, why-choose-us, FAQ, CTA, footer
**What's missing:** Testimonials section, Netlify deploy to production
**What's blocking:** Merge PR #18 + link Netlify to main branch

### To finish the site (in order):
1. Merge PR #18 (ESA landing page) — waiting on Richie
2. Link Netlify project to main branch — Richie doing now
3. Add testimonials section (optional but recommended)
4. Test deploy on Netlify
5. Submit

---

## CURRENT BRANCH STATE

| Branch | PR | Status | Last Action |
|---|---|---|---|
| `agent/esa-landing-page` | #18 | DRAFT | netlify.toml + vault + operating contract pushed |
| `main` | — | — | All PRs 13-17 merged |

## COMPLETED THIS SESSION

- [x] PR #13 merged (gitignore guard + check_untracked)
- [x] PRs #14-17 merged (sync, orchestration, agent-loop, README)
- [x] PR #18 opened (ESA landing page + netlify.toml + catalog)
- [x] New Prep Station bot token stored + tested (@HermesPrepStation_Bot)
- [x] All 6 bot descriptions updated
- [x] Branch protection enforcement enabled (enforce_admins: true)
- [x] netlify.toml created + pushed
- [x] Codex/Devin access policy reviewed + approved
- [x] Deferred tasks mapped to docs/DEFERRED-TASKS.md
- [x] HermesOS Operating Contract created at docs/HERMESOS-OPERATING-CONTRACT.md
- [x] Vault structure created on GitHub (9 files pushed to obsidian-vault)
- [x] Slack notifications working
- [x] Storage cleanup: 11 GiB recovered
- [x] Facebook Marketplace listing created
- [x] Full audit of PRs 14-17

## OPEN LOCKS (require Richie decision)

| Lock | Item | Status | Decision Needed |
|---|---|---|---|
| LOCK-4 | HermesOS-Vault (3 GiB) | No remote, live token | Tarball+rotate, push-to-private-repo, or status quo |
| LOCK-5 | OmniRoute wiring | Unknown | Which provider keys loaded? |
| LOCK-6 | royal-collexions-commerce repo | 404 | Create or delete? |
| LOCK-7 | HP visibility | Zero from Mac | Wipe + re-clone, or leave offline |

## BOT MAPPING (final)

| Bot | Username | Display Name | Purpose |
|---|---|---|---|
| Hermes COO | @Hermes_OS1bot | Hermes COO | Task routing, audit, orchestration |
| Prep Station | @HermesPrepStation_Bot | Prep Station | Education/TEFA operations |
| Hermes Voice | @HermesOS2_Bot | Hermes Voice | Voice input |
| Hermes PF | @RichieRichPF_bot | Hermes PF | PumpFun trading |
| Royal Collexions | @RoyalCXL_Bot | Royal Collexions | Shopify commerce |
| The Oracle | @OracleSignalsProphet_Bot | The Oracle | Trading signals |

All bots route to chat ID: 7584154252 (Richie Rich)

## VAULT SYNC (Mac ↔ HP)

**Vault repo:** TEAM-MMM01/obsidian-vault (pushed, has HermesOS structure)
**Structure created:**
```
00-HQ/HermesOS/
├── Operating-Contract/
│   ├── shared-operating-memory.json
│   ├── operating-contract.md
│   ├── routing-policy.md
│   └── memory-write-policy.md
├── State/
│   ├── active-primary.md
│   ├── current-task-ledger.md
│   ├── pending-approvals.md
│   └── handoffs/
├── Runbooks/
│   ├── mac-startup.md
│   └── hp-travel-mode.md
├── Decisions/
│   ├── approved/
│   ├── proposed/
│   └── superseded/
└── Evidence/
    ├── validation/
    ├── incidents/
    └── releases/
```

**Sync method:** Edit on Mac → push to GitHub → pull on HP (manual, no auto-sync)

## KEY FILES

| File | Purpose |
|---|---|
| `config/project-state.json` | Canonical business state |
| `catalog/books.json` | Product catalog (4 items) |
| `catalog/products.json` | Product catalog (14 items, 6 categories) |
| `AGENTS.md` | Agent instructions |
| `docs/DEFERRED-TASKS.md` | All deferred tasks mapped |
| `docs/HERMESOS-OPERATING-CONTRACT.md` | Operating contract |
| `docs/session-state.md` | THIS FILE — resume here |
| `docs/workflow/SYNC_RUNBOOK.md` | Device sync recipe |
| `docs/workflow/NOTIFICATIONS.md` | Notification setup |
| `esa.html` | ESA landing page |
| `esa-style.css` | ESA page styles |
| `netlify.toml` | Netlify deploy config |
| `tools/notifications/__init__.py` | Telegram + Slack senders |
| `tools/orchestration/queue.py` | 8-state workflow queue |

## DISK STATE

- **Available:** ~16 GiB (80% used of 228 GiB)
- **Keychain:** All 6 Telegram bot tokens + chat ID + Slack bot token + webhook URL
- **Shell exports:** Added to `~/.zshrc`

## WHAT'S NEXT (priority order)

### Immediate (today)
1. Merge PR #18 (ESA landing page)
2. Link Netlify to main branch
3. Test deploy
4. Submit site (overdue since Monday)

### This week
1. Resolve LOCK-4 through LOCK-7 (all need Richie decision)
2. Delete stale repos (desktop-tutorial, my-react-app, etc.)
3. Clear Mac disk space (see SPACE-CLEARING.md)

### Next week
1. Set up HP when ready
2. Create remaining Slack channels
3. Voice bot integration
4. Full COO workflow lifecycle
