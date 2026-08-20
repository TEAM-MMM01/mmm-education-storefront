# Dashboard Widgets

These dashboard widgets are the first useful views to build once OmniRoute can read GitHub,
Obsidian-selected docs, and storefront launch status.

## Preparation Station launch status

**Blocked — not a launch candidate**. `config/pages-release.json` keeps `deployment_enabled: false` with an empty `release_skus` list, so no offering is verified for release and the site must not be deployed. The home page presents a TEFA-ready catalog, but every catalog item remains "Coming soon" behind the single-SKU gate and no verified pricing is published. Launch remains blocked until the canonical catalog records a verified, allowlisted release SKU. Owner inputs still outstanding: approved licensed hero photography, and curriculum lane grade-band × time matrix.

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

- **Pricing**: No verified prices published. Every catalog record remains `price_status: illustrative_unverified` with `retail_price_usd: null`; prices are set only at each offering's Odyssey review.
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

1. **Do not deploy** — `config/pages-release.json` keeps `deployment_enabled: false` with no verified release SKU. Deployment stays blocked until a verified, allowlisted offering is recorded.
2. **Verify a release offering** — record a verified Odyssey offering in the canonical catalog and add its SKU to `release_skus` before any launch is considered.
3. **Provide hero photography** — original licensed asset to replace the inline SVG placeholder.
4. **Confirm lane grade-band matrix** — owner provides grade band × weekly pace mapping for the 4 curriculum lanes.