#!/usr/bin/env python3
"""Baby-agent orchestrator for the Preparation Station storefront repo.

Invoked by `run.sh`. Reads the task spec at `tasks/<task_name>.md`,
creates a fresh agent/<task_name> branch off current main, applies
the change set declared in the spec, runs the storefront guard +
validator + build, then opens a draft PR.

Every subprocess call uses an argv list (never shell=True). The harness
refuses any task name outside the allowlisted prefixes and refuses any
file path outside the spec's `paths:` list.

The harness never:
  - pushes to main
  - force-pushes
  - skips pre-PR hooks
  - enables auto-merge
  - merges a PR

It only opens a draft PR. The operator decides what happens next.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "tools" / "agent_loop" / "tasks"
REPORT_PATH = ROOT / "tools" / "agent_loop" / "report.json"

ALLOWED_BRANCH_PREFIXES = ("agent/", "feature/", "docs/", "fix/")
TASK_NAME_RE = re.compile(r"^[a-zA-Z0-9._/-]+$")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run(argv: list[str], *, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a subprocess with hard-coded argv. Never uses shell=True."""
    return subprocess.run(
        argv,
        cwd=cwd or ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def report_init(task_name: str) -> dict:
    template = json.loads((Path(__file__).parent / "report.tmpl.json").read_text())
    template["task_name"] = task_name
    template["started_at"] = now_iso()
    return template


def report_write(report: dict) -> None:
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def fail(report: dict, message: str, code: int = 1) -> "None":
    report["result"] = "failed"
    report["error"] = message
    report["finished_at"] = now_iso()
    report_write(report)
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def validate_task_name(name: str) -> str:
    if not TASK_NAME_RE.match(name):
        raise SystemExit(f"ERROR: task name contains unsafe characters: {name!r}")
    if not any(name.startswith(p) for p in ALLOWED_BRANCH_PREFIXES):
        raise SystemExit(
            "ERROR: task name must start with one of "
            + ", ".join(ALLOWED_BRANCH_PREFIXES)
            + f" (got: {name!r})"
        )
    return name


def load_task_spec(name: str) -> dict:
    spec_path = TASKS_DIR / f"{name}.md"
    if not spec_path.exists():
        raise SystemExit(f"ERROR: missing task spec at {spec_path.relative_to(ROOT)}")
    text = spec_path.read_text(encoding="utf-8")
    paths: list[str] = []
    summary = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            candidate = stripped[2:].strip()
            if candidate and not candidate.startswith("#"):
                paths.append(candidate)
        elif stripped.lower().startswith("summary:"):
            summary = stripped.split(":", 1)[1].strip()
    if not paths:
        raise SystemExit(
            f"ERROR: task spec {spec_path.relative_to(ROOT)} must declare at least one path under a `- ` list"
        )
    return {"path": spec_path, "paths": paths, "summary": summary}


def ensure_clean_main(report: dict) -> None:
    status = run(["git", "status", "--porcelain"], check=False)
    if status.stdout.strip():
        fail(report, "working tree is not clean; commit or stash before running a baby-agent")


def create_branch(name: str, report: dict) -> None:
    # Refuse to clobber an existing branch.
    existing = run(["git", "branch", "--list", name], check=False)
    if existing.stdout.strip():
        fail(report, f"branch {name!r} already exists locally; pick a new task name")
    run(["git", "checkout", "main"], check=True)
    run(["git", "pull", "--ff-only", "origin", "main"], check=False)
    run(["git", "checkout", "-b", name], check=True)
    report["branch"] = name


def verify_paths_only(spec_paths: list[str]) -> None:
    """Refuse to commit any file not declared in the spec.

    Baby-agents are expected to make their edits and then call
    `verify_paths_only` before staging so the harness can guarantee the
    scope of the change set.
    """
    changed = run(["git", "status", "--porcelain"], check=False).stdout.splitlines()
    offending: list[str] = []
    for line in changed:
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if path not in spec_paths:
            offending.append(path)
    if offending:
        raise SystemExit(
            "ERROR: edits exist outside the spec's allowlisted paths:\n  - "
            + "\n  - ".join(offending)
        )


def run_checks(report: dict) -> None:
    checks = [
        ("check_untracked", ["python3", "tools/check_untracked.py"]),
        ("validate_project_state", ["python3", "tools/validate_project_state.py"]),
        ("build", ["python3", "build.py"]),
    ]
    for name, argv in checks:
        completed = run(argv, check=False)
        report["checks"][name] = {
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-400:],
            "stderr_tail": completed.stderr[-400:],
        }
        if completed.returncode != 0:
            fail(report, f"required check failed: {name} (exit {completed.returncode})")


