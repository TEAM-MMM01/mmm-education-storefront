#!/usr/bin/env bash
# Single entry point for the baby-agent harness.
#
# Usage:
#   bash tools/agent_loop/run.sh <task-name>
#   bash tools/agent_loop/run.sh --verify <task-name>
#
# Without --verify, the harness creates a fresh agent/<task> branch off
# current main, prints the spec, and exits so the parent can apply edits.
# Re-invoke with --verify to run the guard + validator + build, push the
# branch, and open a draft PR.
#
# Per AGENTS.md, this script never pushes to main, never force-pushes,
# never enables auto-merge, and never merges a PR.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${REPO_ROOT}"

if [[ $# -lt 1 ]]; then
  printf 'Usage: %s [--verify] <task-name>\n' "$0" >&2
  exit 2
fi

ARGS=()
if [[ "${1:-}" == "--verify" ]]; then
  ARGS+=("--verify")
  shift
fi

TASK_NAME="${1:-}"
if [[ -z "${TASK_NAME}" ]]; then
  printf 'Usage: %s [--verify] <task-name>\n' "$0" >&2
  exit 2
fi

ARGS+=("${TASK_NAME}")

exec python3 "${REPO_ROOT}/tools/agent_loop/baby_agent.py" "${ARGS[@]}"