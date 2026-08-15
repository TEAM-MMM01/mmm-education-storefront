# Agent Execution Skill — Fewer Defects, Stronger Execution

This is a reusable, repository-specific skill for every agent (Codex, Claude,
Devin, local scripts) that writes code or docs here. It exists to reduce the
recurring defect classes we actually see in review and to raise the bar for
reliable, self-validating execution. Use it alongside `AGENTS.md`; where a rule
here restates an `AGENTS.md` rule, `AGENTS.md` wins.

The goal is not more process. It is fewer round trips: land a change that is
correct the first time, validated before review, and free of regressions.

---

## How to use this skill

1. **Before you write:** read `AGENTS.md`, the relevant `docs/workflow/*`, and
   the canonical state files named in `AGENTS.md` (`config/project-state.json`,
   `catalog/books.json`, `config/pages-release.json`). Grep for the constraint
   you are about to touch.
2. **While you write:** keep the change to one focused concern (`AGENTS.md` Git
   workflow). If you find a second problem, note it — do not bundle it.
3. **Before you request review:** run the mandatory gate below and walk the
   Self-Validation Loop until every item is checked.

---

## Mandatory validation gate

Run and read the output of every command before requesting review. A green run
is necessary, not sufficient — you must also reason about what it did *not*
cover.

```bash
python3 tools/validate_project_state.py
python3 build.py
python3 tools/check_untracked.py
git diff --check
git status --short
```

If your change touches the deploy artifact, also dry-run the exact command in
`netlify.toml` and confirm it exits as intended (it is gated by
`tools/build_pages_release.py`; see "Anticipate downstream risk" below).

---

## The Self-Validation Loop

Repeat until nothing fails. Each pass, ask:

1. **Trace the full flow, not the happy path.** Mentally execute every branch,
   including the error path and the "input unchanged / empty / missing" path.
   Multi-phase scripts must be walked end-to-end (argparse, state, file paths).
2. **Cross-platform and cross-environment.** If you shell out to a
   platform-specific binary (`security`, `osascript`), handle the case where it
   is absent (`OSError`/`FileNotFoundError`), not only where it returns
   non-zero. Do not hardcode a single user's home directory or interpreter path.
3. **Re-read the docstring/contract after editing.** If it promises "never
   pushes to main", "pure local", or "returns True only on success", the code
   must actually do that on every path.
4. **Leave no persistent side effect.** If you `git checkout -b`, `cd`, or
   mutate shared state, restore it in a `finally`. Distinguish a benign no-op
   (e.g. "nothing to commit") from a real failure before reporting failure.
5. **Escape/encode data that crosses a boundary.** Text copied from a doc into
   a Markdown/HTML/JSON/shell context must be escaped for that context (e.g.
   stray `_`/`*` break Telegram `parse_mode: "Markdown"`).

---

## Learn from failures (defect patterns seen in this repo)

Each pattern below caused a real defect here. Check your change against all of
them before review.

| Pattern | What went wrong | The fix |
|---|---|---|
| **Narrow exception catch** | Caught `CalledProcessError` only; crashed when `security` was missing on non-macOS. | Catch the whole failure class (`OSError`) and fall back. |
| **Unescaped interpolation** | Doc text with `_` sent with Markdown parse mode → HTTP 400, whole message dropped. | Escape dynamic text for the target format, or drop the parse mode. |
| **Unrestored side effect** | `git checkout -b` left the vault on a throwaway branch; next pull merged into it. | Capture the original branch and restore it in `finally`. |
| **No-op read as failure** | Unchanged file → `git commit` exits non-zero → reported as a failure. | Treat "nothing to commit" as success. |
| **Success printed unconditionally** | Reported "pushed" without checking `returncode`. | Check every `returncode`; only report success when it is true. |
| **Docstring/behavior drift** | Docstring says one thing; a code path does another. | Re-read and reconcile the contract after every edit. |

---

## Anticipate downstream risk

A change is not done when it compiles. Ask what it breaks two steps away.

- **Publishing boundary.** Anything served publicly goes through the allowlist
  in `config/pages-release.json` enforced by `tools/build_pages_release.py`. A
  new page (e.g. a root `esa.html`) is **not** deployed and **not** covered by
  the noindex/claim/SKU smoke tests in `tools/test_pages_release.py` until it is
  added to the allowlist or generated from `src/` via `build.py`. Decide the
  entry point and allowlisting before calling a page "shippable".
- **Release gates.** `--require-ready` is a deliberate hard gate. Do not remove
  it to make a deploy pass; satisfy or explicitly update the gates in
  `config/pages-release.json` instead.
- **Secrets and identifiers.** Never commit credentials, tokens, or personal
  routing identifiers (e.g. a Telegram chat ID) to tracked files. Reference
  secrets by name only (see `docs/HERMESOS-OPERATING-CONTRACT.md` Secrets
  section). Keep private operating notes and local-machine inventories out of
  the repo — they can become publicly served.
- **Docs vs. runtime.** A docstring/table change (e.g. a bot mapping) does not
  change behavior unless the code, env vars, or keychain values change too.
  State clearly whether a doc edit is documentation-only.
- **Machine-specific artifacts.** Absolute paths, one user's home directory, or
  a single interpreter location will silently fail elsewhere. Template them or
  document them as machine-specific.

---

## Build for reliability without regressions

- **One focused change per PR.** Do not couple a site page with deploy config,
  session tooling, and governance docs; reviewers cannot evaluate or revert them
  independently, and coupling hides regressions.
- **No regressions to shared tokens/pipelines.** If design tokens already live
  in one canonical place (`build.py` / shared stylesheet), reuse them; do not
  fork a third copy that will drift.
- **Prefer the established pattern.** Match existing conventions (e.g. use a
  `with urlopen(...)` context manager as in `tools/notifications/__init__.py`)
  rather than introducing a divergent one.
- **Document conflicts, do not silently break one side.** When two requirements
  collide, record the tradeoff in the PR.

---

## Pre-review self-check (paste into the PR description)

```
- [ ] Read AGENTS.md + relevant docs/workflow/* + canonical state files.
- [ ] One focused change; all generated files explained.
- [ ] Mandatory validation gate run; output read, not just exit code.
- [ ] Full flow traced: error path, empty/missing input, cross-platform.
- [ ] Docstring/contract re-read and matches behavior on every path.
- [ ] No unrestored side effects (branch/cwd/shared state restored).
- [ ] Data crossing a format boundary is escaped/encoded.
- [ ] No secrets, tokens, personal identifiers, or private notes committed.
- [ ] Downstream deploy/allowlist/gate impact assessed.
- [ ] No regression to shared tokens, pipelines, or established patterns.
- [ ] Conflicts documented rather than silently broken.
```
