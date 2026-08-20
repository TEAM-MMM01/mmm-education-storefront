#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
STATE="$REPO/config/project-state.json"
RELEASE="$REPO/config/pages-release.json"

if [[ ! -f "$STATE" ]]; then
  echo "❌ config/project-state.json not found"
  exit 1
fi

BRANCH=$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMIT=$(git -C "$REPO" log -1 --oneline 2>/dev/null || echo "unknown")
BUILD=$(python3 "$REPO/build.py" 2>&1 | tail -1 || echo "build error")

if [[ -f "$RELEASE" ]]; then
  LAUNCH_STATUS=$(python3 -c "
import json
d = json.load(open('$RELEASE'))
print('deploy-enabled' if d.get('deployment_enabled') else 'blocked')
" 2>/dev/null || echo "unknown")
else
  LAUNCH_STATUS="unknown"
fi

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