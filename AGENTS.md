# Preparation Station Agent Instructions

These instructions apply to Codex, Claude, Devin, local scripts, and any other
automation working in this repository.

## Source of truth

- GitHub is the source of truth for code and reviewed operating documentation.
- Read `config/project-state.json`, `catalog/books.json`, `LAUNCH_AUDIT.md`, and
  the relevant file under `docs/workflow/` before changing behavior or claims.
- Do not use OmniRoute, Obsidian, a laptop, or an agent workspace as a second
  canonical copy of this repository.

## Git workflow

- Start from current `main` and work on `agent/<short-task-name>`.
- Never push directly to `main`, force-push, auto-merge, or deploy without the
  owner's explicit approval.
- Keep one focused change per pull request and explain all generated files.
- Do not rename the repository in the same pull request as a product, workflow,
  deployment, or domain change.

## Build and validation

Run these checks before requesting review:

```bash
python3 tools/validate_project_state.py
python3 build.py
python3 tools/check_untracked.py   # once PR #13 lands on main
git diff --check
git status --short
```

The first command also runs the storefront JavaScript / order-portal checks
defined in `tools/` (request intake, order tracking). The build pipeline
itself runs `python3 tools/check_untracked.py` (via `.github/workflows/build.yml`)
to reject any forbidden local-only path that has slipped past `.gitignore`.

When storefront source changes, commit the matching generated HTML from
`python3 build.py`. Never edit generated HTML as the only source change.

For the device sync recipe (clones, branches, daily routine, recovery),
follow `docs/workflow/SYNC_RUNBOOK.md` in addition to the workflow docs
listed below.

For Mac orchestration (queue, connectivity, EOD Huddle agenda), use
`tools/orchestration/` in this repo. These scripts are pure local and
require no remote calls.

## Tiered execution and EOD Huddle

This repository follows the HermesOS Control Plane doctrine. Every agent
session must classify its work by tier and L4 risk:

- **Tier 1** — begin automatically: read-only discovery, audits, docs,
  drafts, queue design, test plans, local verification.
- **Tier 2** — begin after scope verification: reversible implementation,
  branch-based code changes, local scripts, PR-ready implementations.
- **Tier 3** — prepare, verify, then request Richie approval before
  executing: production deployments, secret rotation, customer
  communications, financial actions, destructive changes, public
  messaging, pricing or strategy changes.

Workflow truth states (use only these exact seven):

`Locally Complete`, `Queued for Remote Execution`, `Remote Attempted`,
`Remotely Verified`, `Blocked`, `Awaiting Approval`, `Needs Richie's Lock`.

A successful UI, a local commit, a sent message, or a green CI run is
never by itself proof of completion. Verifiers must be a different
model from the writer for L4-2 and above. Unresolved questions are
parked in the EOD Huddle ledger (`obsidian-vault/00-HQ/EOD-Huddle/`)
so nothing disappears.

## Approved business facts

- Public brand: Preparation Station.
- Legal operator: Nationwide Acquisitions, LLC.
- Approved public disclosure: "Preparation Station is operated by Nationwide
  Acquisitions, LLC."
- Temporary support email: `mmminvestment25@gmail.com`.
- Complete requests are acknowledged within one business day.
- Nationwide Acquisitions, LLC is an approved TEFA Marketplace vendor based on
  the owner-provided approval email. Public claims must name the approved legal
  entity and state that each offering is reviewed separately in Odyssey.
- PDSES/ClassWallet status is unknown and must not be advertised as approved.
- The Vulturian is a confirmed title; its author credit, ISBN, price, format,
  description, cover, and printing/fulfillment source remain pending.

## Product and channel boundaries

- Preparation Station owns education-program information, educational product
  presentation, and request/quote workflows.
- Royal Collexions owns non-funded Shopify commerce, dropshipping, fulfillment,
  and canonical coloring-book/book master records.
- Books and coloring books may appear on both sites, but both listings must use
  one canonical SKU and fulfillment record.
- Keep retail payment and funded quote/invoice flows separate.
- TEFA purchases and official TEFA order history stay in Odyssey. Preparation
  Station may mirror fulfillment status only after a secure, attributable import
  or supported integration.
- Do not describe a product as TEFA- or PDSES-eligible unless current,
  product-specific evidence is recorded and approved for publication.

## Safety and privacy

- Never commit credentials, tokens, customer records, child information,
  disability records, school identifiers, financial documents, or raw Obsidian
  vault contents.
- Do not share one GitHub credential among agents. Each service must use its own
  GitHub App or narrowly scoped credential.
- Every automated write must be attributable to a branch, commit, and pull
  request. Concurrent agents must use separate branches.
- Treat OmniRoute as a model gateway. It may route redacted task envelopes, but
  it does not grant GitHub access and must not receive repository credentials.

## Agent quality checklist (from Devin AI review)

Before requesting review on any PR, verify:

- **Full execution flow traced.** Walk through every phase of multi-phase
  workflows end-to-end. If a script has `--verify`, mentally execute phase 2
  and confirm argparse, state, and file paths all work.
- **Docstring/contract match.** Re-read the module docstring after every change.
  If it says "any error counts as offline", catch all exceptions. If it says
  "pure local", don't make network calls by default.
- **AGENTS.md compliance.** Grep AGENTS.md for the relevant constraint before
  any change. Branch prefixes, source-of-truth rules, and approved facts are
  enforced by code review.
- **Conflict documented.** When two requirements conflict (e.g. CodeQL vs test
  isolation), document the tradeoff explicitly rather than silently breaking
  one side.

## Code Review Rules

- Block unsupported approval, price, inventory, shipping, fulfillment, legal,
  or launch-readiness claims.
- Block changes that mix retail checkout with TEFA/PDSES quote or invoice flows.
- Block direct edits to generated HTML when the corresponding source file was
  not updated.
- Block secrets, private notes, or sensitive customer data in tracked files.
- Require `tools/validate_project_state.py` and `build.py` to pass.
