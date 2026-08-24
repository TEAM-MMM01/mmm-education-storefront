#!/usr/bin/env python3
"""Kanban board server — auto-advancing, SSE real-time, full endpoints."""
import json
import os
import uuid
import time
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import logging
import queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler('/tmp/kanban.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

BOARD_PATH = Path.home() / ".hermes-mac" / "kanban" / "board.json"
HISTORY_PATH = Path.home() / ".hermes-mac" / "kanban" / "history.json"
TEMPLATES_PATH = Path(__file__).parent / "templates.json"
AGENTS_PATH = Path.home() / ".hermes-mac" / "kanban" / "agents.json"
DASHBOARD_DIR = Path(__file__).parent

# ── CST Timezone ──
CST = timezone(timedelta(hours=-6))  # CST = UTC-6

def now_cst():
    return datetime.now(CST)

def fmt_cst_12(dt=None):
    """Format datetime as CST 12-hour. e.g. '4:15 PM'"""
    if dt is None:
        dt = now_cst()
    return dt.strftime("%-I:%M %p")

def fmt_cst_full(dt=None):
    """Format as 'Aug 24, 4:15 PM CST'"""
    if dt is None:
        dt = now_cst()
    return dt.strftime("%b %-d, %-I:%M %p")

# ── SSE ──
sse_clients: list[queue.Queue] = []
sse_lock = threading.Lock()

# ── Activity Log ──
activity_log: list[dict] = []
ACTIVITY_MAX = 100

# ── Task History ──
task_history: list[dict] = []
HISTORY_MAX = 500

def load_history():
    global task_history
    try:
        if HISTORY_PATH.exists():
            task_history = json.loads(HISTORY_PATH.read_text())
    except Exception as e:
        logger.error(f"History load error: {e}")
        task_history = []

def save_history():
    try:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_PATH.write_text(json.dumps(task_history[-HISTORY_MAX:], indent=2, default=str))
    except Exception as e:
        logger.error(f"History save error: {e}")

def record_history(task_id: str, title: str, from_col: str, to_col: str, agent: str, priority: str = "", tier: int = 1):
    """Record a task movement in history."""
    entry = {
        "task_id": task_id,
        "title": title,
        "from_column": from_col,
        "to_column": to_col,
        "agent": agent,
        "priority": priority,
        "tier": tier,
        "timestamp": now_cst().isoformat(),
        "display_time": fmt_cst_12(),
    }
    task_history.append(entry)
    if len(task_history) > HISTORY_MAX:
        task_history = task_history[-HISTORY_MAX:]
    save_history()

def get_history_metrics():
    """Calculate completion metrics from history."""
    completed = [h for h in task_history if h["to_column"] == "done"]
    total_moves = len(task_history)

    # Average time to complete
    avg_time = "—"
    if completed:
        times = []
        for h in completed:
            # Find when task started (first move to in_progress)
            task_id = h["task_id"]
            start = next((x for x in task_history if x["task_id"] == task_id and x["to_column"] == "in_progress"), None)
            if start:
                try:
                    t1 = datetime.fromisoformat(start["timestamp"])
                    t2 = datetime.fromisoformat(h["timestamp"])
                    diff = (t2 - t1).total_seconds() / 60
                    if diff > 0:
                        times.append(diff)
                except:
                    pass
        if times:
            avg = sum(times) / len(times)
            if avg < 60:
                avg_time = f"{avg:.0f}m"
            else:
                avg_time = f"{avg/60:.1f}h"

    return {
        "total_completed": len(completed),
        "total_moves": total_moves,
        "avg_time": avg_time,
    }

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

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# ── Activity helpers ──

def add_activity(kind: str, text: str, task_id: str = ""):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "kind": kind,
        "text": text,
        "task_id": task_id,
    }
    activity_log.append(entry)
    if len(activity_log) > ACTIVITY_MAX:
        activity_log.pop(0)
    broadcast_sse({"type": "activity", "entry": entry})

def broadcast_sse(data: dict):
    msg = f"data: {json.dumps(data, default=str)}\n\n"
    dead = []
    with sse_lock:
        for q in sse_clients:
            try:
                q.put_nowait(msg)
            except queue.Full:
                dead.append(q)
        for q in dead:
            sse_clients.remove(q)

# ── Board I/O ──

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
    return [SKILL_PROMPTS[s] for s in skills if s in SKILL_PROMPTS]

# ── AUTO-ADVANCE ENGINE ──

# Time thresholds per column (seconds) — tasks older than this auto-advance
ADVANCE_THRESHOLDS = {
    "ready":        45,   # 45s in ready → move to in_progress
    "in_progress":  90,   # 90s working → move to review
    "review":       60,   # 60s in review → move to done
}

# Max tasks to advance per cycle per column (prevents mass-jump)
MAX_ADVANCE_PER_CYCLE = 2

