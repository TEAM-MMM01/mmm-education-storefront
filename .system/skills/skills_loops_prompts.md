# Skills Prompts and Loops Collection

This file contains reusable prompts and loop structures for agent performance optimization.

## 0. Primary Objective — Compliance-Gated Profitability

Every skill, prompt, and loop in this file optimizes for revenue **subject to** the
launch gates. Profit is the goal; the gates are what keep this vendor eligible to
earn at all. A change that raises revenue by breaking a gate (publishing an
unverified price, marking an SKU available before offering review, claiming
launch-readiness) causes marketplace removal — that is negative ROI, not a win.

```
PROFITABILITY_OBJECTIVE:
- Rank candidate actions by revenue-per-effort, BUT only among actions that also:
  [ ] pass python3 tools/validate_project_state.py
  [ ] pass the release-artifact build/boundary checks (build_pages_release.py)
  [ ] keep config/pages-release.json truthful (no price/SKU claim without a
      verified catalog record; deployment_enabled reflects reality)
- NEVER publish a price without a verified catalog record.
- NEVER mark an SKU/offering "available" before its Odyssey offering review completes.
- NEVER claim launch-readiness while deployment_enabled:false or release_skus is empty.
- Prefer high-margin, low-overhead revenue first (see REVENUE_PRIORITIES).
```

```
REVENUE_PRIORITIES (highest expected value first):
1. Verify + allowlist at least ONE SKU — flips the storefront from $0 to
   transactable (config/pages-release.json release_skus + deployment_enabled).
2. Ship the digital curriculum lanes (one-time family license, ~zero marginal
   cost) ahead of physical kits that carry shipping/fulfillment overhead.
3. Convert the free-worksheet + Mission Guide starter-list funnel into written
   pathway confirmations that end in a verified Odyssey purchase.
4. Pursue institutional / bulk (school & district) site-license inquiries —
   typically the largest curriculum contracts.
5. Grow the separate non-TEFA General Store retail path, where direct checkout
   and margin can run without ESA compliance gates.
```

## 1. Pre-Flight Prompt (run at session start)

```
ACTIVE_AGENT_SKILL_CHECKLIST:
[ ] Read AGENTS.md - tiered execution rules, approved facts, safety/privacy
[ ] Read config/project-state.json - current business state, legal disclosures
[ ] Check git status - no unexpected modifications; branch is agent/<short-task-name>
[ ] Run git diff --check - zero whitespace errors/conflict markers
[ ] Run python3 tools/validate_project_state.py - must pass ("Project state, catalogs, request intake, and order portal are valid.")
[ ] Run python3 build.py - all pages rebuild successfully
[ ] ONLY THEN proceed with task
```

## 2. Post-Action Prompt (run after any code change)

```
POST_ACTION_CHECKLIST:
[ ] Run git diff --check - whitespace/conflict markers clean
[ ] Run python3 tools/validate_project_state.py - valid
[ ] Run python3 build.py - all 16 pages rebuild
[ ] Update changelog/docs if behavior/claims changed
[ ] Push branch + open PR if not already done
[ ] Add entry to .system/updates/updates_log.md
```

## 3. Weekly Performance Review Loop (run weekly, typically Monday)

```
WEEKLY_PERFORMANCE_AUDIT:
1. Build time audit: time python3 build.py 2>&1 | tail -1
2. Validation coverage: count pages passing validate_project_state.py
3. Git diff stats: git diff --stat main..agent/esa-catalog-presentation | tail -5
4. Open PRs count: gh pr list --state open | wc -l
5. Agent session quality: self-assessment (1-5 scale)
6. Recommendations: 
   - Any new skills to add to .system/skills/?
   - Any deprecated skills to remove?
   - Any pipeline optimizations?
   - Any license compliance updates?
```

## 4. Agent Skill Prompts Library

### Skill: Code Review
```
PROMPT: "Run code-review skill on these changes: [diff]. Check for: badge taxonomy compliance, no raw emails, PDSES/ClassWallet separation, Vulturian framing, responsive design, motion system compliance, no speculative pricing/claims."
```

### Skill: Responsive Check
```
PROMPT: "Run responsive-check skill on these changes: [file]. Verify: all grids collapse to 1-column at 760px, header/footer transforms correctly, all new grids follow design-system breakpoints."
```

### Skill: Motion Compliance
```
PROMPT: "Run motion-compliance skill on these changes: [file]. Verify: only transform/opacity animation, 160/220/320/520ms tokens, reveals gated behind html.js, no layout animating properties, prefers-reduced-motion honored."
```

### Skill: License Compliance
```
PROMPT: "Run license-compliance skill on these changes: [file]. Verify: no new proprietary claims, no unverified pricing, no eligibility claims without evidence, proper PDSES/TEFA separation."
```

## 5. Skill Discovery Loop (run monthly)

```
SKILL_DISCOVERY_LOOP:
1. gh repo search "education catalog" --limit 10
2. gh repo search "TEFA vendor" --limit 10
3. web search "Preparation Station products" -- top 5 results
4. gh repo search "agent skill" --limit 10
5. Review .system/skills/ for unused skills (remove if not used in 90 days)
6. Add newly discovered skills to .system/skills/
7. Update skills_inventory.md with new entries
8. Run pre-flight checklist before adding any new skill
```

## 6. Skill Installation Template

```
To install a new skill:
1. gh repo clone REPO_URL /tmp/skill-repo
2. Review /tmp/skill-repo/SKILL.md for instructions
3. Review /tmp/skill-repo/README.md for usage patterns
4. Adapt patterns to repo conventions (branch prefixes, validation gates)
5. Move skill to .system/skills/skill-name.md
6. Add entry to skills_inventory.md
7. Test on a non-critical file first
8. Run pre-flight checklist before production use
```

## 7. Performance Metrics Tracker

```
MONTHLY_PERFORMANCE_METRICS:
- Build time: _____ seconds (target: < 5s)
- Validation pass rate: _____ % (target: 100%)
- Open PRs: _____ (target: < 5)
- Agent session time to first commit: _____ minutes (target: < 10)
- Bug escape rate: _____ per quarter (target: 0)
- Skills added: _____ (target: periodic additions)
- Skills retired: _____ (target: periodic cleanup)
```

## 8. Revenue Metrics Tracker

Ties the profitability objective (Section 0) to numbers. Compliance is a hard
gate: any month with a gate breach counts as $0 progress regardless of revenue.

```
MONTHLY_REVENUE_METRICS:
- Verified + allowlisted SKUs: _____ (target: >= 1; unblocks all storefront revenue)
- deployment_enabled: true / false (target: true only when >= 1 verified SKU exists)
- Curriculum lanes past offering review: _____ / 4 (target: increasing)
- Starter-list requests received: _____ (funnel top; from Mission Guide handoff)
- Written pathway confirmations sent: _____ (funnel mid)
- Verified Odyssey purchases: _____ (funnel bottom = realized revenue)
- Institutional / bulk inquiries: _____ (target: pursue every one)
- Compliance gate breaches: _____ (target: 0 — any breach voids the month)
```
