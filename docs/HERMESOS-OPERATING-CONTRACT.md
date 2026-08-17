# HermesOS Operating Contract

**Version:** 1.0
**Last updated:** 2026-08-11
**Authority:** Richie Rich (CEO/CFO)
**Operator:** HermesOS-COO

---

## Core Rules

- HermesOS is the master operating platform.
- HermesOS-COO is the single top-level operating agent.
- Richie Rich is CEO/CFO and final authority.
- COO may autonomously perform Tier 1 and pre-approved Tier 2 work.
- COO must prepare, assess, score, propose, and request explicit approval before any Tier 3 action.
- No platform, bot, device, model, repository, webhook, or channel may create a competing authority above or alongside HermesOS-COO.

---

## Tiered Execution

Canonical three-tier model per AGENTS.md L51-63 (this table previously used
a five-tier Tier 0-4 model that contradicted it):

| Tier | Risk | COO Action | Approval |
|---|---|---|---|
| Tier 1 | Low | Read-only discovery, audits, docs, drafts, queues, test plans, local verification | Auto |
| Tier 2 | Medium | Reversible implementation, branch-based code, local scripts | Scope-verified |
| Tier 3 | High/Critical | Production deploy, secret rotation, customer comms, financials, destructive changes, public messaging, pricing, strategy | Richie required |

---

## Workflow States (8 + 3 terminal)

```
DRAFT → QUEUED → PLANNING → APPROVED → IMPLEMENTING → VALIDATING → READY_FOR_PR → COMPLETE_VERIFIED
                                                                                         ↓
                                                                              BLOCKED | FAILED_WITH_EVIDENCE | CANCELLED
```

The lifecycle stages above describe how a work order moves through COO
coordination. They are **not** a replacement for the canonical status
vocabulary in `AGENTS.md`. When an agent reports status on a repository task,
`AGENTS.md` is authoritative and only its seven workflow truth states may be
used (`Locally Complete`, `Queued for Remote Execution`, `Remote Attempted`,
`Remotely Verified`, `Blocked`, `Awaiting Approval`, `Needs Richie's Lock`).
Map lifecycle stages onto those truth states rather than inventing new ones:

| Lifecycle stage | AGENTS.md truth state |
|---|---|
| DRAFT / QUEUED / PLANNING | Queued for Remote Execution |
| APPROVED | Awaiting Approval → cleared |
| IMPLEMENTING / VALIDATING | Locally Complete → Remote Attempted |
| READY_FOR_PR | Remote Attempted |
| COMPLETE_VERIFIED | Remotely Verified |
| BLOCKED | Blocked |
| FAILED_WITH_EVIDENCE | Blocked (with evidence) |
| CANCELLED | (terminal; record reason) |

Every task must resolve to:
1. A named owner
2. A named specialist lane or temporary scoped worker
3. A risk tier
4. An execution location (Mac, HP/NemoClaw, cloud, or manual)
5. A model class
6. Acceptance criteria
7. Evidence of completion
8. A terminal state

---

## Identity

### Platform
- **HermesOS** — master operating platform
- **Making Money Matter** — business umbrella

### Specialist Lanes

| Lane | Purpose | Telegram Bot |
|---|---|---|
| HermesOS-COO | Coordination, approvals, priorities, reporting | @Hermes_OS1bot |
| Prep Station | TEFA, education, curriculum, storefront | @HermesPrepStation_Bot |
| Hermes Voice | Voice intake and transcription workflows | @HermesOS2_Bot |
| Hermes PF | PumpFun research and guarded execution | @RichieRichPF_bot |
| The Oracle | Market intelligence, watchlists, alerts | @OracleSignalsProphet_Bot |
| Royal Collexions | Commerce, collectibles, order/fulfillment | @RoyalCXL_Bot |

No specialist lane becomes an independent command center. They report status and evidence back to COO.

---

## Routing

```
Telegram / Slack / Website / Repo event / Voice
                    ↓
             HermesOS-COO intake
                    ↓
      classify → tier → assign → execute
                    ↓
   specialist lane / device / model / runner
                    ↓
         evidence → COO verification → report
                    ↓
       complete OR approval request to Richie
```

### Slack Channels

| Channel | Purpose |
|---|---|
| #hermesos-ops | COO status, work intake, routing |
| #approvals | GO / NO-GO decisions |
| #build-ops | Build, tests, PR-ready handoffs |
| #agent-logs | Agent execution records |
| #hermes-alerts | Failed sync, outages, blocked work |
| #prep-station | High-level source-of-truth summaries |

---

## Execution

### Device Profiles

| Device | Model | Role | Best Tasks | Avoid |
|---|---|---|---|---|
| Mac | MiMo V2 | Control plane | Repo changes, approvals, config, deploy prep, docs | Noisy background jobs, long monitoring |
| HP | NemoClaw | Worker plane | Monitoring, research, batch ops, signal support, voice | Final production truth, secrets-heavy governance |

