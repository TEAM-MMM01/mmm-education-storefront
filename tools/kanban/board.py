#!/usr/bin/env python3
"""HermesOS Kanban Board — Agent task management with expertise matching.

Manages task cards across columns (Backlog, Ready, In Progress, Review, Done).
Agents pull tasks based on expertise match and performance metrics.
Repetitive tasks become reusable templates that agents can improve.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

BOARD_PATH = Path.home() / ".hermes-mac" / "kanban" / "board.json"
TEMPLATES_PATH = Path.home() / ".hermes-mac" / "kanban" / "templates.json"
METRICS_PATH = Path.home() / ".hermes-mac" / "kanban" / "metrics.json"

# Agent expertise map — weights 0-100 for each skill domain
AGENT_EXPERTISE = {
    "hermes-coo": {
        "description": "Task routing, audit, orchestration, approvals",
        "skills": {
            "orchestration": 95, "routing": 95, "audit": 90,
            "approvals": 95, "documentation": 80, "debugging": 70,
            "code-review": 85, "deployment": 60, "design": 40,
            "trading": 30, "commerce": 50, "education": 60,
        }
    },
    "prep-station": {
        "description": "Education/TEFA operations, product catalog, storefront",
        "skills": {
            "education": 95, "tefa": 95, "catalog": 90,
            "storefront": 85, "documentation": 80, "content": 85,
            "code-review": 60, "debugging": 50, "deployment": 40,
            "design": 50, "trading": 10, "commerce": 70,
        }
    },
    "hermes-voice": {
        "description": "Voice input, transcription, message routing",
        "skills": {
            "voice": 95, "transcription": 95, "routing": 80,
            "documentation": 60, "debugging": 40, "code-review": 30,
            "deployment": 20, "design": 20, "trading": 10,
            "commerce": 30, "education": 40,
        }
    },
    "hermes-pf": {
        "description": "PumpFun trading, token analysis, portfolio management",
        "skills": {
            "trading": 95, "analysis": 90, "portfolio": 95,
            "debugging": 60, "documentation": 50, "code-review": 50,
            "deployment": 30, "design": 20, "education": 20,
            "commerce": 30, "orchestration": 40,
        }
    },
    "royal-collexions": {
        "description": "Shopify commerce, fulfillment, inventory, dropshipping",
        "skills": {
            "commerce": 95, "fulfillment": 95, "inventory": 90,
            "shopify": 95, "debugging": 50, "documentation": 60,
            "code-review": 50, "deployment": 40, "design": 40,
            "trading": 20, "education": 30,
        }
    },
    "the-oracle": {
        "description": "Trading signals, market analysis, predictions",
        "skills": {
            "trading": 95, "signals": 95, "analysis": 95,
            "predictions": 90, "debugging": 50, "documentation": 50,
            "code-review": 40, "deployment": 20, "design": 20,
            "education": 20, "commerce": 20,
        }
    },
}

COLUMNS = ["backlog", "ready", "in_progress", "review", "done"]
PRIORITIES = ["critical", "high", "medium", "low"]
TIERS = [0, 1, 2, 3, 4]  # Execution tiers


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _load(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def _load_board() -> dict:
    return _load(BOARD_PATH)


def _save_board(board: dict):
    _save(BOARD_PATH, board)


def _load_templates() -> dict:
    return _load(TEMPLATES_PATH)


def _save_templates(templates: dict):
    _save(TEMPLATES_PATH, templates)


def _load_metrics() -> dict:
    return _load(METRICS_PATH)


def _save_metrics(metrics: dict):
    _save(METRICS_PATH, metrics)


def _generate_id() -> str:
    return str(uuid.uuid4())[:8]


def calculate_expertise_match(agent_id: str, task_skills: list[str]) -> float:
    """Calculate how well an agent's expertise matches task requirements."""
    if agent_id not in AGENT_EXPERTISE:
        return 0.0
    agent_skills = AGENT_EXPERTISE[agent_id]["skills"]
    if not task_skills:
        return 50.0  # Neutral if no skills specified
    scores = [agent_skills.get(skill, 0) for skill in task_skills]
    return sum(scores) / len(scores) if scores else 0.0


