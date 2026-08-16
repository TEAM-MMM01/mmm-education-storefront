# Preparation Station order operations

Preparation Station presents one customer order-history experience while keeping
the two purchasing systems separate.

## Source boundaries

| Order source | Where payment happens | Authoritative history | Preparation Station role |
| --- | --- | --- | --- |
| TEFA | Official Odyssey Marketplace | Odyssey parent/vendor portals | Mirror fulfillment status after a secure import or supported integration |
| Direct site | Hosted direct checkout | Direct payment provider plus the private order backend | Create the order after a verified payment webhook and show status |

Never ask a family to enter TEFA credentials on Preparation Station. Never
represent the public site as an alternate TEFA checkout. Odyssey remains the
authority for funded payment, approval, official order history, and the program
order number.

## Customer access

`store/track.html` requests a secure email link from the configured private API.
It must not return order data to an unauthenticated email/reference lookup. The
checked-in `config/order-portal.json` remains disabled until the backend has:

- email magic-link authentication;
- customer-level authorization on every order read;
- rate limiting and a non-enumerating response;
- HTTPS and an allowlisted storefront origin;
- an audit trail for imports and status changes;
- a deletion and retention policy;
- no child, disability, school, TEFA credential, bank, or card data.

The browser must not store order records in `localStorage` or public files.

## Importing previous orders

Use `PREVIOUS_ORDER_IMPORT_TEMPLATE.csv` only as an offline import template.
Never commit a completed copy. Import previous TEFA and direct orders into the
private backend after matching each row to an adult-controlled customer email.

Required import behavior:

1. Normalize `source` to `tefa_odyssey` or `direct_site`.
2. Keep the Odyssey or direct-payment order number in `source_reference`.
3. Create one internal `PSO-...` order ID per source order.
4. Group line items under that order without child or program-account data.
5. Reject duplicate `(source, source_reference)` pairs.
6. Record the importing operator, timestamp, and source file checksum privately.
7. Send no customer email until a human reviews the imported order.

For TEFA orders, update Preparation Station from an Odyssey-approved export or a
documented Odyssey integration. Until one exists, use a manual operator import
and reconcile against Odyssey before changing `approved`, `shipped`, refunded,
or canceled statuses.

## Direct checkout gate

Direct checkout is separate from the Stripe connection inside Odyssey. It may be
enabled only when every allowed SKU has a verified fixed price, inventory or
made-to-order rule, tax treatment, shipping rule, return policy, and fulfillment
owner.

The direct payment provider must call a verified webhook. Create an order only
after the webhook confirms the payment event; do not trust a browser success
page. Store provider secrets only in the backend environment. The public config
may contain hosted payment URLs only after the corresponding SKU is allowlisted.

## TEFA launch checklist

- Connect Nationwide Acquisitions, LLC banking inside Odyssey's Stripe flow.
- Upload offerings in the vendor portal.
- Record each Odyssey offering ID and review status in the canonical catalog.
- Preview each offering in Odyssey before it is published.
- Keep purchases and official order history in Odyssey.
- Add the final Preparation Station URL to the TEFA Finder profile.

Vendor approval allows the approved company to participate. Each offering still
requires Odyssey review before families can purchase it with TEFA funds.
