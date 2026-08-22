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

## Where a verified SKU lives (implemented)

**Background — why a separate file exists.** The release gate and the state
validator have opposite requirements for `public_listing_allowed`:

- `tools/build_pages_release.py:133-137` **requires** the release SKU's catalog
  record to have `public_listing_allowed: true` and
  `funding_eligibility.tefa == "verified_product_evidence"`.
- `tools/validate_project_state.py:265` **requires every item in**
  `catalog/products.json` to have `public_listing_allowed` **false**, with
  `price_status == "illustrative_unverified"` (`tools/validate_project_state.py:266`)
  and `retail_price_usd` null (`tools/validate_project_state.py:267`).

You therefore **cannot** verify one of the fixed 18 SKUs by flipping it in place
inside `catalog/products.json`.

**Resolution (already implemented in this PR):** verified, launch-eligible
offerings live in a **separate catalog file, `catalog/tefa-offerings.json`**,
distinct from the 18-item illustrative set. This works because
`tools/build_pages_release.py:76-86` globs **every** `catalog/*.json`, so a SKU
recorded there satisfies the release gate, while `tools/validate_project_state.py`
keeps validating `catalog/products.json` unchanged. A new validator,
`validate_tefa_offerings()` in `tools/validate_project_state.py`, enforces the
verified shape of the new file and is wired into `main()`
(`tools/validate_project_state.py:460-463`); the file ships empty today and
scales to many verified SKUs over time.

**Key rule:** the verified SKU is a **new** `PS-XX-###` SKU placed **only** in
`catalog/tefa-offerings.json`. Do **not** add it to `catalog/products.json`,
`store/cart.js`, or the shop `data-request-sku` controls — those three must stay
exactly equal to the fixed-18 set (`tools/validate_project_state.py:280`,
`tools/validate_project_state.py:301`), and `validate_tefa_offerings()` also
requires the verified SKU to be distinct from the 18.

---

## Field checklist (per gate)

Verification adds one item to `catalog/tefa-offerings.json` and sets the fields
below. Each row lists the field and the enforcing check.

### A. Verified catalog record — new item in `catalog/tefa-offerings.json`

Append one object to the `items` array (the file ships with `items: []`):

| Field | Set to | Enforced by |
|---|---|---|
| `sku` | a new `PS-XX-###`, distinct from the 18 | `tools/validate_project_state.py` `validate_tefa_offerings()` |
| `name` | the verified offering name | `validate_tefa_offerings()` |
| `public_listing_allowed` | `true` | `tools/build_pages_release.py:133-134`; `validate_tefa_offerings()` |
| `tefa_offering_status` | `"approved"` | `validate_tefa_offerings()` |
| `odyssey_offering_id` | the real Odyssey ID | `validate_tefa_offerings()` |
| `funding_eligibility.tefa` | `"verified_product_evidence"` | `tools/build_pages_release.py:135-137`; `validate_tefa_offerings()` |

Optional growth/profitability fields (validated only when present, so you can
add them as data matures):

| Field | Set to | Purpose |
|---|---|---|
| `retail_price_usd` | non-negative number or `null` | reference only; the customer-facing price is the Odyssey offering record, not this site |
| `target_margin_pct` | `0`–`100` | margin signal for `REVENUE_PRIORITIES` ranking |
| `fulfillment_mode` | `digital_zero_marginal` \| `physical_kit` \| `made_to_order` \| `dropship` | time-buyback signal — prefer `digital_zero_marginal` first |

The SKU must resolve to **exactly one** catalog record across all
`catalog/*.json` (`tools/build_pages_release.py:128-130`), which is why it must
not be duplicated into `catalog/products.json`.

**Fill-in template.** Copy the object below into the `items` array of
`catalog/tefa-offerings.json` and replace every `REPLACE_*` value with real,
verified data. Do **not** commit it with the placeholder values — the file must
keep `"items": []` until a genuine verified record exists, or you falsely
satisfy the launch gate. Required fields first, optional growth fields after:

```json
{
  "sku": "PS-XX-###",
  "name": "REPLACE_verified_offering_name",
  "public_listing_allowed": true,
  "tefa_offering_status": "approved",
  "odyssey_offering_id": "REPLACE_real_odyssey_offering_id",
  "funding_eligibility": { "tefa": "verified_product_evidence" },
  "retail_price_usd": null,
  "target_margin_pct": null,
  "fulfillment_mode": "digital_zero_marginal"
}
```

