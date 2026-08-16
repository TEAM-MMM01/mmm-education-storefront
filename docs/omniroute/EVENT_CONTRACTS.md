# OmniRoute Event Contracts

These event contracts are proposed placeholders for implementation. They should be aligned
with the real OmniRoute API before production use.

## Common envelope

```json
{
  "event": "string",
  "source": "github|codex|obsidian|dashboard|storefront",
  "repository": "TEAM-MMM01/mmm-education-storefront",
  "branch": "string",
  "actor": {
    "system": "codex|claude|devin|human|other",
    "identity": "attributable GitHub actor or app",
    "access_mode": "read|branch_write|pull_request"
  },
  "risk": "low|medium|high",
  "summary": "string",
  "links": [],
  "payload": {}
}
```

## Proposed events

| Event | Purpose |
| --- | --- |
| `github.pr.opened` | A PR is ready for review. |
| `github.pr.merged` | Approved work landed on the stable branch. |
| `build.passed` | Build command completed successfully. |
| `build.failed` | Build command failed and needs attention. |
| `launch.blocker.added` | A launch blocker was identified. |
| `launch.blocker.resolved` | A launch blocker was removed. |
| `obsidian.note.promoted` | A note became structured operating context. |
| `product.ready_for_review` | A product has enough confirmed details for review. |
| `agent.task.requested` | A redacted, bounded task is ready to be assigned. |
| `agent.pull_request.opened` | An attributable agent branch produced a draft PR. |

## Model-routing fields

Every routable task should include:

- Task type.
- Risk level.
- Required files or notes.
- Must-run checks.
- Output format.
- Human approval requirement.

## Access boundary

OmniRoute routes redacted task envelopes; it does not grant repository access. Codex,
Claude, Devin, and any later agent must authenticate to GitHub independently and follow
`AGENTS.md`. Never include a GitHub token, application private key, customer record, child
information, or raw Obsidian note in an event payload.

OmniRoute must not push to `main`, merge, deploy, or reuse one agent's branch for another
agent. Its safe write boundary is an attributable agent branch and draft pull request.