def find_best_agent(task_skills: list[str], exclude: list[str] = None) -> str:
    """Find the best agent for a task based on expertise match."""
    exclude = exclude or []
    best_agent = None
    best_score = -1
    for agent_id in AGENT_EXPERTISE:
        if agent_id in exclude:
            continue
        score = calculate_expertise_match(agent_id, task_skills)
        if score > best_score:
            best_score = score
            best_agent = agent_id
    return best_agent or "hermes-coo"


def create_task(
    title: str,
    description: str = "",
    skills: list[str] = None,
    priority: str = "medium",
    tier: int = 1,
    column: str = "backlog",
    assignee: str = None,
    parent_id: str = None,
    template_id: str = None,
    metadata: dict = None,
) -> dict:
    """Create a new task card."""
    task_id = _generate_id()
    skills = skills or []

    if not assignee:
        assignee = find_best_agent(skills)

    task = {
        "id": task_id,
        "title": title,
        "description": description,
        "skills": skills,
        "priority": priority,
        "tier": tier,
        "column": column,
        "assignee": assignee,
        "parent_id": parent_id,
        "template_id": template_id,
        "metadata": metadata or {},
        "created_at": _now(),
        "updated_at": _now(),
        "started_at": None,
        "completed_at": None,
        "time_spent_seconds": 0,
        "attempts": 0,
        "status": "active",
        "tags": [],
        "blocked_by": [],
        "subtasks": [],
    }

    board = _load_board()
    if "tasks" not in board:
        board["tasks"] = []
    board["tasks"].append(task)
    _save_board(board)

    return task


def move_task(task_id: str, to_column: str) -> dict:
    """Move a task to a different column."""
    board = _load_board()
    for task in board.get("tasks", []):
        if task["id"] == task_id:
            task["column"] = to_column
            task["updated_at"] = _now()
            if to_column == "in_progress":
                task["started_at"] = _now()
                task["attempts"] += 1
            elif to_column == "done":
                task["completed_at"] = _now()
                if task["started_at"]:
                    started = dt.datetime.fromisoformat(task["started_at"])
                    completed = dt.datetime.fromisoformat(task["completed_at"])
                    task["time_spent_seconds"] = (completed - started).total_seconds()
            _save_board(board)
            return task
    return {"error": f"Task {task_id} not found"}


def assign_task(task_id: str, agent_id: str) -> dict:
    """Assign a task to an agent."""
    board = _load_board()
    for task in board.get("tasks", []):
        if task["id"] == task_id:
            task["assignee"] = agent_id
            task["updated_at"] = _now()
            _save_board(board)
            return task
    return {"error": f"Task {task_id} not found"}


def get_agent_tasks(agent_id: str, column: str = None) -> list[dict]:
    """Get all tasks for an agent, optionally filtered by column."""
    board = _load_board()
    tasks = [t for t in board.get("tasks", []) if t["assignee"] == agent_id]
    if column:
        tasks = [t for t in tasks if t["column"] == column]
    return sorted(tasks, key=lambda t: PRIORITIES.index(t["priority"]) if t["priority"] in PRIORITIES else 3)


def get_board_summary() -> dict:
    """Get a summary of the board state."""
    board = _load_board()
    tasks = board.get("tasks", [])
    summary = {
        "total": len(tasks),
        "by_column": {col: 0 for col in COLUMNS},
        "by_agent": {},
        "by_priority": {p: 0 for p in PRIORITIES},
        "by_skill": {},
    }
    for task in tasks:
        col = task.get("column", "backlog")
        if col in summary["by_column"]:
            summary["by_column"][col] += 1
        agent = task.get("assignee", "unassigned")
        summary["by_agent"][agent] = summary["by_agent"].get(agent, 0) + 1
        pri = task.get("priority", "medium")
        if pri in summary["by_priority"]:
            summary["by_priority"][pri] += 1
        for skill in task.get("skills", []):
            summary["by_skill"][skill] = summary["by_skill"].get(skill, 0) + 1
    return summary


