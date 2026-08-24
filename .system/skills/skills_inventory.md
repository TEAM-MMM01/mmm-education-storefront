# Agent Skills Inventory — Preparation Station

This inventory catalogs all available agent skills, their status, and when they should be deployed.

## Core Repo Skills (built-in, always available)

| Skill | File | Tier | When to Use |
|---|---|---|---|
| Agent Execution Skill | `.system/skills/agent_execution_skill.md` | 1-3 | Every session — mandatory pre-flight |
| Design System Unifier | PR #38 (merged) | 2 | When unifying global header/footer/tokens across pages |
| ESA Framework Integrator | PR #41 (merged, work from PR #39 completed) | 2 | When transforming home page into TEFA-ready catalog |
| Storefront Validator | `tools/validate_project_state.py` | 1-3 | Before any PR; validates 16 pages |
| Build Pipeline | `build.py` | 1-3 | Every source change; inlines CSS + validates |

## External Skills (pull from GitHub as needed)

| Skill Repo | Description | Deploy Tier |
|---|---|---|
| `OpenHands/software-agent-sdk` | Modular SDK for building AI agents | 2-3 (as needed) |
| `anthropics/claude-agent-sdk-python` | Python SDK for Claude Code | 2-3 (as needed) |
| `TEAM-MMM01/hermes-agent` | Agent that grows with you | 2-3 (as needed) |
| `TEAM-MMM01/tandem-browser` | AI-Human symbiotic browser | 3 (needs owner setup) |

## Skill Loops & Prompts

### 1. Pre-Flight Loop (run at session start)
```
1. Read AGENTS.md (Tier rules, approved facts)
2. Read config/project-state.json (current business state)
3. Check git status (unexpected modifications?)
4. Run git diff --check (whitespace/conflict markers?)
5. Run python3 tools/validate_project_state.py (valid?)
6. ONLY THEN: proceed with task
```

### 2. Post-Action Loop (run after any code change)
```
1. Run git diff --check (whitespace/conflict markers?)
2. Run python3 tools/validate_project_state.py (valid?)
3. Run python3 build.py (all pages rebuild?)
4. Update changelog/docs if behavior/claims changed
5. Push branch + open PR (if not already done)
```

### 3. Weekly Performance Review Loop (run weekly)
```
1. Audit build times (python3 build.py timing)
2. Audit validation coverage (how many pages pass validate?)
3. Audit git diff stats (what changed since last week?)
4. Audit PR count (open PRs, age, blocker status)
5. Report to operator with recommendations
```

## Recent Skill Updates

| Date | Skill | Change | Impact |
|---|---|---|---|
| 2026-08-24 | Kanban Dashboard | Full server rebuild with all endpoints | All tools functional |
| 2026-08-24 | Skills Audit | All skills/prompts/loops reviewed and verified | No conflicts found |
| 2026-08-19 | Agent Execution Skill | Full rewrite with tiered enforcement | Reduced review round-trips |
| 2026-08-19 | ESA Integration PR #41 | Completed work from PR #39 | Catalog presentation live |
| 2026-08-19 | Dashboard Widgets | Updated with real-time state | Operational visibility |

## Skills to Pull from GitHub (priority order)

| Priority | Repo | What to Pull | Why |
|---|---|---|---|
| **High** | `OpenHands/software-agent-sdk` | Agent lifecycle patterns, self-validation loops | Standardize our skill format |
| **High** | `anthropics/claude-agent-sdk-python` | Code generation patterns, error handling | Improve code quality from Claude |
| **Medium** | `TEAM-MMM01/hermes-agent` | Growth-with-you agent patterns | Context-aware assistance |
| **Low** | `TEAM-MMM01/tandem-browser` | Web automation patterns | If browser automation needed |

## How to Pull a Skill

1. `gh repo clone REPO_URL /tmp/skill-repo`
2. Review `README.md` and `docs/` for usage patterns
3. Adapt patterns to repo conventions (branch prefixes, validation gates)
4. Document in `.system/skills/` for team reuse
5. Test on a non-critical file first

## Performance Metrics to Track

| Metric | Target | Current | Trend |
|---|---|---|---|
| Build time | < 5 seconds | ~0.08s | ⬆️ Improving |
| Validation pass rate | 100% | 100% | ➰ Stable |
| Open PRs | < 5 | 2 | ⬇️ Decreasing |
| Agent session time to first commit | < 10 minutes | varies | ⬆️ Depends on task |
| Bug escape rate | 0 per quarter | 0 | ➰ Stable |