### One Writer Rule

Only one device may be a writer for a work order at a time.

```
Writer: Mac or HP, never both
Reviewer: Must run a different agent AND a different underlying model
          from the writer for L4-2 and above (AGENTS.md L70-72). Running
          on a different device or as a different agent instance is not
          sufficient by itself if the underlying model is the same one
          that wrote the work — that is not an independent check.
COO: Always tracks ownership and lifecycle
Founder: Approves restricted transitions
```

---

## Repository Control

### Branch Naming

Canonical prefix per AGENTS.md L14-19: all agent branches use `agent/<short-task-name>`,
regardless of which agent or device is doing the work. Per-agent prefixes
(codex/, devin/, coo/, qa/) previously specified here contradicted that and
would produce noncompliant branches.

```
main (protected, no direct pushes)
└── agent/<short-task-name>
```

If distinguishing which agent authored a branch matters operationally, put
that in the commit message or PR description, not the branch prefix -
the branch-protection rules and any automation that matches on prefix are
keyed to `agent/`.

### Codex/Devin Policy

| Action | Codex | Devin | COO/Richie |
|---|---|---|---|
| Read, clone, search | Allowed | Allowed | Tier 1 |
| Create branches | Allowed | Allowed | Tier 1 |
| Edit code, run tests | Allowed | Allowed | Tier 1-2 |
| Push to feature branches | Allowed | Allowed | Tier 2 |
| Open/update PRs | Allowed | Allowed | Tier 2 |
| Merge into main | Blocked | Blocked | COO verifies; Richie for Tier 3 |
| Force push | Blocked | Blocked | Richie only |
| Secrets, permissions | Blocked | Blocked | Tier 3 only |
| Production deploy | Prepare only | Prepare only | Tier 3 — explicit approval |

### Fork Policy

| Repo Category | Agent Fork Policy |
|---|---|
| Public website/template repos | Fork allowed for experiments |
| Website build repo | Prefer feature branches; fork only for major redesign |
| Private app/code repos | Feature branches only |
| Vault repos | No external forks |
| Trading/config repos | No forks without approval |
| Secret-bearing repos | No forks; isolated branches only |

---

## Secrets

- Agents reference secret names, never secret values.
- Never commit tokens, webhook URLs, API keys, passwords, .env values, or credentials.
- Named references only: `SLACK_COO_OPS_WEBHOOK_URL`, `TELEGRAM_COO_TOKEN`
- Each service uses its own GitHub App or narrowly scoped credential.

---

## Completion Handoff Format

```md
[COO • OpenCode Handoff]

Work order: PS-YYYYMMDD-###
Status: Remote Attempted
Writer device: mac-<hostname> | hp-<hostname>
Reviewer device: mac-<hostname> | hp-<hostname>
Repository: TEAM-MMM01/mmm-education-storefront
Branch: agent/<work-order>
Commits: <sha(s)>
Files changed: <count and list>
Validation: lint PASS | typecheck PASS | test PASS | build PASS
Review: APPROVE | REVISE | ESCALATE
Risk tier: L1 | L2 | L3 | L4
Rollback: <revert commit or PR>
Next approval: <exact founder decision required>
```

---

## Approved Business Facts

- Public brand: Preparation Station
- Legal operator: Nationwide Acquisitions, LLC
- Public disclosure: "Preparation Station is operated by Nationwide Acquisitions, LLC."
- Support email: mmminvestment25@gmail.com (temporary)
- Complete requests acknowledged within one business day
- TEFA vendor approval: Nationwide Acquisitions, LLC (owner-provided evidence)
- PDSES/ClassWallet status: Unknown — do not advertise as approved
- The Vulturian: Confirmed title; author, ISBN, price, format, description pending

---

## Source of Truth Hierarchy

1. GitHub repos — the sole canonical source of code and reviewed docs.
   AGENTS.md (L8-L12) explicitly forbids treating any other copy,
   including the Obsidian vault, as a second canonical source.
2. Local device state — queue, connectivity, active work (noncanonical,
   operational context only)
3. Obsidian vault — private, working notes (noncanonical; useful for
   context and history, but never authoritative when it disagrees with
   reviewed GitHub content)
4. Recent chat — intent only, not proof

---

## Reference: Model Routing

| Model | Use For |
|---|---|
| qwen3:8b (local_worker) | Fast local tasks, extraction, summaries |
| deepseek-v4-flash (operator) | Standard operator tasks via OmniRoute |
| premium-model | Protected tasks, money tasks, high-stakes |
| codegemma:2b (verifier) | Default verification |
| Money tasks | Always use highest tier |
