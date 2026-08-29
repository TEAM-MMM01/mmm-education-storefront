# Preparation Station storefront

## Current launch status

**Current recommendation: publish a truthful TEFA vendor/catalog information release first.** Nationwide Acquisitions, LLC is an approved TEFA Marketplace vendor operating Preparation Station. Each offering still requires separate Odyssey review, and TEFA purchases plus official order history remain in Odyssey. General Store remains a development preview and does not accept payment.

**Live site:** https://preparationstation.org (catalog: https://preparationstation.org/catalog). Prototype hosts (`preparation-station.pages.dev`, GitHub Pages, Vercel) may lag production.

The storefront is a **public product-information preview, not a commerce launch**.
TEFA purchases and official order history remain in Odyssey. Direct checkout,
online quote intake, and customer order access stay disabled until their separate
security, product-fact, fulfillment, and owner-approval gates pass. Historical
owner-action issues #6–#8 are closed; current launch truth is maintained in
`config/project-state.json` and `LAUNCH_AUDIT.md`, not inferred from issue state.

See [LAUNCH_AUDIT.md](LAUNCH_AUDIT.md) for the keep / improve / trim / hide-relabel matrix, remaining blockers, and launch gates.
For a staged product-information release, follow
[docs/workflow/PRODUCT_INFO_SOFT_LAUNCH.md](docs/workflow/PRODUCT_INFO_SOFT_LAUNCH.md).

Canonical business/program state is recorded in
[`config/project-state.json`](config/project-state.json), and canonical starter
book records are in [`catalog/books.json`](catalog/books.json). All coding agents
must follow [`AGENTS.md`](AGENTS.md); access and PR-only write rules are described
in [`docs/workflow/AGENT_ACCESS.md`](docs/workflow/AGENT_ACCESS.md).

A self-contained storefront page for families spending TEFA and other state education
funds with Preparation Station. `index.html` is the main deliverable: one file, no build step to
view it. Open it in a browser, upload it to any static host,
or paste its contents into a vendor profile that accepts HTML.

The canonical 18-item educational catalog is in `catalog/products.json`. All
items remain price-, fulfillment-, and Odyssey-review-pending until verified.
The customer order entry point is `store/track.html`; its private API is disabled
until secure email-link authentication and customer-level authorization exist.
See `docs/workflow/ORDER_OPERATIONS.md` for historical imports, TEFA status
mirroring, and the separate direct-checkout gate.

The public information experience presents five educational product departments while
keeping all unverified prices, fulfillment promises, and product-level program claims
disabled. TEFA-funded purchases happen only in Odyssey. Direct retail checkout is a
separate future channel and remains disabled.

## Storefront pages (`store/`)

`store/shop.html`, `store/product.html`, `store/order.html`, and `store/track.html`
provide catalog browsing, a product-information request path, and a secure order-access
entry point. Product buttons remain disabled until the request backend is enabled and the
SKU is explicitly allowlisted. There is no TEFA checkout on this site: families purchase
approved offerings and review official order history in Odyssey.

Every product still needs verified catalog facts and a dedicated product detail page before
it can be enabled. The current detail-page example is the AI Literacy Bench Kit; it is not
an approved offering or a purchasable listing.

The Situation Handling & Self-Command department now includes two additions aimed at the
transition into adulthood: an **Interview & First Job Prep Kit** (mock interviews, resume
worksheet, follow-up scripts) and an **Adulting Launch Kit** (first apartment, pay stubs,
basic taxes and insurance). Both are genuinely educational, so they stay in the ESA store
rather than the General Store below.

## General Store (`general-store/`)

A second, separate prototype for retail goods — a family book (*The Vulturian*) and a
handful of original activity/coloring books — paid by card rather than invoiced through a
program. It's kept apart from the ESA store on purpose: TEFA/ESA funds cover approved
educational expenses, and a coloring book or novel invoiced alongside skill kits risks a
program questioning the invoice. See `general-store/README.md` for the full breakdown of
what's a working prototype versus what still needs a real payment processor, a real tax
rate, and real book details wired in — none of that is invented here.

