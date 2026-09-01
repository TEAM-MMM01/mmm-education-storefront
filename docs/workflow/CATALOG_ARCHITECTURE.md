# Preparation Station catalog architecture

## Canonical destination

- Public catalog URL: `https://preparationstation.org/catalog`
- Source: `src/catalog.html`
- Generated public page: `catalog/index.html`
- `catalog.html` is compatibility-only and redirects to `/catalog`.

## Structural baseline

The Grok catalog (`https://storm-ruby-sail-cobalt.grok.me`) is the current structural/design baseline for the catalog experience. Use its strongest information-architecture patterns, not its testimonials or unsupported claims.

Current target hierarchy:

1. Clear catalog/TEFA context and one primary catalog destination.
2. Flagship curriculum with prominent verified SKU, price, duration, and offering status.
3. Consistent comparison cards for the current curriculum pathways.
4. Simple product-detail and written-confirmation actions.
5. Clear separation between discovery on Preparation Station and TEFA-funded purchasing in Odyssey.
6. Learning-plan/free-resource routes that support families without creating a second catalog.

## Legacy ESA / ESA Launch Command review

The old ESA architecture is not a current catalog source or route. Its useful patterns were reviewed from the historical integration record and retained only where they improve the Grok-baseline experience.

### Retain

- restrained offering-status taxonomy;
- consistent product-card anatomy (name, SKU, duration, price/status, concise purpose, CTA);
- responsive one/two/three-column comparison behavior;
- reduced-motion and no animation of price, approval status, or purchase instructions;
- clear TEFA-vs-retail purchasing boundaries;
- inquiry/privacy rule: never request Odyssey credentials, payment credentials, or sensitive student records in catalog forms;
- useful CTA coverage so comparison paths lead to product detail, written confirmation, learning-plan help, or free resources;
- validation before shipping.

### Do not retain

- `/esa` as the catalog;
- ESA Launch Command or an ESA microsite as a public architecture;
- ESA product sheets as the primary public catalog model;
- a second catalog with different names/prices/statuses;
- reviewer/testimonial content that cannot be independently verified;
- placeholder or planning products presented as listed/approved offerings;
- direct TEFA checkout or Odyssey credential collection on Preparation Station.

## Source-of-truth rule

Grok is the design/structure baseline, not the factual product database. Current repository product records and approved business facts win whenever a SKU, name, price, duration, status, or compliance claim conflicts with a mockup/reference.

## Current reviewer-safety rule

No testimonials or simulated social proof should appear in the TEFA-facing catalog. Prefer factual, verifiable guidance.

## Done gate

Before declaring the catalog ready:

- run `python3 tools/validate_project_state.py`;
- run `python3 build.py`;
- run `git diff --check`;
- verify `/catalog` is generated and `catalog.html` redirects to it;
- verify all six current curriculum detail links resolve;
- reconcile SKU/name/price/duration/status against the product detail records;
- verify no legacy ESA catalog route is presented as current;
- verify no unsupported approval/eligibility/testimonial claims remain.
