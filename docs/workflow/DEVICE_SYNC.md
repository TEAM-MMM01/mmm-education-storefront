# Device Sync Plan

The operating rule is simple: devices are access points, not the source of truth.

For the executable, copy-pasteable recipe (clone URLs, branch names, daily
sync commands, recovery on a lost device), see
[`SYNC_RUNBOOK.md`](SYNC_RUNBOOK.md).

## Source-of-truth map

| Area | Source of truth | Sync method |
| --- | --- | --- |
| Storefront code | GitHub repositories | Git clone, pull, branch, PR |
| Build/review history | GitHub pull requests | GitHub web, CLI, dashboard |
| Business notes | Obsidian vault | Obsidian Sync or private Git repo |
| Structured operating docs | GitHub docs | Markdown committed to repos |
| Routing and automation | OmniRoute | API/events after integration |
| Dashboard status | Dashboard app | Reads GitHub, OmniRoute, and selected docs |

## Recommended Mac and HP setup

1. Authenticate GitHub CLI on each device.
2. Clone required repos under a consistent folder such as `~/GitHub/`.
3. Install Obsidian on each device.
4. Use Obsidian Sync for the day-to-day vault, or a private GitHub vault repo if the
   owner prefers Git versioning for notes.
5. Keep generated secrets, tokens, and credentials out of Git and Obsidian notes.

## Do not do this

- Do not make one laptop the only canonical copy of the work.
- Do not paste long-lived access tokens into chat, notes, or committed files.
- Do not put the whole Obsidian vault inside the storefront repo.
- Do not mix General Store launch claims into ESA storefront documentation.
