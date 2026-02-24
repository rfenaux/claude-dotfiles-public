---
name: deviate
description: Declare and handle work deviations (bugs, architectural changes, scope creep, blockers) with appropriate routing and tracking.
async:
  mode: never
  require_sync:
    - deviation classification
    - user decision
    - task routing
context: fork
---

# /deviate - Deviation Handler

Handle work deviations gracefully when implementation diverges from plan. Inspired by GSD (Get Shit Done) deviation rules.

## Trigger

Invoke this skill when:
- User explicitly says `/deviate`, "deviation", "deviate"
- Work diverges from original plan (bug found, architectural change needed)
- Scope creep detected ("also need", "while we're here")
- Blocker encountered that prevents progress

## Why This Exists

During implementation, reality often differs from plan:
- Bugs discovered that need immediate attention
- Architectural assumptions prove wrong
- Scope expands beyond original intent
- External blockers halt progress

Without explicit deviation handling, these situations cause:
- Context thrashing (jumping between tasks)
- Lost decisions (why did we change direction?)
- Incomplete original work (started but never finished)

## Deviation Types

| Type | Trigger Patterns | Default Action |
|------|------------------|----------------|
| `bug` | "found bug", "this breaks", "error", "exception" | Ask: fix now or spawn task? |
| `architectural` | "need to rethink", "fundamentally wrong", "redesign" | Pause current, escalate to user |
| `scope_creep` | "also need", "while we're here", "one more thing" | Park idea via `/focus park` |
| `blocker` | "can't proceed", "blocked by", "waiting on" | Add to CTM blockers, suggest switch |

## Commands

| Command | Action |
|---------|--------|
| `/deviate` | Auto-detect type from recent context |
| `/deviate bug` | Declare bug deviation |
| `/deviate bug --fix` | Fix immediately, track deviation |
| `/deviate bug --spawn` | Spawn separate task for fix |
| `/deviate architectural` | Pause and escalate |
| `/deviate scope` | Park the idea |
| `/deviate blocker "reason"` | Log blocker, suggest alternatives |
| `/deviate --list` | Show recent deviations |

## Behavior

### Bug Deviation
```
/deviate bug

┌─────────────────────────────────────────────────────────────┐
│  BUG DEVIATION DETECTED                                      │
│                                                              │
│  Context: [brief description of bug]                         │
│                                                              │
│  Options:                                                    │
│  1. Fix now (--fix) - Quick fix, track as deviation         │
│  2. Spawn task (--spawn) - Create separate CTM task         │
│  3. Ignore - Continue with known issue                       │
│                                                              │
│  Recommendation: [based on severity/time estimate]           │
└─────────────────────────────────────────────────────────────┘
```

**If --fix chosen:**
1. Log deviation to CTM current agent
2. Fix the bug
3. Track time spent
4. Resume original work
5. Decision recorded: "Deviated to fix: [bug description]"

**If --spawn chosen:**
1. Create new CTM agent for bug fix
2. Add dependency: original task blocked by bug task
3. Switch to bug task
4. After fix, auto-switch back to original

### Architectural Deviation
```
/deviate architectural

┌─────────────────────────────────────────────────────────────┐
│  ARCHITECTURAL DEVIATION                                     │
│                                                              │
│  This requires rethinking the approach.                      │
│                                                              │
│  Current assumption: [what we thought]                       │
│  Reality: [what we discovered]                               │
│                                                              │
│  Actions:                                                    │
│  1. Pause current task                                       │
│  2. Document the issue                                       │
│  3. Discuss new approach                                     │
│                                                              │
│  [Awaiting your input on new direction]                      │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
1. Pause current CTM agent
2. Record architectural issue in agent context
3. Create decision prompt for DECISIONS.md
4. Wait for user direction before proceeding

### Scope Creep Deviation
```
/deviate scope

┌─────────────────────────────────────────────────────────────┐
│  SCOPE CREEP DETECTED                                        │
│                                                              │
│  Idea: [the new thing user mentioned]                        │
│                                                              │
│  This is outside current task scope.                         │
│                                                              │
│  Options:                                                    │
│  1. Park it (recommended) - Add to future ideas              │
│  2. Add to current - Expand scope (not recommended)          │
│  3. Spawn task - Create separate CTM task                    │
└─────────────────────────────────────────────────────────────┘
```

**If parked:**
1. Add to CTM agent's "parked_ideas" field
2. Optionally add to project backlog
3. Continue with original scope
4. Message: "Parked: [idea]. Will revisit after current task."

### Blocker Deviation
```
/deviate blocker "waiting on API credentials"

┌─────────────────────────────────────────────────────────────┐
│  BLOCKER LOGGED                                              │
│                                                              │
│  Blocker: waiting on API credentials                         │
│  Added to: [current agent] blockers                          │
│                                                              │
│  Options:                                                    │
│  1. Switch to another task (recommended)                     │
│  2. Work on unblocked parts                                  │
│  3. Wait (do nothing)                                        │
│                                                              │
│  Available tasks: [list unblocked CTM agents]                │
└─────────────────────────────────────────────────────────────┘
```

**Behavior:**
1. Add blocker to CTM agent
2. Mark agent as "blocked" status
3. Show alternative tasks
4. Suggest context switch

## Integration with CTM

Deviations are tracked in CTM agent context:

```json
{
  "context": {
    "deviations": [
      {
        "type": "bug",
        "timestamp": "2026-02-02T08:30:00Z",
        "description": "Auth token expiring prematurely",
        "action": "fix",
        "time_spent_minutes": 15,
        "resolved": true
      }
    ],
    "parked_ideas": [
      "Add rate limiting (scope creep, parked 2026-02-02)"
    ]
  }
}
```

## Auto-Detection

When `/deviate` is called without a type, analyze recent conversation for:

1. **Bug signals:** Error messages, "doesn't work", "broken", stack traces
2. **Architectural signals:** "wrong approach", "need to rethink", "fundamentally"
3. **Scope signals:** "also", "while we're at it", "one more thing", "might as well"
4. **Blocker signals:** "waiting", "can't", "blocked", "depends on"

If detection confidence < 70%, ask user to specify type.

## Decision Recording

All deviations that change direction are auto-offered for DECISIONS.md:

> "Deviation recorded. Want me to add this to DECISIONS.md?"
>
> **T-XXX: [Deviation summary]**
> - Type: [bug/architectural/scope/blocker]
> - Original plan: [what we were doing]
> - Deviation: [what happened]
> - Resolution: [how we handled it]

## Configuration

See `~/.claude/config/deviation-rules.json` for pattern customization.

## Example Session

```
User: hmm this auth flow is completely wrong, we need sessions not JWTs

Claude: I detect an architectural deviation.

/deviate architectural

┌─────────────────────────────────────────────────────────────┐
│  ARCHITECTURAL DEVIATION                                     │
│                                                              │
│  Current assumption: JWT-based authentication                │
│  Reality: Session-based auth is required                     │
│                                                              │
│  This requires rethinking the approach.                      │
│                                                              │
│  Actions taken:                                              │
│  1. Paused current task                                      │
│  2. Logged architectural issue                               │
│                                                              │
│  Want me to record this decision and discuss the new         │
│  session-based approach?                                     │
└─────────────────────────────────────────────────────────────┘
```

## Related Skills

- `/focus` - For parking ideas and managing attention
- `/ctm` - Task management integration
- `/checkpoint` - Session state preservation
- `/progress` - View current state including deviations
