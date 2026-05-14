---
name: upload-task
description: Upload one or more tasks to LUMA (Gabriel's local task manager). Use when the user asks to "add a task to LUMA", "create a LUMA task", "upload tasks to LUMA", or describes work items they want tracked. Parses natural language into LUMA's task schema and sends it to the running LUMA server.
---

# Upload tasks to LUMA

You're helping push tasks into LUMA, a local task manager running at `http://localhost:3000`. The user will describe what they want done; you parse it into LUMA's schema and send it via the helper script.

## LUMA task schema

Each task must be a JSON object with these fields:

| Field | Type | Notes |
| :---- | :--- | :---- |
| `title` | string | **Required.** Short, imperative. e.g. "Draft Q3 report" |
| `desc` | string | Optional longer description. |
| `category` | string | One of: `Praise team`, `Research`, `Meetups`, `Building Selah`, `Manzanita`. Omit if uncertain. |
| `status` | string | One of: `Not Started`, `Up Next`, `In Progress`, `Done`. Defaults to `Not Started`. |
| `due` | string | ISO date `YYYY-MM-DD`. Only set if the user gave a specific due date. |
| `impact` | int 1-5 | 1=negligible, 3=affects multiple tasks, 5=affects everything. Default 3. |
| `urgency` | int 1-5 | 1=whenever, 3=this week, 5=today. Default 3. |
| `effort` | int 1-5 | 1=minutes, 3=half-day, 5=multi-day. Default 3. |
| `link` | string | Optional URL. |
| `recurring` | string | `""`, `daily`, `weekly`, or `multi-weekly`. Default `""`. |
| `recurDays` | string[] | Only when recurring is `weekly`/`multi-weekly`. e.g. `["Mon","Thu"]`. |

## Workflow

1. **Parse** the user's request into one or more task objects. If the request is ambiguous on title vs. description, put the pithy action in `title` and anything extra in `desc`.
2. **Infer categories** conservatively. If the user didn't imply a category, leave it unset.
3. **Resolve relative dates** ("Friday", "next week") to absolute `YYYY-MM-DD` using today's date from the environment.
4. **Call the helper script** to upload each task:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/upload_task.py '<json-task-object>'
```

   Or upload a batch in one call by passing a JSON array:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/upload_task.py '[{...}, {...}]'
```

5. **Confirm** to the user what was uploaded (titles + categories + due dates) in a brief summary. Don't echo the full JSON.

## Error handling

- If the script prints `SERVER_UNREACHABLE`, tell the user the LUMA server isn't running and suggest: `python3 /Users/gabriel/Documents/Claude/Projects/LUMA/LUMA/server.py`
- If the script prints `INVALID_TASK`, re-read the error detail and correct the fields.

## Examples

User: *"Add 'email the board about funding' to LUMA, due Friday, high urgency"*
→ One task: `{"title": "Email the board about funding", "due": "2026-04-24", "urgency": 5, "category": "Meetups"}`

User: *"Upload these three research items..."*
→ Array of three task objects, each with `category: "Research"`.

User: *"Add a daily 15-min stretching reminder"*
→ `{"title": "15-min stretching", "recurring": "daily", "effort": 1, "urgency": 2}`
