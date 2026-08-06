# OmniRoute Integration Plan

OmniRoute is not connected to this repository yet. This folder defines the intended
contract so the dashboard and routing layer can be wired in without changing the storefront
workflow later.

## Purpose

OmniRoute should route work to the best available model, agent, or system based on task
type, risk, required context, and acceptance criteria.

## Initial routing targets

- Code agent: source changes, builds, generated-file checks, PR preparation.
- Documentation agent: README, launch audit, SOPs, product docs, Obsidian-safe templates.
- Audit agent: placeholder scans, ESA/General Store boundary checks, launch-readiness checks.
- Research agent: current external facts when explicitly requested and sourced.
- Dashboard agent: status cards, blocker summaries, PR/build/deployment signals.

## Current status

- GitHub repository workflow: planned in repo documentation.
- Obsidian vault workflow: planned in repo documentation.
- OmniRoute API or event bus: not provided yet.
- Dashboard implementation: not connected yet.

## Next requirement

To wire this for real, provide one of these implementation targets:

- OmniRoute GitHub repository name.
- Dashboard GitHub repository name.
- OmniRoute API endpoint and authentication method.
- Existing event schema.
- A README or design note explaining OmniRoute's current architecture.

Until one of those exists, model routing remains manual and these files are the planned
contract rather than an active integration.
