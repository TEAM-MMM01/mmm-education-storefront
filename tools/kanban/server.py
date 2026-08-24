#!/usr/bin/env python3
"""HermesOS Kanban Dashboard Server — serves the UI and API."""

import json
import http.server
import ssl
import socket
import socketserver
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import urlparse
import os

import sys
sys.path.insert(0, str(Path(__file__).parent))
from board import (
    _load_board, _save_board, _load_templates, _save_templates,
    move_task, create_task, create_template, spawn_from_template,
    get_agent_tasks, find_best_agent, calculate_expertise_match,
    AGENT_EXPERTISE, COLUMNS, _load_metrics
)

PORT = 8088
HTTPS_PORT = 8443
DASHBOARD_PATH = Path(__file__).parent / "dashboard.html"

# OmniRoute config
OMNIROUTE_BASE = os.environ.get("OMNIROUTE_BASE_URL", "http://localhost:20128/v1")
OMNIROUTE_KEY = os.environ.get("OMNIROUTE_API_KEY", "")
OMNIROUTE_MODEL = os.environ.get("OMNIROUTE_MODEL", "codex/gpt-5.6-sol-medium")


class KanbanHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == "/" or parsed.path == "/dashboard":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_PATH.read_bytes())
            return
        
        if parsed.path == "/api/board":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(_load_board(), default=str).encode())
            return
        
        if parsed.path == "/api/templates":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(_load_templates(), default=str).encode())
            return
        
        if parsed.path == "/api/agents":
            agents = []
            for agent_id, info in AGENT_EXPERTISE.items():
                agents.append({
                    "id": agent_id,
                    "name": info["description"],
                    "skills": info["skills"]
                })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(agents).encode())
            return
        
        if parsed.path == "/api/metrics":
            metrics = _load_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(metrics, default=str).encode())
            return
        
        if parsed.path == "/api/agent-budgets":
            budgets_path = Path(__file__).parent / "agent_budgets.json"
            if budgets_path.exists():
                budgets = json.loads(budgets_path.read_text())
            else:
                budgets = {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(budgets, default=str).encode())
            return
        
        if parsed.path == "/api/agent-heartbeats":
            heartbeats_path = Path(__file__).parent / "agent_heartbeats.json"
            if heartbeats_path.exists():
                heartbeats = json.loads(heartbeats_path.read_text())
            else:
                heartbeats = {}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(heartbeats, default=str).encode())
            return
        
        if parsed.path == "/api/board-summary":
            board = _load_board()
            tasks = board.get("tasks", [])
            summary = {
                "total": len(tasks),
                "by_column": {},
                "by_agent": {},
                "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "by_tier": {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
            }
            for t in tasks:
                col = t.get("column", "backlog")
                summary["by_column"][col] = summary["by_column"].get(col, 0) + 1
                agent = t.get("assignee", "unassigned")
                summary["by_agent"][agent] = summary["by_agent"].get(agent, 0) + 1
                pri = t.get("priority", "medium")
                if pri in summary["by_priority"]:
                    summary["by_priority"][pri] += 1
                tier = t.get("tier", 1)
                if tier in summary["by_tier"]:
                    summary["by_tier"][tier] += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(summary, default=str).encode())
            return
        
        if parsed.path == "/api/agent-pull":
            agent_id = parsed.query.split("=")[-1] if "=" in parsed.query else ""
            if agent_id:
                tasks = get_agent_tasks(agent_id, column="ready") or get_agent_tasks(agent_id, column="backlog")
                if tasks:
                    task = tasks[0]
                    result = move_task(task["id"], "in_progress")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, default=str).encode())
                else:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "no_tasks"}).encode())
            return
        
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        parts = parsed.path.strip("/").split("/")
        
        # Handle /api/move/{taskId}/{column}
        if len(parts) == 4 and parts[0] == "api" and parts[1] == "move":
            task_id = parts[2]
            new_column = parts[3]
            
            if new_column in COLUMNS:
                result = move_task(task_id, new_column)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(result, default=str).encode())
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Invalid column"}')
            return
        
        # Handle /api/move (column in body)
        if len(parts) == 2 and parts[0] == "api" and parts[1] == "move":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""
            
            if body:
                data = json.loads(body)
                task_id = data.get("task_id", "")
                new_column = data.get("column", "")
                
                if new_column in COLUMNS and task_id:
                    result = move_task(task_id, new_column)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(result, default=str).encode())
                else:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b'{"error": "Missing task_id or invalid column"}')
            else:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "No body"}')
            return
        
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "template-spawn":
            template_id = parts[2]
            result = spawn_from_template(template_id)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result, default=str).encode())
            return
        
        if parsed.path == "/api/create-task":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            task = create_task(
                title=body.get("title", "Untitled"),
                description=body.get("description", ""),
                skills=body.get("skills", []),
                priority=body.get("priority", "medium"),
                tier=body.get("tier", 1),
                assignee=body.get("assignee"),
            )
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(task, default=str).encode())
            return
        
        if parsed.path == "/api/spawn-agent":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            agent_type = body.get("type", "")
            task_desc = body.get("task", "")
            
            # Find best agent for the task
            from board import AGENT_EXPERTISE
            best_agent = "hermes-coo"
            if agent_type in AGENT_EXPERTISE:
                best_agent = agent_type
            
            task = create_task(
                title=f"Agent Task: {task_desc[:50]}",
                description=task_desc,
                skills=body.get("skills", []),
                priority=body.get("priority", "medium"),
                tier=body.get("tier", 1),
                assignee=best_agent,
            )
            move_task(task["id"], "in_progress")
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "agent": best_agent,
                "task": task,
                "message": f"Agent {best_agent} spawned and working on: {task_desc[:50]}"
            }, default=str).encode())
            return
        
        if parsed.path == "/api/ai":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            query = body.get("query", "")
            voice = body.get("voice", False)
            
            response = process_ai_query(query)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "response": response,
                "voice": voice
            }).encode())
            return
        
        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def call_omniroute(prompt: str) -> str:
    """Call OmniRoute API for AI reasoning."""
    if not OMNIROUTE_KEY or OMNIROUTE_KEY == "PASTE_YOUR_ENDPOINT_KEY_HERE":
        return ""
    
    try:
        payload = json.dumps({
            "model": OMNIROUTE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0.7
        }).encode()
        
        req = urllib.request.Request(
            f"{OMNIROUTE_BASE}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OMNIROUTE_KEY}"
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"(AI unavailable: {e})"


def process_ai_query(query: str) -> str:
    """Process AI query with reasoning."""
    q = query.lower()
    board = _load_board()
    tasks = board.get("tasks", [])
    
    # Try OmniRoute first for complex queries
    if any(word in q for word in ["why", "how", "should", "recommend", "suggest", "analyze", "explain", "reason"]):
        context = f"Kanban board state: {len(tasks)} tasks. "
        cols = {}
        for t in tasks:
            c = t.get("column", "backlog")
            cols[c] = cols.get(c, 0) + 1
        context += f"Columns: {cols}. "
        high = [t["title"] for t in tasks if t.get("priority") in ("critical", "high") and t.get("column") != "done"]
        if high:
            context += f"High priority: {', '.join(high[:5])}. "
        
        prompt = f"You are Hermes, an AI coo. Board context: {context}\n\nQuestion: {query}\n\nAnswer concisely:"
        ai_response = call_omniroute(prompt)
        if ai_response and "unavailable" not in ai_response:
            return ai_response
    
    # Local pattern matching for quick queries
    if "summary" in q or "status" in q:
        cols = {}
        for t in tasks:
            c = t.get("column", "backlog")
            cols[c] = cols.get(c, 0) + 1
        return (f"Board: {len(tasks)} total | "
                f"Backlog: {cols.get('backlog',0)} | "
                f"Ready: {cols.get('ready',0)} | "
                f"In Progress: {cols.get('in_progress',0)} | "
                f"Review: {cols.get('review',0)} | "
                f"Done: {cols.get('done',0)}")
    
    if "blocked" in q or "stuck" in q:
        blocked = [t for t in tasks if t.get("column") == "blocked"]
        return f"Blocked: {len(blocked)} tasks" if blocked else "No blocked tasks."
    
    if "next" in q or "important" in q or "priority" in q:
        high = [t for t in tasks if t.get("priority") in ("critical", "high") and t.get("column") != "done"]
        if high:
            return "High priority:\n" + "\n".join(f"• {t['title']} ({t['column']})" for t in high[:5])
        return "No high-priority tasks. You're clear!"
    
    if "spawn" in q or "create task" in q:
        return "Use: python3 tools/kanban/board.py create 'task name' -s 'skills' -p priority"
    
    if "agent" in q:
        # Find best agent for mentioned skills
        skills = [s for s in ["trading", "education", "commerce", "code", "debug", "deploy", "voice", "tefa", "shopify"] if s in q]
        if skills:
            best = find_best_agent(skills)
            return f"Best agent for {', '.join(skills)}: {best} ({calculate_expertise_match(best, skills):.0f}% match)"
        return "Available agents: " + ", ".join(AGENT_EXPERTISE.keys())
    
    if "help" in q:
        return ("Commands: summary, next steps, blocked, spawn [agent], "
                "assign [task], agent [skills], help")
    
    # Fall back to OmniRoute for unknown queries
    ai_response = call_omniroute(f"You are Hermes AI. User asks: {query}. Answer concisely about task management.")
    if ai_response and "unavailable" not in ai_response:
        return ai_response
    
    return "Try: summary, next steps, blocked, spawn, or ask me anything!"


class ReuseTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


def main():
    import threading
    
    # Get local IP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except:
        local_ip = "localhost"
    finally:
        s.close()
    
    print(f"🚀 Kanban Dashboard running!")
    print(f"   HTTP:  http://localhost:{PORT}")
    print(f"   HTTPS: https://{local_ip}:{HTTPS_PORT}")
    print(f"   iPad:  Open Safari → https://{local_ip}:{HTTPS_PORT}")
    print(f"\n   Voice works on HTTPS (iPad access)")
    print(f"   Press Ctrl+C to stop")
    
    # Start HTTP server in thread
    httpd = ReuseTCPServer(("0.0.0.0", PORT), KanbanHandler)
    httpd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    http_thread.start()
    
    # Start HTTPS server
    cert_path = Path(__file__).parent / "cert.pem"
    key_path = Path(__file__).parent / "key.pem"
    
    if cert_path.exists() and key_path.exists():
        httpsd = ReuseTCPServer(("0.0.0.0", HTTPS_PORT), KanbanHandler)
        httpsd.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert_path, key_path)
        httpsd.socket = context.wrap_socket(httpsd.socket, server_side=True)
        
        https_thread = threading.Thread(target=httpsd.serve_forever, daemon=True)
        https_thread.start()
        print(f"   HTTPS: ✅ Active on port {HTTPS_PORT}")
    else:
        print(f"   HTTPS: ❌ No SSL certs found")
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        httpd.shutdown()


if __name__ == "__main__":
    main()
