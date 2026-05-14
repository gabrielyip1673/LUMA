#!/usr/bin/env python3
"""
LUMA MCP server — stdio transport, JSON-RPC 2.0.

Exposes LUMA task operations as MCP tools. No external dependencies beyond
Python 3.8+ stdlib. Talks to the LUMA HTTP server on localhost:3000.

Tools:
  - upload_task      Create one task in LUMA.
  - upload_tasks     Create a batch of tasks.
  - check_luma       Ping the LUMA server.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "luma"
SERVER_VERSION = "0.2.0"
LUMA_URL = os.environ.get("LUMA_URL", "http://localhost:3000")

VALID_CATEGORIES = {"Infrastructure", "Research", "Networking", "Building", "Learning the Ropes"}
VALID_STATUSES = {"Not Started", "Up Next", "In Progress", "Done"}
VALID_RECURRING = {"", "daily", "weekly", "multi-weekly"}
VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

TASK_PROPERTIES = {
    "title": {"type": "string", "description": "Short, imperative task title. Required."},
    "desc": {"type": "string", "description": "Longer description or notes."},
    "category": {
        "type": "string",
        "enum": sorted(VALID_CATEGORIES) + [""],
        "description": "Leave empty if uncertain.",
    },
    "status": {"type": "string", "enum": sorted(VALID_STATUSES), "default": "Not Started"},
    "due": {"type": "string", "description": "ISO date YYYY-MM-DD. Omit if no due date."},
    "impact": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
    "urgency": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
    "effort": {"type": "integer", "minimum": 1, "maximum": 5, "default": 3},
    "link": {"type": "string", "description": "Optional URL."},
    "recurring": {"type": "string", "enum": sorted(VALID_RECURRING)},
    "recurDays": {
        "type": "array",
        "items": {"type": "string", "enum": sorted(VALID_DAYS)},
        "description": "Only when recurring is weekly/multi-weekly.",
    },
}

TOOLS = [
    {
        "name": "upload_task",
        "description": (
            "Create one task in LUMA (Gabriel's local task manager). "
            "Only `title` is required. Returns the generated task id."
        ),
        "inputSchema": {
            "type": "object",
            "properties": TASK_PROPERTIES,
            "required": ["title"],
        },
    },
    {
        "name": "upload_tasks",
        "description": "Create multiple tasks in LUMA in a single call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": TASK_PROPERTIES,
                        "required": ["title"],
                    },
                }
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "check_luma",
        "description": "Ping the LUMA server to verify it's reachable on localhost:3000.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ---------- stdio helpers ----------

def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def log(*args):
    print(*args, file=sys.stderr, flush=True)


def err(id_, code, message):
    send({"jsonrpc": "2.0", "id": id_, "error": {"code": code, "message": message}})


def ok(id_, result):
    send({"jsonrpc": "2.0", "id": id_, "result": result})


# ---------- task validation ----------

def normalize(task):
    if not isinstance(task, dict):
        return None, "task must be an object"
    title = str(task.get("title", "")).strip()
    if not title:
        return None, "title is required"

    def clamp(v, default):
        try:
            return min(5, max(1, int(v)))
        except (TypeError, ValueError):
            return default

    cat = task.get("category") or ""
    if cat and cat not in VALID_CATEGORIES:
        return None, f"category must be one of {sorted(VALID_CATEGORIES)} or empty"

    status = task.get("status") or "Not Started"
    if status not in VALID_STATUSES:
        return None, f"status must be one of {sorted(VALID_STATUSES)}"

    recurring = task.get("recurring") or ""
    if recurring not in VALID_RECURRING:
        return None, f"recurring must be one of {sorted(VALID_RECURRING)}"

    recur_days = task.get("recurDays") or []
    if not isinstance(recur_days, list) or any(d not in VALID_DAYS for d in recur_days):
        return None, f"recurDays must be a list from {sorted(VALID_DAYS)}"

    due = task.get("due") or ""
    if due:
        try:
            time.strptime(due, "%Y-%m-%d")
        except ValueError:
            return None, "due must be YYYY-MM-DD"

    uid = f"{int(time.time() * 1000)}_{title[:4].replace(' ', '')}"
    return {
        "id": uid,
        "created": int(time.time() * 1000),
        "title": title,
        "desc": str(task.get("desc", "")),
        "category": cat,
        "status": status,
        "due": due,
        "impact": clamp(task.get("impact"), 3),
        "urgency": clamp(task.get("urgency"), 3),
        "effort": clamp(task.get("effort"), 3),
        "dependencies": [],
        "link": str(task.get("link", "")),
        "recurring": recurring,
        "recurDays": recur_days,
    }, None


# ---------- HTTP to LUMA ----------

def http_post(path, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        LUMA_URL + path,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            raw = resp.read().decode("utf-8") or "{}"
            return True, json.loads(raw)
    except urllib.error.URLError as e:
        return False, f"cannot reach LUMA at {LUMA_URL} — is the server running? ({e.reason})"
    except Exception as e:
        return False, f"upload failed: {e}"


def http_get(path):
    try:
        with urllib.request.urlopen(LUMA_URL + path, timeout=3) as resp:
            return True, resp.read().decode("utf-8")
    except urllib.error.URLError as e:
        return False, str(e.reason)
    except Exception as e:
        return False, str(e)


# ---------- tool handlers ----------

def tool_upload_task(args):
    task, verr = normalize(args)
    if verr:
        return text(f"INVALID_TASK: {verr}"), True
    ok_, resp = http_post("/api/inbox", {"tasks": [task]})
    if not ok_:
        return text(resp), True
    return text(f"Queued 1 task in LUMA: '{task['title']}' (id={task['id']}). LUMA will pick it up within ~3s."), False


def tool_upload_tasks(args):
    items = args.get("tasks", [])
    if not isinstance(items, list) or not items:
        return text("INVALID_TASK: 'tasks' must be a non-empty array"), True
    normalized = []
    for i, t in enumerate(items):
        n, verr = normalize(t)
        if verr:
            return text(f"INVALID_TASK: item {i}: {verr}"), True
        normalized.append(n)
    ok_, resp = http_post("/api/inbox", {"tasks": normalized})
    if not ok_:
        return text(resp), True
    titles = ", ".join(f"'{t['title']}'" for t in normalized)
    return text(f"Queued {len(normalized)} tasks in LUMA: {titles}."), False


def tool_check_luma(_args):
    ok_, resp = http_get("/__version")
    if not ok_:
        return text(f"LUMA is NOT reachable at {LUMA_URL}. Start it with: python3 /Users/gabriel/Documents/Claude/Projects/LUMA/LUMA/server.py"), True
    return text(f"LUMA is up at {LUMA_URL} (current version hash: {resp[:8]}...)."), False


TOOL_HANDLERS = {
    "upload_task": tool_upload_task,
    "upload_tasks": tool_upload_tasks,
    "check_luma": tool_check_luma,
}


def text(s):
    return {"content": [{"type": "text", "text": s}]}


# ---------- JSON-RPC dispatch ----------

def handle(req):
    method = req.get("method")
    params = req.get("params") or {}
    id_ = req.get("id")
    is_notification = "id" not in req

    if method == "initialize":
        ok(id_, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })
        return

    if method == "notifications/initialized" or method == "initialized":
        return  # notification, no response

    if method == "tools/list":
        ok(id_, {"tools": TOOLS})
        return

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments") or {}
        handler = TOOL_HANDLERS.get(name)
        if not handler:
            err(id_, -32601, f"unknown tool: {name}")
            return
        try:
            result, is_err = handler(args)
        except Exception as e:
            err(id_, -32603, f"tool '{name}' crashed: {e}")
            return
        payload = dict(result)
        if is_err:
            payload["isError"] = True
        ok(id_, payload)
        return

    if method in ("shutdown", "exit"):
        if not is_notification:
            ok(id_, None)
        if method == "exit":
            sys.exit(0)
        return

    if is_notification:
        return
    err(id_, -32601, f"method not found: {method}")


def main():
    log(f"luma MCP server starting (LUMA_URL={LUMA_URL})")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as e:
            log(f"bad json: {e}")
            continue
        try:
            handle(req)
        except Exception as e:
            log(f"handler crashed: {e}")
            if "id" in req:
                err(req["id"], -32603, str(e))


if __name__ == "__main__":
    main()
