#!/usr/bin/env python3
"""Agent task puller — agents call this to get their next task."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from board import get_agent_tasks, move_task, AGENT_EXPERTISE

def pull_task(agent_id: str) -> dict:
    """Pull the highest priority ready task for an agent."""
    tasks = get_agent_tasks(agent_id, column="ready")
    if not tasks:
        # Try backlog
        tasks = get_agent_tasks(agent_id, column="backlog")
    
    if not tasks:
        return {"status": "no_tasks", "message": f"No tasks available for {agent_id}"}
    
    task = tasks[0]  # Highest priority first
    move_task(task["id"], "in_progress")
    
    return {
        "status": "task_assigned",
        "task": task,
        "agent": agent_id,
        "expertise_match": "high" if any(
            AGENT_EXPERTISE.get(agent_id, {}).get("skills", {}).get(s, 0) > 70
            for s in task.get("skills", [])
        ) else "medium",
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: agent_pull.py <agent_id>")
        sys.exit(1)
    
    result = pull_task(sys.argv[1])
    print(json.dumps(result, indent=2))
