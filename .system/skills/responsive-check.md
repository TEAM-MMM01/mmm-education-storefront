# Responsive Check Skill

## Description
Validates that all new grids and layouts collapse appropriately at mobile breakpoints (760px) per the design-system responsive rules.

## Checklist
- [ ] All .grid, .card-grid, .resource-grid, .lane-grid, .trust-strip, .vendor-grid, .site-footer__grid collapse to 1-column at 760px
- [ ] .site-header__inner transforms to 1-column layout
- [ ] .header-actions transforms to full-width with flex-start justification
- [ ] .hero__grid, .cta-band, .vendor-grid transform to 1-column
- [ ] .card-grid, .resource-grid transform to 2-column then 1-column
- [ ] .timeline-card transforms to 1-column with start-justified CTA
- [ ] .timeline-card__cta transforms to start-justified

## Usage
```yaml
- name: Responsive Check
  uses: .system/skills/responsive-check.md
