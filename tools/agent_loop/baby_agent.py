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

# Only agent/ branches per AGENTS.md convention.
ALLOWED_BRANCH_PREFIXES = ("agent/",)
TASK_NAME_RE = re.compile(r"^[a-zA-Z0-9._/-]+$")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


_BRANCH_RE = re.compile(r"^[a-zA-Z0-9_\-/]+$")

# Only these executables may be invoked by the baby-agent harness.
_ALLOWED_CMDS = frozenset({"git", "python3", "gh"})

# Timeout for each subprocess call (seconds). Prevents indefinite hangs.
TIMEOUT_SECONDS = 120


def _sanitize_branch(name: str) -> str:
    """Validate a branch name to prevent shell injection."""
    if not name or len(name) > 200:
        raise SystemExit(f"ERROR: branch name {name!r} is empty or too long")
    if not _BRANCH_RE.match(name):
        raise SystemExit(f"ERROR: branch name {name!r} contains disallowed characters")
    return name


def run_git(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a git command with validated arguments."""
    return subprocess.run(["git", *args], cwd=cwd or ROOT, check=check, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)


def run_python(script: str, *args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a python3 script with validated arguments."""
    return subprocess.run(["python3", script, *args], cwd=cwd or ROOT, check=check, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)


def run_gh(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a gh CLI command with validated arguments."""
    return subprocess.run(["gh", *args], cwd=cwd or ROOT, check=check, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)


def run(argv: list[str], *, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a subprocess. Never uses shell=True.

    The first element of *argv* must be in ``_ALLOWED_CMDS``.  Remaining
    elements are passed through unchanged; callers are responsible for
    sanitising any value derived from external input.
    """
    if not argv:
        raise SystemExit("ERROR: empty command")
    cmd = argv[0]
    if cmd not in _ALLOWED_CMDS:
        raise SystemExit(f"ERROR: command {cmd!r} is not in the allowlist")
    return subprocess.run(
        [cmd, *argv[1:]],
        cwd=cwd or ROOT,
        check=check,
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
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
    _notify_failure(report["task_name"], message)
    raise SystemExit(code)


def _notify_failure(task_name: str, error: str) -> None:
    """Best-effort notification on failure. Never blocks the main flow."""
def _notify_failure(task_name: str, error: str) -> None:
    """Best-effort notification on failure. Never blocks the main flow."""
    try:
        if str(ROOT) not in sys.path:
            sys.path.insert(0, str(ROOT))
        from tools.notifications import send_telegram, send_slack, fmt_task_failed
        text = fmt_task_failed(task_name, error)
        send_telegram(text)
        send_slack(text)
    except Exception:
        pass  # Notification is best-effort; never crash on failure.


def validate_task_name(name: str) -> str:
    if not TASK_NAME_RE.match(name):
        raise SystemExit(f"ERROR: task name contains unsafe characters: {name!r}")
    if not any(name.startswith(p) for p in ALLOWED_BRANCH_PREFIXES):
        raise SystemExit(
            "ERROR: task name must start with one of "
            + ", ".join(ALLOWED_BRANCH_PREFIXES)
            + f" (got: {name!r})"
        )
    # Prevent directory traversal: resolved path must stay under TASKS_DIR.
    candidate = (TASKS_DIR / f"{name}.md").resolve()
    if not str(candidate).startswith(str(TASKS_DIR.resolve()) + "/"):
        raise SystemExit(f"ERROR: task name {name!r} escapes the tasks directory")
    return name


def load_task_spec(name: str) -> dict:
    spec_path = (TASKS_DIR / f"{name}.md").resolve()
    # Double-check traversal guard at runtime.
    if not str(spec_path).startswith(str(TASKS_DIR.resolve()) + "/"):
        raise SystemExit(f"ERROR: task spec path escapes the tasks directory")
    if not spec_path.exists():
        raise SystemExit(f"ERROR: missing task spec at {spec_path.relative_to(ROOT)}")
    text = spec_path.read_text(encoding="utf-8")
    paths: list[str] = []
    summary_lines: list[str] = []
    in_paths = False
    in_summary = False
    for line in text.splitlines():
        stripped = line.strip()
        # Track sections by heading.
        if stripped.lower().rstrip(":") in ("paths", "summary"):
            in_paths = stripped.lower().startswith("paths")
            in_summary = stripped.lower().startswith("summary")
            continue
        # A new heading resets section tracking.
        if stripped.startswith("#") and not stripped.startswith("- "):
            in_paths = False
            in_summary = False
            continue
        if in_paths and stripped.startswith("- "):
            candidate = stripped[2:].strip()
            if candidate and not candidate.startswith("#"):
                paths.append(candidate)
        elif in_summary and stripped:
            summary_lines.append(stripped)
        elif stripped.lower().startswith("summary:"):
            summary_lines.append(stripped.split(":", 1)[1].strip())
    if not paths:
        raise SystemExit(
            f"ERROR: task spec {spec_path.relative_to(ROOT)} must declare at least one path under a `paths:` section"
        )
    summary = "\n".join(summary_lines).strip()
    return {"path": spec_path, "paths": paths, "summary": summary}


def ensure_clean_main(report: dict) -> None:
    status = run_git("status", "--porcelain", check=False)
    if status.stdout.strip():
        fail(report, "working tree is not clean; commit or stash before running a baby-agent")


def create_branch(name: str, report: dict) -> None:
    name = _sanitize_branch(name)
    # Refuse to clobber an existing branch.
    existing = run_git("branch", "--list", name, check=False)
    if existing.stdout.strip():
        fail(report, f"branch {name!r} already exists locally; pick a new task name")
    run_git("checkout", "main", check=True)
    # Fail hard if main is not up to date — do not silently continue.
    pull = run_git("pull", "--ff-only", "origin", "main", check=False)
    if pull.returncode != 0:
        fail(report, f"git pull --ff-only failed: {pull.stderr.strip()}")
    run_git("checkout", "-b", name, check=True)
    report["branch"] = name


def verify_on_branch(report: dict) -> None:
    """In verify mode, confirm we're on the expected task branch."""
    result = run_git("rev-parse", "--abbrev-ref", "HEAD", check=False)
    branch = result.stdout.strip()
    expected = report["task_name"]
    if branch != expected:
        fail(report, f"expected to be on branch {expected!r}, but on {branch!r}")
    report["branch"] = branch


def verify_paths_only(spec_paths: list[str]) -> None:
    """Refuse to commit any file not declared in the spec.

    Baby-agents are expected to make their edits and then call
    `verify_paths_only` before staging so the harness can guarantee the
    scope of the change set.
    """
    changed = run_git("status", "--porcelain", check=False).stdout.splitlines()
    offending: list[str] = []
    for line in changed:
        path = line[3:]
        if " -> " in path:
            # Validate both sides of a rename.
            src, dst = path.split(" -> ", 1)
            if src not in spec_paths:
                offending.append(src)
            if dst not in spec_paths:
                offending.append(dst)
            continue
        if path not in spec_paths:
            offending.append(path)
    if offending:
        raise SystemExit(
            "ERROR: edits exist outside the spec's allowlisted paths:\n  - "
            + "\n  - ".join(offending)
        )


def run_checks(report: dict) -> None:
    checks = [
        ("check_untracked", "tools/check_untracked.py"),
        ("validate_project_state", "tools/validate_project_state.py"),
        ("build", "build.py"),
        ("git_diff_check", None),  # special: inline
    ]
    for name, script in checks:
        if name == "git_diff_check":
            completed = run_git("diff", "--check", check=False)
        else:
            completed = run_python(script, check=False)
        report["checks"][name] = {
            "exit_code": completed.returncode,
            "stdout_tail": completed.stdout[-400:],
            "stderr_tail": completed.stderr[-400:],
        }
        if completed.returncode != 0:
            fail(report, f"required check failed: {name} (exit {completed.returncode})")


def commit_and_push(spec: dict, report: dict) -> None:
    # Stage only the paths declared in the task spec.
    run_git("add", "--", *spec["paths"], check=True)
    status = run_git("status", "--porcelain", check=False)
    if not status.stdout.strip():
        fail(report, "no staged changes; baby-agent made no edits")
    # Warn if there are unstaged changes outside allowed paths (do not stage them).
    unstaged = run_git("status", "--porcelain", "--", *spec["paths"], check=False)
    all_files = run_git("status", "--porcelain", check=False)
    allowed_set = set(spec["paths"])
    for line in all_files.stdout.strip().splitlines():
        if not line.strip():
            continue
        # Status format: XY filename
        fname = line[3:].strip()
        if fname not in allowed_set:
            report["notes"].append(f"WARNING: unstaged change outside allowed paths: {fname}")
    diff = run_git("diff", "--cached", "--stat", check=True).stdout
    if not diff.strip():
        fail(report, "no staged changes after build; baby-agent made no edits")
    title = f"agent: {Path(report['task_name']).name}"
    run_git("commit", "-m", title, check=True)
    # Record commit/push failures through fail() instead of raising.
    push = run_git("push", "--set-upstream", "origin", report["branch"], check=False)
    if push.returncode != 0:
        fail(report, f"git push failed: {push.stderr.strip()}")


def open_draft_pr(report: dict, body: str) -> None:
    title = f"agent: {Path(report['task_name']).name}"
    completed = run_gh(
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
    parser.add_argument("--verify", action="store_true", help="Run checks, push, and open the draft PR")
    parser.add_argument("task_name", help="Task name, e.g. agent/fix-typo-in-README")
    args = parser.parse_args()
    task_name = validate_task_name(args.task_name)

    report = report_init(task_name)
    spec = load_task_spec(task_name)
    report["notes"].append(f"loaded spec with {len(spec['paths'])} allowed paths")

    if not args.verify:
        # Phase 1: create branch, then exit for the caller to apply edits.
        ensure_clean_main(report)
        create_branch(task_name, report)
        report["notes"].append("branch created; waiting for caller to apply edits and re-invoke --verify")
        report["result"] = "branched"
        report["finished_at"] = now_iso()
        report_write(report)
        print(
            "Branch created. Apply the edits declared in "
            f"{spec['path'].relative_to(ROOT)}, then re-run:\n"
            f"  python3 tools/agent_loop/baby_agent.py --verify {task_name}"
        )
        return 0

    # Phase 2: verify, commit, push, open PR.
    verify_on_branch(report)
    verify_paths_only(spec["paths"])
    run_checks(report)
    commit_and_push(spec, report)
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
        "- git diff --check (whitespace errors)",
        "",
        "Draft PR only. Owner review and merge required per AGENTS.md.",
    ]
    open_draft_pr(report, "\n".join(body_lines))

    report["result"] = "pr_opened"
    report["finished_at"] = now_iso()
    report_write(report)
    print(f"PR opened: {report['pr']['url']}")
    _notify_pr_opened(report)
    return 0


def _notify_pr_opened(report: dict) -> None:
    """Best-effort notification when a PR is opened. Never blocks."""
    try:
        from tools.notifications import send_telegram, send_slack, fmt_pr_opened
        pr_num = report["pr"].get("number", 0)
        branch = report["branch"]
        task = Path(report["task_name"]).name
        text = fmt_pr_opened(pr_num, branch, f"agent: {task}")
        send_telegram(text)
        send_slack(text)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
