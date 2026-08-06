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

## Model-routing fields

Every routable task should include:

- Task type.
- Risk level.
- Required files or notes.
- Must-run checks.
- Output format.
- Human approval requirement.
