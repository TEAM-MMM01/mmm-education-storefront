# Preparation Station — Design System

Source of truth: `src/base/design-system.css` (inlined into every page by
`build.py`). This document is the component map + implementation brief for
any agent building on the system.

Art direction: warm, practical, premium, family-trustworthy, curriculum-forward.
Brand: **Preparation Station**. Tagline: **"Practical curriculum for life ahead."**

---

## 1. Deliverable inventory

| Artifact | Location | Status |
|---|---|---|
| CSS (token + component layer) | `src/base/design-system.css` | ✅ live |
| Page-layer CSS (fonts + page-specific) | `src/info/shared.css`, `store/shared_style.css` | ✅ live |
| Build composition | `build.py` (`__INFO_SHARED_CSS__`, `__STORE_SHARED_CSS__` markers) | ✅ live |
| Global header/footer lockup (all 16 pages) | every page's `<header class="site-header">` / `<footer class="site-footer">` | ✅ live |
| Components (cards w/ media, badges, tabs, timeline, CTA band) | defined in base CSS, **adoption pending** on page markup | ⏳ ready |
| Design-system starter (owner source) | `/Users/queent./Downloads/preparation-station-design-system.css` | reference |

## 2. Rules (non-negotiable)

1. **Brand lockup is identical sitewide** — wordmark + tagline; no per-page variations.
2. **Nationwide Acquisitions, LLC appears only in business-information contexts**:
   About, TEFA guide, Terms, Privacy, Shipping. Never in the global header/footer,
   home, stores, FAQ, Contact, By Age, or Funding Help consumer layouts.
3. **No raw public email display.** Use *Get in touch* CTAs → `contact.html`.
   Functional mailto routes stay only where they power a flow: the contact-page
   request button, the Mission Guide builder (JS), the TEFA vendor contact block.
4. **Product cards are image-ready**: every card includes `.card__media`
   (4:3, gradient placeholder, no fake product photos — use category artwork
   or the placeholder).
5. **Motion** follows `docs/workflow/MOTION_SYSTEM.md`: transform/opacity only,
   160/220/320/520ms tokens, reveals gated behind `<html class="js">` (reuse
   `.reveal` / `.stagger` — never add a second reveal system).
6. **Never animate pricing, approval status, or purchase instructions.**

## 3. Component map

| Component | Classes | Purpose | Status |
|---|---|---|---|
| Header | `.site-header`, `.site-header__inner`, `.brand`, `.brand__wordmark`, `.brand__tagline`, `.site-nav`, `.site-nav__list`, `.site-nav__link`, `.header-actions` | Global lockup + nav + Start a Request CTA | ✅ live |
| Buttons | `.btn`, `.btn--primary`, `.btn--secondary`, `.btn--ghost`, `.arr` | CTAs, controls (44px min target) | ✅ live |
| Footer | `.site-footer`, `.site-footer__grid`, `.footer-brand`, `.footer-heading`, `.footer-links`, `.footer-note` | Support/legal links, compliance notes | ✅ live |
| Badges | `.badge`, `.badge--approved`, `.badge--review`, `.badge--info` | Status language (approved / in review / informational) | ⏳ adopt |
| Card | `.card`, `.card__media`, `.card__media img`, `.card__body`, `.card__eyebrow`, `.card__title`, `.card__meta`, `.card__footer`, `.price` | Product/category cards | ⏳ adopt |
| Tabs / filters | `.tab-row`, `.tab`, `.filter-chip`, `.is-active` | By Age banding, catalog filters | ⏳ adopt |
| Timeline | `.timeline-list`, `.timeline-card`, `.timeline-card__number`, `.timeline-card__label`, `.timeline-card__title`, `.timeline-card__cta` | Age-band readiness views, pathway steps | ⏳ adopt |
| Trust strip | `.trust-strip`, `.trust-item`, `.trust-item__icon` | Proof points (approved vendor, review process) | ⏳ extend |
| CTA band | `.cta-band` | End-of-page conversion strip | ⏳ adopt |
| Forms | `.form-grid`, `.field`, `.label`, `.input`, `.select`, `.textarea`, `.help-text` | Contact/request forms | ⏳ adopt |
| Tables | `.table-wrap`, `th`, `td` | Pricing/status matrices (e.g. TEFA guide) | ✅ live (tefa-table variant) |
| Hero | `.hero`, `.hero__grid`, `.hero__content`, `.hero__actions`, `.hero__badges`, `.hero__panel` | Landing hero | ⏳ adopt |
| Shell | `.page-shell`, `.page-section`, `.section-heading`, `.eyebrow` | Layout scaffolding | ✅ live (`.wrap`/`.band` aliases) |
| Utilities | `.stack-sm/md/lg`, `.cluster`, `.centered`, `.surface-panel` | Composition helpers | ✅ live |

