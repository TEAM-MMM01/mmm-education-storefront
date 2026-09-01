# ESA Launch Command — production integration

This changelog maps the ESA Launch Command framework
(esa-launch-command.richie-rich007.chatgpt.site) into the live Preparation
Station website. It records how each directive requirement was converted
into a real, committed change on `agent/esa-catalog-presentation`.

All edits obey the standing repo rules:
- Verified in-repo facts only (no invented pricing, eligibility, or coverage).
- Never describe a product as TEFA-/PDSES-eligible without current evidence.
- AGENTS.md source-of-truth facts dominate (Vulturian = confirmed title,
  details pending; PDSES/ClassWallet not confirmed; legal entity reserved
  for business-information contexts).
- One focused change per PR; PR depends on the design-system base (PR #38).
- Branch: `agent/esa-catalog-presentation` (off the design-system branch).

## 1. Deliverable inventory

| ESA framework item | Where it lives in the production site |
|---|---|
| Hero visual (original illustration) | `src/page.html` hero right column, inline SVG panel + caption |
| Hero compliance strip (exact directive wording) | `src/page.html` hero chips |
| 4 guided curriculum lanes with covers + full product-card fields | `src/page.html` new `#curricula` section |
| Catalog expansion (9 planning concepts) | `src/page.html` new `#expansion` section |
| Free resource library (4 printable worksheets + guided plan + free books) | `src/page.html` new `#resources` section + `resources/*.html` |
| Vendor contact panel + TEFA summary | `src/page.html` new `#vendor` section |
| Pricing ladder (owner-approved 2026-08-19) | `src/page.html` new `#pricing` section |
| 5-status badge taxonomy | `src/base/design-system.css` (`--badge-*` tokens + `.badge--available`, `.badge--offering-review`, `.badge--supplier-review`, `.badge--planning`, `.badge--retail-only`) |
| Cover-art tiles (original SVG, no licensed stock photos) | `src/base/design-system.css` `.cover-art` + `.cover--career/living/ai/reading/math/sci/studio/vulturian/tools/family` |
| Lane-card component (meta dl of format/status/includes/license) | `src/base/design-system.css` `.lane-card` |
| Resource-tile component | `src/base/design-system.css` `.resource-tile` |
| Vendor-grid panel | `src/base/design-system.css` `.vendor-grid` / `.vendor-panel` / `.inquiry-note` |

## 2. Directive-by-directive checklist

| Directive requirement | Status | Notes |
|---|---|---|
| Hero visual, original/owned only | Done | Flat inline SVG workspace scene; caption "approved photography to follow" |
| Consistent visual treatment for each core lane | Done | 4 `.cover-art` gradient + SVG motif tiles per lane |
| Catalog-expansion visuals (Vulturian, Math, Scientist, Studio) | Done | All four rendered as cards with SVG covers |
| Free-resource tiles (budget, paycheck, savings, business idea, plan) | Done | 4 original printable worksheets + Mission Guide link + ESA launch page link for free books |
| Consistent product-card system (image, name, grade band, format, outcome, status, CTA) | Done on home cards | Lane cards include all fields; expansion cards include grade band only where the directive specified it |
| 5 new expansion offerings | Done | Financial Literacy G6–12, Business Builder G8–12, Home Systems G6–12, Career Journal G6–10, Family Pacing all |
| Apply status taxonomy (Available / Offering Review / Supplier Review / Planning Concept / Direct Retail Only) | Done | Tokens + classes defined; cards use `.badge--offering-review` (lanes) and `.badge--planning` (expansion + Vulturian) |
| Never display item as TEFA-eligible unless verified | Honored | All entry badges are `offering-review` or `planning`; no "available" badges in expansion section |
| Vendor contact section (paste-ready copy) | Done | `#vendor` section, exact directive wording |
| TEFA summary paragraph (paste-ready copy) | Done | `#vendor` right panel, exact directive wording |
| Add real URL only after confirming | Honored | Canonical production domain is recorded in project state |
| Add contact email / phone only after confirming | Honored | Leftover address-permitted-routes replaced with "Get in touch" CTA (no raw email/phone) |
| Keep PDSES/ClassWallet separate from TEFA | Honored | `#vendor` + status page mention PDSES as "not yet confirmed" |
| TEFA note (approved vendor, individual offerings reviewed separately) | Done | In `#vendor` panel |
| Inquiry note (no student records, health, payment, credentials via forms) | Done | `.inquiry-note` highlight inside `#vendor` |
| Compliance strip wording (Approved TEFA Marketplace Vendor / Catalog Offerings Under Review / No Payment Collected Here) | Done | Hero chips now match directive wording exactly |
| Retail/TEFA pricing separation note | Done | Bullet list in `#pricing` section |
| Price-includes note (one-time family license, lessons, facilitator) | Done | In `#pricing` lead paragraph |
| Family/browse-by-age/TEFA/schools journeys all reach a useful CTA | Honored | Every card has a "Plan this lane" or "Get in touch" CTA |
| Never animate pricing, approval, or purchase instructions | Honored | No entry/exit animations on cards or content; only the existing `.reveal` opacity+transform module |
| Responsive at 375px→desktop | Done | All new grids collapse to 1-column at 760px; existing breakpoint honored |
| Validate before deploy | Done | `build.py` ✅, `validate_project_state.py` ✅, `git diff --check` ✅, HTML parse ✅ |

## 3. What is NOT done (known gaps, for transparency)

| Item | Reason | Recommended next step |
|---|---|---|
| Store shop "Under offering review" badges not retokened to the new taxonomy | Store uses its own visual style (`.eligible` monospace uppercase). Swap changes the store aesthetic and needs a per-page design decision. | Store component review in a separate PR. |
| Licensed hero photography | The directive permits original/owned only; we shipped an original SVG scene. A real photo changes the seller trust signal and needs a licensed source. | Owner provides approved photography asset. |
| Curriculum-lane grade bands and weekly-time fields | Not stated in the directive for the lanes; in-repo data covers only the pricing ladder. Adding fields would be invented. | Owner confirms grade band × time matrix per lane. |
| Service-level response time / guaranteed maintenance | Not in scope for the marketing presentation. | Add when TEFA reviewers request it. |
| Production deploy | AGENTS.md requires explicit owner approval before deploy. | Owner approves; deploy via `static.yml` workflow_dispatch (or wrangler for Cloudflare). |

## 4. Verification

```bash
python3 build.py                        # ✅ all 16 pages
python3 tools/validate_project_state.py # ✅ valid
git diff --check                        # ✅ clean
```

## 5. Branch + PR

- Branch: `agent/esa-catalog-presentation`
- Base: `agent/design-system-unification` HEAD (PR #38 must merge first)
- PR: opened after this commit; awaits owner review.

## 6. Date

2026-08-19.