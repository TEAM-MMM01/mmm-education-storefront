# Dashboard Widgets

These dashboard widgets are the first useful views to build once OmniRoute can read GitHub,
Obsidian-selected docs, and storefront launch status.

## Preparation Station launch status

**ESA-launch candidate**. The home page has been transformed into a TEFA-ready catalog presentation per the ESA Launch Command framework. All ESA directive items are integrated (hero, curriculum lanes, catalog expansion, free resources, vendor contact, pricing framework). Build + validate + diff-check all pass. Two items require owner input: approved licensed hero photography, and curriculum lane grade-band × time matrix. Design-system base (PR #38) is merged; PR #39 is open awaiting owner review.

## Open PRs

| PR | Branch | Title | Status | Owner Approval |
|---|---|---|---|---|
| **#38** | `agent/design-system-unification` | Global design-system unification per master redesign spec | Open, ready for review | Yes (merged PR #38 required before #39 lands) |
| **#39** | `agent/esa-catalog-presentation` | ESA Launch Command framework into the home catalog | Open, code complete, awaiting review | Yes |

## Build status

- **Command**: `python3 build.py`
- **Result**: ✅ All 16 pages rebuilt cleanly
- **Latest commit**: `0bb3ff1 fix(esal-integration): handle 4× scrutiny bugs`
- **Generated pages**: index.html, store/*, general-store/*, info/* — all in sync with sources
- **Diff check**: `git diff --check` clean

## ESA product readiness

- **Pricing ladder** (owner-approved 2026-08-19): Starter $299 / Focused $1,695 / Complete $1,995 / Signature $2,495 / Structured reading $2,295
- **5-status badge taxonomy**: `.badge--available / .badge--offering-review / .badge--supplier-review / .badge--planning / .badge--retail-only`
- **Curriculum lanes**: 4 lanes with cover-art, format/status/includes/license fields, all under offering review
- **Catalog expansion**: 9 planning-concept cards (Vulturian + Math + Scientist + Studio + 5 new with grade bands)
- **Free resources**: 4 original printable worksheets + Mission Guide link + ESA launch page link for free books
- **Vendor contact**: paste-ready directive copy; Get-in-touch CTA only; inquiry-note highlight
- **Compliance strip**: Approved TEFA Marketplace Vendor / Catalog Offerings Under Review / No Payment Collected Here

## General Store preview status

General Store remains a physical-kit catalog ("Five departments, one mission") with its own `.eligible` markings and separate cart system (`preparation_station_gs_cart_v1`). No direct-commerce requirements merged; remains preview-only.

## Launch blockers

| Blocker | Item | Required owner input |
|---|---|---|
| **#1** | Hero photography: placeholder SVG currently | Approved licensed asset needed |
| **#2** | Lane grade-band × time matrix | Owner confirms grade bands × time per lane |

## Next operator actions

1. **Approve PR #39** (ESA framework integration) — code is complete, all checks pass.
2. **Deploy production** — after PR #39 merges, trigger `static.yml` workflow_dispatch (GitHub Pages at `preparation-station.pages.dev`) or `npx wrangler pages deploy . --project-name preparation-station --branch main`.
3. **Provide hero photography** — original licensed asset to replace the inline SVG placeholder.
4. **Confirm lane grade-band matrix** — owner provides grade band × weekly pace mapping for the 4 curriculum lanes.