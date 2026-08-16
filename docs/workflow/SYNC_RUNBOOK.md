# Device Sync Runbook

This runbook is the single, executable recipe for keeping every Preparation
Station workstation (Mac, HP, and any future device) in step with GitHub. It
is the practical companion to `AGENTS.md`, `docs/workflow/DEVICE_SYNC.md`,
`docs/workflow/GITHUB_WORKFLOW.md`, and `docs/workflow/AGENT_ACCESS.md`.

The rule is unchanged: **GitHub is the source of truth; devices are access
points, not canonical copies.**

## 1. Required repos for a Preparation Station device

| Repo | Visibility | Purpose | Clone URL | Default branch |
| --- | --- | --- | --- | --- |
| `mmm-education-storefront` | public | Storefront code, validator, build, CI | `https://github.com/TEAM-MMM01/mmm-education-storefront.git` | `main` |
| `obsidian-vault` | private | Obsidian operating notes (Hermes, businesses, launch control) | `https://github.com/TEAM-MMM01/obsidian-vault.git` | `main` |
| `obsidian-sync` | private | Git-based sync helper for the Obsidian vault | `https://github.com/TEAM-MMM01/obsidian-sync.git` | `main` |

Optional companion repos (clone only if the device needs them):

| Repo | Purpose |
| --- | --- |
| `royal-collexions-brand-system` | Royal Collexions retail/dropshipping (planned; clone only after it exists and is reviewed) |
| `HermesOS-*` | Orchestration runtime; treat as separate from this storefront repo per `config/project-state.json` |

## 2. Recommended layout on a device

Keep clones under a single parent so the recipe is identical on every device:

```
~/Projects/TEAM-MMM01/
  mmm-education-storefront/
  obsidian-vault/
  obsidian-sync/
```

The parent name `TEAM-MMM01` mirrors the GitHub owner so a new device can be
provisioned with the same commands regardless of which machine the operator
is sitting at.

## 3. First-time setup on a new device

```bash
# 1. Authenticate GitHub CLI (per-device; never share a token).
gh auth login

# 2. Clone the three required repos side by side.
mkdir -p ~/Projects/TEAM-MMM01 && cd ~/Projects/TEAM-MMM01
git clone https://github.com/TEAM-MMM01/mmm-education-storefront.git
git clone https://github.com/TEAM-MMM01/obsidian-vault.git
git clone https://github.com/TEAM-MMM01/obsidian-sync.git

# 3. Confirm each repo is on the canonical default branch and clean.
for r in mmm-education-storefront obsidian-vault obsidian-sync; do
  echo "=== $r ==="
  git -C "$r" status -sb
  git -C "$r" branch --show-current
done
```

Expected output: each repo on its default branch with no uncommitted changes.

## 4. Daily sync routine

```bash
# Pull all three repos to current default branch.
for r in mmm-education-storefront obsidian-vault obsidian-sync; do
  echo "=== $r ==="
  git -C ~/Projects/TEAM-MMM01/"$r" fetch --prune
  git -C ~/Projects/TEAM-MMM01/"$r" pull --ff-only
done

# Run the storefront guard + validator + build to confirm local state matches CI.
cd ~/Projects/TEAM-MMM01/mmm-education-storefront
python3 tools/check_untracked.py
python3 tools/validate_project_state.py
python3 build.py
```

The storefront command exits non-zero on any forbidden local-only path, on any
canonical-fact drift, or on any generated-page mismatch. If any command fails,
do not push; reconcile locally first.

## 5. Obsidian vault sync

The vault is its own Git repo (`obsidian-vault`). Use `obsidian-sync/sync.sh`
for the Git round-trip; Obsidian Sync (paid) is also acceptable for daily
note edits but never replaces Git as the canonical mirror.

```bash
cd ~/Projects/TEAM-MMM01/obsidian-vault
~/Projects/TEAM-MMM01/obsidian-sync/sync.sh --dry-run   # preview
~/Projects/TEAM-MMM01/obsidian-sync/sync.sh             # commit
```

Rules (from `AGENTS.md`):

- Never store credentials, tokens, customer records, child information,
  disability records, school identifiers, or financial documents in the
  vault.
- Do not work from a long-lived branch in the vault. Branch per task, PR,
  merge, delete.
- Do not share one GitHub credential across machines. Each device must use
  its own keychain-stored token.

## 6. Branch and PR conventions

Same on every repo:

- `main` — reviewed, stable.
- `agent/<short-task-name>` — agent-produced changes (Codex, Claude, Devin).
- `feature/<short-task-name>` — human-authored feature work.
- `docs/<short-task-name>` — documentation-only work.

Do not push directly to `main`. Open a draft PR, run the build workflow, and
wait for owner approval before merge. See
`docs/workflow/GITHUB_WORKFLOW.md` for the full task loop.

## 7. What to never commit (any repo)

These are enforced by `.gitignore` plus `tools/check_untracked.py` in the
storefront repo:

- `.claude/` — local Claude Code session memory.
- `_org-backup/` — local snapshot directories.
- `_audits/` — local secret-scan / audit-run outputs.
- `.DS_Store`, `*.log`, `*.swp`, `*.swo`, `*~` — OS / editor noise.
- `.venv/`, `venv/`, `__pycache__/` — Python build artifacts.

If you legitimately need a new ignore pattern, change `.gitignore` in a
dedicated PR and update the regex list in `tools/check_untracked.py` in the
same PR.

## 8. If a device is lost or replaced

```bash
# On the new device, after gh auth login:
mkdir -p ~/Projects/TEAM-MMM01 && cd ~/Projects/TEAM-MMM01
git clone https://github.com/TEAM-MMM01/mmm-education-storefront.git
git clone https://github.com/TEAM-MMM01/obsidian-vault.git
git clone https://github.com/TEAM-MMM01/obsidian-sync.git
```

If the vault used Obsidian Sync (paid), restore the vault from Obsidian Sync
on top of the Git clone. Git history will be preserved as long as no
uncommitted changes remain on the lost device.

## 9. HP-specific notes

- The HP must use the same layout (`~/Projects/TEAM-MMM01/`).
- The HP must use a separate GitHub credential, stored in its own keychain.
  Never copy a token from the Mac to the HP.
- The HP is intended as additional storage and a clean clone target, not as a
  second canonical editor. Day-to-day editing should happen on the Mac or in
  the cloud, then pushed, then pulled on the HP.
- Items discovered on the HP that are not already in a repo should be
  ingested through a dedicated `agent/hp-inbox` PR so the PR record explains
  what was kept, what was discarded, and why.

## 10. Quick checklist before requesting review on any PR

```
[ ] Branched off current main, named agent/<task> or docs/<task>
[ ] Read AGENTS.md and the relevant docs/workflow/* file
[ ] Ran python3 tools/check_untracked.py locally (passes)
[ ] Ran python3 tools/validate_project_state.py locally (passes)
[ ] Ran python3 build.py locally (idempotent; no generated-page drift)
[ ] Reviewed git diff --stat and git diff before committing
[ ] PR body explains every generated file (build artifacts, regenerated HTML)
[ ] Draft PR opened; owner approval obtained before merge or deploy
```