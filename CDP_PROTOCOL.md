# Cognitive Delegation Protocol (CDP)

> Created: 2026-01-08 | Version: 1.0

## Overview

CDP defines how the primary conversation delegates work to sub-agents while keeping context lightweight. It uses **function-call semantics**:

- **Input (HANDOFF.md)** — Parameters the agent needs
- **Processing** — Agent works in isolated context
- **Output (OUTPUT.md)** — Structured return value

The primary conversation never sees the agent's full working context — only the return value.

---

## Why CDP?

| Problem | CDP Solution |
|---------|--------------|
| Primary context bloat | Work happens in isolated agent context |
| Lost agent knowledge | OUTPUT.md captures essential results |
| Unclear handoffs | HANDOFF.md defines exact requirements |
| Inconsistent returns | Standardized OUTPUT.md format |

---

## Workspace Structure

Every delegated task gets a workspace:

```
.agent-workspaces/
└── {task-id}/
    ├── HANDOFF.md      # Input: What agent needs to know
    ├── WORK.md         # Scratchpad: Agent's working notes (optional)
    └── OUTPUT.md       # Output: Return value for primary
```

**Task ID format:** `{agent-name}-{timestamp}` (e.g., `worker-20260108-134852`)

---

## HANDOFF.md Specification

Written by primary before spawning agent:

```markdown
# Task Handoff

## Task
[Clear, specific task description]

## Context
[Essential background — only what's needed to execute]

## Key Files
- `/path/to/file.py` — Why it's relevant
- `/path/to/config.json` — What to look for

## Constraints
- [Time/scope limits]
- [Must use X, avoid Y]
- [Dependencies]

## Expected Deliverables
- [ ] Script that does X
- [ ] Updated config
- [ ] Test coverage

## Return Requirements
[What primary needs to know in OUTPUT.md]
```

### Handoff Principles

1. **Minimal context** — Only what agent needs, not everything you know
2. **Explicit files** — List specific files, not "check the codebase"
3. **Clear deliverables** — What success looks like
4. **Return requirements** — What primary needs back

---

## OUTPUT.md Specification

Written by agent upon completion:

```markdown
# Task Complete: [Short Title]

**Status:** completed | blocked | needs-input
**Duration:** [time spent]
**Agent:** [agent-name]

## Summary
[1-3 sentences — what was done, high-level outcome]

## Deliverables
| File | Description |
|------|-------------|
| `/path/to/script.py` | Does X when Y |
| `/path/to/config.json` | Configuration for Z |

## Decisions Made
- **[Decision]**: [Rationale]
- **[Decision]**: [Rationale]

## For Primary
[Critical information the main conversation must know]
[Gotchas, warnings, next steps, blockers]

## Files Modified
- `path/to/file.py` — Added function X
- `path/to/other.py` — Fixed bug in Y
```

### Output Principles

1. **Summary first** — Primary should understand outcome in 3 sentences
2. **Deliverables table** — Clear paths + what each file does
3. **Decisions explicit** — Choices made that affect future work
4. **For Primary section** — Anything the main conversation MUST know

---

## WORK.md (Optional)

Agent's scratchpad for complex tasks:

```markdown
# Working Notes

## Progress
- [x] Step 1: Analyzed requirements
- [x] Step 2: Created initial implementation
- [ ] Step 3: Testing

## Observations
- Found that X requires Y
- API has rate limit of Z

## Blockers
- Need clarification on X

## Scratch
[Code snippets, debug output, temporary notes]
```

This file stays in agent scope — primary never reads it.

---

## Protocol Flow

```
PRIMARY                           AGENT
   │                                │
   │ 1. Create workspace            │
   │ 2. Write HANDOFF.md            │
   │ 3. Spawn agent ────────────────▶
   │                                │ 4. Read HANDOFF.md
   │                                │ 5. Execute task
   │                                │ 6. Write OUTPUT.md
   │ ◀──────────────────────────────│ 7. Signal complete
   │ 8. Read OUTPUT.md              │
   │ 9. Continue with results       │
   │                                │
```

---

## Integration with CTM

### Spawning with CDP

```bash
# Via CTM (recommended)
ctm delegate "Implement login feature" --agent worker

# Creates:
# - Agent in CTM queue
# - Workspace with HANDOFF.md template
# - Switches to agent context
```

### Completion Flow

When agent completes:
1. Agent writes OUTPUT.md
2. CTM marks agent complete
3. CTM extracts decisions to project memory
4. Primary notified with OUTPUT.md path

### Tracking

```bash
ctm list --delegated     # Show all delegated tasks
ctm show <id> --output   # Read OUTPUT.md for task
```

---

## Agent Compliance

All agents MUST follow CDP when spawned via delegation:

### Required Behaviors

1. **Read HANDOFF.md first** — Understand task before starting
2. **Stay in scope** — Only do what's in HANDOFF.md
3. **Write OUTPUT.md last** — Before signaling completion
4. **Use standard format** — Follow OUTPUT.md specification

