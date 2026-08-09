# Product and Commerce Boundaries

## Preparation Station

Preparation Station is the public education brand operated by Nationwide
Acquisitions, LLC. It owns Texas-program information, educational product
presentation, product/funding review requests, and quote or invoice workflows.

Preparation Station may list and sell books and coloring books through a
self-pay path when the product facts, price, inventory, policies, tax, payment,
and fulfillment are ready. A funded pathway remains a separate quote/invoice
flow and requires product-specific eligibility evidence.

## Royal Collexions

Royal Collexions owns non-funded Shopify commerce, dropshipping, retail
fulfillment, and each book or coloring book's canonical master record. The
master record owns the SKU, title, creator credit, artwork, ISBN, production
files, price, inventory, printing source, shipping, and returns configuration.

## Shared book rule

One canonical Royal Collexions product may have two channel listings:

1. Royal Collexions retail listing.
2. Preparation Station education-focused listing.

Both listings must reference the same canonical SKU and fulfillment record.
They must not create conflicting identifiers, prices, inventory, or shipping
promises. The canonical starter records are in `catalog/books.json`.

## Funding claim rule

TEFA and PDSES/ClassWallet are separate programs. Company approval does not by
itself prove that a particular product is eligible. A program or product claim
may be enabled only after current evidence is recorded, reviewed, and marked
publishable in `config/project-state.json` and the relevant catalog record.
