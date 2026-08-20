# Agent Execution Skill — Preparation Station Edition

This repository-specific skill wraps the generic `docs/workflow/AGENT_EXECUTION_SKILL.md`
with domain constraints from `AGENTS.md`, `config/project-state.json`, and the
validators (`build.py`, `tools/validate_project_state.py`).

## Mandatory Pre-Conditions (run before ANY code/doc write)

1. **Read AGENTS.md** — tiered execution (Tier 1/2/3), approved facts, safety/privacy
2. **Read config/project-state.json** — current brand, legal operator, program statuses
3. **Check git status** — no unexpected modifications; branch is `agent/<short-task-name>`
4. **Run `git diff --check`** — zero whitespace errors/conflict markers
5. **Run `python3 tools/validate_project_state.py`** — must output "Project state, catalogs, request intake, and order portal are valid."

## Change Tier Classification

| Tier | Risk Level | Example | Approval Required |
|---|---|---|---|
| **Tier 1** | Begin automatically | Read-only discovery, drafts, docs, audits, queue design | None |
| **Tier 2** | Reversible implementation | Branch-based code changes, local scripts, PR-ready implementations | None (but must pass gate) |
| **Tier 3** | Prepare, verify, then request Richie approval | Production deployments, secret rotation, customer communications, financial actions, destructive changes, public messaging, pricing/strategy changes | **Richie's explicit approval required** |

## Self-Validation Loop (run BEFORE requesting review)

Walk through every phase of multi-phase workflows end-to-end. For each phase:

- **Full execution flow traced** — if a script has `--verify`, mentally execute phase 2 and confirm argparse, state, and file paths all work.
- **Docstring/contract match** — re-read the module docstring after every change. If it says "any error counts as offline", catch all exceptions. If it says "pure local", don't make network calls by default.
- **AGENTS.md compliance** — grep AGENTS.md for the relevant constraint before any change. Branch prefixes, source-of-truth rules, and approved facts are enforced by code review.
- **Conflict documented** — when two requirements conflict (e.g. CodeQL vs test isolation), document the tradeoff explicitly rather than silently breaking one side.

## Change Documentation Requirements

For every PR, the body must include:

- **What changed** — concise summary (one sentence)
- **What was NOT changed** — items that were considered but deliberately excluded
- **Verification commands run** — `build.py` output, `validate_project_state.py` output, `git diff --check` result
- **Known gaps** — items that require owner input (these are not blocking but must be documented)
- **Branch relationship** — this PR depends on/conflicts with which other PRs/branches

## Tiered Execution Enforcement

- **Tier 1** — begin automatically: read-only discovery, audits, docs, drafts, queue design, test plans, local verification.
- **Tier 2** — begin after scope verification: reversible implementation, branch-based code changes, local scripts, PR-ready implementations.
- **Tier 3** — prepare, verify, then request Richie approval before executing: production deployments, secret rotation, customer communications, financial actions, destructive changes, public messaging, pricing or strategy changes.

## Approved Business Facts (never contradict)

- Public brand: Preparation Station.
- Legal operator: Nationwide Acquisitions, LLC.
- Approved public disclosure: "Preparation Station is operated by Nationwide Acquisitions, LLC."
- Temporary support email: `mmminvestment25@gmail.com`.
- Complete requests are acknowledged within one business day.
- Nationwide Acquisitions, LLC is an approved TEFA Marketplace vendor based on the owner-provided approval email. Public claims must name the approved legal entity and state that each offering is reviewed separately in Odyssey.
- PDSES/ClassWallet status is unknown and must not be advertised as approved.
- The Vulturian is a confirmed title; its author credit, ISBN, price, format, description, cover, and printing/fulfillment source remain pending.

## Code Review Rules (enforced by reviewer)

- Block unsupported approval, price, inventory, shipping, fulfillment, legal, or launch-readiness claims.
- Block changes that mix retail checkout with TEFA/PDSES quote or invoice flows.
- Block direct edits to generated HTML when the corresponding source file was not updated.
- Block secrets, private notes, or sensitive customer data in tracked files.
- Require `tools/validate_project_state.py` and `build.py` to pass.

## EOD Huddle Ledger

Every agent session must classify its work by tier and L4 risk and record it in the EOD Huddle ledger (`obsidian-vault/00-HQ/EOD-Huddle/`) so nothing disappears.
