# Premium Website Motion System

**Scope:** Preparation Station (landing, ESA page, storefronts, info pages).
**Standard:** motion is *guided clarity, not flash* — every animation explains a
state change or supports a business goal (discover, compare, choose, request, buy).
**Reuse:** copy the token block + modules into any future client build.

---

## Motion principles (permanent rules)

1. Motion must explain what changed.
2. Motion must support a business goal: discover, compare, choose, request, or buy.
3. Motion must be faster for controls (160–220ms) and slower for section reveals
   (320–520ms). Hero entrance max 700ms.
4. Motion must work on mobile and keyboard flows (hover effects get `:focus-visible`
   equivalents; never rely on hover alone).
5. Motion must respect `prefers-reduced-motion` (see Reduced-motion spec).
6. Motion must never delay important information — pricing, approval status, or
   purchase instructions render visible immediately.

Do **not** use motion as decoration. No looping decoration, no parallax, no
bounces. Animate only `transform` and `opacity` (compositor-friendly); never
layout properties.

---

## Motion tokens

Every page's `:root` carries these tokens (landing `src/page.html`,
`esa-style.css`, `store/shared_style.css`, `src/info/shared.css`):

```css
--ease-standard: cubic-bezier(0.16, 1, 0.3, 1);
--ease-soft:     cubic-bezier(0.22, 1, 0.36, 1);
--ease-exit:     cubic-bezier(0.4, 0, 1, 1);
--dur-fast:      160ms;   /* micro-interactions */
--dur-ui:        220ms;   /* controls, toggles, hover */
--dur-panel:     320ms;   /* accordions, modals, trays */
--dur-section:   520ms;   /* scroll reveals */
--dur-hero:      700ms;   /* hero entrance only */
--motion-y-sm:   6px;
--motion-y-md:   12px;
--motion-y-lg:   20px;
--motion-scale-hover: 1.015;
```

Opacity choreography: initial reveal `0 → 1`; translateY `12–20px → 0`;
cards/panels `scale 0.985 → 1` (via `--motion-scale-hover`). Avoid big zooms.

---

## Reusable modules

All module CSS lives in the shared stylesheets, and every reveal is gated
behind `<html class="js">` so content stays visible with no JS:

```css
html.js .reveal{opacity:0; transform:translateY(var(--motion-y-lg)); ...}
html.js .reveal.in{opacity:1; transform:none}
html.js .reveal-fade{opacity:0; transition:opacity var(--dur-ui) ...}
html.js .reveal-fade.in{opacity:1}
html.js .stagger > *{opacity:0; transform:translateY(var(--motion-y-md)); ...}
html.js .stagger.in > *{opacity:1; transform:none}
```

| Module | Class | Where |
|---|---|---|
| `fade-up-reveal` | `.reveal` (+ `.d1`–`.d4` delays) | section headers, hero, cards |
| `fade-only` | `.reveal-fade` | confirmation panels, toasts |
| `stagger-children` | `.stagger` on a parent | card grids, steps, product shelves |
| `sticky-header-compress` | `.site-head.scrolled` / `.topbar.scrolled` | landing, esa, store, general-store |
| `card-lift-hover` | `.card-lift`, or built into `.card/.product/.step-card/.date-card` | hover/focus raise + shadow |
| `cta-arrow-nudge` | `.arr` inside `.btn:hover` | all primary CTAs |
| `nav-underline-glide` | `.nav a::after` (`right:100% → 0`) | landing, info navs |
| `accordion-expand` | `details.motion-acc` + `.acc-body` grid-rows trick | all FAQs |
| `tab-indicator-glide` | n/a (dept tabs scroll; no JS tab system) | — |
| `timeline-highlight-shift` | n/a (hover lift only on `.t-card`) | — |
| `count-up-metric` | n/a — no unverified metrics on site; add only for verified numbers | — |
| `logo-draw-in` | n/a — brand is text, not SVG | — |
| `toast-slide-in` | cart toast (cart.js) + landing launch-chip | store, landing |

The accordion module uses the `grid-template-rows: 0fr → 1fr` trick with a
single inner wrapper (`<div class="acc-body"><div>…content…</div></div>`), so
height animates without JavaScript and never runs on layout properties.

---

## Section-by-section map (this site)

| Section | Motion | Business purpose |
|---|---|---|
| Header/nav | fade/slide on load, compress on scroll, underline glide | orientation |
| Hero | eyebrow → headline → sub → CTAs → chips (stagger) | reading order → action |
| Trust strip / bar | fade in first; no decoration | trust before product info |
| Timeline / steps | reveal + stagger | guided progression |
| Department & product cards | reveal stagger + card-lift + arrow nudge | discover / choose |
| Compare/progress (order) | reveal; labels never animate | clarity |
| FAQ | accordion height+opacity, `+` rotates 45° | reduce friction |
| Final CTA | fade-up heading + staggered buttons | conversion |
| Footer | link hovers only, no heavy motion | stability / trust |

---

## Pop-ups and funnels

- Free-resource / lead modal: backdrop `0 → 1`, panel `translateY(16px)→0`,
  opacity `0 → 1`, 280–340ms, `prefers-reduced-motion` → instant, soft.
- Purchase reminder: small non-blocking tray slide-in, clear dismiss.
- Never feel spammy — this is education.

---

## Reduced-motion spec (non-negotiable)

With `prefers-reduced-motion: reduce`:

- reveals/staggers are **fully visible** (no transform, no opacity, no delays),
- no parallax, no orbiting background, no pulsing launcher rings,
- accordions still open/close instantly but clearly,
- modals appear cleanly without movement,
- hover lifts disabled (`transform:none`),
- the `js` class is still added, so interactive state cues (`.in`) remain set.

---

## Performance guardrails

- Animate `transform`/`opacity` only — compositor-friendly, no layout thrash.
- `transition-delay` max ~500ms; stagger cap of 9 children (60ms steps).
- Observers `unobserve()` after first reveal (once-on-view).
- No `will-change` on every element — only where a sustained animation needs it.
- Nothing blocks first paint: hero reveals run at `--dur-fast`/`--dur-ui` and the
  observer fires immediately for in-view elements.

---

## QA checklist

- [ ] All 16 pages pass Lighthouse (perf ≥ 90, a11y 100, CLS ≤ 0.1).
- [ ] Content is fully visible with JS disabled and with reduced motion.
- [ ] Keyboard: all accordions toggle with Enter/Space; focus-visible matches hover.
- [ ] Mobile (375px) and desktop (1280px) reveals look intentional, no pop-in.
- [ ] No animation delays or hides pricing/approval-status/purchase instructions.
- [ ] No looping/parallax/decorative motion anywhere.
- [ ] `python3 tools/validate_project_state.py` + `python3 build.py` pass.