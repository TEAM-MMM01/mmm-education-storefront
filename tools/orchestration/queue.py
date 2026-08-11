#!/usr/bin/env python3
"""Mac-side orchestration state for HermesOS Control Plane.

Pure local. No remote calls. Implements the seven workflow truth states
from the HermesOS Control Plane doctrine (Locally Complete, Queued for
Remote Execution, Remote Attempted, Remotely Verified, Blocked, Awaiting
Approval, Needs Richie's Lock).

Every record is JSON-serializable, has an idempotency key, timestamps,
and a retry counter. The queue lives in ~/.hermes-mac/queue/ and survives
restarts. Workers can be re-run without duplicating remote actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import uuid
from pathlib import Path


_DEFAULT_QUEUE_ROOT = Path.home() / ".hermes-mac" / "queue"


def _resolve_queue_root() -> Path:
    """Resolve queue root, honoring HERMES_MAC_QUEUE_ROOT for test isolation."""
    raw = os.environ.get("HERMES_MAC_QUEUE_ROOT")
    if raw:
        candidate = Path(raw).resolve()
        # Ensure the resolved path is a reasonable location (under home or /tmp).
        home = Path.home().resolve()
        tmp = Path("/tmp").resolve()
        if not (str(candidate).startswith(str(home) + os.sep)
                or str(candidate).startswith(str(tmp) + os.sep)
                or candidate == home
                or candidate == tmp):
            raise SystemExit(f"ERROR: HERMES_MAC_QUEUE_ROOT {candidate} escapes home/tmp")
        return candidate
    return _DEFAULT_QUEUE_ROOT


QUEUE_ROOT = _resolve_queue_root()
QUEUE_ROOT.mkdir(parents=True, exist_ok=True)

# Workflow IDs and record IDs must match this pattern.  Anything else is
# rejected before it can touch the filesystem, preventing path traversal.
_VALID_ID_RE = re.compile(r"^wf-\d{8}T\d{6}-[0-9a-f]{8}$")


def _sanitize_id(raw: str) -> str:
    """Validate a workflow/record ID and return it, or abort."""
    if _VALID_ID_RE.match(raw):
        return raw
    raise SystemExit(f"ERROR: invalid workflow id {raw!r}")


def _safe_record_path(workflow_id: str) -> Path:
    """Return the record path, aborting if it would escape QUEUE_ROOT."""
    wid = _sanitize_id(workflow_id)
    resolved = (QUEUE_ROOT / f"{wid}.json").resolve()
    if not str(resolved).startswith(str(QUEUE_ROOT.resolve()) + os.sep):
        raise SystemExit(f"ERROR: path {resolved} escapes queue root")
    return resolved

# The seven allowed workflow states. Anything else is a bug.
ALLOWED_STATES = {
    "Locally Complete",
    "Queued for Remote Execution",
    "Remote Attempted",
    "Remotely Verified",
    "Blocked",
    "Awaiting Approval",
    "Needs Richie's Lock",
}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def new_workflow_id() -> str:
    return f"wf-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:8]}"


def cmd_enqueue(args: argparse.Namespace) -> int:
    if args.state not in ALLOWED_STATES:
        print(f"ERROR: state {args.state!r} is not one of the seven allowed states", file=sys.stderr)
        return 2
    workflow_id = args.id or new_workflow_id()
    record = {
        "schema_version": 1,
        "workflow_id": workflow_id,
        "task_name": args.task_name,
        "work_lane": args.lane,
        "tier": args.tier,
        "l4_risk": args.l4_risk,
        "state": args.state,
        "device": args.device,
        "environment": args.environment,
        "owner": args.owner,
        "supporting_agent": args.agent,
        "writer_model": args.writer,
        "verifier_model": args.verifier,
        "repo": args.repo,
        "branch": args.branch,
        "files": args.files.split(",") if args.files else [],
        "dependencies": args.deps.split(",") if args.deps else [],
        "definition_of_done": args.dod,
        "validation_method": args.validation,
        "rollback_path": args.rollback,
        "idempotency_key": args.idempotency or workflow_id,
        "retry_count": 0,
        "max_retries": int(args.max_retries),
        "next_retry_at": None,
        "blocker": args.blocker,
        "next_action": args.next_action,
        "delivery_target": args.target,
        "history": [{"ts": now_iso(), "event": "enqueued", "state": args.state}],
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    record_path = _safe_record_path(workflow_id)
    if record_path.exists():
        print(f"ERROR: workflow {workflow_id} already exists; use 'update' instead", file=sys.stderr)
        return 1
    record_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"enqueued {workflow_id} ({args.state})")
    return 0


def cmd_update(args: argparse.Namespace) -> int:
    path = _safe_record_path(args.id)
    if not path.exists():
        print(f"ERROR: no workflow with id {args.id}", file=sys.stderr)
        return 1
    record = json.loads(path.read_text(encoding="utf-8"))
    if args.new_state and args.new_state not in ALLOWED_STATES:
        print(f"ERROR: state {args.new_state!r} is not allowed", file=sys.stderr)
        return 2
    if args.new_state:
        record["history"].append({"ts": now_iso(), "event": "state-change", "from": record["state"], "to": args.new_state, "note": args.note})
        record["state"] = args.new_state
        if args.new_state == "Remote Attempted":
            record["retry_count"] = record.get("retry_count", 0) + 1
    record["updated_at"] = now_iso()
    if args.next_action:
        record["next_action"] = args.next_action
    if args.note:
        record.setdefault("history", []).append({"ts": now_iso(), "event": "note", "text": args.note})
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"updated {args.id} -> {record['state']}")
    return 0


def cmd_list(_args: argparse.Namespace) -> int:
    rows = sorted(QUEUE_ROOT.glob("wf-*.json"))
    if not rows:
        print("(no workflows)")
        return 0
    for row in rows:
        resolved = row.resolve()
        if not str(resolved).startswith(str(QUEUE_ROOT.resolve()) + os.sep):
            continue
        record = json.loads(resolved.read_text(encoding="utf-8"))
        print(
            f"{record['workflow_id']:38s}  {record['state']:24s}  retries={record.get('retry_count', 0):>2}  {record.get('task_name', '')}"
        )
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    path = _safe_record_path(args.id)
    if not path.exists():
        print(f"ERROR: no workflow with id {args.id}", file=sys.stderr)
        return 1
    print(path.read_text(encoding="utf-8"))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HermesOS Mac orchestration queue")
    sub = parser.add_subparsers(dest="cmd", required=True)

    en = sub.add_parser("enqueue", help="Create a workflow record")
    en.add_argument("--task-name", required=True)
    en.add_argument("--lane", choices=["build", "revenue", "audit", "support", "research", "protected"], required=True)
    en.add_argument("--tier", choices=["1", "2", "3"], required=True, help="Execution tier (1=auto, 2=scope-verified, 3=owner-lock)")
    en.add_argument("--l4-risk", choices=["L4-0", "L4-1", "L4-2", "L4-3"], default="L4-0", help="L4 risk classification")
    en.add_argument("--state", choices=sorted(ALLOWED_STATES), required=True)
    en.add_argument("--device", default="mac")
    en.add_argument("--environment", default="local")
    en.add_argument("--owner", required=True)
    en.add_argument("--agent", default="agent")
    en.add_argument("--writer", default="")
    en.add_argument("--verifier", default="")
    en.add_argument("--repo", default="")
    en.add_argument("--branch", default="")
    en.add_argument("--files", default="")
    en.add_argument("--deps", default="")
    en.add_argument("--dod", default="")
    en.add_argument("--validation", default="")
    en.add_argument("--rollback", default="")
    en.add_argument("--idempotency", default="")
    en.add_argument("--max-retries", default="3")
    en.add_argument("--blocker", default="")
    en.add_argument("--next-action", default="")
    en.add_argument("--target", default="")
    en.add_argument("--id", default="")
    en.add_argument("--created-by", dest="agent", default="agent")
    en.set_defaults(func=cmd_enqueue)

    up = sub.add_parser("update", help="Update an existing workflow")
    up.add_argument("--id", required=True)
    up.add_argument("--new-state", choices=sorted(ALLOWED_STATES))
    up.add_argument("--note", default="")
    up.add_argument("--next-action", default="")
    up.set_defaults(func=cmd_update)

    ls = sub.add_parser("list", help="List workflows")
    ls.set_defaults(func=cmd_list)

    sh = sub.add_parser("show", help="Show one workflow as JSON")
    sh.add_argument("--id", required=True)
    sh.set_defaults(func=cmd_show)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())