- `sku` — a new `PS-XX-###` (e.g. a verified digital lane), **not** one of the
  18 illustrative SKUs.
- `public_listing_allowed`, `tefa_offering_status`, `odyssey_offering_id`,
  `funding_eligibility.tefa` — all required and checked by
  `validate_tefa_offerings()` in `tools/validate_project_state.py`.
- `retail_price_usd` — the verified amount, or `null` if not yet set. It is
  accepted here (as a non-negative number) by `validate_tefa_offerings()` in
  `tools/validate_project_state.py:339-342` **with no gate change needed**. Note
  it is still not printed into `src/page.html` / `store/*` source — the
  customer-facing price is the Odyssey offering record; this field is the
  repository's record of the verified amount.
- `target_margin_pct` / `fulfillment_mode` — optional; set them to feed the
  `REVENUE_PRIORITIES` ranking in `.system/skills/skills_loops_prompts.md`
  (`digital_zero_marginal` is the highest time-buyback mode).

**Priced example (path: attaching a real price to a verified offering).** Once
an offering is verified, record its price here — this is the correct place for
pricing and needs no change to any validator or gate:

```json
{
  "sku": "PS-DL-601",
  "name": "REPLACE_verified_digital_lane_name",
  "public_listing_allowed": true,
  "tefa_offering_status": "approved",
  "odyssey_offering_id": "REPLACE_real_odyssey_offering_id",
  "funding_eligibility": { "tefa": "verified_product_evidence" },
  "retail_price_usd": 395,
  "target_margin_pct": 85,
  "fulfillment_mode": "digital_zero_marginal"
}
```

Why this does not contradict the other gates:

- `catalog/products.json` (the fixed 18) stays `retail_price_usd: null` /
  `price_status: illustrative_unverified` (`tools/validate_project_state.py:266-267`).
  Those are illustrative, unverified items — a price there would be a false
  claim, which is why it is forbidden.
- The public-source price scanner (`tools/validate_project_state.py:287`) only
  guards `src/page.html`, `store/src/shop.html`, and `store/src/product.html`.
  `catalog/tefa-offerings.json` is a data file under the forbidden `catalog/`
  top level, is never shipped, and is not scanned — so a verified price here is
  allowed and invisible to that scanner.
- Result: verified offerings carry real prices; unverified illustrative items
  never do. The two rules are complementary, not contradictory.

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
| `endpoint` | valid HTTPS Worker endpoint | `tools/build_pages_release.py:152-154`; `tools/validate_project_state.py:357-361` |
| `allowed_skus` | include the release SKU (now accepted because `main()` unions verified offering SKUs into `known_skus` at `tools/validate_project_state.py:460-463`) | `tools/validate_project_state.py:347-353` |
| `support_email` | must match `config/project-state.json` `business.support_email` | `tools/validate_project_state.py:320-323` |

Note: `config/project-state.json:15-16` records the support email as
`temporary` — replace it with the permanent address before enabling intake, and
keep the two files in sync or `tools/validate_project_state.py:320-323` fails.

### E. Public source must reference only the release SKU

The allowlisted public HTML/JS/JSON must contain that one SKU and **no other**
SKU-shaped identifiers (`tools/build_pages_release.py:139-144`). Since the
storefront currently shows all 18 SKUs (e.g. `store/src/shop.html`), the public
release artifact's allowlist must be scoped so only the release SKU appears in
shipped sources. See Section F for the worked mechanics — this is the single
most error-prone step in the whole release.

---

## F. Allowlist scoping — worked example (the fiddly step)

**How the check works.** `public_source_skus()` (`tools/build_pages_release.py:89-96`)
reads every allowlisted `.html` / `.js` / `.json` file returned by
`manifest_source_files()` (`tools/test_pages_release.py:59-70`) and collects
every match of the SKU pattern `(?:[A-Z]{2,}-){2}\d{3}`
(`tools/build_pages_release.py:22`). `readiness_blockers()` then requires that
collected set to equal **exactly** `{release_sku}`
(`tools/build_pages_release.py:139-144`). One stray SKU string anywhere in a
shipped file fails the gate.

**Why this bites.** The generated storefront pages embed many `PS-XX-###`
strings today:

- `index.html` — the Mission Guide `CATALOG` array lists all 18 SKUs.
- `store/shop.html` — every product card carries a `<span class="sku">` and a
  `data-request-sku`.
- `store/product.html` — the featured SKU plus related-item SKUs.
- `store/cart.js` — the canonical SKU map (all 18).

If any of these stay in the release `required` allowlist as-is,
`public_source_skus()` returns all 18 and the gate fails with
`public artifact sources must contain only the selected release SKU; found [...]`.

**Two ways to scope it (pick one, per the owner's launch intent):**

1. **Minimal single-SKU landing (recommended for the first release).** Ship a
   small, purpose-built public page set that references only the one verified
   SKU, and **remove** the multi-SKU pages (`index.html`, `store/shop.html`,
   `store/product.html`, `store/cart.js`) from `source_allowlist.required` in
   `config/pages-release.json`. The verified-offering page becomes the entry
   point. Lowest risk: the released artifact literally cannot leak an
   unverified SKU.

2. **Full storefront, SKUs stripped from shipped copy.** Keep the storefront
   pages but ensure the *shipped* generated output contains only the release
   SKU — i.e. the "Coming soon" 17 must not emit `PS-XX-###` strings in the
   released HTML/JS. This is a larger change to `build.py` / the source
   templates and is **not recommended** for the first release; it is easy to
   miss one string and it widens the review surface.

**Constraints to respect while scoping (all enforced):**

- You cannot release repo-internal directories. `safe_relative_path()`
  (`tools/test_pages_release.py:73-85`) forbids `catalog/`, `src/`, `tools/`,
  `general-store/`, etc., and from `config/` allows **only**
  `config/request-intake.json` and `config/order-portal.json`.
- Every link target in an allowlisted page must itself be allowlisted, or
  `tools/test_pages_release.py:100-110` fails with
  `Release link target is missing: <page> -> <target>`. When you drop pages
  from the allowlist, also drop or update links that pointed at them.
- The catalog files (`catalog/products.json`, `catalog/tefa-offerings.json`)
  are **never** shipped (they live under the forbidden `catalog/` top level), so
  the verified SKU in `catalog/tefa-offerings.json` does not itself count toward
  `public_source_skus()` — only shipped `.html`/`.js`/`.json` do.

**Verify the scoping worked:**

```bash
artifact="$(mktemp -d)/pages-release"
python3 tools/build_pages_release.py --output "$artifact" --require-ready
# Must NOT print: "public artifact sources must contain only the selected release SKU"
python3 tools/test_pages_release.py "$artifact"
# Must NOT print any "Release link target is missing" line
```

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

## G. Tier 3 pricing checklist (governance)

Recording or changing a price is a **Tier 3 action** under `AGENTS.md:62-65`
("pricing or strategy changes"). Follow this order — do not flip a price live
without Richie's explicit approval:

1. **Product verified first.** The authoritative price is set and shown during
   Odyssey offering review, not on this site (`src/page.html:781-786`). Do not
   record a price until the offering has a real `odyssey_offering_id` and
   `funding_eligibility.tefa: verified_product_evidence`.
2. **Record the verified amount** in `catalog/tefa-offerings.json`
   `retail_price_usd` — allowed only on verified records
   (`tools/validate_project_state.py:339-342`). Never in `catalog/products.json`
   or in `src/page.html` / `store/*` source (`tools/validate_project_state.py:266-267`,
   `tools/validate_project_state.py:287`).
3. **Separate verifier.** A different agent/person from the one who wrote the
   change must verify it — a green CI run or local commit is not proof of
   completion (`AGENTS.md:86-88`).
4. **Request Richie's explicit approval** before it goes live (`AGENTS.md:62-63`).
5. **Status must read `Awaiting Approval` or `Needs Richie's Lock`** until Richie
   signs off — those are the only honest truth states for an unapproved pricing
   change (`AGENTS.md:67-70`).
6. **Never animate or delay price display** (`AGENTS.md:84`); the pricing panel
   must not be reveal-gated (`src/page.html:772-774`).

---

## What this runbook does NOT authorize

- It does not deploy. Tier 3 production deployment requires the owner's explicit
  approval (`LAUNCH_AUDIT.md`).
- It does not permit publishing a price without a verified catalog record, nor
  marking any SKU available before Odyssey offering review completes
  (`.system/skills/skills_loops_prompts.md`, Section 0).