### Agent Frontmatter

Agents should declare CDP compliance:

```yaml
---
name: my-agent
cdp:
  version: 1.0
  input_requirements:
    - task description
    - key files
  output_includes:
    - deliverables
    - decisions
---
```

---

## Example: Script Creation

### Primary delegates:

**HANDOFF.md:**
```markdown
# Task Handoff

## Task
Create a Python script that processes CSV files and outputs JSON.

## Context
We have customer data in CSV format that needs to be converted for the new API.

## Key Files
- `/project/data/sample.csv` — Example input format
- `/project/api/schema.json` — Required output schema

## Constraints
- Use pandas for CSV parsing
- Output must validate against schema
- Handle missing fields gracefully

## Expected Deliverables
- [ ] `scripts/csv_to_json.py` — Main conversion script
- [ ] `tests/test_conversion.py` — Test coverage

## Return Requirements
- How to run the script
- Any edge cases discovered
- Performance notes for large files
```

### Agent returns:

**OUTPUT.md:**
```markdown
# Task Complete: CSV to JSON Converter

**Status:** completed
**Duration:** 12 minutes
**Agent:** worker

## Summary
Created a CSV to JSON conversion script using pandas. Handles missing fields by
using schema defaults. Includes CLI interface and test suite with 94% coverage.

## Deliverables
| File | Description |
|------|-------------|
| `scripts/csv_to_json.py` | Main script — run with `python csv_to_json.py input.csv output.json` |
| `tests/test_conversion.py` | Test suite — run with `pytest tests/` |

## Decisions Made
- **Used Click for CLI**: Better UX than argparse, already in project deps
- **Batch processing for large files**: Chunked reads to handle files >1GB
- **Schema validation on output**: Fails fast if output doesn't match schema

## For Primary
- Script handles files up to 2GB tested, beyond that consider streaming
- Missing fields get `null` unless schema has default
- Run `pip install click` if not installed (added to requirements.txt)

## Files Modified
- `scripts/csv_to_json.py` — New file (187 lines)
- `tests/test_conversion.py` — New file (94 lines)
- `requirements.txt` — Added click dependency
```

### Primary receives:

Only the OUTPUT.md content — not the 50+ tool calls the agent made to write and test the script.

---

## Native Behavior

CDP is the **default** for all Task tool delegations:

1. Primary creates workspace + HANDOFF.md
2. Agent runs in background (async by default)
3. Agent writes OUTPUT.md on completion
4. Primary reads OUTPUT.md only

No special flags needed — this is how delegation works.

---

## Quick Reference

### For Primary (Caller)

```markdown
1. Create workspace: `.agent-workspaces/{task-id}/`
2. Write HANDOFF.md with: task, context, files, constraints, deliverables
3. Spawn agent with workspace path
4. Wait for completion
5. Read OUTPUT.md for results
```

### For Agents (Callee)

```markdown
1. Read HANDOFF.md — understand requirements
2. Execute task — stay in scope
3. Use WORK.md for scratchpad (optional)
4. Write OUTPUT.md — summary, deliverables, decisions, for-primary
5. Signal completion
```

---

## Appendix: Status Values

| Status | Meaning |
|--------|---------|
| `completed` | Task done, all deliverables ready |
| `blocked` | Cannot proceed, needs external action |
| `needs-input` | Requires clarification from primary |
| `partial` | Some deliverables done, others blocked |

---

## Execution Strategies (v2.0)

CDP v2.0 adds automatic execution strategy selection based on task complexity scoring.

### Strategy Types

| Strategy | When | Pattern |
|----------|------|---------|
| **parallel** | Low complexity, no dependencies | All subtasks run simultaneously |
| **sequential** | Low-medium complexity, has dependencies | Tasks execute in dependency order |
| **pipeline** | High complexity, few dependencies | Data flows through processing stages |
| **fan-out-fan-in** | High complexity, many dependencies | Distribute work, then aggregate results |

### Auto-Selection

| Complexity Score | Dependency Count | Selected Strategy |
|-----------------|-----------------|-------------------|
| < 0.4 | 0 | parallel |
| < 0.7 | > 0 | sequential |
| >= 0.7 | <= 2 | pipeline |
| >= 0.7 | > 2 | fan-out-fan-in |

### HANDOFF.md v2.0 Template Addition

When delegating, include an Execution Strategy section:

```markdown
## Execution Strategy
- **Mode**: sequential | parallel | pipeline | fan-out-fan-in
- **Complexity**: 0.75
- **Model Hint**: opus | sonnet | haiku
- **Auto-calculated**: true | false
```

### Model Hints

| Complexity | Recommended Model |
|-----------|------------------|
| LOW (< 0.4) | haiku |
| MEDIUM (0.4 - 0.7) | sonnet |
| HIGH (> 0.7) | opus |

Model hints are advisory -- the spawning agent may override based on task requirements.
