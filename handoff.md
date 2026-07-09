# LUMA Project Handoff Document

**Date:** 2026-07-08
**Project:** LUMA — Local Unified Management App
**Repository:** https://github.com/gabrielyip1673/LUMA
**GitHub Pages:** https://gabrielyip1673.github.io/LUMA/
**Local URL:** http://localhost:3000

---

## Project Overview

LUMA is a zero-dependency, single-file task manager built with vanilla HTML, CSS, and JavaScript. All data lives in the browser's `localStorage` — no accounts, no cloud, no frameworks. The entire app is contained in a single `LUMA.html` file (~2100+ lines).

---

## Project Structure

```
/Users/gabriel/Documents/Claude/Projects/LUMA/
├── .gitignore
├── README.md
├── index.html                    # GitHub Pages redirect → LUMA/LUMA.html
├── LUMA/
│   ├── LUMA.html                 # The entire app (single file)
│   ├── server.py                 # Live-reload dev server + inbox API (port 3000)
│   ├── .luma_token               # Bearer token for API auth (excluded from git)
│   ├── bg.avif                   # Background image (God Emperor Doom, 1400x700, 136KB)
│   ├── weekly_job_search_routine.html  # Reference schedule (imported into Job Routine)
│   └── server.log                # Server logs (excluded from git)
├── luma-plugin/
│   ├── .claude-plugin/plugin.json  # Plugin manifest (name: luma, v0.1.0)
│   ├── README.md
│   ├── mcp/luma_mcp_server.py      # MCP server with upload_task, upload_tasks, check_luma
│   ├── scripts/upload_task.py      # CLI helper to upload tasks
│   └── skills/upload-task/SKILL.md # Claude Code skill definition
└── handoff.md                    # This file
```

---

## Views (5 total + Job Routine)

1. **Priority View** — Tasks ranked by weighted score: `(impact * 2) + (urgency * 3) + (6 - effort)`. Highest priority floats to top.
2. **Kanban Board** — Drag-and-drop columns: Not Started, Up Next, In Progress, Done. Clicking empty space in a column opens new task modal with that status pre-set.
3. **Thread View** — 7-day grid with category rows and day columns. Tasks sorted by priority within each cell. Rows are draggable to reorder categories. Row order persists in localStorage (`luma_thread_order`).
4. **Calendar View** — Monthly calendar showing tasks by due date. Drag to reschedule. Click a day to add a task on that date. Bypasses the 7-day filter so all tasks show regardless of distance from today.
5. **Job Routine** — Structured daily/weekly schedule with checkboxes that reset every Sunday (week-based localStorage key). Steps can be exported as LUMA tasks with two-way sync.

---

## Task Features

- **Scoring:** Impact, urgency, effort ratings (1-5). Default for new tasks is **2** for all three.
- **Categories:** Color-coded groups with the following current configuration:
  - `Praise team` — `#10b981` (green)
  - `ETC` — `#6b7280` (gray)
  - `Personal Life` — `#ec4899` (pink)
  - `Building` — `#8b5cf6` (purple)
  - `Work` — `#3b82f6` (blue)
- **Recurring Tasks:** Daily, weekly, or multi-weekly recurrence with specific day selection. Completing a recurring task auto-creates the next occurrence.
- **Dependencies:** Link tasks together to track what blocks what. Dependency-blocked tasks show orange left border.
- **Search & Filtering:** Full-text search across titles and descriptions, filter by category or status.
- **7-Day Window Filter:** By default, only tasks due within 7 days are shown (except in calendar view). Selecting "all tasks" sort option bypasses this.

---

## Color Scheme / Theming

CSS variables defined in `:root`:
```css
--bg: #f5f4f0;            /* Page background */
--surface: #fafaf7;        /* Surface elements (eggshell white) */
--surface-2: #f0efeb;      /* Secondary surface */
--border: #e0dfda;         /* Borders */
--text: #2a2e2a;           /* Primary text (dark) */
--text-dim: #6f7468;       /* Dimmed text */
--accent: #4a6b6f;         /* Accent color (teal/sage) */
--accent-glow: rgba(74, 107, 111, 0.15);  /* Accent glow */
--accent-dim: #36504f;     /* Darker accent */
--success: #6b8e6b;        /* Success color */
```

- Background image (God Emperor Doom) is base64-encoded directly in CSS on the `main` element
- Background uses `cover no-repeat fixed` sizing to scale with viewport
- UI elements use `rgba(250, 250, 247, 0.95)` translucent backgrounds with `backdrop-filter: blur(8px)`
- Header/tabs bar is fully opaque (`background: var(--surface)`)
- Calendar header has same translucent eggshell white background as calendar cells

---

## Server (server.py)

- **Port:** 3000
- **Framework:** Python 3.8+ stdlib only (`http.server`), ~145 lines
- **Live Reload:** Injects a script into LUMA.html that polls `GET /__version` (MD5 hash) and auto-refreshes on change
- **Inbox API:**
  - `POST /api/inbox` — Accepts tasks (requires bearer token via `Authorization` header)
  - `GET /api/inbox` — Drains pending tasks (no auth, polled by browser every 3 seconds)
  - `GET /__version` — Returns MD5 hash of LUMA.html for live-reload
- **Token:** Stored in `.luma_token` file or `LUMA_TOKEN` env var
  - Current token value: `njUuQmylswgrEPi5nkPwCWPTaBwHOpU6USsFUsSnb6c`
