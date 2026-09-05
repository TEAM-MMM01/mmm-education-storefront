# Session State — Preparation Station

**Last updated:** 2026-08-24
**Session:** mmm-education-storefront
**Resumption point:** Continue from here on next session

---

## SITE STATUS

**Deploy target:** Vercel (not Netlify — netlify.toml is legacy)
**Live URL:** https://preparationstation.org
**Domain:** preparationstation.org (owned)
**Status:** ESA landing page LIVE with all sub-pages deployed

### Email Addresses
- Hello@preparationstation.org — general support
- Sales@preparationstation.org — sales inquiries
- Support@preparationstation.org — help/support

### Live Pages (all return 200)
- `/` — ESA landing page (hero, how-it-works, catalog, FAQ, CTA)
- `/about` — About page
- `/contact` — Contact page
- `/faq` — FAQ page
- `/esa` — ESA info page
- `/tefa` — TEFA Marketplace info page
- `/privacy` — Privacy policy
- `/terms` — Terms of service
- `/shipping` — Shipping info
- `/shop-by-age` — Shop by age

### Still Needed
- Testimonials section (optional but recommended)
- TEFA submission email (draft at `docs/tefa-email-draft.md`)

---

## CURRENT BRANCH STATE

| Branch | PR | Status | Last Action |
|---|---|---|---|
| `main` | — | — | All PRs 13-17, 18, 38, 41-52 merged |

---

## WHAT'S BEEN COMPLETED

### Core Infrastructure
- [x] PR #13-17 merged (gitignore, sync, orchestration, agent-loop, README)
- [x] PR #18 merged (ESA landing page)
- [x] PR #38 merged (design system unification)
- [x] PR #41-52 merged (various improvements)
- [x] Branch protection enforcement enabled
- [x] Codex/Devin access policy reviewed + approved

### Bots & Notifications
- [x] All 6 Telegram bots verified live
  - Hermes COO (@Hermes_OS1bot) ✅
  - Prep Station (@HermesPrepStation_Bot) ✅
  - Hermes Voice (@HermesOS2_Bot) ✅ — correct token found
  - Hermes PF (@RichieRichPF_bot) ✅
  - Royal Collexions (@RoyalCXL_Bot) ✅
  - The Oracle (@OracleSignalsProphet_Bot) ✅
- [x] Telegram notifications working
- [x] iMessage notifications working

### Kanban Dashboard
- [x] Dashboard rebuilt with original animated design
- [x] Server with all 10 endpoints functional
- [x] Always-on via cron auto-restart
- [x] Voice, AI chat, agent spawning, templates — all working

### Documentation
- [x] HermesOS Operating Contract created
- [x] All skills/prompts/loops audited
- [x] Session state updated
- [x] Deferred tasks updated

---

## OPEN LOCKS (require Richie decision)

| Lock | Item | Status | Decision Needed |
|---|---|---|---|
| LOCK-4 | HermesOS-Vault (3 GiB) | No remote, live token | Tarball+rotate, push-to-private-repo, or status quo |
| LOCK-5 | OmniRoute wiring | Unknown | Which provider keys loaded? |
| LOCK-6 | royal-collexions-commerce repo | 404 | Create or delete? |
| LOCK-7 | HP visibility | Zero from Mac | Wipe + re-clone, or leave offline |

---

## BOT MAPPING (final)

| Bot | Username | Display Name | Purpose | Status |
|---|---|---|---|---|
| Hermes COO | @Hermes_OS1bot | Hermes COO | Task routing, audit, orchestration | ✅ Live |
| Prep Station | @HermesPrepStation_Bot | Prep Station | Education/TEFA operations | ✅ Live |
| Hermes Voice | @HermesOS2_Bot | Hermes Voice | Voice input | ✅ Live (token: AAH2tp...) |
| Hermes PF | @RichieRichPF_bot | Hermes PF | PumpFun trading | ✅ Live |
| Royal Collexions | @RoyalCXL_Bot | Royal Collexions | Shopify commerce | ✅ Live |
| The Oracle | @OracleSignalsProphet_Bot | The Oracle | Trading signals | ✅ Live |

All bots route to chat ID `7584154252`.

---

## VAULT SYNC (Mac ↔ HP)

**Vault repo:** TEAM-MMM01/obsidian-vault (pushed, has HermesOS structure)
**Sync method:** Edit on Mac → push to GitHub → pull on HP (manual, no auto-sync)

---

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

---

## DISK STATE

- **Available:** ~16 GiB (80% used of 228 GiB)
- **Keychain:** Telegram bot tokens, chat ID stored by named reference only
- **Shell exports:** Added to `~/.zshrc`

---

## WHAT'S NEXT (priority order)

### Immediate (today)
1. ~~Merge PR #18~~ ✅
2. ~~Link deploy to main branch~~ ✅ (Vercel)
3. ~~Test deploy~~ ✅
4. ~~Submit site~~ ✅
5. ~~Create The Oracle bot via BotFather~~ ✅ DONE
6. Get proper Slack bot token (xoxb- format)

### This week
1. Resolve LOCK-4 through LOCK-7 (all need Richie decision)
2. Send TEFA submission email (draft at `docs/tefa-email-draft.md`)
3. Close stale PRs #39, #40, #43 (already closed)

### Next week
1. Set up HP when ready
2. Create remaining Slack channels
3. Full COO workflow lifecycle