def create_template(
    name: str,
    description: str,
    skills: list[str],
    prompt_template: str,
    priority: str = "medium",
    tier: int = 1,
    tags: list[str] = None,
) -> dict:
    """Create a reusable task template from a repetitive task."""
    template_id = _generate_id()
    template = {
        "id": template_id,
        "name": name,
        "description": description,
        "skills": skills,
        "prompt_template": prompt_template,
        "priority": priority,
        "tier": tier,
        "tags": tags or [],
        "created_at": _now(),
        "updated_at": _now(),
        "usage_count": 0,
        "avg_time_seconds": 0,
        "success_rate": 100.0,
        "improvements": [],
    }
    templates = _load_templates()
    if "templates" not in templates:
        templates["templates"] = []
    templates["templates"].append(template)
    _save_templates(templates)
    return template


def spawn_from_template(template_id: str, context: dict = None) -> dict:
    """Create a task from a template with optional context."""
    templates = _load_templates()
    for template in templates.get("templates", []):
        if template["id"] == template_id:
            prompt = template["prompt_template"]
            if context:
                for key, value in context.items():
                    prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
            task = create_task(
                title=template["name"],
                description=prompt,
                skills=template["skills"],
                priority=template["priority"],
                tier=template["tier"],
                template_id=template_id,
                tags=template["tags"],
            )
            template["usage_count"] += 1
            template["updated_at"] = _now()
            _save_templates(templates)
            return task
    return {"error": f"Template {template_id} not found"}


def record_metric(agent_id: str, task_id: str, success: bool, time_seconds: float):
    """Record performance metrics for an agent."""
    metrics = _load_metrics()
    if "agents" not in metrics:
        metrics["agents"] = {}
    if agent_id not in metrics["agents"]:
        metrics["agents"][agent_id] = {
            "total_tasks": 0, "successful": 0, "failed": 0,
            "total_time_seconds": 0, "avg_time_seconds": 0,
            "success_rate": 100.0, "skill_performance": {},
        }
    agent = metrics["agents"][agent_id]
    agent["total_tasks"] += 1
    if success:
        agent["successful"] += 1
    else:
        agent["failed"] += 1
    agent["total_time_seconds"] += time_seconds
    agent["avg_time_seconds"] = agent["total_time_seconds"] / agent["total_tasks"]
    agent["success_rate"] = (agent["successful"] / agent["total_tasks"]) * 100
    _save_metrics(metrics)


def get_agent_metrics(agent_id: str) -> dict:
    """Get performance metrics for an agent."""
    metrics = _load_metrics()
    return metrics.get("agents", {}).get(agent_id, {
        "total_tasks": 0, "successful": 0, "failed": 0,
        "total_time_seconds": 0, "avg_time_seconds": 0,
        "success_rate": 100.0,
    })


def improve_template(template_id: str, improvement: str) -> dict:
    """Record an improvement to a template."""
    templates = _load_templates()
    for template in templates.get("templates", []):
        if template["id"] == template_id:
            template["improvements"].append({
                "description": improvement,
                "timestamp": _now(),
            })
            template["updated_at"] = _now()
            _save_templates(templates)
            return template
    return {"error": f"Template {template_id} not found"}


def get_repetitive_tasks(min_runs: int = 3) -> list[dict]:
    """Find tasks that have been run multiple times (candidates for templates)."""
    board = _load_board()
    templates = _load_templates()
    template_usage = {t["id"]: t.get("usage_count", 0) for t in templates.get("templates", [])}

    candidates = []
    for task in board.get("tasks", []):
        if task.get("template_id"):
            usage = template_usage.get(task["template_id"], 0)
            if usage >= min_runs:
                candidates.append({
                    "task": task,
                    "template_id": task["template_id"],
                    "usage_count": usage,
                })
    return candidates