## Launch blueprint

`LAUNCH_BLUEPRINT.md` defines the operator-grade Definition of Done for taking
this prototype live: storefront UX, parent/child shopping psychology, funding
program guardrails, service monetization, checkout/fulfillment operations, launch
gates, deployment/shareable-URL decisions, and first-sale workflow. Use it as the
canonical readiness checklist before removing prototype labels or publishing
commerce paths.

## Operations workflow

`docs/workflow/` documents how GitHub branches, Codex work, device sync, and pull
requests should stay organized across Mac, HP, and cloud-agent environments. Start
with `docs/workflow/NEXT_STEPS.md` for the owner-facing checklist.
`docs/obsidian/` provides the recommended Obsidian vault structure and safe note
templates. `docs/omniroute/` records the planned OmniRoute event contracts and
dashboard widgets; OmniRoute is not connected yet, so those contracts are
implementation-ready guidance rather than an active routing integration.

## Editing

Edit `src/page.html` for the main page, or anything under `store/src/` or
`general-store/src/` for the mockups, then rebuild everything at once:

```
python3 build.py
```

That inlines the four subset webfonts from `fonts/` into `index.html`, and inlines the
same fonts plus `store/shared_style.css` (shared design tokens for both mockup sets) into
each `store/*.html` and `general-store/*.html`. Editing the built files directly works
too, but the next build overwrites them.

## Owner: quick way to update the site

1. **Make your change.** Main page: `src/page.html`. Catalog/store pages:
   `store/src/*.html`. Shared style: `store/shared_style.css`. Or just tell an
   agent what to change and it will make the edit.
2. **Rebuild and check:**
   ```
   python3 build.py
   python3 tools/validate_project_state.py
   ```
3. **Commit on a branch and push:**
   ```
   git checkout -b agent/your-change
   git add -A
   git commit -m "describe the change"
   git push origin agent/your-change
   ```
4. **Open a pull request** (agents can do this for you) and look at the
   **Files changed** tab and the preview links posted on the PR before merging.
5. **Merge only after you've reviewed it.** Once you say it looks good, an
   agent can merge and the site updates automatically on Cloudflare Pages
   (https://preparation-station.pages.dev), GitHub Pages, and Vercel within a
   few minutes.

> If you edit the built `index.html` directly, the next `python3 build.py` run
> overwrites it — always edit `src/page.html` instead.

## Before any purchase path goes live

- Record verified price, availability, fulfillment, shipping, returns, and support facts
  for each enabled SKU.
- Record Odyssey approval and the offering ID before describing an item as TEFA-approved.
- Complete and test Formspree before enabling product-information requests.
- Complete hosted checkout, webhook, tax, refund, and fulfillment testing before enabling
  any direct retail purchase.
- Keep customer orders and TEFA documents in authorized private systems, never this public
  repository.

## How it is built

- **Fonts.** Satoshi (body/nav), Cabinet Grotesk (display), DM Mono (labels,
  SKUs, and ledger figures), all under the SIL Open Font License. Self-hosted
  woff2 files are subset and inlined as data URIs so the page never calls out
  to a font CDN.
- **Themes.** A single warm beige palette (`--paper: #f8f4ed`) is locked site-wide;
  there is no OS-dark override, so vendor pages always print and read the same.
- **Accessibility.** Text and control colours are checked against WCAG AA on both
  grounds. The accent splits into `--accent` for anything carrying text and
  `--accent-lit` for decoration only, because the brighter tone does not hold
  contrast as small type on the light paper.
- **Print.** Families print vendor pages for their funding file, so there is a print
  stylesheet: navigation and buttons drop out, the dark bands invert to white, and
  FAQ answers expand.
- **Motion.** A staged hero reveal and scroll-triggered fades, both disabled under
  `prefers-reduced-motion`.
