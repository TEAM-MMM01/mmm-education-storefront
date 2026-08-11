# Baby-Agent Harness

A minimal, audited harness for spawning short-lived sub-agents that work on
this repository under the rules in `AGENTS.md`. It exists so that a parent
agent (Codex, Claude, Devin, or a local script) can hand a focused task to
a sub-agent and receive a draft PR without ever touching `main`, never
deploying, and never sharing credentials.

The harness is intentionally boring: Python + Git only, no new services, no
new dependencies, no daemon. Every command in this directory is invoked
explicitly by an operator (or by a trusted parent agent) and emits a
machine-readable `report.json` next to the working tree.

## What a baby-agent does

1. Reads `AGENTS.md` and the relevant docs (`docs/workflow/*`).
2. Creates a fresh branch `agent/<task-name>` off current `main`.
3. Makes a focused change (one logical change per branch).
4. Runs the storefront guard + validator + build:
   - `python3 tools/check_untracked.py`
   - `python3 tools/validate_project_state.py`
   - `python3 build.py`
5. If all three pass, opens a **draft** pull request against `main` using
   the GitHub CLI and writes the PR URL to `report.json`.
6. If any check fails, aborts with non-zero exit and a human-readable error
   in `report.json`.

The harness never pushes to `main`, never enables auto-merge, never edits
`config/project-state.json` without operator confirmation, and never reads
or writes anything outside the repository root.

## Files

| File | Purpose |
| --- | --- |
| `run.sh` | Single entry point. `bash tools/agent_loop/run.sh <task-name>` |
| `baby_agent.py` | Orchestrator: branch → edit (delegated to caller) → validate → push → PR |
| `select_task.py` | Reads `tasks/<name>.md` and prints the task body + safety checks |
| `report.tmpl.json` | Shape of `report.json` emitted on success/failure |

## Usage

```bash
# 1. Write a task spec under tasks/<name>.md (see tasks/README.md).
# 2. From the repo root, on current main:
bash tools/agent_loop/run.sh fix/typo-in-README

# 3. Read report.json for the PR URL (or the failure reason).
cat report.json
```

## Safety properties

- **No `git push` to `main`.** The push target is always the new
  `agent/<task>` branch, with `--set-upstream`.
- **No `--force` and no `--no-verify`.** Both are forbidden by the harness.
- **No `gh pr merge` and no `gh pr edit --enable-auto-merge`.** The PR is
  always opened as `--draft` and the harness exits; the operator decides.
- **No shell interpolation.** Every subprocess call uses an argv list with
  no `shell=True`. User-supplied strings are passed only as positional
  arguments after explicit allowlist checks.
- **Allowlisted branch prefixes.** The harness refuses any task name that
  would produce a branch not starting with `agent/`, `feature/`, `docs/`,
  or `fix/`.
- **Allowlisted file paths.** The baby-agent edits only files declared in
  `tasks/<name>.md` under a `paths:` list. Files outside the list cause an
  abort.
- **Pre-PR checks mandatory.** If `check_untracked.py`,
  `validate_project_state.py`, or `build.py` exits non-zero, the harness
  aborts and writes the failure to `report.json`.

## What this is NOT

- Not an orchestrator that auto-merges PRs.
- Not a daemon or scheduler.
- Not a credential store. GitHub auth uses the operator's own `gh` CLI
  session, never a token pasted into a file.
- Not a replacement for `AGENTS.md`. Every baby-agent still reads and
  follows `AGENTS.md` on every run.