# ─── CLI ──────────────────────────────────────────────────────────────

def cmd_create(args):
    task = create_task(
        title=args.title,
        description=args.description or "",
        skills=args.skills.split(",") if args.skills else [],
        priority=args.priority,
        tier=args.tier,
        assignee=args.assignee,
    )
    print(f"✅ Task created: {task['id']}")
    print(f"   Title: {task['title']}")
    print(f"   Assignee: {task['assignee']}")
    print(f"   Priority: {task['priority']} | Tier: {task['tier']}")
    print(f"   Skills: {', '.join(task['skills'])}")


def cmd_move(args):
    result = move_task(args.task_id, args.column)
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ Task {args.task_id} moved to {args.column}")


def cmd_assign(args):
    result = assign_task(args.task_id, args.agent)
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ Task {args.task_id} assigned to {args.agent}")


def cmd_list(args):
    if args.agent:
        tasks = get_agent_tasks(args.agent, args.column)
    else:
        board = _load_board()
        tasks = board.get("tasks", [])
        if args.column:
            tasks = [t for t in tasks if t["column"] == args.column]

    if not tasks:
        print("No tasks found.")
        return

    for task in tasks:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task["priority"], "⚪")
        print(f"{icon} [{task['id']}] {task['title']}")
        print(f"   Column: {task['column']} | Agent: {task['assignee']} | Tier: {task['tier']}")
        if task.get("skills"):
            print(f"   Skills: {', '.join(task['skills'])}")
        print()


def cmd_board(args):
    summary = get_board_summary()
    print("📋 Kanban Board Summary")
    print(f"   Total tasks: {summary['total']}")
    print()
    print("By Column:")
    for col, count in summary["by_column"].items():
        bar = "█" * count
        print(f"   {col:15s} {count:3d} {bar}")
    print()
    print("By Agent:")
    for agent, count in sorted(summary["by_agent"].items(), key=lambda x: -x[1]):
        print(f"   {agent:20s} {count:3d}")
    print()
    print("By Priority:")
    for pri, count in summary["by_priority"].items():
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(pri, "⚪")
        print(f"   {icon} {pri:10s} {count:3d}")


def cmd_template_create(args):
    template = create_template(
        name=args.name,
        description=args.description or "",
        skills=args.skills.split(",") if args.skills else [],
        prompt_template=args.prompt,
        priority=args.priority,
        tier=args.tier,
    )
    print(f"✅ Template created: {template['id']}")
    print(f"   Name: {template['name']}")
    print(f"   Skills: {', '.join(template['skills'])}")


def cmd_template_spawn(args):
    task = spawn_from_template(args.template_id)
    if "error" in task:
        print(f"❌ {task['error']}")
    else:
        print(f"✅ Task spawned from template: {task['id']}")
        print(f"   Title: {task['title']}")
        print(f"   Assignee: {task['assignee']}")


def cmd_template_list(args):
    templates = _load_templates()
    for t in templates.get("templates", []):
        print(f"📝 [{t['id']}] {t['name']}")
        print(f"   Skills: {', '.join(t['skills'])}")
        print(f"   Used: {t['usage_count']}x | Success: {t['success_rate']}%")
        print()


def cmd_metrics(args):
    if args.agent:
        m = get_agent_metrics(args.agent)
        print(f"📊 Metrics for {args.agent}:")
        print(f"   Total tasks: {m['total_tasks']}")
        print(f"   Success rate: {m['success_rate']:.1f}%")
        print(f"   Avg time: {m['avg_time_seconds']:.1f}s")
    else:
        metrics = _load_metrics()
        print("📊 All Agent Metrics:")
        for agent_id, m in metrics.get("agents", {}).items():
            print(f"\n   {agent_id}:")
            print(f"     Tasks: {m['total_tasks']} | Success: {m['success_rate']:.1f}%")
            print(f"     Avg time: {m['avg_time_seconds']:.1f}s")


