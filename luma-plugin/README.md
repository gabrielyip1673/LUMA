# LUMA Plugin

A Claude Code plugin that lets you upload tasks to LUMA (your local task manager) from any Claude session — including Cowork/Agent Teams.

## What it does

Exposes a skill `/luma:upload-task`. You describe tasks in natural language; the skill parses them into LUMA's schema and POSTs them to the running LUMA server. LUMA polls the server inbox every ~3 seconds and imports new tasks into its localStorage automatically.

## Architecture

```
Claude  ──(skill)──>  upload_task.py  ──HTTP POST──>  server.py /api/inbox
                                                              │
LUMA.html  <──HTTP GET──────────────────────────── /api/inbox (drains queue)
   │
   └──> localStorage (luma_tasks_v4)
```

## Install

1. Start the LUMA server:

   ```bash
   python3 /Users/gabriel/Documents/Claude/Projects/LUMA/LUMA/server.py
   ```

2. Open LUMA in a browser: http://localhost:3000

3. Load the plugin in Claude Code (dev mode):

   ```bash
   claude --plugin-dir /Users/gabriel/Documents/Claude/Projects/LUMA/luma-plugin
   ```

   Or install persistently via a marketplace. See Claude Code plugin docs.

## Usage

In any Claude session:

> "Add 'Prep slides for Friday's talk' to LUMA — category Building, due 2026-04-24, high urgency"

Claude invokes `/luma:upload-task`, which parses the request, calls the helper script, and LUMA picks the task up within a few seconds.

Batch uploads work too:

> "Upload these to LUMA: 1) Review PR #42 2) Email the vendor 3) Book the venue for May 10"

## Files

- `.claude-plugin/plugin.json` — manifest
- `skills/upload-task/SKILL.md` — instructions Claude follows when invoked
- `scripts/upload_task.py` — validates and POSTs tasks to the inbox

## Server additions

The server exposes:

- `POST /api/inbox` — accepts `{"tasks": [...]}`; queues tasks
- `GET /api/inbox` — returns and clears the queue (called by LUMA.html)

## Error signals from the script

- `OK <count>` — success
- `SERVER_UNREACHABLE` — server isn't running on :3000
- `INVALID_TASK: <detail>` — schema problem