- **Note:** Server must be manually started each session. macOS TCC blocks LaunchAgents from accessing `~/Documents`, so auto-start via LaunchAgent doesn't work without granting Full Disk Access to python3.
- **Start command:** `python3 /Users/gabriel/Documents/Claude/Projects/LUMA/LUMA/server.py &`

---

## Job Routine (Current Configuration)

The Job Routine tab contains a structured weekly job search schedule with these tasks:

### Daily (Mon-Fri):
- Apply to 10 targeted listings (founding GTM / BizOps / Founders Associate at sub-50-person companies)
- Update networking conversations in APHRA
- Update rejections and interview progress in APHRA

### Mon/Wed/Fri:
- Send 2 cold DMs
- Update Joseph on progress

### Monday Only:
- Search for a networking event

### Sat-Sun:
- Full off / rest

The routine resets every Sunday using a week-based localStorage key (`luma_jr_<year>_<week>`).

---

## Claude Code Plugin (luma-plugin/)

Exposes LUMA as MCP tools inside Claude Code:
- `upload_task` — Create a single task
- `upload_tasks` — Batch create tasks
- `check_luma` — Verify server is running

**Note:** The plugin scripts (`upload_task.py` and `luma_mcp_server.py`) need to be updated to send the bearer token with requests (known pending issue).

---

## GitHub Setup

- **Repo:** `gabrielyip1673/LUMA` (public)
- **GitHub Pages:** Enabled, deploys from `main` branch (legacy mode, not workflow). Root `index.html` redirects to `LUMA/LUMA.html`.
- **Git user:** `gabrielyip1673`
- **.gitignore excludes:** `.luma_token`, `.DS_Store`, `__pycache__/`, `*.pyc`, `server.log`, `.vscode/`, `.idea/`, `.claude/settings.local.json`, `*.xlsx`, `*.pages`, `*.webp`

---

## Key Implementation Details

### Drag-and-Drop Systems
- **Kanban:** Cards draggable between columns to change status
- **Thread View:** Two separate drag systems using different `dataTransfer` types:
  - `application/luma-task` — Drag individual tasks between cells (changes date/category)
  - `application/luma-row` — Drag entire category rows to reorder vertically
- **Calendar:** Tasks draggable between days to reschedule

### Date Picker
Custom popup calendar replacing native `<input type="date">`. Functions: `dpOpen()`, `dpClose()`, `dpRender()`, `dpSelectDate(dateStr)`. Today's date highlighted with darker font.

### localStorage Keys
- `luma_tasks_v4` — All task data
- `luma_thread_order` — Thread view category row order
- `luma_jr_<year>_<week>` — Job Routine checkbox states (resets weekly)

### Click-to-Add Task
- **Calendar:** Click empty day space → new task with that date pre-filled
- **Thread:** Click empty cell → new task with date + category pre-filled
- **Kanban:** Click empty column space → new task with that status pre-filled

---

## Changes Made in This Session

1. **Removed 5 lunch break entries** from Job Routine (all days)
2. **Created LaunchAgent** for auto-start — failed due to macOS TCC restrictions on `~/Documents` access; removed the plist
3. **Port change attempt (3000 → 3002)** — Reverted because localStorage is tied to origin, causing all tasks to disappear
4. **Pushed to GitHub** — Force-pushed to existing `gabrielyip1673/LUMA` repo
5. **Created README.md** — Project overview, setup, API docs
6. **Set up GitHub Pages** — Legacy deploy from main branch with root index.html redirect
7. **Changed accent color to red** — Then reverted back to original teal/sage (`#4a6b6f`)
8. **Background scaling** — Changed from `100% auto` to `cover` so image scales with viewport
9. **Kanban click-to-add** — Clicking empty space in a kanban column opens new task modal with that column's status pre-set
10. **Thread view priority sorting** — Tasks within each category cell sorted by priority score (highest first)
11. **Default scoring changed** — New tasks default to 2 (was 3) for impact, urgency, and effort
12. **Job Routine replaced** — Updated to simplified daily/weekly structure focused on applications, APHRA updates, cold DMs, and Joseph check-ins; "Apply to 5 roles" entries
13. **Added then removed EdPursuit category** — Added with amber color `#f59e0b`, then fully removed
14. **Calendar month header** — Added translucent eggshell white background to match other calendar elements
15. **Calendar view filter fix** — Calendar view now bypasses the 7-day window filter so tasks with any due date are visible on the calendar

---

## Known Issues / Pending Work

1. **Plugin auth:** `upload_task.py` and `luma_mcp_server.py` in the luma-plugin need to send the bearer token with POST requests (currently would get 401)
2. **Server persistence:** No auto-start mechanism. Server must be manually started each session (`python3 server.py &`). LaunchAgent approach blocked by macOS TCC.
3. **Duplicate root files:** There are orphaned `LUMA.html` and `server.py` files in the project root (outside `/LUMA/`) that are old copies and remain untracked by git.

---

## User Context

- **User:** Gabriel (`gabrielyip1673` on GitHub)
- **Job search focus:** Founding GTM / BizOps / Founders Associate roles at sub-50-person companies
- **Tools mentioned:** APHRA (job application tracker), LinkedIn, Ashby
- **Accountability partner:** Joseph (Mon/Wed/Fri check-ins)
- **Background image preference:** God Emperor Doom (Marvel) with translucent UI overlay
- **Color preference:** Eggshell white surfaces, teal/sage accent (reverted from red)
