# Owner Next Steps

Use this checklist to get GitHub, Obsidian, OmniRoute, and the dashboard organized without
making any one device the source of truth.

## Current answer

No, this storefront repository is not running through OmniRoute yet. The repository now has
planning docs for OmniRoute, but real routing requires the OmniRoute repo, API endpoint,
event schema, or dashboard codebase that should receive events.

## Step 1: secure GitHub access

Do this first because GitHub should be the source of truth for code and reviewed operating
docs.

1. Revoke any GitHub token that was pasted into a terminal, chat, note, screenshot, or
   shared document.
2. On the Mac and HP, use browser-based GitHub CLI login instead of pasting long-lived
   tokens into shell commands.
3. Confirm each device can run:

   ```bash
   gh auth status
   git clone https://github.com/TEAM-MMM01/mmm-education-storefront.git
   ```

4. Keep all future code changes on branches and pull requests.

## Step 2: choose the Obsidian sync method

Pick one before creating lots of notes.

### Recommended default

Use Obsidian Sync for the daily working vault across Mac and HP. It is the simplest path
for business notes, decisions, product ideas, and SOP drafts.

### Automation-friendly option

Create a private GitHub repo only for selected operating docs that agents and dashboards
can read. Do not put secrets, raw tokens, personal mail, private customer data, or the
entire daily Obsidian vault into that repo.

### Recommended hybrid

- Obsidian Sync for private daily notes.
- GitHub markdown docs for approved operating context.
- OmniRoute reads GitHub docs and selected exported note summaries later.

## Step 3: create the Obsidian vault

Create this vault on the chosen sync method. The repository includes a helper for this step:

```bash
python3 tools/create_obsidian_vault.py ~/Obsidian/TEAM-MMM01\ Operations\ Vault
```

The helper creates the folder structure and starter notes outside this storefront repo.

Create this vault layout:

```text
TEAM-MMM01 Operations Vault/
  00-Inbox/
  01-Companies/
  02-Projects/
  03-Products/
  04-SOPs/
  05-Meetings/
  06-Finance/
  07-Legal-Admin/
  08-Dashboards/
  09-Archive/
```

Start with these notes:

```text
01-Companies/Preparation Station.md
02-Projects/Preparation Station Storefront.md
02-Projects/OmniRoute Dashboard.md
02-Projects/Hermes Agent.md
03-Products/High Ticket Bundles.md
04-SOPs/GitHub PR Workflow.md
04-SOPs/Codex Cloud Workflow.md
08-Dashboards/Launch Status Dashboard.md
```

## What is now handled in this repo

- Pull requests now have a checklist for storefront safety, OmniRoute status, testing, and
  owner approval gates.
- GitHub Issues now have forms for storefront tasks, OmniRoute routing tasks, and Obsidian
  operations tasks.
- GitHub Actions now runs `python3 build.py` on pull requests and `main` pushes, then checks
  that generated storefront pages are committed.
- `tools/create_obsidian_vault.py` now creates the recommended Obsidian vault scaffold on
  any device without committing the real daily vault into this repository.

## Step 4: decide what OmniRoute should control first

Start small. Do not try to automate the entire business at once.

Recommended first routing jobs:

1. Send GitHub PR status into the dashboard.
2. Send build pass/fail status into the dashboard.
3. Route documentation tasks to a documentation model/agent.
4. Route code edits to a code model/agent.
5. Route launch-readiness checks to an audit model/agent.

## Step 5: provide the missing OmniRoute details

To wire OmniRoute for real, provide one of these:

- OmniRoute GitHub repository name.
- Dashboard GitHub repository name.
- OmniRoute API endpoint and authentication method.
- Existing event schema.
- A README or design note explaining OmniRoute's current architecture.

Without that, this repo can only define the planned contract; it cannot send real events.

## Step 6: add dashboard widgets in this order

1. Open PRs.
2. Latest build result.
3. Launch blockers.
4. ESA product readiness.
5. General Store preview status.
6. Next owner action.
7. OmniRoute assignment queue.

## Step 7: storefront launch work after operations are organized

After the workflow is stable, return to the storefront launch path:

1. Confirm ESA products and prices with real supplier costs.
2. Remove or clearly mark placeholders.
3. Keep General Store preview-only until real commerce infrastructure exists.
4. Connect quote requests to a real operator task or CRM.
5. Choose preview deployment first, then production domain later.

## Owner decision needed now

**Current state (2026-08-24):**
- Site is LIVE on Vercel (not Netlify)
- All sub-pages deployed and returning 200
- Kanban dashboard running with all tools functional
- 6 Telegram bots verified (5 live, 1 needs BotFather)
- GitHub Actions restricted to TEAM-MMM01-owned actions

Choose the next implementation target:

1. **Create The Oracle bot** via BotFather — enables trading signals lane.
2. **Get Slack bot token** (xoxb- format) — enables Slack notifications.
3. **Send TEFA submission email** — draft at `docs/tefa-email-draft.md`.
4. **Resolve LOCK-4 through LOCK-7** — all need Richie decision.
5. **OmniRoute wiring** — give the OmniRoute/dashboard repo or API details.
