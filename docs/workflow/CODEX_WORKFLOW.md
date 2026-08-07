# Codex Workflow

Codex should operate through GitHub branches and pull requests. The goal is repeatable,
reviewable work rather than one-off edits on a local machine.

## Before editing

Codex should confirm the current branch, inspect repository instructions, read relevant
launch documentation, and stop if the repository state does not match the requested task.

## During editing

- Make the smallest complete change that satisfies the task.
- Prefer source files over generated files.
- Keep ESA and General Store boundaries intact.
- Preserve placeholders when facts are unknown.
- Use explicit documentation when a system is planned but not active.

## After editing

Run the relevant checks, summarize the results, commit the change, and open a draft PR
when GitHub access is available.

## Model-routing readiness

Until OmniRoute is connected, model selection is manual. Once OmniRoute is available, Codex
work items should include:

- Task type: code, docs, audit, design, data, compliance review, or operations.
- Risk level: low, medium, or high.
- Required context files.
- Required checks.
- PR title and acceptance criteria.

These fields give OmniRoute enough structure to assign the best available model or agent
for each task.