def commit_and_push(spec: dict, report: dict) -> None:
    run(["git", "add", "--", *spec["paths"]], check=True)
    diff = run(["git", "diff", "--cached", "--stat"], check=True).stdout
    if not diff.strip():
        fail(report, "no staged changes; baby-agent made no edits")
    title = f"agent: {Path(report['task_name']).name}"
    body_lines = [
        spec["summary"] or "Automated change by tools/agent_loop/baby_agent.py.",
        "",
        "Scope (paths touched, declared in task spec):",
        *[f"- `{p}`" for p in spec["paths"]],
        "",
        "Pre-PR checks:",
        "- check_untracked.py (local-only path guard)",
        "- validate_project_state.py (canonical facts + catalog + JS portals)",
        "- build.py (idempotent static-site build)",
        "",
        "Draft PR only. Owner review and merge required per AGENTS.md.",
    ]
    run(["git", "commit", "-m", title], check=True)
    run(["git", "push", "--set-upstream", "origin", report["branch"]], check=True)


def open_draft_pr(report: dict) -> None:
    title = f"agent: {Path(report['task_name']).name}"
    body = "\n".join(
        [
            "Draft PR opened by `tools/agent_loop/baby_agent.py`.",
            "",
            "Owner action required per AGENTS.md.",
            "",
            "- [ ] Owner review",
            "- [ ] Manual merge (no auto-merge configured)",
        ]
    )
    completed = run(
        [
            "gh",
            "pr",
            "create",
            "--repo",
            "TEAM-MMM01/mmm-education-storefront",
            "--base",
            "main",
            "--head",
            report["branch"],
            "--draft",
            "--title",
            title,
            "--body",
            body,
        ],
        check=False,
    )
    if completed.returncode != 0:
        fail(report, f"gh pr create failed: {completed.stderr.strip()}")
    pr_url = completed.stdout.strip().splitlines()[-1]
    report["pr"]["url"] = pr_url
    match = re.search(r"/pull/(\d+)", pr_url)
    if match:
        report["pr"]["number"] = int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a baby-agent task.")
    parser.add_argument("task_name", help="Task name, e.g. fix/typo-in-README")
    args = parser.parse_args()
    task_name = validate_task_name(args.task_name)

    report = report_init(task_name)
    spec = load_task_spec(task_name)
    report["notes"].append(f"loaded spec with {len(spec['paths'])} allowed paths")

    ensure_clean_main(report)
    create_branch(task_name, report)
    report["notes"].append("branch created; waiting for caller to apply edits and re-invoke --verify")

    # The harness is intentionally a state machine: a parent agent applies
    # the edit, then re-invokes this script with --verify to finish the
    # push + PR step. We do not edit files ourselves in this scaffold so
    # the harness is auditable and the parent stays in control.
    if "--verify" not in sys.argv:
        print(
            "Branch created. Apply the edits declared in "
            f"{spec['path'].relative_to(ROOT)}, then re-run:\n"
            f"  python3 tools/agent_loop/baby_agent.py --verify {task_name}"
        )
        report["result"] = "branched"
        report["finished_at"] = now_iso()
        report_write(report)
        return 0

    verify_paths_only(spec["paths"])
    run_checks(report)
    commit_and_push(spec, report)
    open_draft_pr(report)

    report["result"] = "pr_opened"
    report["finished_at"] = now_iso()
    report_write(report)
    print(f"PR opened: {report['pr']['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())