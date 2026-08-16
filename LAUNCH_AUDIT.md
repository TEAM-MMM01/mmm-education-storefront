# TEFA / ESA launch audit

Reviewed against the repository state on 2026-08-15. This audit treats the repository as the source of truth and does not assume that disabled foundations are production services.

## Recommendation

**Publish only a truthful TEFA vendor and catalog-information release. Keep every purchase, request, and order-data service disabled until its own gate passes.**

Nationwide Acquisitions, LLC is an approved TEFA Marketplace vendor operating Preparation Station. Each offering still requires separate Odyssey review, and TEFA purchases plus official order history remain in Odyssey. Direct retail is a separate future channel.

## 1. Keep

- The strict separation between ESA/TEFA invoice flows and direct retail.
- Odyssey as the only TEFA purchase and official order-history system.
- Funding copy that distinguishes vendor approval from offering approval.
- The shared styling/build structure, accessible themes, print support, and reduced-motion behavior.
- General Store as a development-only preview for staged rollout.

## 2. Improve

- Replace all public placeholders: contact details, hours, response times, shipping turnaround, legal business identity, returns, accepted programs, and operating commitments.
- Verify supplier cost, public price, margin, packaging, inventory/made-to-order rule, and fulfillment expectations for every ESA SKU.
- Give each ESA product a complete, accurate product-detail page instead of routing all cards to one stand-in page.
- Configure and rehearse the disabled Formspree request path only after at least one SKU is verified and allowlisted.
- Add final mobile/desktop regression coverage after real content is inserted.

## 3. Trim

- Remove duplicate or low-value paths that do not help the first ESA release.
- Remove buyer-facing retail actions that look transactable before the retail backend exists.
- Reduce speculative category/product language until titles, descriptions, prices, and inventory are confirmed.
- Keep the first release focused on the smallest truthful ESA catalog that can be fulfilled well.

## 4. Hide / relabel

- Relabel every ESA cross-link from **General store** to **General Store Preview**.
- Relabel General Store cart, checkout, add-to-cart, and confirmation actions as previews.
- Remove "real checkout," "pay," and "place order" language from the prototype UI.
- Do not link General Store from the customer-facing ESA launch path until retail products, policies, tax, payment, and fulfillment are complete.

## 5. Remaining blockers

### Business facts

Phone, hours, shipping turnaround, returns, direct-purchase terms, and permanent support ownership must be verified. The legal operator and temporary support email are recorded.

### Product truth

Illustrative pricing, repeated stand-in product pages, unfinished book metadata, working-title coloring books, and placeholder images cannot appear as finished customer facts.

### TEFA operations

Upload offerings in Odyssey, record each offering ID and review status, and keep funded purchases in Odyssey. The website request path stays disabled until its Formspree endpoint and SKU allowlist pass rehearsal.

### Retail operations

General Store needs a PCI-compliant processor, real tax configuration, accurate shipping rates, finalized product metadata, order creation, customer email, and fulfillment tracking.

## Repository-verifiable release evidence

**Workflow truth state: `Blocked`.** This is Tier 2 release-record maintenance; the
Tier 3 production deployment remains outside this change and requires Richie’s
explicit approval. The following values reflect only evidence present in this
repository as of 2026-08-15:

| Release check | Repository record | Recorded result |
| --- | --- | --- |
| TEFA release SKU | `config/pages-release.json` has an empty `release_skus` list; no item under `catalog/` records `funding_eligibility.tefa` as `verified_product_evidence`. | No release SKU is verified. Company-level vendor approval is not product eligibility. |
| Request-intake endpoint | `config/request-intake.json` is disabled and its `endpoint` is empty. | No endpoint is verified. |
| Backend end-to-end rehearsal | `config/pages-release.json` records `request_backend.e2e_verified` as `false`. | Not verified. |
| Owner notification | `config/pages-release.json` records `owner_notification_verified` as `false`. | Not verified. |
| Customer confirmation | `config/pages-release.json` records `customer_confirmation_verified` as `false`. | Not verified. |
| Verification time | `config/pages-release.json` records `verified_at` as `null`. | No timestamp is recorded because no end-to-end verification evidence exists; when verification occurs, this field must contain a timezone-aware ISO 8601 value. |

`deployment_enabled` remains `false`. A local build or static test does not
satisfy any remote or operational release check. Set verification fields only
after privacy-safe evidence from the same end-to-end rehearsal is attached to a
reviewed pull request, and do not deploy unless all gates pass and Richie
explicitly approves the Tier 3 action.

## Launch gates

The public information release can move forward when all of the following are true:

- No public ESA page contains `[___]`, `[__]`, `TBD`, unfinished business claims, or prototype-only stand-ins.
- Every public ESA product has verified content, price, fit, shipping expectation, and return/support guidance.
- No disabled request, tracking, or checkout control implies that a live service exists.
- Navigation makes TEFA/Odyssey the obvious funded-purchase path and keeps General Store out of the deployed artifact.
- Build and smoke checks pass on the final generated pages at mobile and desktop widths.

## Ruthless review conclusion

- **Improved:** launch language, path priority, and the documented source of truth.
- **Trimmed:** false-live retail signals and equal prominence for unfinished commerce.
- **Intentionally left out:** fake payments, generic tax/legal claims, invented book/product details, and speculative public promises.
- **Ship decision:** do not ship the current tree as public commerce. Complete the gates above, then publish the TEFA vendor and catalog-information release only.
