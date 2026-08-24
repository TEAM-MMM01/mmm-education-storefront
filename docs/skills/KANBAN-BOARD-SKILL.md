# Kanban Board Skill

## Overview
Self-hosted Kanban dashboard with voice AI, drag-and-drop, and agent spawning.

## Access
- **Local**: http://localhost:8088
- **iPad**: http://192.168.12.187:8088
- **HTTPS (voice)**: https://192.168.12.187:8443

## The 5 Columns

| Column | Meaning | When to use |
|--------|---------|-------------|
| **Backlog** | Tasks that exist but aren't urgent | Create tasks here |
| **Ready** | You've decided this matters | When you want agents to start |
| **In Progress** | Agent is actively working | Happens when agent pulls |
| **Review** | Work done, needs your approval | Agent finished, you check |
| **Done** | Completed and approved | You approve the work |

## The Flow
```
Backlog → Ready → In Progress → Review → Done
  "Idea"   "Do it"   "Working"   "Check"   "Done!"
```

## Quick Commands

| Action | How |
|--------|-----|
| Create task | Type in AI: "Create task: Fix bug" |
| Move card | Drag it to the column |
| Assign agent | Click 👥 tab → select agent → describe |
| Ask AI | Click 🤖 → "What should I do next?" |
| Voice | Click 🤖 → speak your question |

## Priority Colors
- 🔴 Critical = Do NOW
- 🟠 High = Important, do today
- 🟡 Medium = Do this week
- 🟢 Low = Whenever

## Agent Matching
Skills are matched automatically:
- `code-review` → Hermes COO
- `education` → Prep Station
- `trading` → Hermes PF
- `oracle` → The Oracle

## Access Outside House
Use Cloudflare Tunnel:
```bash
cloudflared tunnel --url http://localhost:8088
```
This gives you a public URL you can use anywhere.

## Files
- Server: `tools/kanban/server.py`
- Board: `tools/kanban/board.py`
- Dashboard: `tools/kanban/dashboard.html`
- Data: `~/.hermes-mac/kanban/board.json`
