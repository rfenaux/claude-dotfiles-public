---
name: status-bundle-update
description: Consolidate 4 manual status update steps into one command - CTM progress, status report, task list, and checkpoint.
async:
  mode: never
  require_sync:
    - CTM updates
    - user confirmation
---

# /status-bundle - Bundled Status Update

End-of-work-block ritual that consolidates 4 manual steps into 1 command. Found in 6+ sessions across Rescue and Forsee-Power projects as a recurring manual pattern that costs 5-10 minutes per occurrence.

## Trigger

Invoke this skill when:
- User says `/status-bundle`, "update status", "ship update", "end of day update"
- End of significant work block
- Before session end when meaningful work was completed
- Before meetings requiring status visibility

## Why This Exists

Status updates currently require 4 separate actions that happen at least once per work session:
1. Updating CTM task progress (manual % + decisions + blockers)
2. Updating the project status report file
3. Updating task lists / todos
4. Creating a CTM checkpoint for session recovery

Bundling eliminates the "did I forget to checkpoint?" problem and ensures status is always consistent across all tracking systems.

## Commands

| Command | Action |
|---------|--------|
| `/status-bundle` | Run full 4-step bundle |
| `/status-bundle --quick` | CTM progress + checkpoint only (skip report) |
| `/status-bundle --report` | Generate status report only |

## Workflow

### Step 1: Update CTM Progress
- Read current CTM task state via `ctm progress`
- Update progress percentage based on work completed
- Add new decisions via `ctm context add --decision`
- Add new blockers via `ctm context add --blocker`
- Update next actions

### Step 2: Update Status Report
- If project has a status report file (STATUS.md, status-report.md), update it
- Content: current phase, blockers, completed items, next steps, hours estimate
- If no report exists, offer to create one from template

### Step 3: Update Task List
- Mark completed tasks in CTM or project task tracking
- Add newly discovered tasks from this work block
- Update priorities based on work done and new information

### Step 4: Create Checkpoint
- Run `ctm checkpoint` to snapshot current state
- Enables clean session recovery if context is lost

## Output Format

```
Status Bundle Updated:
  CTM: [task name] — [progress]% (+X% this session)
  Decisions: [N] new decisions recorded
  Blockers: [N] active ([M] new, [K] resolved)
  Report: Updated [file] with [N] changes
  Tasks: [completed] done, [new] added, [total] remaining
  Checkpoint: Saved at [timestamp]
```

## Integration

- **CTM**: `ctm progress`, `ctm context add`, `ctm checkpoint`
- **DECISIONS.md**: Records decisions found during update
- **SESSIONS.md**: Appends session summary if significant
- **Status report**: Project-specific status document
- **`/deviate`**: If blocker found during update, routes to deviation handler
