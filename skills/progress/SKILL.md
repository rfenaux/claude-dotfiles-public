---
name: progress
description: Unified progress view with intelligent routing. Shows CTM status, task details, and suggests next actions based on context.
async:
  mode: never
  require_sync:
    - status display
    - routing suggestions
context: fork
---

# /progress - Progress & Routing

Unified progress view inspired by GSD's intelligent routing. Shows current state and suggests next actions.

## Trigger

Invoke this skill when:
- User says `/progress`, "progress", "where am I", "what's next"
- User asks about current status or task state
- At session start to orient (complements CTM brief)
- When deciding what to work on next

## Commands

| Command | Action |
|---------|--------|
| `/progress` | Show unified status + routing |
| `/progress [task-id]` | Detailed task progress |
| `/progress --verify` | Run verification checklist |
| `/progress --routing` | Just show routing suggestions |

## Session Tracking

Progress views include session context via `${CLAUDE_SESSION_ID}` (v2.1.9+):
- Links progress snapshots to specific sessions for `/resume` continuity
- Enables "What was I working on in that session?" queries
- Session ID appears in the status box header

## Behavior

### Default View (`/progress`)

```
┌─────────────────────────────────────────────────────────────┐
│  PROGRESS                                                    │
├─────────────────────────────────────────────────────────────┤
│  Current Task: [Task Title]                                  │
│  ID: [task-id] | Status: [active/paused/blocked]            │
│  Progress: 65% ████████████░░░░░░░░                          │
├─────────────────────────────────────────────────────────────┤
│  RECENT ACTIVITY                                             │
│  • [timestamp] Decision: [summary]                           │
│  • [timestamp] File modified: [path]                         │
│  • [timestamp] Checkpoint: [summary]                         │
├─────────────────────────────────────────────────────────────┤
│  QUEUE (3 tasks)                                             │
│  1. [id] Task A (85%) - ready                                │
│  2. [id] Task B (20%) - blocked by X                         │
│  3. [id] Task C (0%) - pending                               │
├─────────────────────────────────────────────────────────────┤
│  SUGGESTED NEXT                                              │
│  → Continue current task (has momentum)                      │
│  OR                                                          │
│  → Switch to Task A (nearly complete)                        │
└─────────────────────────────────────────────────────────────┘
```

### Detailed Task View (`/progress [task-id]`)

```
┌─────────────────────────────────────────────────────────────┐
│  TASK DETAIL: [Task Title]                                   │
├─────────────────────────────────────────────────────────────┤
│  Progress: 65% (manual) / 72% (inferred)                    │
│                                                              │
│  FILES:                                                      │
│  ✓ src/auth.ts (modified 10m ago)                           │
│  ✓ src/login.ts (modified 25m ago)                          │
│  ○ tests/auth.test.ts (not touched)                         │
│                                                              │
│  VERIFY:                                                     │
│  ✓ Requirements covered                                      │
│  ○ Tests passing                                             │
│  ○ Docs updated                                              │
│                                                              │
│  DONE WHEN:                                                  │
│  ○ All tests green                                           │
│  ○ PR approved                                               │
│  ○ Deployed to staging                                       │
│                                                              │
│  DEVIATIONS:                                                 │
│  • [bug] Fixed auth token expiry (15m)                       │
│                                                              │
│  DECISIONS:                                                  │
│  • Use JWT with 15min TTL (2026-02-02)                       │
└─────────────────────────────────────────────────────────────┘
```

### Verification View (`/progress --verify`)

```
┌─────────────────────────────────────────────────────────────┐
│  VERIFICATION CHECKLIST                                      │
├─────────────────────────────────────────────────────────────┤
│  REQUIREMENTS                                                │
│  ✓ [REQ-1] User can login                                   │
│  ✓ [REQ-2] Token refresh works                              │
│  ○ [REQ-3] Logout clears session                            │
│                                                              │
│  FILES COVERAGE                                              │
│  ✓ All planned files modified                                │
│  ⚠ 1 unplanned file touched (deviation logged)              │
│                                                              │
│  TESTS                                                       │
│  ○ Unit tests: not run                                       │
│  ○ Integration tests: not run                                │
│                                                              │
│  OVERALL: 67% verified                                       │
│                                                              │
│  ACTION: Run tests to complete verification                  │
└─────────────────────────────────────────────────────────────┘
```

## Routing Logic

The skill analyzes context and suggests the optimal next action:

### Routing Rules

| Condition | Suggestion |
|-----------|------------|
| Current task has recent activity | "Continue current (has momentum)" |
| Current task blocked | "Switch to unblocked task [id]" |
| Task nearly complete (>80%) | "Complete [task] before switching" |
| Multiple tasks ready | "Prioritize [highest priority task]" |
| All tasks blocked | "Address blockers or start new task" |
| No active tasks | "Start new task with `ctm spawn`" |

### Priority Factors

1. **Momentum** - Recent activity in last 30min gets priority
2. **Completion proximity** - Tasks >80% get completion priority
3. **CTM priority score** - Urgency × value × recency
4. **Blockers** - Blocked tasks deprioritized
5. **Dependencies** - Tasks blocking others get priority

## Integration

### With CTM
- Reads from `~/.claude/ctm/scheduler.json` for queue
- Uses agent data for progress details
- Respects CTM priority scoring

### With Structured Tasks
- Shows files/verify/done fields if present
- Calculates completion from structured criteria
- Highlights unmet verification items

### With Deviations
- Shows recent deviations on task
- Factors deviation time into estimates

## Implementation

When invoked:

1. **Load CTM state**
   ```python
   from scheduler import get_scheduler
   from agents import get_agent, AgentIndex

   scheduler = get_scheduler()
   current_id = scheduler.state.get("current_agent")
   ```

2. **Gather recent activity**
   - Last 5 checkpoints
   - Recent decisions
   - Modified files (from git or task tracking)

3. **Calculate progress**
   - Manual: `state.progress_pct`
   - Inferred: From files touched, verify items, done items

4. **Determine routing**
   - Apply routing rules
   - Consider momentum, completion, priority

5. **Display**
   - Format as bordered box
   - Include routing suggestion

## Example Session

```
User: /progress

┌─────────────────────────────────────────────────────────────┐
│  PROGRESS                                                    │
├─────────────────────────────────────────────────────────────┤
│  Current: Implement JWT Authentication                       │
│  ID: auth-jwt | Status: active | Progress: 65%              │
├─────────────────────────────────────────────────────────────┤
│  RECENT                                                      │
│  • 10m ago: Modified src/auth.ts                            │
│  • 25m ago: Decision - Use 15min token TTL                  │
│  • 30m ago: Deviation - Fixed token refresh bug             │
├─────────────────────────────────────────────────────────────┤
│  QUEUE                                                       │
│  1. [api-rate] API Rate Limiting (0%) - pending             │
│  2. [db-migrate] DB Migration (blocked by api-rate)         │
├─────────────────────────────────────────────────────────────┤
│  → Continue current task (has momentum, 65% complete)        │
└─────────────────────────────────────────────────────────────┘
```

## Related Skills

- `/ctm` - Full task management
- `/deviate` - Handle work deviations
- `/checkpoint` - Manual state capture
- `/focus` - ADHD focus anchoring
