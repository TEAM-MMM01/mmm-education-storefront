# Product and information page soft launch

Use this plan to publish useful product information while the transaction and
remainder-of-site work continues. The first release is a **private review
preview**, not a public commerce launch.

## Release boundary

Publish these paths for stakeholder and invited-family review:

- `/` — overview and funding information
- `/store/shop.html` — ESA catalog preview
- `/store/product.html` — the sample product-detail template

Keep the following outside promotional and paid-traffic links until their
operations are complete:

- `/store/order.html` — quote flow remains a prototype
- `/general-store/` — retail checkout, tax, payment, and fulfillment are not live

Every preview entry point must state that final availability, ordering, and
fulfillment details are still under review and that no payment is collected.

## Before sharing a preview URL

- Choose a preview host and confirm HTTPS works.
- Add `noindex` at the host level or protect the preview with a password.
- Replace or intentionally label every customer-visible placeholder.
- Verify product names, SKUs, contents, age guidance, prices, and images with the
  owner responsible for fulfillment.
- Test `/`, `/store/shop.html`, and `/store/product.html` at phone and desktop
  widths, including keyboard navigation and print output.
- Confirm all links stay inside the preview or clearly identify unfinished paths.
- Assign one inbox and one person to collect feedback and product corrections.

## Production launch gates

Move product and information pages from preview to public only when:

1. Each published SKU has verified price, inventory or made-to-order status,
   handling time, shipping expectation, and return/support guidance.
2. Product-detail routes no longer send every product to a single stand-in page.
3. Funding language has been checked against current program and vendor status.
4. Privacy, terms, shipping, returns, accessibility, and contact information are
   linked and owner-approved.
5. Quote requests create both a customer confirmation and an owned internal
   record; no request depends solely on a pre-filled email.
6. Analytics captures page views, product views, primary CTA clicks, and quote
   requests without collecting unnecessary student information.
7. A final build and mobile/desktop smoke test pass on the deployed URL.

## Recommended next build order

1. Create a product data source for verified catalog facts.
2. Generate a unique detail page for every launch SKU from that source.
3. Replace placeholders and add approved policy/contact pages.
4. Connect the quote form to confirmation and internal follow-up automation.
5. Add deployment previews and URL smoke checks to CI.
6. Rehearse one complete funded-order journey before public promotion.

Continue developing unfinished pages on branches and preview deployments. Keep
the public release branch limited to verified product information and completed
customer paths.
