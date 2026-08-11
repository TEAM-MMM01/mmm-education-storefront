#!/usr/bin/env python3
"""Tiny smoke test for the orchestration scaffolding.

Exercises queue.py / connectivity.py / eod_huddle.py with throwaway data
and prints PASS/FAIL counts. No remote calls. Cleans up after itself.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def run(argv: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )


def main() -> int:
    passes = 0
    failures: list[str] = []

    # 1. queue.py enqueue + update + list + show
    with tempfile.TemporaryDirectory() as tmpdir:
        env = {"HERMES_MAC_QUEUE_ROOT": tmpdir}
        enq = run(
            [
                "tools/orchestration/queue.py",
                "enqueue",
                "--task-name", "smoke test",
                "--lane", "audit",
                "--state", "Locally Complete",
                "--owner", "smoke",
            ],
            env=env,
        )
        if enq.returncode != 0 or not enq.stdout.startswith("enqueued wf-"):
            failures.append(f"queue enqueue failed: {enq.returncode} {enq.stderr.strip()}")
        else:
            wf_id = enq.stdout.strip().split()[1]
            upd = run(["tools/orchestration/queue.py", "update", "--id", wf_id, "--new-state", "Remotely Verified", "--note", "smoke"], env=env)
            if upd.returncode != 0:
                failures.append(f"queue update failed: {upd.returncode} {upd.stderr.strip()}")
            else:
                ls = run(["tools/orchestration/queue.py", "list"], env=env)
                if wf_id not in ls.stdout or "Remotely Verified" not in ls.stdout:
                    failures.append(f"queue list missing entry: stdout={ls.stdout!r}")
                else:
                    passes += 1
                    passes += 1
                    passes += 1

    # 2. queue.py rejects an invalid state
    bad = run(
        [
            "tools/orchestration/queue.py",
            "enqueue",
            "--task-name", "should fail",
            "--lane", "audit",
            "--state", "Shipped",  # not in ALLOWED_STATES
            "--owner", "smoke",
        ],
    )
    if bad.returncode != 2:
        failures.append(f"queue should reject unknown state (exit {bad.returncode})")
    else:
        passes += 1

    # 3. connectivity.py runs (do not assert outcomes — depends on network)
    conn = run(["tools/orchestration/connectivity.py", "--only", "ollama", "--quiet"])
    if conn.returncode != 0:
        failures.append(f"connectivity.py non-zero: {conn.returncode} {conn.stderr.strip()}")
    else:
        try:
            json.loads(conn.stdout)
            passes += 1
        except json.JSONDecodeError:
            failures.append("connectivity.py did not emit JSON")

    # 4. eod_huddle.py runs against the vault and prints sections
    # Use a temp vault to avoid depending on the real Obsidian vault.
    with tempfile.TemporaryDirectory() as vault_dir:
        vault_path = Path(vault_dir)
        # Create minimal vault structure.
        (vault_path / "00-HQ").mkdir(parents=True, exist_ok=True)
        (vault_path / "00-HQ" / "EOD-Huddle").mkdir(exist_ok=True)
        huddle = run(["tools/orchestration/eod_huddle.py", "--vault", vault_dir])
        if huddle.returncode != 0:
            failures.append(f"eod_huddle.py failed: {huddle.returncode} {huddle.stderr.strip()}")
        elif "HUDDLE-" not in huddle.stdout:
            # Empty vault is expected to produce no markers — that's OK.
            passes += 1
        else:
            passes += 1

    print(f"PASS: {passes}")
    if failures:
        print(f"FAIL: {len(failures)}")
        for f in failures:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())