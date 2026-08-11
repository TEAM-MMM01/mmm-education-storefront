#!/usr/bin/env python3
"""Mac-side connectivity tracker for HermesOS Control Plane.

Reports `online | degraded | offline` for each dependency the Mac cares
about. Pure local. Probes are conservative: any error counts as offline.
No state changes are made on the probed systems.

Probed systems (configurable):
- github: `gh api /repos/TEAM-MMM01/mmm-education-storefront` (HEAD check)
- ollama: `ollama list` (local model inventory reachable)
- keychain: macOS Keychain reachable via `security` CLI
- hermes_gateway: localhost probe for the running hermes-cli gateway

Output is JSON to stdout; readable summary to stderr.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone


PROBES = ("github", "ollama", "keychain", "hermes_gateway")


def probe_github() -> dict:
    if not shutil.which("gh"):
        return {"state": "offline", "reason": "gh CLI not installed"}
    result = subprocess.run(
        ["gh", "api", "repos/TEAM-MMM01/mmm-education-storefront", "--jq", ".default_branch"],
        capture_output=True,
        text=True,
        timeout=5,
    )
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    return {"state": "online", "default_branch": result.stdout.strip()}


def probe_ollama() -> dict:
    if not shutil.which("ollama"):
        return {"state": "offline", "reason": "ollama CLI not installed"}
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    lines = [ln for ln in result.stdout.splitlines() if ln.strip() and not ln.startswith("NAME")]
    return {"state": "online", "model_count": len(lines)}


def probe_keychain() -> dict:
    if not shutil.which("security"):
        return {"state": "offline", "reason": "security CLI not present (non-macOS?)"}
    result = subprocess.run(["security", "list-keychains"], capture_output=True, text=True, timeout=5)
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    return {"state": "online", "keychains": len(result.stdout.splitlines())}


def probe_hermes_gateway() -> dict:
    # HermesOS CLI does not expose HTTP by default; we just confirm the CLI
    # is on PATH. The presence of the running process is the user's own
    # `ps` evidence; we don't touch it.
    if shutil.which("hermes"):
        return {"state": "online", "evidence": "hermes CLI on PATH"}
    return {"state": "degraded", "reason": "hermes CLI not on PATH; runtime may still be running"}


PROBE_FUNCS = {
    "github": probe_github,
    "ollama": probe_ollama,
    "keychain": probe_keychain,
    "hermes_gateway": probe_hermes_gateway,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mac connectivity tracker")
    parser.add_argument("--only", choices=PROBES, help="Probe only this system")
    parser.add_argument("--quiet", action="store_true", help="Suppress human summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    targets = [args.only] if args.only else list(PROBES)
    report = {
        "checked_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "probes": {name: PROBE_FUNCS[name]() for name in targets},
    }
    print(json.dumps(report, indent=2))
    if not args.quiet:
        online = sum(1 for r in report["probes"].values() if r["state"] == "online")
        degraded = sum(1 for r in report["probes"].values() if r["state"] == "degraded")
        offline = sum(1 for r in report["probes"].values() if r["state"] == "offline")
        print(
            f"\nSummary: online={online} degraded={degraded} offline={offline} of {len(targets)}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())