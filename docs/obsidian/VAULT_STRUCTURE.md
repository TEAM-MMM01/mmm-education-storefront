# Obsidian Vault Structure

Use Obsidian for business memory, decisions, product thinking, SOPs, and meeting notes.
Use GitHub for code and reviewed operational documentation.

## Recommended vault

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

## Starter notes

```text
01-Companies/Preparation Station.md
02-Projects/Preparation Station Storefront.md
02-Projects/OmniRoute Dashboard.md
02-Projects/Hermes Agent.md
03-Products/ESA Product Ideas.md
03-Products/High Ticket Bundles.md
04-SOPs/GitHub PR Workflow.md
04-SOPs/Codex Cloud Workflow.md
04-SOPs/Launch Checklist.md
08-Dashboards/Launch Status Dashboard.md
```

## Sync recommendation

Obsidian Sync is the safest default for daily notes across Mac and HP. A private GitHub
vault repo is useful for structured operating docs, but it requires more care around merge
conflicts. The preferred long-term setup is Obsidian Sync for the human vault and GitHub
for selected docs that agents and dashboards need to read.

## Scaffold command

Run the helper from the repository root to create the vault on each device after choosing
your sync method:

```bash
python3 tools/create_obsidian_vault.py ~/Obsidian/TEAM-MMM01\ Operations\ Vault
```

The helper refuses to create the daily vault inside this storefront repository unless
`--allow-inside-repo` is passed for a deliberate test fixture.
