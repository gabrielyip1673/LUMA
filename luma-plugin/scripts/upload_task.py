#!/usr/bin/env python3
"""
Upload one or more tasks to the local LUMA server.

Usage:
  upload_task.py '<json-object-or-array>'

Prints one of:
  OK <count>             - tasks queued successfully
  SERVER_UNREACHABLE     - LUMA server not responding on localhost:3000
  INVALID_TASK: <detail> - task failed schema validation
"""
import json
import sys
import time
import urllib.request
import urllib.error

LUMA_URL = "http://localhost:3000/api/inbox"
VALID_CATEGORIES = {"Infrastructure", "Research", "Networking", "Building", "Learning the Ropes"}
VALID_STATUSES = {"Not Started", "Up Next", "In Progress", "Done"}
VALID_RECURRING = {"", "daily", "weekly", "multi-weekly"}
VALID_DAYS = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}


def normalize(task):
    """Validate and fill defaults. Returns (task_or_None, error_or_None)."""
    if not isinstance(task, dict):
        return None, "Task must be a JSON object"

    title = str(task.get("title", "")).strip()
    if not title:
        return None, "title is required"

    def clamp(v, default):
        try:
            n = int(v)
            return min(5, max(1, n))
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
    normalized = {
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
    }
    return normalized, None


def main():
    if len(sys.argv) < 2:
        print("INVALID_TASK: missing JSON argument")
        sys.exit(1)

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        print(f"INVALID_TASK: bad JSON - {e}")
        sys.exit(1)

    items = payload if isinstance(payload, list) else [payload]
    normalized = []
    for i, item in enumerate(items):
        n, err = normalize(item)
        if err:
            print(f"INVALID_TASK: item {i}: {err}")
            sys.exit(1)
        normalized.append(n)

    body = json.dumps({"tasks": normalized}).encode("utf-8")
    req = urllib.request.Request(
        LUMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status in (200, 201, 204):
                print(f"OK {len(normalized)}")
                return
            print(f"INVALID_TASK: server returned {resp.status}")
            sys.exit(1)
    except urllib.error.URLError:
        print("SERVER_UNREACHABLE")
        sys.exit(1)
    except Exception as e:
        print(f"INVALID_TASK: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
