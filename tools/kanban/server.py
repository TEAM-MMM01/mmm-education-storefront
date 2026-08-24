#!/usr/bin/env python3
"""Kanban board server - fully functional with all endpoints."""
import json
import os
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import logging
import subprocess
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/kanban.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

BOARD_PATH = Path.home() / ".hermes-mac" / "kanban" / "board.json"
TEMPLATES_PATH = Path(__file__).parent / "templates.json"
AGENTS_PATH = Path.home() / ".hermes-mac" / "kanban" / "agents.json"
DASHBOARD_DIR = Path(__file__).parent

AGENTS = [
    {"id": "hermes-coo", "name": "Hermes COO", "icon": "🦁", "role": "Operations", "status": "active", "color": "#f778ba"},
    {"id": "prep-station", "name": "Prep Station", "icon": "📚", "role": "Education", "status": "active", "color": "#58a6ff"},
    {"id": "hermes-pf", "name": "Hermes PF", "icon": "💰", "role": "Finance", "status": "active", "color": "#a371f7"},
    {"id": "royal-collexions", "name": "Royal Collexions", "icon": "👑", "role": "Commerce", "status": "active", "color": "#d29922"},
    {"id": "the-oracle", "name": "The Oracle", "icon": "🔮", "role": "Analytics", "status": "active", "color": "#3fb950"},
    {"id": "hermes-voice", "name": "Hermes Voice", "icon": "🎤", "role": "Voice Agent", "status": "active", "color": "#f0883e"},
]

DEFAULT_TEMPLATES = [
    {"id": "code-review", "name": "Code Review", "description": "Review code changes", "skills": ["code", "review"], "assignee": "hermes-coo", "priority": "high", "tier": 2},
    {"id": "deploy", "name": "Deploy to Production", "description": "Deploy changes to production", "skills": ["deploy"], "assignee": "hermes-coo", "priority": "critical", "tier": 3},
    {"id": "email-draft", "name": "Draft Email", "description": "Draft a professional email", "skills": ["email", "write"], "assignee": "prep-station", "priority": "medium", "tier": 1},
    {"id": "research", "name": "Research Task", "description": "Research a topic or competitor", "skills": ["research", "analyze"], "assignee": "the-oracle", "priority": "medium", "tier": 1},
    {"id": "telegram-send", "name": "Send Telegram", "description": "Send notification via Telegram", "skills": ["telegram"], "assignee": "hermes-voice", "priority": "low", "tier": 1},
    {"id": "site-audit", "name": "Site Audit", "description": "Audit site for issues", "skills": ["code", "review", "analyze"], "assignee": "hermes-coo", "priority": "high", "tier": 2},
    {"id": "content-write", "name": "Write Content", "description": "Write page content or copy", "skills": ["write"], "assignee": "prep-station", "priority": "medium", "tier": 1},
    {"id": "bug-fix", "name": "Bug Fix", "description": "Fix a reported bug", "skills": ["code", "debug"], "assignee": "hermes-coo", "priority": "high", "tier": 2},
]

SKILL_PROMPTS = {
    "code": "Run code-review skill. Check for: badge taxonomy, no raw emails, PDSES/TEFA separation, responsive design, motion compliance.",
    "review": "Run review checklist. Verify: spec match, no regressions, tests pass, docs updated.",
    "write": "Run content writing skill. Check: clarity, brand voice, no speculative claims, TEFA compliance.",
    "research": "Run research skill. Gather: web sources, competitor analysis, market data.",
    "analyze": "Run analysis skill. Check: data accuracy, trend identification, actionable insights.",
    "deploy": "Run deployment skill. Verify: tests pass, build clean, rollback plan ready.",
    "email": "Run email skill. Check: professional tone, no secrets, clear call-to-action.",
    "telegram": "Run notification skill. Verify: message format, no sensitive data, correct channel.",
    "design": "Run design skill. Check: responsive at 760px, motion tokens, accessibility.",
    "debug": "Run debugging skill. Trace: reproduce, isolate, fix, verify.",
}

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def load_board():
    try:
        if BOARD_PATH.exists():
            return json.loads(BOARD_PATH.read_text())
    except Exception as e:
        logger.error(f"Board load error: {e}")
    return {"tasks": []}

