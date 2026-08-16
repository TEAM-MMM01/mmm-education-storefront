# Baby-Agent Tasks

Each baby-agent task is a Markdown file in this directory whose filename
matches the branch it produces (without `.md`).

## Format

```markdown
# <one-line summary>

Summary: <one-paragraph description of the change>

paths:
- <relative path inside the repo>
- <relative path inside the repo>
```

The harness reads `paths:` and refuses to stage any file outside that
list. Keep the list tight; one logical change per task.

## Examples

See `tasks/README.md` (this file) and the harness README at
`tools/agent_loop/README.md` for usage.

## Why Markdown and not YAML/JSON

Markdown is readable in `gh pr diff`, in plain `cat`, and in Obsidian. The
harness only needs two fields (`summary:` and the bullet list), both of
which round-trip cleanly through Markdown.