def cmd_suggest(args):
    """Suggest best agent for a task based on skills."""
    skills = args.skills.split(",") if args.skills else []
    best = find_best_agent(skills)
    print(f"🎯 Best agent for skills [{', '.join(skills)}]: {best}")
    print(f"   Match score: {calculate_expertise_match(best, skills):.0f}/100")
    print()
    print("All agents ranked:")
    scores = []
    for agent_id in AGENT_EXPERTISE:
        score = calculate_expertise_match(agent_id, skills)
        scores.append((agent_id, score))
    for agent_id, score in sorted(scores, key=lambda x: -x[1]):
        bar = "█" * int(score / 5)
        print(f"   {agent_id:20s} {score:5.1f} {bar}")


def main():
    parser = argparse.ArgumentParser(description="HermesOS Kanban Board")
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new task")
    p_create.add_argument("title", help="Task title")
    p_create.add_argument("-d", "--description", help="Task description")
    p_create.add_argument("-s", "--skills", help="Comma-separated skills")
    p_create.add_argument("-p", "--priority", default="medium", choices=PRIORITIES)
    p_create.add_argument("-t", "--tier", type=int, default=1, choices=TIERS)
    p_create.add_argument("-a", "--assignee", help="Agent to assign")
    p_create.set_defaults(func=cmd_create)

    # move
    p_move = sub.add_parser("move", help="Move task to column")
    p_move.add_argument("task_id", help="Task ID")
    p_move.add_argument("column", choices=COLUMNS)
    p_move.set_defaults(func=cmd_move)

    # assign
    p_assign = sub.add_parser("assign", help="Assign task to agent")
    p_assign.add_argument("task_id", help="Task ID")
    p_assign.add_argument("agent", help="Agent ID")
    p_assign.set_defaults(func=cmd_assign)

    # list
    p_list = sub.add_parser("list", help="List tasks")
    p_list.add_argument("-a", "--agent", help="Filter by agent")
    p_list.add_argument("-c", "--column", help="Filter by column")
    p_list.set_defaults(func=cmd_list)

    # board
    p_board = sub.add_parser("board", help="Show board summary")
    p_board.set_defaults(func=cmd_board)

    # template create
    p_tc = sub.add_parser("template-create", help="Create task template")
    p_tc.add_argument("name", help="Template name")
    p_tc.add_argument("-d", "--description", help="Template description")
    p_tc.add_argument("-s", "--skills", help="Comma-separated skills")
    p_tc.add_argument("-p", "--prompt", required=True, help="Prompt template (use {variable} placeholders)")
    p_tc.add_argument("--priority", default="medium", choices=PRIORITIES)
    p_tc.add_argument("--tier", type=int, default=1, choices=TIERS)
    p_tc.set_defaults(func=cmd_template_create)

    # template spawn
    p_ts = sub.add_parser("template-spawn", help="Create task from template")
    p_ts.add_argument("template_id", help="Template ID")
    p_ts.set_defaults(func=cmd_template_spawn)

    # template list
    p_tl = sub.add_parser("template-list", help="List templates")
    p_tl.set_defaults(func=cmd_template_list)

    # metrics
    p_m = sub.add_parser("metrics", help="Show agent metrics")
    p_m.add_argument("-a", "--agent", help="Filter by agent")
    p_m.set_defaults(func=cmd_metrics)

    # suggest
    p_s = sub.add_parser("suggest", help="Suggest best agent for skills")
    p_s.add_argument("-s", "--skills", required=True, help="Comma-separated skills")
    p_s.set_defaults(func=cmd_suggest)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
