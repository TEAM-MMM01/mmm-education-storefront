# Public-safe contact intake activation

This is the production activation checklist for the Turnstile-gated
Cloudflare Worker. Do not set `config/request-intake.json` `enabled` to
`true` until every item below is complete and the owner names the
activation pull request.

The browser must never send `x-intake-secret`. A secret in page source,
headers, or JavaScript is public. The replacement is:

1. Browser sends only form fields plus a Cloudflare Turnstile token.
2. The Worker verifies method, content-type, origin, Turnstile
   siteverify, schema, size, honeypot, timing, and a best-effort rate
   limit.
3. The Worker uses server-only secrets to email operations.

## Required environment names

Worker secrets (`wrangler secret put`, never committed):

- `TURNSTILE_SECRET_KEY`
- `RESEND_API_KEY`

Worker vars (already named in `workers/preparation-station-intake/wrangler.toml`):

- `ALLOWED_ORIGIN` — production value `https://preparationstation.org`
- `TURNSTILE_HOSTNAMES` — production value `preparationstation.org`
  (no `localhost` in production)
- `OPERATIONS_EMAIL`
- `RESEND_FROM_EMAIL`

Public storefront config (`config/request-intake.json`):

- `turnstile_sitekey` — the public widget sitekey only
- `endpoint` — the HTTPS Worker URL
- `enabled` — stay `false` until this checklist is finished

## Owner configuration

1. Create a Cloudflare Turnstile widget for `preparationstation.org`
   (managed mode). Keep the secret out of git and chat.
2. Deploy Worker `preparation-station-intake` from this repository.
3. Put `TURNSTILE_SECRET_KEY` and `RESEND_API_KEY` with Wrangler.
4. Confirm `ALLOWED_ORIGIN` is exactly `https://preparationstation.org`.
5. Confirm `TURNSTILE_HOSTNAMES` is `preparationstation.org`.
6. Confirm operations mail arrives at the configured operations inbox.

## Local mock path (no email)

```bash
node --test workers/preparation-station-intake/test/index.test.js
python3 tools/validate_project_state.py
python3 build.py
node tools/test_request_intake.js
```

Those Worker tests mock siteverify and Resend. They must not send mail.

## Production smoke test (after owner approval)

Use one synthetic adult-controlled request. Do not include student
records, health information, payment details, program-account
credentials, bank information, or Social Security numbers.

1. Open production `contact.html`.
2. Complete the pathway form and the Turnstile widget.
3. Submit.
4. Confirm the on-page success copy:
   “Request received. We'll reply within one business day with best-fit
   options, current status, and the correct purchase path.”
5. Confirm the operations email arrived with the `PSQ-` reference.
6. Repeat with an invalid email to confirm the validation error state.
7. Force a server failure (or temporarily break the Worker) only if the
   owner approves that rehearsal, and confirm:
   “We could not send your request right now. Please try again shortly.
   If the issue continues, use the support contact listed below.”
8. Delete the synthetic notification after the rehearsal.

## Enablement PR

Only then, in a separate reviewed pull request:

1. Set `endpoint` to the live Worker URL.
2. Set `turnstile_sitekey` to the public sitekey.
3. Set `enabled` to `true`.
4. Run `python3 build.py` so generated `contact.html` matches config.
5. Do not mix this enablement with catalog, checkout, or TEFA listing work.
