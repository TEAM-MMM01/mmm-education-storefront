# SKU Verification Runbook — First TEFA Release

**Purpose.** This is the fill-in-the-blank checklist for turning the storefront
from $0 (all 18 SKUs gated "Coming soon") into transactable. Verifying and
allowlisting **one** SKU is `REVENUE_PRIORITIES` #1 in
`.system/skills/skills_loops_prompts.md`.

**Who does this.** The verification facts (Odyssey offering ID, verified TEFA
product evidence, end-to-end request rehearsal) are **owner/operational actions**
— an agent cannot manufacture them. This runbook maps each fact to the exact
repository field and the validator that enforces it, so once the facts exist the
edit is mechanical and review-safe.

**Golden rule.** Never set a readiness field on owner recollection or a passing
local unit test. Attach privacy-safe evidence from the same end-to-end rehearsal
to the reviewed release PR (`docs/workflow/PAGES_RELEASE.md`).

---

## ⚠️ Blocker you must resolve first: the two validators contradict

The release gate and the state validator disagree about `public_listing_allowed`:

- `tools/build_pages_release.py:133-137` **requires** the release SKU's catalog
  record to have `public_listing_allowed: true` and
  `funding_eligibility.tefa == "verified_product_evidence"`.
- `tools/validate_project_state.py:265` **requires every item in**
  `catalog/products.json` to have `public_listing_allowed` **false**, with
  `price_status == "illustrative_unverified"` (`tools/validate_project_state.py:266`)
  and `retail_price_usd` null (`tools/validate_project_state.py:267`).

So you **cannot** satisfy both by flipping an existing `catalog/products.json`
item in place — `validate_project_state.py` will fail the moment you set
`public_listing_allowed: true` there. Also note `products.json` items do not
carry a `funding_eligibility` block today (only `catalog/books.json` items do,
per `tools/validate_project_state.py:234-236`).

**Decision required from the owner/maintainer before verification:** decide where
the verified release record lives. Options, in order of least disruption:

1. **Add a separate verified-offerings catalog file** (e.g.
   `catalog/tefa-offerings.json`) that holds only verified SKUs with
   `public_listing_allowed: true` + `funding_eligibility.tefa:
   verified_product_evidence`. `tools/build_pages_release.py:76-86` scans **all**
   `catalog/*.json`, so it will find the SKU there, while
   `tools/validate_project_state.py` keeps validating `products.json` as the
   fixed 18-item illustrative set. **This requires a small validator change** to
   recognize the new file (and to stop requiring the release SKU to be one of the
   18 illustrative records).
2. **Relax `validate_products()`** to allow a verified state per-item. Higher
   blast radius; touches the 18-item invariant (`tools/validate_project_state.py:256`).

Do not proceed to the field checklist below until this is decided, because the
SKU's home determines every path in it.

---

## Field checklist (per gate)

Once the "SKU home" decision above is made, verification sets the following.
Each row lists the file, the field, and the enforcing check.

### A. Catalog record for the chosen SKU

| Field | Set to | Enforced by |
|---|---|---|
| `public_listing_allowed` | `true` | `tools/build_pages_release.py:133-134` |
| `funding_eligibility.tefa` | `"verified_product_evidence"` | `tools/build_pages_release.py:135-137` |
| `tefa_offering_status` | `"approved"` | `tools/validate_project_state.py:269-273` (only if kept in `products.json`) |
| `odyssey_offering_id` | the real Odyssey ID | required when approved: `tools/validate_project_state.py:274-275` |

The SKU must resolve to **exactly one** catalog record across all
`catalog/*.json` (`tools/build_pages_release.py:128-130`).

### B. Release manifest — `config/pages-release.json`

| Field | Set to | Enforced by |
|---|---|---|
| `deployment_enabled` | `true` | `tools/build_pages_release.py:111-112` |
| `release_skus` | exactly one SKU | `tools/build_pages_release.py:114-116` |
| `request_backend.e2e_verified` | `true` | `tools/build_pages_release.py:157-158` |
| `request_backend.owner_notification_verified` | `true` | `tools/build_pages_release.py:159-160` |
| `request_backend.customer_confirmation_verified` | `true` | `tools/build_pages_release.py:161-162` |
| `request_backend.verified_at` | timezone-aware ISO 8601 (e.g. `2026-09-01T14:30:00-05:00`) | `tools/build_pages_release.py:163-164`, `tools/build_pages_release.py:99-106` |

Keep `source_allowlist` complete: every file that an allowlisted page links to
must also be allowlisted, or `tools/test_pages_release.py:100-110` fails with
`Release link target is missing: <page> -> <target>`.

### C. Canonical state — `config/project-state.json`

| Field | Set to | Enforced by |
|---|---|---|
| `programs.tefa.evidence_status` | `"verified_repository_record"` | `tools/build_pages_release.py:120-121` |
| `programs.tefa.public_approval_claim_allowed` | `true` (already is) | `tools/build_pages_release.py:122-123` |

### D. Request intake — `config/request-intake.json`

| Field | Set to | Enforced by |
|---|---|---|
| `enabled` | `true` | `tools/build_pages_release.py:150-151`; `tools/validate_project_state.py:362-364` |
| `endpoint` | valid `https://formspree.io/f/<id>` | `tools/build_pages_release.py:152-154`; `tools/validate_project_state.py:357-361` |
| `allowed_skus` | include the release SKU (must exist in the catalog SKU set) | `tools/validate_project_state.py:347-353` |
| `support_email` | must match `config/project-state.json` `business.support_email` | `tools/validate_project_state.py:320-323` |

Note: `config/project-state.json:15-16` records the support email as
`temporary` — replace it with the permanent address before enabling intake, and
keep the two files in sync or `tools/validate_project_state.py:320-323` fails.

### E. Public source must reference only the release SKU

The allowlisted public HTML/JS/JSON must contain that one SKU and **no other**
SKU-shaped identifiers (`tools/build_pages_release.py:139-144`). Since the
storefront currently shows all 18 SKUs (e.g. `store/src/shop.html`), the public
release artifact's allowlist must be scoped so only the release SKU appears in
shipped sources.

---

## Verify locally before opening the release PR

```bash
# 1. State + catalog invariants (must print the "valid" line)
python3 tools/validate_project_state.py

# 2. Rebuild generated pages and commit them (CI compares committed output)
python3 build.py

# 3. Artifact shape (no --require-ready): builds and lists remaining blockers
artifact="$(mktemp -d)/pages-release"
python3 tools/build_pages_release.py --output "$artifact"
python3 tools/test_pages_release.py "$artifact"

# 4. The real gate — must pass with zero blockers only when truly ready
python3 tools/build_pages_release.py --output "$artifact" --require-ready
```

Step 4 currently fails **by design** and lists every unfinished gate
(`docs/workflow/PAGES_RELEASE.md`). It should pass only in the commit where all
of A–E are satisfied with attached evidence.

---

## What this runbook does NOT authorize

- It does not deploy. Tier 3 production deployment requires the owner's explicit
  approval (`LAUNCH_AUDIT.md`).
- It does not permit publishing a price without a verified catalog record, nor
  marking any SKU available before Odyssey offering review completes
  (`.system/skills/skills_loops_prompts.md`, Section 0).
