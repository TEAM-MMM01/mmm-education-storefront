#!/usr/bin/env bash
# dashboard-status.sh — Quick Preparation Station system status
# Reads config/project-state.json and Git refs; outputs a one-line status.

set -euo pipefail

# Resolve the repository root from this script's own location so the tool is
# portable across clones, CI workspaces, and directory layouts.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
REPO="$(cd -- "$SCRIPT_DIR/.." >/dev/null 2>&1 && pwd)"
STATE="$REPO/config/project-state.json"
RELEASE="$REPO/config/pages-release.json"

if [[ ! -f "$STATE" ]]; then
  echo "❌ config/project-state.json not found"
  exit 1
fi

BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMIT=$(git -C "$REPO" log -1 --oneline 2>/dev/null || echo "unknown")
BUILD=$(python3 "$REPO/build.py" 2>&1 | tail -1 || echo "build error")

# Derive launch status from canonical release configuration rather than
# grepping page copy: deployment_enabled plus at least one verified release SKU.
LAUNCH_STATUS=$(python3 -c "
import json
try:
    d = json.load(open('$RELEASE'))
    if d.get('deployment_enabled') and d.get('release_skus'):
        print('launch-ready')
    else:
        print('blocked')
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")

# Derive key facts from state
TEFA_APPROVAL=$(python3 -c "
import json; d=json.load(open('$STATE')); print(d['programs']['tefa']['approval_status'])
" 2>/dev/null || echo "unknown")

echo "=== Preparation Station System Status ==="
echo "Branch:  $BRANCH"
echo "Commit:  $COMMIT"
echo "Build:   $BUILD"
echo "Launch:  $LAUNCH_STATUS"
echo "TEFA:    $TEFA_APPROVAL"
echo "----------------------------------------"
echo "Open PRs:"
gh pr list --state open --jq '.[] | "  ## " + .number + ": " + .title' 2>/dev/null || echo "  (gh pr list unavailable)"
echo "----------------------------------------"
echo "Widgets: docs/omniroute/DASHBOARD_WIDGETS.md"