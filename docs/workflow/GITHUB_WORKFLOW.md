# GitHub Workflow

Preparation Station uses GitHub as the source of truth for code, launch documentation,
and pull-request review. Local devices and cloud agents should be treated as workstations,
not as the canonical copy of the business system.

## Branches

- `main` is the stable reviewed branch.
- `agent/<short-task-name>` is for Codex or other agent-produced changes.
- `feature/<short-task-name>` is for human-authored feature work.
- `docs/<short-task-name>` is for documentation-only work.

Do not merge directly to `main`. Open a pull request, review the generated diff, and merge
only after the owner approves the change.

## Standard task loop

1. Start from the current `main` branch.
2. Create a focused working branch.
3. Read the relevant docs before editing.
4. Edit source files, not only generated HTML.
5. Run the documented build or validation command.
6. Review `git diff` before committing.
7. Commit with a concise message.
8. Open a draft PR for owner review.
9. Do not deploy, publish, or merge without approval.

## Automated checks

Pull requests and pushes to `main` run the `Build storefront` GitHub Actions workflow. The
workflow runs `python3 build.py` and fails if generated storefront pages differ from the
committed files.

Issue templates capture storefront, OmniRoute, and Obsidian tasks with the context needed
for agent routing and owner review.

## Storefront-specific rules

- Keep Preparation Station branding visible and consistent.
- Preserve ESA/funding documentation as the primary storefront path until direct commerce
  is operational.
- Keep General Store clearly labeled as a preview until payment, tax, order creation,
  shipping, fulfillment, and confirmed product details are live.
- Do not invent prices, policies, legal claims, vendor approvals, product facts, or launch
  readiness.

## Device strategy

The Mac, HP, and cloud agents should all sync through GitHub instead of syncing directly
with each other. If a device is lost or replaced, clone the repositories from GitHub and
restore Obsidian from its chosen sync source.
