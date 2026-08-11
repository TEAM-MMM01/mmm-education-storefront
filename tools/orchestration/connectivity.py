#!/usr/bin/env python3
"""Mac-side connectivity tracker for HermesOS Control Plane.

Reports `online | degraded | offline` for each dependency the Mac cares
about. Pure local. Probes are conservative: any error counts as offline.
No state changes are made on the probed systems.

Probed systems (configurable):
- ollama: `ollama list` (local model inventory reachable)
- keychain: macOS Keychain reachable via `security` CLI
- hermes_gateway: localhost probe for the running hermes-cli gateway
- github: `gh api /repos/TEAM-MMM01/mmm-education-storefront` (HEAD check)
  NOTE: GitHub probe is OPT-IN only (--probe github) since it requires
  network access, contradicting the "pure local" contract.

Output is JSON to stdout; readable summary to stderr.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone


# Default probes are local-only. GitHub requires network, so it is opt-in.
LOCAL_PROBES = ("ollama", "keychain", "hermes_gateway")
ALL_PROBES = ("ollama", "keychain", "hermes_gateway", "github")


def _safe_run(cmd: list[str], timeout: int = 5) -> subprocess.CompletedProcess:
    """Run a subprocess, converting timeouts and OS errors to offline results."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr=f"command timed out after {timeout}s"
        )
    except OSError as exc:
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr=str(exc)
        )


def probe_ollama() -> dict:
    if not shutil.which("ollama"):
        return {"state": "offline", "reason": "ollama CLI not installed"}
    result = _safe_run(["ollama", "list"])
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    lines = [ln for ln in result.stdout.splitlines() if ln.strip() and not ln.startswith("NAME")]
    return {"state": "online", "model_count": len(lines)}


def probe_keychain() -> dict:
    if not shutil.which("security"):
        return {"state": "offline", "reason": "security CLI not present (non-macOS?)"}
    result = _safe_run(["security", "list-keychains"])
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    return {"state": "online", "keychains": len(result.stdout.splitlines())}


def probe_hermes_gateway() -> dict:
    # HermesOS CLI does not expose HTTP by default; we just confirm the CLI
    # is on PATH. The presence of the running process is the user's own
    # `ps` evidence; we don't touch it.
    if shutil.which("hermes"):
        return {"state": "degraded", "reason": "hermes CLI on PATH; runtime status unknown (not probed)"}
    return {"state": "offline", "reason": "hermes CLI not on PATH"}


def probe_github() -> dict:
    if not shutil.which("gh"):
        return {"state": "offline", "reason": "gh CLI not installed"}
    result = _safe_run(
        ["gh", "api", "repos/TEAM-MMM01/mmm-education-storefront", "--jq", ".default_branch"]
    )
    if result.returncode != 0:
        return {"state": "offline", "reason": (result.stderr or result.stdout).strip()[:200]}
    return {"state": "online", "default_branch": result.stdout.strip()}


PROBE_FUNCS = {
    "ollama": probe_ollama,
    "keychain": probe_keychain,
    "hermes_gateway": probe_hermes_gateway,
    "github": probe_github,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mac connectivity tracker")
    parser.add_argument("--only", choices=ALL_PROBES, help="Probe only this system")
    parser.add_argument("--probe", action="append", choices=ALL_PROBES,
                        help="Add a probe (repeatable). Default: local-only probes.")
    parser.add_argument("--quiet", action="store_true", help="Suppress human summary")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.only:
        targets = [args.only]
    else:
        targets = list(LOCAL_PROBES)
        if args.probe:
            targets.extend(p for p in args.probe if p not in targets)
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
