# Formspree + Turnstile owner setup

Public values only. The Turnstile **secret** stays in the Formspree and
Cloudflare dashboards. Never commit it, log it, or put it in page source.

Approved public configuration keys, stored in
`config/formspree-intake.json` (optional local/build override via the
same environment-variable names):

- `PATHWAY_RECOMMENDATION_FORMSPREE_ID`
- `SCHOOL_DISTRICT_QUOTE_FORMSPREE_ID`
- `TURNSTILE_SITE_KEY`

`restricted_domain` is `preparationstation.org`. Forms enable when the
two public Formspree IDs are valid **and** `enabled` is `true`. The
Turnstile widget renders only if `TURNSTILE_SITE_KEY` is also set. The
Turnstile **secret** stays in dashboards only.

PR #75 (Cloudflare Worker + Resend) is parked as a future custom-intake
option for automation, CRM routing, or Formspree replacement. It is not
the public contact path.

## Dashboard steps already required

1. Create two Formspree forms:
   **Preparation Station — Pathway Recommendation** and
   **Preparation Station — School & District Quote**.
2. Copy each public Formspree form ID (the hash in
   `https://formspree.io/f/{id}`).
3. Set the real delivery destination(s) in Formspree. Do not put the
   inbox address in site HTML.
4. Enable Formspree **Restrict to Domain** for `preparationstation.org`
   (no `www` prefix unless that is the only hostname).
5. Create a Cloudflare Turnstile widget for hostname
   `preparationstation.org`. Copy the public sitekey only.
6. In each Formspree form, enable CAPTCHA → Cloudflare Turnstile and
   paste the Turnstile **secret** only inside Formspree.
7. Put the public Formspree IDs into `config/formspree-intake.json`,
   optionally add `TURNSTILE_SITE_KEY`, set `enabled` to `true`, and
   run `python3 build.py`. Do not commit the Turnstile secret.
8. Deploy the pull request to Vercel preview.
9. Send one synthetic, non-sensitive pathway recommendation.
10. Send one synthetic, non-sensitive school/district quote.
11. Confirm delivery, success state, failure state, Turnstile, no mail
    app, and no secret in source besides the public sitekey and form IDs.
12. Ask for merge/activation approval only after both tests pass.

Required on-page copy:

- Privacy: “Please do not include student records, health information, payment details, or program-account credentials.”
- Success: “Request received. We'll reply within one business day with best-fit options, current status, and the correct purchase path.”
- Failure: “We could not send your request right now. Please try again shortly. If the issue continues, use the support contact listed below.”