def save_board(board):
    try:
        BOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
        BOARD_PATH.write_text(json.dumps(board, indent=2, default=str))
    except Exception as e:
        logger.error(f"Board save error: {e}")

def load_templates():
    try:
        if TEMPLATES_PATH.exists():
            return json.loads(TEMPLATES_PATH.read_text())
    except:
        pass
    return DEFAULT_TEMPLATES

def load_agents():
    return AGENTS

def get_skill_prompt(skills):
    prompts = []
    for s in skills:
        if s in SKILL_PROMPTS:
            prompts.append(SKILL_PROMPTS[s])
    return prompts

class KanbanHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DASHBOARD_DIR), **kwargs)

    def log_message(self, format, *args):
        logger.info(f"{self.client_address[0]} - {format % args}")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/health":
            return self.send_json({"status": "healthy", "timestamp": datetime.now().isoformat()})

        if path == "/api/board":
            return self.send_json(load_board())

        if path == "/api/templates":
            return self.send_json({"templates": load_templates()})

        if path == "/api/agents":
            return self.send_json({"agents": load_agents()})

        if path == "/api/skills":
            return self.send_json({"skills": list(SKILL_PROMPTS.keys()), "prompts": SKILL_PROMPTS})

        if self.path == "/":
            self.path = "/dashboard.html"

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        data = self.read_body()

        board = load_board()

        if path.startswith("/api/move/"):
            return self.handle_move(board, path)

        if path == "/api/task" or path == "/api/create-task":
            return self.handle_create_task(board, data)

        if path == "/api/template-spawn/" or path.startswith("/api/template-spawn/"):
            return self.handle_template_spawn(board, path, data)

        if path == "/api/spawn-agent":
            return self.handle_spawn_agent(board, data)

        if path == "/api/ai":
            return self.handle_ai(board, data)

        if path == "/api/voice":
            return self.handle_voice(board, data)

        self.send_json({"error": "Not found"}, 404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/delete/"):
            task_id = parsed.path.split("/")[-1]
            board = load_board()
            board["tasks"] = [t for t in board["tasks"] if t["id"] != task_id and not t["id"].startswith(task_id)]
            save_board(board)
            return self.send_json({"deleted": True})
        self.send_json({"error": "Not found"}, 404)

    def read_body(self):
        cl = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(cl) if cl > 0 else b'{}'
        try:
            return json.loads(body) if body else {}
        except:
            return {}

    def handle_move(self, board, path):
        parts = path.strip("/").split("/")
        task_id = parts[2] if len(parts) > 2 else ""
        new_column = parts[3] if len(parts) > 3 else ""
        for task in board["tasks"]:
            if task["id"] == task_id or task["id"].startswith(task_id):
                task["column"] = new_column
                task["updated_at"] = datetime.now().isoformat()
                if new_column == "in_progress" and not task.get("started_at"):
                    task["started_at"] = datetime.now().isoformat()
                elif new_column == "done":
                    task["completed_at"] = datetime.now().isoformat()
                save_board(board)
                return self.send_json(task)
        self.send_json({"error": "Task not found"}, 404)

    def handle_create_task(self, board, data):
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": data.get("title", "Untitled"),
            "description": data.get("description", ""),
            "skills": data.get("skills", []),
            "priority": data.get("priority", "medium"),
            "tier": data.get("tier", 1),
            "column": data.get("column", "backlog"),
            "assignee": data.get("assignee", "hermes-coo"),
            "parent_id": data.get("parent_id"),
            "template_id": data.get("template_id"),
            "metadata": data.get("metadata", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "time_spent_seconds": 0,
            "attempts": 0,
            "status": "active",
            "tags": data.get("tags", []),
            "blocked_by": data.get("blocked_by", []),
            "subtasks": data.get("subtasks", []),
        }
        board["tasks"].append(new_task)
        save_board(board)
        self.send_json(new_task)

    def handle_template_spawn(self, board, path, data):
        parts = path.strip("/").split("/")
        template_id = parts[2] if len(parts) > 2 else data.get("template_id", "")
        templates = load_templates()
        template = next((t for t in templates if t["id"] == template_id), None)
        if not template:
            return self.send_json({"error": "Template not found"}, 404)
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": template.get("name", "Untitled"),
            "description": template.get("description", ""),
            "skills": template.get("skills", []),
            "priority": template.get("priority", "medium"),
            "tier": template.get("tier", 1),
            "column": data.get("column", "ready"),
            "assignee": template.get("assignee", "hermes-coo"),
            "parent_id": None,
            "template_id": template_id,
            "metadata": {},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "time_spent_seconds": 0,
            "attempts": 0,
            "status": "active",
            "tags": [],
            "blocked_by": [],
            "subtasks": [],
        }
        board["tasks"].append(new_task)
        save_board(board)
        self.send_json(new_task)

    def handle_spawn_agent(self, board, data):
        task_title = data.get("task", "Baby agent task")
        agent_type = data.get("agent", "hermes-coo")
        skills = data.get("skills", [])
        skill_prompts = get_skill_prompt(skills)
        new_task = {
            "id": str(uuid.uuid4())[:8],
            "title": f"[Baby:{agent_type}] {task_title}",
            "description": f"Baby agent spawned for: {task_title}\n\nSkill prompts:\n" + "\n".join(skill_prompts) if skill_prompts else "",
            "skills": skills,
            "priority": data.get("priority", "medium"),
            "tier": 1,
            "column": "in_progress",
            "assignee": agent_type,
            "parent_id": None,
            "template_id": None,
            "metadata": {"spawned_by": "operator", "skill_prompts": skill_prompts},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "time_spent_seconds": 0,
            "attempts": 0,
            "status": "active",
            "tags": ["baby-agent"],
            "blocked_by": [],
            "subtasks": [],
        }
        board["tasks"].append(new_task)
        save_board(board)
        self.send_json(new_task)

    def handle_ai(self, board, data):
        message = data.get("message", "")
        msg_lower = message.lower()
        response = ""

        if "create task" in msg_lower or "add task" in msg_lower:
            response = "Creating task... Use the spawn button or ask me what to create."
        elif "status" in msg_lower:
            cols = {}
            for t in board.get("tasks", []):
                c = t.get("column", "unknown")
                cols[c] = cols.get(c, 0) + 1
            response = f"Board status: {len(board.get('tasks',[]))} total tasks. " + ", ".join(f"{k}:{v}" for k, v in cols.items())
        elif "agent" in msg_lower:
            response = "Available agents: " + ", ".join(a["name"] for a in AGENTS)
        elif "skill" in msg_lower:
            response = "Available skills: " + ", ".join(SKILL_PROMPTS.keys())
        elif "help" in msg_lower:
            response = "I can: create tasks, show status, spawn agents, list skills, move tasks. Try: 'create task: Fix bug' or 'show status'"
        else:
            response = f"Received: '{message}'. I can help with tasks, agents, and skills. Type 'help' for options."

        return self.send_json({"response": response, "timestamp": datetime.now().isoformat()})

    def handle_voice(self, board, data):
        command = data.get("command", "").lower()
        if "create task" in command or "add task" in command:
            title = command.replace("create task", "").replace("add task", "").strip(": ")
            if title:
                new_task = {
                    "id": str(uuid.uuid4())[:8],
                    "title": title,
                    "description": "Created via voice command",
                    "skills": [],
                    "priority": "medium",
                    "tier": 1,
                    "column": "ready",
                    "assignee": "hermes-coo",
                    "parent_id": None,
                    "template_id": None,
                    "metadata": {"source": "voice"},
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "started_at": None,
                    "completed_at": None,
                    "time_spent_seconds": 0,
                    "attempts": 0,
                    "status": "active",
                    "tags": ["voice-created"],
                    "blocked_by": [],
                    "subtasks": [],
                }
                board["tasks"].append(new_task)
                save_board(board)
                return self.send_json({"action": "created", "task": new_task})
        return self.send_json({"action": "unknown", "message": "Try: 'create task [description]'"})

    def send_json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def send_head(self):
        response = super().send_head()
        path = self.path.lstrip("/")
        if path == "" or path.endswith(".html"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        return response

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8088))
    server = ThreadedHTTPServer(("0.0.0.0", port), KanbanHandler)
    logger.info(f"Kanban server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