## 4. Page-by-page mapping

| Page | Build source | Purpose | Uses |
|---|---|---|---|
| Home | `src/page.html` → `index.html` | Landing: hero, trust strip, mission guide launcher | header/footer ✅; hero + trust-item partially; inner retoken pending |
| Catalog | `store/src/shop.html` (+product/order/track) | ESA storefront: product/category browsing, offering status, order/quote | header/footer ✅; badges + `.card__media` next |
| By Age | `src/info/shop-by-age.html` | Readiness/age browsing (distinct from Catalog) | header/footer ✅; tabs + timeline-card next |
| Mission Guide | `index.html#guide` (home section) | Guided selector building a request list | header/footer ✅ |
| Funding Help | `esa.html` (standalone, `esa-style.css` + inlined base) | TEFA/ESA funding explainer | header/footer ✅; inner retoken pending |
| About | `src/info/about.html` | Mission, vendor approval, entity disclosure (approved context) | header/footer ✅ |
| Contact | `src/info/contact.html` | Request form (Formspree) + email button (no visible address) | header/footer ✅; forms next |
| FAQ | `src/info/faq.html` | Questions, service boundaries | header/footer ✅ |
| Legal/footer pages | `src/info/{privacy,terms,shipping}.html` | Policies; entity retained (business context) | header/footer ✅ |
| TEFA guide | `src/info/tefa.html` | Reviewer-facing guide; entity + vendor contact block retained | header/footer ✅; tefa-table ✅ |
| General Store | `general-store/src/*` | Retail preview (Royal Collexions boundary); separate cart system | header/footer ✅ |

## 5. Implementation brief (where each class is used)

- **Header block** (copy this skeleton onto any new page; paths relative to page location):

```html
<header class="site-header">
  <div class="wrap site-header__inner">
    <a class="brand" href="MAIN_SITE_URL">
      <span class="brand__wordmark">Preparation Station</span>
      <span class="brand__tagline">Practical curriculum for life ahead.</span>
    </a>
    <nav class="site-nav" aria-label="Main">
      <ul class="site-nav__list">
        <li><a class="site-nav__link" href="MAIN_SITE_URL">Home</a></li>
        <li><a class="site-nav__link" href="store/shop.html">Catalog</a></li>
        <li><a class="site-nav__link" href="shop-by-age.html">By Age</a></li>
        <li><a class="site-nav__link" href="MAIN_SITE_URL#guide">Mission Guide</a></li>
        <li><a class="site-nav__link" href="esa.html">Funding Help</a></li>
        <li><a class="site-nav__link" href="about.html">About</a></li>
        <li><a class="site-nav__link" href="contact.html">Contact</a></li>
      </ul>
    </nav>
    <div class="header-actions">
      <a class="btn btn--primary" href="contact.html">Start a Request</a>
    </div>
  </div>
</header>
```

- **Footer block**: `.site-footer` with `.site-footer__grid` (brand column + 3
  link groups) and `.footer-note` (compliance text, date, Get in touch). Entity
  line goes in `.footer-note` ONLY on About/TEFA/legal pages.
- **Product card** (image-ready):

```html
<article class="card">
  <div class="card__media" role="img" aria-label="Category artwork placeholder"></div>
  <div class="card__body">
    <span class="card__eyebrow">Practical &amp; Trade</span>
    <h3 class="card__title">Home &amp; Repair Tool Roll</h3>
    <span class="badge badge--review">Planned</span>
    <p>Hands-on learning …</p>
    <div class="card__footer"><span class="price">—</span><a class="btn btn--secondary" href="#">Details</a></div>
  </div>
</article>
```

- **Status vocabulary**: `badge--approved` (marketplace-approved), `badge--review`
  (under offering review), `badge--info` (informational). Map existing store
  status text onto these three; never add new badge variants.
- **Motion**: any `.reveal`/`.stagger` usage must remain gated behind
  `html.js` (the base ships the gate in `@media (prefers-reduced-motion: reduce)`).

## 6. Build pipeline note

`build.py` inlines the base + page-layer CSS once per page-set and inlines the
font subsets (`fonts/*.woff2`). Never edit built HTML in `index.html`,
`store/*.html`, `general-store/*.html`, or root `about.html`-style pages
directly — edit `src/` sources and rebuild. `esa.html` is standalone (external
`esa-style.css` + inlined base) and is edited directly.

Validation before any PR: `python3 tools/validate_project_state.py`,
`python3 build.py`, `git diff --check`.