# Preparation Station request intake

The product-information request path uses a private Cloudflare Worker to create
an internal inquiry record and forward a sanitized notification to operations.
It does not collect payment, approve a product for TEFA or PDSES/ClassWallet,
accept an order, or replace Odyssey. TEFA purchases and official order history
remain in the Odyssey Marketplace.

`config/request-intake.json` is intentionally disabled. Its endpoint may remain
blank until deployment approval. `enabled` must stay `false` and `allowed_skus`
must stay empty until setup and an end-to-end test are complete, so the online
submit button remains unavailable unless owner-approved launch work is finished.

## Data boundary

The browser sends only:

- adult contact name and email;
- selected program or purchase path;
- catalog SKUs and quantities;
- optional nonsensitive notes;
- a client reference, submission timestamp, source label, and internal owner;
- the `_gotcha` honeypot field.

Do not request or submit a child's full name, disability or school records,
account numbers, financial documents, Social Security numbers, credentials, or
attachments. No payment or funding-program account data belongs in this form.

The client generates a `PSQ-YYYYMMDD-...` reference before submission. The
Worker forwards the same reference to the internal notification channel, and the
customer sees it in the confirmation UI and downloadable text receipt. A retry
keeps the reference so the operator can recognize a possible duplicate after an
interrupted response.

## Backend and operating policy

Cloudflare Worker intake is the selected backend because it keeps request
handling private, enforces origin and shared-secret validation, and sends owner
notifications without exposing a public endpoint in source.

The temporary owner notification address is `mmminvestment25@gmail.com`.
Nationwide Acquisitions, LLC owns follow-up. Review the operations inbox each
business day, acknowledge complete requests within one business day, and use
the client reference in follow-up.

Do not log full request payloads. Delete transient intake notifications and any
copied operational notes within 30 days after final follow-up unless a request
becomes an accepted transaction and must be transferred into the approved
business/accounting system.

## Administrator setup

1. Create the Cloudflare Worker `preparation-station-intake`.
2. Set Worker secrets with Wrangler after owner approval, not in source:
   `INTAKE_SHARED_SECRET`, `RESEND_API_KEY`.
3. Set Worker vars at deployment time for:
   `ALLOWED_ORIGIN`, `OPERATIONS_EMAIL`, `RESEND_FROM_EMAIL`.
4. Keep the storefront `enabled` flag `false` until launch SKU verification,
   preview rehearsal, and owner approval are complete.
5. Add only verified launch products to `allowed_skus`. Each value must be an
   existing `PS-...` SKU in `store/cart.js`. Keep the list empty while no
   product has verified price, availability, and fulfillment facts.
6. Set the Worker endpoint in `config/request-intake.json`, then set `enabled`
   to `true` only in the same reviewed pull request that is approved for launch.
7. Run the checks below and obtain separate approval before deployment.

## Validation and end-to-end rehearsal

Run locally:

```bash
node tools/test_request_intake.js
python3 tools/validate_project_state.py
python3 build.py
git diff --check
```

On an approved HTTPS preview, add a catalog item and submit a synthetic request
using an adult-controlled email and no personal student data. Verify all of the
following before considering the intake live:

1. The button is disabled when configuration is missing, malformed, or marked disabled.
2. Loading, validation, failure, and retry messages are usable.
3. The confirmation shows a client reference and downloads a receipt.
4. The Worker accepts only the approved origin and secret, and forwards only approved fields.
5. The owner notification arrives at the temporary support inbox.
6. No approval, price, inventory, shipping, or payment claims are implied by the confirmation.
7. Remove synthetic notifications after the rehearsal.

Deployment, public approval claims, payment, repository rename, and domain
changes remain separate owner-approved work.
