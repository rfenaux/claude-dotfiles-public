# Agent Context Protocol (ACP) - Global

> **Created:** 2025-12-19
> **Version:** 1.0
> **Scope:** All projects using Claude Code
> **Author:** Raphaël Fenaux

---

## Purpose

This protocol ensures parallel agents can execute independently without context exhaustion by:
1. **Externalizing context** to `.md` files instead of accumulating in memory
2. **Enabling auto-compaction** through file-based state management
3. **Providing resumability** if agents are interrupted
4. **Isolating agent workspaces** so parallel agents don't interfere

**Works with any project** - workspaces are created in the current project directory.

---

## Quick Start

### For Orchestrators (Main Claude Instance)

When launching parallel agents with the Task tool:

```markdown
## Include in agent prompt:

### Agent Context Protocol - MANDATORY

Workspace: .agent-workspaces/{task-id}/

1. **First action**: Create workspace and initialize state files
2. **Every 3-5 tool calls**: Update AGENT_STATE.md and PROGRESS.md
3. **Log files read**: Append to SOURCES.md with key excerpts
4. **On completion**: Write OUTPUT.md with deliverables

CRITICAL: Write to files frequently. Do NOT accumulate context in memory.
```

### For Agents (Subagents)

Follow this lifecycle:
1. Create workspace directory
2. Initialize state files
3. Update files every 3-5 tool calls
4. Write OUTPUT.md when done

---

## Architecture

### Workspace Location
```
{project-root}/.agent-workspaces/{task-id}/
```

**task-id format:** `{agent-name}-{YYYYMMDD}-{HHMM}`
- Example: `erd-generator-20251219-1630`
- Example: `kb-synthesizer-20251219-1645`

### File Structure
```
.agent-workspaces/
├── {task-id-1}/
│   ├── AGENT_STATE.md    # Working memory, current position
│   ├── PROGRESS.md       # Task checklist with completion status
│   ├── OUTPUT.md         # Final deliverable (signals completion)
│   └── SOURCES.md        # Files read with key excerpts
├── {task-id-2}/
│   └── ...
```

### File Purposes

| File | Purpose | When Updated |
|------|---------|--------------|
| `AGENT_STATE.md` | Current context, key findings, next actions | Every 3-5 tool calls |
| `PROGRESS.md` | Subtask checklist with [x]/[~]/[ ] status | Each subtask completion |
| `OUTPUT.md` | Final output for orchestrator | At task completion |
| `SOURCES.md` | Files read with excerpts (prevents re-reading) | When reading files |

---

## Agent Lifecycle

### Phase 1: Initialization

```bash
# Agent's first actions:
mkdir -p .agent-workspaces/{task-id}
```

Then create initial files:

**AGENT_STATE.md:**
```markdown
# Agent State: {Task Name}

> **Task ID:** {task-id}
> **Started:** {timestamp}
> **Status:** active

## Task
{Original task description}

## Current Position
Starting task execution

## Key Findings
(none yet)

## Next Actions
1. {First step}
```

**PROGRESS.md:**
```markdown
# Progress: {Task Name}

> **Last Updated:** {timestamp}

## Subtasks
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Completion: 0/3 (0%)
```

### Phase 2: Execution

**Every 3-5 tool calls**, update state files:

```markdown
# Update AGENT_STATE.md:
- Add key findings discovered
- Update current position
- Revise next actions

# Update PROGRESS.md:
- Mark completed items [x]
- Mark in-progress items [~]
- Update completion percentage
```

**When reading files**, add to SOURCES.md:
```markdown
### {file-path}
- **Relevant for:** {why this file matters}
- **Key excerpt:** (max 500 chars)
```

### Phase 3: Auto-Compaction (If Context Low)

When context approaches limits:

1. Write comprehensive summary to AGENT_STATE.md
2. Ensure PROGRESS.md is current
3. Signal: `"AGENT COMPACT NEEDED - Resume from .agent-workspaces/{task-id}/"`

A new agent instance can then resume by reading the workspace.

### Phase 4: Completion

Write **OUTPUT.md**:
```markdown
# Output: {Task Name}

> **Completed:** {timestamp}

## Summary
{2-3 sentence summary}

## Deliverables Created
- `{path}` - {description}

## Files Modified
- `{path}` - {what changed}

## Key Decisions
| Decision | Rationale |
|----------|-----------|
| {Decision} | {Why} |
```

Mark all PROGRESS.md items as [x].

---

## Orchestrator Instructions

### Generating Task IDs

```javascript
// JavaScript example
const taskId = `${agentName}-${new Date().toISOString().slice(0,10).replace(/-/g,'')}-${new Date().toTimeString().slice(0,5).replace(':','')}`;
// Result: "erd-generator-20251219-1630"
```

### Agent Prompt Template

Include this in every parallel agent prompt:

