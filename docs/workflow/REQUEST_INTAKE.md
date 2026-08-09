# Preparation Station request intake

The product-information request path uses Formspree to create an internal request
record. It does not collect payment, approve a product for TEFA or
PDSES/ClassWallet, accept an order, or replace Odyssey. TEFA purchases and
official order history remain in the Odyssey Marketplace.
`config/request-intake.json` is intentionally disabled and has
no endpoint and an empty SKU allowlist, so the online submit button remains
unavailable until setup and an end-to-end test are complete.

## Data boundary

The browser sends only:

- adult contact name and email;
- selected program or purchase path;
- catalog SKUs and quantities;
- optional nonsensitive notes;
- a client reference, submission timestamp, source label, and internal owner;
- Formspree's `_gotcha` honeypot field.

Do not request or submit a child's full name, disability or school records,
account numbers, financial documents, Social Security numbers, credentials, or
attachments. No payment or funding-program account data belongs in this form.

The client generates a `PSQ-YYYYMMDD-...` reference before submission. Formspree
stores the same reference with the request, and the customer sees it in the
confirmation UI and downloadable text receipt. A retry keeps the reference so
the operator can recognize a possible duplicate after an interrupted response.

## Backend and operating policy

Formspree is the selected first backend because it accepts AJAX submissions,
keeps a dashboard record, and sends owner notifications without a custom
server. Its Free tier currently starts at 50 submissions per month. AJAX forms
return HTTP 429 when the plan limit is reached, which the storefront converts
to a retry/email message. Confirm current limits before launch:

- <https://help.formspree.io/articles/building-your-form/submit-forms-with-javascript-ajax>
- <https://help.formspree.io/articles/account-management/account-limits>
- <https://help.formspree.io/articles/form-and-project-settings/system-limits>
- <https://help.formspree.io/articles/building-your-form/honeypot-spam-filtering>

The temporary owner notification address is `mmminvestment25@gmail.com`.
Nationwide Acquisitions, LLC owns follow-up. Review the inbox/dashboard each
business day, acknowledge complete requests within one business day, and use
the client reference in follow-up.

Delete each Formspree intake record within 30 days after final follow-up. If a
request becomes an accepted transaction, move only the necessary record into
the approved business/accounting system and apply its retention rules. Review
and clear closed intake records at least monthly.

The on-page confirmation does not depend on a paid Formspree feature. An email
autoresponse can be configured separately if the selected Formspree plan
supports it; do not claim email confirmation until that workflow is tested.

## Administrator setup

1. Create a Formspree dashboard form named `Preparation Station requests`.
2. Set its verified notification destination to
   `mmminvestment25@gmail.com` and confirm the first submission/activation.
3. Restrict allowed domains after the preview and production URLs are known.
4. Keep Formspree spam protection enabled. The storefront also supplies the
   documented `_gotcha` honeypot.
5. Copy the dashboard endpoint in the form
   `https://formspree.io/f/FORM_ID`. The form ID is public configuration, not a
   credential; never commit an API key, deploy key, token, or account password.
6. Add only verified launch products to `allowed_skus`. Each value must be an
   existing `PS-...` SKU in `store/cart.js`. Keep the list empty while no
   product has verified price, availability, and fulfillment facts. A mixed
   cart containing any SKU outside this allowlist is refused rather than
   silently submitting an incomplete request.
7. Set the endpoint in `config/request-intake.json`, then set `enabled` to
   `true` in the same reviewed pull request. Validation rejects an enabled
   configuration with an empty or unknown SKU allowlist.
8. Run the checks below and obtain separate approval before deployment.

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

1. The button is disabled when configuration is missing, malformed, or marked
   disabled.
2. Loading, validation, failure, rate-limit, and retry messages are usable.
3. The confirmation shows a client reference and downloads a receipt.
4. Formspree contains one internal record with the same reference, program,
   SKUs/quantities, owner, and timestamp—and no unapproved fields.
5. The owner notification arrives at the temporary support inbox.
6. If autoresponse is enabled, the customer acknowledgement arrives and does
   not claim eligibility, approval, price, inventory, shipping, or payment.
7. Delete the synthetic Formspree record after the rehearsal.

Deployment, public approval claims, payment, repository rename, and domain
changes remain separate owner-approved work.
