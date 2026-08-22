# Manual Pages release gate

GitHub Pages must publish only a reviewed Preparation Station release artifact,
never the repository root. The active workflow is manual-only and will stop
before upload or deployment while any launch gate is incomplete.

## Public artifact boundary

`config/pages-release.json` is the explicit source-file allowlist. The artifact
currently permits only the Preparation Station landing page, funded-store pages,
their request/tracking scripts, and the reviewed public runtime configuration.
The builder adds `robots.txt` and `.nojekyll` itself.

The artifact must never include General Store, `.git`, `.github`, source
templates, catalogs, operating documents, agent instructions, tools, or other
repository internals. `tools/test_pages_release.py` rejects unexpected files,
unsafe local links, missing targets, symlinks, and General Store links.

Every released HTML file receives:

```html
<meta name="robots" content="noindex, nofollow, noarchive">
```

The generated `robots.txt` disallows all crawlers. These controls reduce search
discovery; they are not authentication and do not make a public GitHub Pages URL
private. Use a host with access control for a genuinely private preview.

## Hard deployment gates

The manual workflow fails unless all of the following are true in one reviewed
commit on `main`:

1. `deployment_enabled` is explicitly set to `true`.
2. `release_skus` contains exactly one SKU.
3. The company-level TEFA evidence is recorded as
   `verified_repository_record`, and the canonical state allows the public
   approval claim.
4. That SKU exists exactly once in the canonical catalog, has
   `public_listing_allowed: true`, and uses
   `funding_eligibility.tefa: verified_product_evidence`.
5. The allowlisted public HTML/JavaScript/JSON contains that SKU and no other
   SKU-shaped product identifiers.
6. `config/request-intake.json` exists, is enabled, and contains a valid HTTPS
   Worker endpoint.
7. A privacy-safe end-to-end rehearsal has verified the stored request, owner
   notification, customer on-page confirmation, and timezone-aware verification
   timestamp in `config/pages-release.json`.

The release manifest is intentionally closed now. Do not flip its readiness
fields based only on owner recollection or a successful local unit test; attach
the relevant non-sensitive evidence to the reviewed release PR.

## Local checks

CI can exercise the allowlist and smoke checks without pretending the storefront
is launch-ready:

```bash
artifact="$(mktemp -d)/pages-release"
python3 tools/build_pages_release.py --output "$artifact"
python3 tools/test_pages_release.py "$artifact"
```

The real deployment path adds `--require-ready`; it must currently fail and list
the unfinished gates.

## Existing Pages exposure

Changing the workflow stops future automatic deployments but does not erase the
artifact already served by GitHub Pages. Until the one-SKU release is approved,
the repository owner should unpublish or disable the existing Pages site in
**Settings → Pages**. That settings change is separate from this pull request.

The obsolete sample Next.js workflow was removed from active Actions. Its full
history remains recoverable in Git, so no archive copy is deployed or kept as a
second runnable workflow.
## Host mirroring (Cloudflare Pages)

The release artifact is host-agnostic. To mirror on Cloudflare Pages, either:

1. **Dashboard Direct Upload** (no secrets): create a Cloudflare Pages project
   and set
   - Build command: `python3 tools/build_pages_release.py --output pages-release --require-ready`
   - Build output directory: `pages-release`
   The `--require-ready` gate fails the build until every gate in
   `config/pages-release.json` is complete — do not drop it.
2. **CI workflow** (mirrors static.yml): run
   `.github/workflows/cloudflare.yml` from the Actions tab on `main`. Requires
   repo secrets `CLOUDFLARE_API_TOKEN` (Pages:Edit scope) and
   `CLOUDFLARE_ACCOUNT_ID`, and a Cloudflare Pages project named
   `preparation-station`. The workflow enforces the same `--require-ready`
   gate and artifact boundary checks as the GitHub Pages path.

Cloudflare Pages is a mirror, never a bypass: the same launch gates, allowlist,
and smoke checks apply before anything is uploaded.
