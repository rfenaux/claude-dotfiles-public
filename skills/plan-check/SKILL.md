---
name: plan-check
description: Verify current work against task plan. Warns when editing files not in the task's files list or deviating from verification criteria.
async:
  mode: never
  require_sync:
    - plan verification
    - deviation detection
context: fork
---

# /plan-check - Plan Verification

Verify current work aligns with task plan. Inspired by GSD's plan-checker loop.

## Trigger

Invoke this skill when:
- User says `/plan-check`, "check plan", "am I on track"
- Before major file changes to verify alignment
- When uncertain if work is within scope
- After completing a section to verify coverage

## Why This Exists

It's easy to drift from the original plan:
- Editing files not in scope
- Missing verification steps
- Forgetting completion criteria
- Scope creep without awareness

Plan-check provides a checkpoint to ensure alignment.

## Commands

| Command | Action |
|---------|--------|
| `/plan-check` | Full verification against current CTM task |
| `/plan-check files` | Check only file coverage |
| `/plan-check verify` | Check only verification items |
| `/plan-check done` | Check only completion criteria |
| `/plan-check [file]` | Check if specific file is in plan |

## Behavior

### Full Verification (`/plan-check`)

```
┌─────────────────────────────────────────────────────────────┐
│  PLAN CHECK: [Task Title]                                    │
├─────────────────────────────────────────────────────────────┤
│  FILES (3/4)                                                 │
│  ✓ src/auth.ts (in plan, modified)                          │
│  ✓ src/login.ts (in plan, modified)                         │
│  ○ tests/auth.test.ts (in plan, not touched)                │
│  ⚠ src/utils.ts (NOT in plan, was modified)                 │
├─────────────────────────────────────────────────────────────┤
│  VERIFY (1/3)                                                │
│  ✓ Tests pass                                                │
│  ○ No lint errors                                            │
│  ○ Type check clean                                          │
├─────────────────────────────────────────────────────────────┤
│  DONE WHEN (0/2)                                             │
│  ○ PR merged                                                 │
│  ○ Deployed to staging                                       │
├─────────────────────────────────────────────────────────────┤
│  OVERALL: 67% aligned                                        │
│                                                              │
│  ⚠ WARNING: 1 file modified outside plan                    │
│  → Use /deviate scope to acknowledge, or add to plan        │
└─────────────────────────────────────────────────────────────┘
```

### File Check (`/plan-check files`)

```
User: /plan-check files

┌─────────────────────────────────────────────────────────────┐
│  FILE COVERAGE                                               │
├─────────────────────────────────────────────────────────────┤
│  PLANNED FILES:                                              │
│  ✓ src/auth.ts - modified 10m ago                           │
│  ✓ src/login.ts - modified 25m ago                          │
│  ○ tests/auth.test.ts - not touched                         │
│                                                              │
│  UNPLANNED MODIFICATIONS:                                    │
│  ⚠ src/utils.ts - modified 5m ago                           │
│  ⚠ package.json - modified 15m ago                          │
│                                                              │
│  STATUS: 2 unplanned files modified                          │
└─────────────────────────────────────────────────────────────┘
```

### Single File Check (`/plan-check src/new-file.ts`)

```
User: /plan-check src/new-file.ts

┌─────────────────────────────────────────────────────────────┐
│  FILE CHECK: src/new-file.ts                                 │
│                                                              │
│  ⚠ NOT IN PLAN                                               │
│                                                              │
│  This file is not in the current task's files list.         │
│                                                              │
│  Options:                                                    │
│  1. Add to plan: ctm files add [id] src/new-file.ts         │
│  2. Acknowledge deviation: /deviate scope                    │
│  3. Continue anyway (not recommended)                        │
└─────────────────────────────────────────────────────────────┘
```

## Integration

### With CTM
- Reads task.files, task.verify, task.done_when from current agent
- Uses git status to detect modifications
- Compares planned vs actual file changes

### With Deviations
- Unplanned modifications trigger deviation suggestion
- Can auto-log as scope_creep deviation

### With Progress
- `/progress --verify` uses plan-check internally
- Contributes to progress percentage calculation

## Data Sources

### From CTM Agent
```json
{
  "task": {
    "files": [
      {"path": "src/auth.ts", "action": "modify", "status": "pending"},
      {"path": "tests/auth.test.ts", "action": "create", "status": "pending"}
    ],
    "verify": [
      {"check": "Tests pass", "status": "pending"},
      {"check": "No lint errors", "status": "pending"}
    ],
    "done_when": [
      {"condition": "PR merged", "status": "pending"}
    ]
  }
}
```

### From Git
```bash
git status --porcelain  # Modified files
git diff --name-only    # Changed files
```

## Updating Plan

If files need to be added to plan:

```bash
# Add file to current task
ctm files add [id] src/new-file.ts

# Mark verification item as done
ctm verify check [id] "Tests pass"

# Mark completion criterion as done
ctm done check [id] "PR merged"
```

## When to Use

**Good times to plan-check:**
- Before committing (are all planned files covered?)
- After significant work session
- When about to edit a new file
- Before marking task complete

**Skip plan-check when:**
- In quick mode (`/quick`)
- Task has no structured fields
- Exploratory work (not implementation)

## Related Skills

- `/deviate` - Handle deviations from plan
- `/progress` - Overall task progress
- `/ctm` - Task management
- `/quick` - Skip plan tracking
