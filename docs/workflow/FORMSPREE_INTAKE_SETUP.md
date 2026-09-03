# Formspree + Turnstile owner setup

Do not merge or activate this pull request until every step below is
complete and both synthetic tests pass. Public values only go in
`config/formspree-intake.json`. The Turnstile **secret** stays in the
Formspree and Cloudflare dashboards. Never commit it.

1. Create two Formspree forms at https://formspree.io/dashboard
   named **Preparation Station — Pathway Recommendation** and
   **Preparation Station — School & District Quote**.
2. Copy each public Formspree form ID (the hash in
   `https://formspree.io/f/{id}`).
3. Set the real delivery destination(s) in each Formspree form
   (operations inbox). Do not put that inbox address in site HTML.
4. Enable Formspree **Restrict to Domain** for `preparationstation.org`
   (no `www` prefix unless that is the only hostname).
5. Create a Cloudflare Turnstile widget for production hostname
   `preparationstation.org` (managed mode). Copy the public sitekey
   only.
6. In each Formspree form, enable CAPTCHA → Cloudflare Turnstile and
   paste the Turnstile **secret** only inside Formspree. Do not put
   `TURNSTILE_SECRET_KEY` in this repository, Vercel public env, or
   page source.
7. Add only public values to `config/formspree-intake.json` in a
   reviewed follow-up: `pathway_form_id`, `quote_form_id`,
   `turnstile_sitekey`, then `enabled: true`. Run `python3 build.py`.
8. Deploy that follow-up to a Vercel preview.
9. Send one synthetic, non-sensitive pathway recommendation
   (adult name, adult email, no student records, health, payment, or
   credentials).
10. Send one synthetic, non-sensitive school/district quote the same way.
11. Confirm: both emails arrived, success copy appeared, a validation
    error appears for an empty required field, Turnstile ran, no mail
    app opened, and no secret is visible in page source or network
    payloads besides the public sitekey and form IDs.
12. Ask for merge/activation approval only after both tests pass.

Required on-page copy after activation:

- Privacy: “Please do not include student records, health information, payment details, or program-account credentials.”
- Success: “Request received. We'll reply within one business day with best-fit options, current status, and the correct purchase path.”
- Failure: “We could not send your request right now. Please try again shortly. If the issue continues, use the support contact listed below.”
