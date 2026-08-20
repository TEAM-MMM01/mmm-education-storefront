# Code Review Skill

## Description
Automated code review for Preparation Station repository. Checks for:
- Badge taxonomy compliance (5-status system)
- No raw email displays
- PDSES/ClassWallet separation from TEFA
- Vulturian framing per AGENTS.md
- Responsive design compliance
- Motion system compliance
- No speculative pricing/claims

## Usage
```yaml
- name: Code Review
  uses: .system/skills/code-review.md
  # or as a prompt: "Run the code-review skill on these changes..."
```

## Review Checklist
- [ ] All badge classes use the 5-status taxonomy
- [ ] No raw email addresses visible (only "Get in touch" CTAs)
- [ ] PDSES/ClassWallet not advertised as TEFA-approved
- [ ] Vulturian has "Confirmed title; details pending" framing
- [ ] No speculative pricing or unverified product claims
- [ ] Responsive: new grids collapse to 1-column at 760px
- [ ] Motion follows MOTION_SYSTEM.md tokens
- [ ] No placeholder imagery without licensed asset plan
