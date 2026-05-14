# LUMA

A single-file local task manager built with vanilla HTML, CSS, and JavaScript. All data lives in your browser's `localStorage` — no accounts, no cloud, no dependencies.

![Views](https://img.shields.io/badge/views-5-c0392b) ![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen) ![Single File](https://img.shields.io/badge/single_file-HTML-blue)

## Views

- **Priority** — ranked task list sorted by impact, urgency, and effort scores
- **Kanban** — drag-and-drop board with Not Started, Up Next, In Progress, and Done columns
- **Thread** — week-long grid organized by category rows and day columns
- **Calendar** — monthly calendar with task due dates, drag to reschedule
- **Job Routine** — structured daily schedule with checkboxes that reset weekly

## Features

- Drag-and-drop across all views (reorder tasks, change status, reschedule dates, reassign categories)
- Custom categories with color coding
- Task scoring (impact / urgency / effort, 1-5 scale)
- Recurring tasks (daily, weekly, multi-weekly with day selection)
- Dependency tracking between tasks
- Full-text search and category/status filtering
- Inbox API for receiving tasks from external tools
- Live-reload dev server

## Quick Start

```bash
# Start the server
python3 LUMA/server.py

# Open in browser
open http://localhost:3000
```

Requires Python 3.8+. No `pip install` needed — stdlib only.

## Project Structure

```
LUMA/
  LUMA.html                  # The entire app (single file)
  server.py                  # Live-reload server + inbox API
  bg.avif                    # Background image asset
  weekly_job_search_routine.html  # Reference schedule (imported into Job Routine)
luma-plugin/
  mcp/luma_mcp_server.py     # MCP server for Claude Code integration
  scripts/upload_task.py     # CLI helper to upload tasks
  skills/upload-task/SKILL.md # Claude Code skill definition
```

## Inbox API

The server exposes a task inbox so external tools can push tasks into LUMA:

```bash
# Upload a task
curl -X POST http://localhost:3000/api/inbox \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"tasks": [{"title": "Review PR", "category": "Work", "urgency": 4}]}'
```

LUMA polls `GET /api/inbox` every 3 seconds and imports new tasks automatically.

Authentication is configured via a `.luma_token` file or `LUMA_TOKEN` environment variable.

## Claude Code Plugin

The `luma-plugin/` directory contains an MCP server that exposes LUMA as a tool inside Claude Code:

- `upload_task` — create a single task
- `upload_tasks` — batch create tasks
- `check_luma` — verify the server is running

## Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS, single file, no build step
- **Storage**: `localStorage` (all data stays on your machine)
- **Server**: Python `http.server` (stdlib only, ~145 lines)
- **Protocol**: MCP (Model Context Protocol) for AI tool integration
