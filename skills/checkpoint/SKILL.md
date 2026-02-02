---
name: checkpoint
description: Manual session checkpointing with structured context capture. Summarizes current state, records to CTM, and enables clean session breaks.
async:
  mode: never
  require_sync:
    - interactive session
    - context preservation
---

# /checkpoint - Session Checkpoint

Manual checkpoint creation for long sessions. Captures current context, records to CTM, and prepares for clean breaks or continuations.

## Trigger

Invoke this skill when:
- User says "/checkpoint", "checkpoint", "save state"
- Session at 2h/4h/6h mark (per Session Health Protocol)
- User says "I need a break", "stepping away", "save progress"
- Before context compaction is imminent
- User asks to preserve current work state

## Why This Exists

Meta-analysis revealed only 0.3% of sessions have manual checkpoints, causing context loss and repeated explanations. This skill provides structured checkpointing to increase capture rate to 10+ per week.

## Behavior

When invoked:

### 1. Context Summary
Generate a brief summary of:
- **Active task**: What we're working on
- **Current state**: Where we are in the task
- **Recent decisions**: Key choices made this session
- **Pending items**: What's not yet resolved

### 2. CTM Recording
Execute:
```bash
ctm checkpoint --force
```

### 3. Decision Check
Review conversation for unrecorded decisions:
- Check for trigger phrases: "we decided", "let's go with", "switching to"
- If found, offer: "I found X decisions not yet recorded. Add to DECISIONS.md?"

### 4. Confirmation
Respond with:
```
✅ Checkpoint saved.

**Context preserved:**
- Task: [current task]
- State: [current state]
- Decisions: [count] recorded

Ready to continue or take a break?
```

## Integration

Works with:
- **CTM**: Uses `ctm checkpoint` for persistent storage
- **DECISIONS.md**: Offers to record pending decisions
- **Session Health Protocol**: Auto-prompted at 2h/4h/6h marks

## Commands

```bash
/checkpoint           # Full checkpoint with context capture
/checkpoint quick     # Just CTM checkpoint, no summary
/checkpoint force     # Checkpoint even if recent one exists
```

## Files

| Path | Purpose |
|------|---------|
| `~/.claude/ctm/checkpoints/*.json` | Checkpoint data |
| `project/.claude/context/DECISIONS.md` | Decision records |
| `project/.claude/context/SESSIONS.md` | Session summaries |

## Example

```
User: /checkpoint

Claude: ✅ Checkpoint saved.

**Context preserved:**
- Task: Implementing meta-analysis config optimizations
- State: CLAUDE.md updated (6/6), skills creation in progress
- Decisions: 2 recorded (Response format structure, Agent pattern detection)

I found 1 decision not yet recorded:
> "We're using parallel worker spawning for session analysis"

Record to DECISIONS.md? [Y/n]

Ready to continue or take a break?
```
