# Agent Access and Update Control

## Current access model

The repository is currently public, so its tracked, non-sensitive contents can
be read without granting an agent write access. Public visibility does not give
an agent permission to push, create branches, edit issues, or open pull
requests.

| System | Read status | Write status | Required setup |
| --- | --- | --- | --- |
| Codex | Connected for this repository | Verified through the connected GitHub app | Keep repository selected in Codex GitHub settings |
| Claude | Public read only until configured | Not verified | Install/configure Claude's GitHub integration for this repository |
| Devin | Public read only until configured | Not verified | Connect Devin's GitHub integration and select this repository |
| OmniRoute | Can route model requests | Not a GitHub writer | Do not give it a shared GitHub token; route only redacted task envelopes |
| Local Mac/HP | Available through each device's clone | Available through the owner's authenticated GitHub CLI | Use device-specific keychain authentication and pull requests |

## Required write policy

Every service must use its own attributable GitHub identity or GitHub App.
Never copy a personal access token into prompts, Obsidian, OmniRoute, source
files, or shared shell history.

All automated writers must:

1. Start from current `main`.
2. Use a unique `agent/<short-task-name>` branch.
3. Read `AGENTS.md` and canonical JSON state.
4. Run the validator and build.
5. Open a draft pull request.
6. Wait for owner approval before merge or deployment.

Agents must not reuse another agent's branch. If two agents need the same file,
sequence their pull requests or have the later agent rebase after the first PR
merges.

## Service setup gates

### Codex

Codex is connected and can work through a GitHub branch and pull request. Keep
`AGENTS.md` at the repository root so repository-specific rules apply to work
and reviews.

### Claude

Grant access only to this repository, not every repository in the account.
Contents, issues, and pull-request write access are sufficient for an agent that
works through branches and pull requests. Repository secrets, workflows, and
deployment permissions should remain disabled unless a specific reviewed
automation requires them.

### Devin

Connect the GitHub integration, select this repository, and complete its
repository environment setup. Keep direct pushes to `main` prohibited and have
Devin open pull requests from its own branches.

### OmniRoute

OmniRoute is a model gateway, not a source-control authority. It may receive the
redacted event shape in `docs/omniroute/EVENT_CONTRACTS.md`. GitHub webhooks,
tokens, repository write actions, and customer or Obsidian data remain outside
OmniRoute until a separate private HermesOS adapter is designed and reviewed.

## Access verification

For each new agent, verify access with a harmless documentation-only branch and
draft pull request. Do not test write access on `main`, change repository
visibility, enable deployment, or create a live product claim as an access test.