def auto_advance_tick():
    """Run every 30s. Advance tasks that have been in their column long enough."""
    try:
        board = load_board()
        now = datetime.now()
        changed = False
        advances = 0

        # Sort tasks by priority within each column
        for col, threshold in ADVANCE_THRESHOLDS.items():
            candidates = []
            for t in board["tasks"]:
                if t["column"] != col:
                    continue
                # Skip blocked tasks
                if t.get("blocked_by"):
                    continue
                # Skip tasks with tier >= 3 (need human approval)
                if t.get("tier", 1) >= 3:
                    continue

                updated = t.get("updated_at") or t.get("created_at")
                if not updated:
                    continue
                try:
                    updated_dt = datetime.fromisoformat(updated)
                except:
                    continue

                elapsed = (now - updated_dt).total_seconds()
                if elapsed >= threshold:
                    candidates.append((t, elapsed, PRIORITY_ORDER.get(t.get("priority", "medium"), 2)))

            # Sort by priority (critical first), then by wait time (longest first)
            candidates.sort(key=lambda x: (x[2], -x[1]))

            for task, elapsed, _ in candidates[:MAX_ADVANCE_PER_CYCLE]:
                next_col = {
                    "ready": "in_progress",
                    "in_progress": "review",
                    "review": "done",
                }.get(col)

                if not next_col:
                    continue

                old_col = task["column"]
                task["column"] = next_col
                task["updated_at"] = now.isoformat()
                task["attempts"] = task.get("attempts", 0) + 1

                if next_col == "in_progress" and not task.get("started_at"):
                    task["started_at"] = now.isoformat()
                elif next_col == "done":
                    task["completed_at"] = now.isoformat()
                    task["time_spent_seconds"] = task.get("time_spent_seconds", 0) + elapsed

                agent_name = task.get("assignee", "unassigned")
                add_activity("task",
                    f"#{task['id'][:8]} {task['title'][:40]} → {next_col} ({agent_name})",
                    task["id"])
                record_history(task["id"], task["title"], old_col, next_col, agent_name,
                    task.get("priority", ""), task.get("tier", 1))
                logger.info(f"Auto-advance: {task['id'][:8]} {old_col} → {next_col}")
                changed = True
                advances += 1

        if changed:
            save_board(board)
            broadcast_sse({"type": "board", "tasks": board["tasks"]})

        if advances > 0:
            add_activity("system", f"Advanced {advances} task(s) this cycle")

    except Exception as e:
        logger.error(f"Auto-advance error: {e}")

def auto_advance_loop():
    """Background thread: tick every 30s."""
    while True:
        time.sleep(30)
        auto_advance_tick()

# ── HTTP Handler ──

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

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

        if path == "/api/activity":
            return self.send_json({"activity": list(reversed(activity_log[-50:]))})

        if path == "/api/history":
            return self.send_json({"history": task_history[-100:], "metrics": get_history_metrics()})

        if path == "/api/events":
            return self.handle_sse()

        if self.path == "/":
            self.path = "/dashboard.html"

        super().do_GET()

    def handle_sse(self):
        """Server-Sent Events endpoint for real-time updates."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = queue.Queue(maxsize=50)
        with sse_lock:
            sse_clients.append(q)

        try:
            # Send initial board state
            board = load_board()
            init_msg = f"data: {json.dumps({'type': 'board', 'tasks': board['tasks']}, default=str)}\n\n"
            self.wfile.write(init_msg.encode())
            self.wfile.flush()

            while True:
                try:
                    msg = q.get(timeout=30)
                    self.wfile.write(msg.encode())
                    self.wfile.flush()
                except queue.Empty:
                    # Send keepalive
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with sse_lock:
                if q in sse_clients:
                    sse_clients.remove(q)

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
                old_col = task["column"]
                task["column"] = new_column
                task["updated_at"] = datetime.now().isoformat()
                if new_column == "in_progress" and not task.get("started_at"):
                    task["started_at"] = datetime.now().isoformat()
                elif new_column == "done":
                    task["completed_at"] = datetime.now().isoformat()
                save_board(board)
                add_activity("task", f"#{task['id'][:8]} moved {old_col} → {new_column}", task["id"])
                record_history(task["id"], task["title"], old_col, new_column,
                    task.get("assignee", "unassigned"), task.get("priority", ""), task.get("tier", 1))
                broadcast_sse({"type": "board", "tasks": board["tasks"]})
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
        add_activity("task", f"Created: {new_task['title'][:40]} → {new_task['column']}", new_task["id"])
        broadcast_sse({"type": "board", "tasks": board["tasks"]})
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
        add_activity("task", f"Spawned from template: {new_task['title'][:30]}", new_task["id"])
        broadcast_sse({"type": "board", "tasks": board["tasks"]})
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
        add_activity("agent", f"Agent {agent_type} spawned for: {task_title[:30]}", new_task["id"])
        broadcast_sse({"type": "board", "tasks": board["tasks"]})
        self.send_json(new_task)

    def handle_ai(self, board, data):
        message = data.get("message", data.get("query", ""))
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
                add_activity("task", f"Voice-created: {title[:40]}", new_task["id"])
                broadcast_sse({"type": "board", "tasks": board["tasks"]})
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

    # Start auto-advance background thread
    advancer = threading.Thread(target=auto_advance_loop, daemon=True)
    advancer.start()
    logger.info("Auto-advance engine started (30s tick)")

    add_activity("system", "Kanban server started — auto-advance engine active")

    # Load task history
    load_history()
    logger.info(f"Loaded {len(task_history)} history entries")

    server = ThreadedHTTPServer(("0.0.0.0", port), KanbanHandler)
    logger.info(f"Kanban server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
