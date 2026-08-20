# Motion Compliance Skill

## Description
Validates that all animation follows MOTION_SYSTEM.md: transform/opacity only, 160/220/320/520ms tokens, reveals gated behind `<html class="js">`, no animation-based reveals, no animation of pricing/approval status/purchase instructions.

## Checklist
- [ ] No `animation` property used (only `transition`)
- [ ] Only `transform` and `opacity` properties are animated
- [ ] Faster controls: 160ms (`--dur-fast`), 220ms (`--dur-ui`)
- [ ] Slower controls: 220ms (`--dur-base`), 320ms (`--dur-panel`), 520ms (`--dur-section`)
- [ ] Reveals gated behind `<html class="js">` (content visible without JS)
- [ ] No layout animating properties (margin, padding, width, height, float, position)
- [ ] No animation of pricing, approval status, or purchase instructions
- [ ] `prefers-reduced-motion: reduce` honored (animations disabled)
- [ ] `.reveal`/`.stagger` elements get `opacity:1; transform:none` when reduced motion

## Usage
```yaml
- name: Motion Compliance
  uses: .system/skills/motion-compliance.md
