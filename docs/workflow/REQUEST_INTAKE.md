# Preparation Station request intake

The public contact and school-quote path uses a Cloudflare Worker. It
creates an internal inquiry notification. It does not collect payment,
approve a product for TEFA or PDSES/ClassWallet, accept an order, or
replace Odyssey. TEFA purchases and official order history remain in
the Odyssey Marketplace.

`config/request-intake.json` stays disabled until the activation
checklist in `docs/workflow/CONTACT_INTAKE_ACTIVATION.md` is complete.
`enabled` must stay `false` and `endpoint` / `turnstile_sitekey` may
stay blank until that work is owner-approved.

## Why a browser `x-intake-secret` cannot ship

The previous Worker required `x-intake-secret`. Anything the browser
sends is public: page source, DevTools, and any copied header. A shared
secret in the storefront would not authenticate families. It would only
leak the secret.

The replacement is Cloudflare Turnstile plus origin, schema, size,
honeypot, timing, and rate-limit checks on the Worker. The browser
sends form fields and a Turnstile token. The Worker calls siteverify
with `TURNSTILE_SECRET_KEY`. Resend stays server-side.

## Data boundary

The browser may send only:

- adult / contact name and email
- learner age band
- goal / interest area
- funding / purchase path
- message
- optional school or organization details on the quote path
- a client reference, submission timestamp, source label, and honeypot
- the Turnstile token, which the Worker verifies and discards

Do not request or submit student records, health information, payment
details, TEFA/Odyssey account credentials, bank information, or Social
Security numbers. No attachments.

Required public copy on the form:

“Do not include student records, health information, payment details, or program-account credentials.”

Required success copy:

“Request received. We'll reply within one business day with best-fit options, current status, and the correct purchase path.”

Required failure copy:

“We could not send your request right now. Please try again shortly. If the issue continues, use the support contact listed below.”

## Administrator setup

See `docs/workflow/CONTACT_INTAKE_ACTIVATION.md`. Secrets are set with
Wrangler, never committed:

- `TURNSTILE_SECRET_KEY`
- `RESEND_API_KEY`

## Validation

```bash
node --test workers/preparation-station-intake/test/index.test.js
node tools/test_request_intake.js
python3 tools/validate_project_state.py
python3 build.py
git diff --check
```
