#!/usr/bin/env bash
# dashboard-status.sh — Quick Preparation Station system status
# Reads config/project-state.json and Git refs; outputs a one-line status.

set -euo pipefail

REPO="/Users/queent./Projects/TEAM-MMM01/mmm-education-storefront"
STATE="$REPO/config/project-state.json"

if [[ ! -f "$STATE" ]]; then
  echo "❌ config/project-state.json not found"
  exit 1
fi

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
COMMIT=$(git log -1 --oneline 2>/dev/null || echo "unknown")
BUILD=$(python3 "$REPO/build.py" 2>&1 | tail -1 || echo "build error")

# Derive launch status
if grep -q "ESA Launch Command" "$REPO/src/page.html" 2>/dev/null; then
  LAUNCH_STATUS="ESA-integrated"
else
  LAUNCH_STATUS="pre-ESA"
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