```markdown
## Agent Context Protocol - MANDATORY

**Task ID:** {task-id}
**Workspace:** .agent-workspaces/{task-id}/

You MUST follow file-based context management:

1. **Initialize** (First action):
   ```bash
   mkdir -p .agent-workspaces/{task-id}
   ```
   Then create AGENT_STATE.md with task description and PROGRESS.md with checklist.

2. **During execution** (Every 3-5 tool calls):
   - Update AGENT_STATE.md with key findings and current position
   - Update PROGRESS.md with completed/in-progress items
   - Log files you read to SOURCES.md with key excerpts (max 500 chars each)

3. **Reference files instead of re-reading**:
   - Check SOURCES.md before reading the same file twice
   - Use excerpts from SOURCES.md when possible

4. **On completion**:
   - Write OUTPUT.md with summary and deliverables list
   - Mark all PROGRESS.md items as [x]

**CRITICAL:** Do NOT accumulate context in memory. Write to files frequently.
This prevents context exhaustion and enables resumability.
```

### Monitoring Agents

```bash
# Check if agent completed (OUTPUT.md exists)
test -f .agent-workspaces/{task-id}/OUTPUT.md && echo "Complete"

# Check progress percentage
grep "Completion:" .agent-workspaces/{task-id}/PROGRESS.md

# Read final output
cat .agent-workspaces/{task-id}/OUTPUT.md
```

### Resuming Interrupted Agents

```markdown
## Resume Task: {task-id}

Resume from workspace: .agent-workspaces/{task-id}/

1. Read AGENT_STATE.md for current position and context
2. Read PROGRESS.md for completed/pending subtasks
3. Read SOURCES.md for files already processed
4. Continue from where the previous agent left off
5. Follow Agent Context Protocol for updates
```

---

## Helper Script

Create this in any project or globally:

```bash
#!/bin/bash
# check_agents.sh - Check status of parallel agents

WORKSPACE_DIR=".agent-workspaces"

if [ ! -d "$WORKSPACE_DIR" ]; then
    echo "No agent workspaces in current directory."
    exit 0
fi

echo "=== Agent Workspaces ==="
for TASK_DIR in "$WORKSPACE_DIR"/*; do
    [ -d "$TASK_DIR" ] || continue
    TASK_ID=$(basename "$TASK_DIR")

    if [ -f "$TASK_DIR/OUTPUT.md" ]; then
        echo "✅ $TASK_ID - COMPLETED"
    elif [ -f "$TASK_DIR/AGENT_STATE.md" ]; then
        PROGRESS=$(grep "Completion:" "$TASK_DIR/PROGRESS.md" 2>/dev/null || echo "unknown")
        echo "🔄 $TASK_ID - IN PROGRESS ($PROGRESS)"
    else
        echo "⏳ $TASK_ID - INITIALIZING"
    fi
done
```

---

## Best Practices

### Do
✅ Generate unique task-id for each agent invocation
✅ Include full ACP instructions in agent prompts
✅ Check OUTPUT.md to determine completion
✅ Use SOURCES.md to avoid re-reading files
✅ Update state files every 3-5 tool calls

### Don't
❌ Reuse task-ids across different agent runs
❌ Skip the workspace initialization
❌ Let agents accumulate context in memory
❌ Forget to include ACP instructions in prompts
❌ Check agent status by reading their internal context

---

## Cleanup

Old workspaces can be cleaned up periodically:

```bash
# Remove workspaces older than 7 days
find .agent-workspaces -type d -mtime +7 -exec rm -rf {} +

# Or remove all completed workspaces
for dir in .agent-workspaces/*/; do
    [ -f "${dir}OUTPUT.md" ] && rm -rf "$dir"
done
```

---

## Integration with .gitignore

Add to project `.gitignore`:
```
.agent-workspaces/
```

---

## Examples

### Example 1: Launching ERD Generator

```markdown
## Task ID: erd-generator-20251219-1630

Generate an ERD for the customer data model.

## Agent Context Protocol - MANDATORY
(Include full protocol instructions here)

## Task
Read the data model documentation and create a Mermaid ERD diagram.
```

### Example 2: Parallel Document Enrichment

Launch multiple agents simultaneously:
```
Task 1: enrich-part-i-20251219-1600
Task 2: enrich-part-ii-20251219-1600
Task 3: enrich-part-iii-20251219-1600
```

Each agent works in isolated workspace, no context conflicts.

### Example 3: Resuming After Interruption

```markdown
## Resume: erd-generator-20251219-1630

The previous agent was interrupted. Resume the task.

Read workspace: .agent-workspaces/erd-generator-20251219-1630/
- AGENT_STATE.md has current position and findings
- PROGRESS.md shows completed subtasks
- SOURCES.md has files already processed

Continue from saved state. Follow Agent Context Protocol.
```

---

**End of Agent Context Protocol**

---

## Cross-References

| Related | Purpose |
|---------|---------|
| [CDP_PROTOCOL.md](CDP_PROTOCOL.md) | Base delegation protocol |
| [CTM_GUIDE.md](CTM_GUIDE.md) | Task management integration |
| [AGENTS_INDEX.md](AGENTS_INDEX.md) | Agent catalog and capabilities |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | Full architecture overview |
