---
name: cdp-delegate
description: Enforces the Cognitive Delegation Protocol when spawning sub-agents. Internal helper skill.
model: haiku
tools:
  - Read
  - Write
user-invocable: false
---

# CDP Delegate Skill

Enforces the Cognitive Delegation Protocol when spawning sub-agents. Use this skill to delegate tasks while keeping the primary context lightweight.

## Trigger

Invoke when:
- Delegating a task to a sub-agent
- User says "delegate", "offload", "background task"
- Task is substantial enough to warrant isolation

## Protocol

When delegating, you MUST follow this exact sequence:

### Step 1: Create Workspace

```bash
TASK_ID="{agent-name}-$(date +%Y%m%d-%H%M%S)"
WORKSPACE=".agent-workspaces/${TASK_ID}"
mkdir -p "${WORKSPACE}"
```

### Step 2: Write HANDOFF.md

Create `${WORKSPACE}/HANDOFF.md` with this structure:

```markdown
# Task Handoff

**Task ID:** {task-id}
**Agent:** {agent-name}
**Created:** {timestamp}

## Task
[Clear, specific task description - what needs to be done]

## Context
[Essential background - ONLY what's needed to execute]
[Do NOT dump entire conversation history]

## Key Files
- `/path/to/file.ext` — Why it's relevant
- `/path/to/other.ext` — What to look for

## Constraints
- [Scope limits]
- [Must use X, avoid Y]
- [Time constraints if any]

## Expected Deliverables
- [ ] Deliverable 1
- [ ] Deliverable 2

## Return Requirements
[What primary needs back in OUTPUT.md]
[Be specific about what information matters]
```

### Step 3: Spawn Agent

Use the Task tool with:
- `subagent_type`: The appropriate agent name
- `prompt`: "Read HANDOFF.md at {workspace}/HANDOFF.md and execute the task. Write your results to OUTPUT.md in the same directory."
- `run_in_background`: true (for async agents)

### Step 4: On Agent Completion

When agent completes:
1. Read ONLY `${WORKSPACE}/OUTPUT.md`
2. Extract the "Summary" and "For Primary" sections
3. Report these to the user
4. Do NOT read the full agent transcript or WORK.md

## OUTPUT.md Expected Format

Agents will write:

```markdown
# Task Complete: [Title]

**Status:** completed | blocked | needs-input
**Duration:** [time]
**Agent:** [agent-name]

## Summary
[1-3 sentences]

## Deliverables
| File | Description |
|------|-------------|
| `path` | What it does |

## Decisions Made
- **[Decision]**: [Rationale]

## For Primary
[Critical info for main conversation]

## Files Modified
- `path` — What changed
```

## Context Isolation Rules

**DO pass to agent:**
- Specific task requirements
- Relevant file paths
- Constraints and scope
- Expected output format

**DO NOT pass to agent:**
- Full conversation history
- Unrelated context
- Your reasoning process
- Other tasks in progress

## Example Usage

**User request:** "Analyze the codebase structure and create a summary"

**CDP Delegate flow:**

1. Create workspace: `.agent-workspaces/worker-20260115-112605/`

2. Write HANDOFF.md:
```markdown
# Task Handoff

**Task ID:** worker-20260115-112605
**Agent:** worker
**Created:** 2026-01-15 11:26:05

## Task
Analyze the codebase structure and create a summary document.

## Context
User wants to understand the project organization.

## Key Files
- `/project/` — Root directory to analyze

## Constraints
- Focus on high-level structure
- Don't read every file, sample representative ones

## Expected Deliverables
- [ ] Markdown summary of codebase structure

## Return Requirements
- Directory tree overview
- Key components identified
- Architecture patterns observed
```

3. Spawn worker agent with HANDOFF.md path

4. On completion, read OUTPUT.md and report summary to user

## Integration

This skill integrates with:
- **CTM**: Use `ctm delegate` for tracked delegation
- **ACP**: For long-running tasks, agent adds PROGRESS.md
- **RAG**: OUTPUT.md can be indexed for future reference

## Quick Reference

```
1. mkdir -p .agent-workspaces/{task-id}/
2. Write HANDOFF.md (minimal context)
3. Spawn agent → agent reads HANDOFF.md
4. Agent works in isolation
5. Agent writes OUTPUT.md
6. Read OUTPUT.md ONLY (not full transcript)
7. Report summary to user
```
