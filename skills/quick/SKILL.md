---
name: quick
description: Ad-hoc task execution without CTM ceremony. For small, self-contained tasks under 5 minutes that don't need cross-session tracking.
async:
  mode: never
  require_sync:
    - task execution
    - completion detection
---

# /quick - Quick Mode

Execute small tasks without CTM overhead. Inspired by GSD's quick mode.

## Trigger

Invoke this skill when:
- User says `/quick`, "quick task", "just quickly"
- Task is small and self-contained (< 5 minutes)
- No need for cross-session tracking
- User wants to avoid context switching ceremony

## Why This Exists

Not everything needs full task management:
- Fixing a typo
- Adding a single log statement
- Quick lookup or calculation
- One-off file edit

CTM is powerful but has overhead. Quick mode provides:
- Immediate execution
- No scheduler updates
- No checkpoint creation
- Optional minimal tracking

## Commands

| Command | Action |
|---------|--------|
| `/quick "task"` | Execute without any tracking |
| `/quick --track "task"` | Execute + minimal CTM record |
| `/quick --done` | Exit quick mode, return to previous context |
| `/quick --list` | Show recent quick tasks (if tracked) |

## Behavior

### Basic Quick Task

```
User: /quick "Fix the typo in README line 42"

Claude: Quick mode activated.

[Reads README.md]
[Fixes typo]
[Shows diff]

Done. Quick task completed.

Returning to previous context...
```

### Tracked Quick Task

```
User: /quick --track "Add debug logging to auth.ts"

Claude: Quick mode activated (tracking enabled).

[Executes task]

Done. Logged to quick tasks:
- 2026-02-02 08:30: Add debug logging to auth.ts ✓

Returning to previous context...
```

### Quick Mode State

When in quick mode:
- Current CTM task is preserved but paused
- No new agent created (unless --track)
- Auto-exits on completion or timeout

## Auto-Exit Triggers

Quick mode automatically exits when:
- Task is completed (success/failure)
- User says "done", "back to", "continue"
- User explicitly starts new CTM task
- 10 minutes elapsed without completion
- User says `/quick --done`

## What Qualifies as "Quick"

Good for quick mode:
- Single file edits
- Typo fixes
- Simple calculations
- Quick lookups
- Adding logs or comments
- Running a single command

NOT good for quick mode:
- Multi-file changes
- Requires research or exploration
- Needs decisions tracked
- Will take > 10 minutes
- Might need to pause and resume

## Integration

### With CTM
- Quick tasks don't interrupt CTM priority queue
- `--track` creates minimal agent (status: completed immediately)
- Previous task auto-resumes after quick task

### With Deviations
- If quick task reveals bigger issue → exit quick mode
- Suggest: "This looks bigger than a quick task. Want to spawn a CTM task?"

## Example Flow

```
[Working on Task: Implement Auth]

User: /quick "check what port the server runs on"

Claude: Quick mode.
Server runs on port 3000 (from config/server.json).
Quick task complete.

[Back to: Implement Auth]

User: /quick --track "fix eslint warning in auth.ts line 15"

Claude: Quick mode (tracked).
[Fixes unused import warning]
Done. Logged.

[Back to: Implement Auth]

User: actually this auth module needs a complete rewrite

Claude: This sounds bigger than a quick task.
Want me to:
1. Spawn a new CTM task for the rewrite?
2. Continue in quick mode anyway?
3. Add to current task scope?
```

## Quick Tasks Log

When using `--track`, tasks are logged to `~/.claude/ctm/quick-tasks.json`:

```json
{
  "tasks": [
    {
      "timestamp": "2026-02-02T08:30:00Z",
      "description": "Fix typo in README line 42",
      "status": "completed",
      "duration_seconds": 45,
      "files_touched": ["README.md"],
      "parent_task": "auth-impl-abc123"
    }
  ],
  "stats": {
    "total": 42,
    "today": 3,
    "avg_duration_seconds": 120
  }
}
```

## Related Skills

- `/ctm` - Full task management
- `/deviate` - Handle larger deviations
- `/focus` - ADHD focus anchoring
- `/progress` - View current state
