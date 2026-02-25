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

## Output Contracts (v2.2)

When agents return free-form prose, it inflates main context without proportional benefit. Use these structured contracts for common task types. Target: 1,000-2,000 tokens per return.

### Document Analysis Contract

```
=== DOCUMENT ANALYSIS ===
SOURCE: [file path]
TYPE: [document type]

NUMBERS:
- [metric]: [exact value, no rounding]

REQUIREMENTS:
- REQ: [requirement] | CONDITION: [if/then] | PRIORITY: [P0-P3]

DECISIONS_REFERENCED:
- DEC: [what] | WHY: [rationale] | REJECTED: [alternatives]

CONTRADICTIONS:
- [doc says X] CONTRADICTS [other source says Y]

OPEN:
- [unresolved item] | NEEDS: [who/what]
=== END ===
```

### Research/Exploration Contract

```
=== RESEARCH OUTPUT ===
QUERY: [what was researched]
CONFIDENCE: [high/medium/low] BECAUSE [reason]

CORE_FINDING: [one sentence]

EVIDENCE:
- [data point]: [exact value] | SOURCE: [file:line or URL]

CONCLUSIONS:
- IF [condition] THEN [conclusion] | EVIDENCE: [ref]

GAPS:
- [what was not found or remains uncertain]
=== END ===
```

### Review/QA Contract

```
=== REVIEW OUTPUT ===
REVIEWED: [file path or deliverable]
AGAINST: [standard or spec]
PASS: [yes/no/partial]

ISSUES:
- [critical/major/minor]: [description] | LOCATION: [where] | FIX: [how]

MISSING:
- [expected but not found] | REQUIRED_BY: [spec reference]

INCONSISTENCIES:
- [item A says X] BUT [item B says Y]
=== END ===
```

### When to Use Contracts

| Task Type | Contract | Enforced? |
|-----------|----------|-----------|
| Document processing, summarization | Document Analysis | Required |
| Research, exploration, investigation | Research | Required |
| Code review, QA, audit | Review | Required |
| Code generation, implementation | Standard OUTPUT.md | Optional |
| Single-file targeted edits | No contract needed | N/A |

### Integration with CDP

Add to HANDOFF.md `## Return Requirements`:
```markdown
## Return Requirements
Use: RESEARCH_OUTPUT contract (1-2K tokens max)
```

Agents receiving this instruction format their OUTPUT.md using the specified contract instead of free-form prose.

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

---

## IPC Extension (v2.1)

CDP v2.1 adds bidirectional Inter-Process Communication so workers can ask clarifying questions mid-execution without losing context.

### When to Use

IPC is enabled by the `/dispatch` skill. Regular CDP tasks (without `/dispatch`) continue using the fire-and-forget HANDOFF/OUTPUT pattern — fully backward compatible.

### IPC Directory

When IPC is enabled, the workspace gains an `ipc/` subdirectory:

```
.agent-workspaces/{task-id}/
  HANDOFF.md      # Input (now with ## Plan checklist)
  WORK.md         # Scratchpad (optional)
  OUTPUT.md       # Return value
  CONTEXT.md      # Context dump on failure (NEW)
  ipc/            # Bidirectional message channel (NEW)
    001.question  # Worker writes (JSON)
    001.answer    # Primary writes (JSON)
    .done         # Worker touches when finished
    .monitor.pid  # Active monitor PID
```

### File Format

**Question** (`{seq}.question` — worker writes):
```json
{
  "seq": 1,
  "timestamp": "2026-02-25T11:30:00Z",
  "question": "The CSV has two date columns. Which is the sort key?",
  "options": ["created_date", "modified_date"],
  "checklist_item": "Handle date format normalization"
}
```

**Answer** (`{seq}.answer` — primary writes):
```json
{
  "seq": 1,
  "timestamp": "2026-02-25T11:32:00Z",
  "answer": "Use created_date"
}
```

### Atomic Write Pattern

All IPC files use the two-step atomic write:
1. Write to `{file}.tmp`
2. `mv {file}.tmp {file}` (atomic on POSIX)

This prevents partial reads when monitor or worker polls.

### IPC Flow

```
PRIMARY                              WORKER
  |  1. Create workspace + ipc/        |
  |  2. Write HANDOFF.md (with Plan)   |
  |  3. Spawn worker (background)      |
  |  4. Start monitor (background) ----+---> polls ipc/
  |                                    | 5. Read HANDOFF.md
  |                                    | 6. Work through Plan items
  |                                    | 7. Hit blocker -> write 001.question
  |                                    | 8. Poll for 001.answer (5s intervals)
  |                                    |         |
  | <-- monitor exits (TaskCompleted) -+---------+
  | 9. Read 001.question               |
  | 10. Write 001.answer               |
  | 11. Respawn monitor ---------------+---> polls again
  |                                    | 12. Finds answer -> continues
  |                                    | 13. Write OUTPUT.md
  |                                    | 14. touch ipc/.done
  | <-- monitor exits (TaskCompleted) -+
  | 15. Read OUTPUT.md                 |
```

### Monitor Script

`~/.claude/scripts/dispatch-monitor.sh` is a lightweight bash script that polls the IPC directory every 2 seconds. It exits when:

| Exit Code | Meaning |
|-----------|---------|
| 0 | Unanswered question found |
| 1 | `.done` sentinel found (worker finished) |
| 2 | `OUTPUT.md` exists (worker may have skipped .done) |
| 3 | Timeout (15 min max lifetime) |

Run via `run_in_background: true`. Exit triggers `TaskCompleted` hook -> `dispatch-ipc-handler.sh` injects context into conversation.

### Timeout Behavior

- Worker polls for answer up to 180 seconds (configurable)
- If no answer arrives: worker writes `CONTEXT.md`, sets OUTPUT.md `status: blocked`, exits
- Primary can resume with a new worker via `/dispatch resume`

### Startup Reconciliation

On session start or `/dispatch status`:
1. Scan `.agent-workspaces/*/ipc/` for directories
2. Check for `*.question` files without matching `*.answer`
3. If found and no `.done` or `OUTPUT.md`: surface orphaned question
4. If `CONTEXT.md` exists without `OUTPUT.md`: offer resume

---

## Checklist-as-State (v2.1)

### Plan Section in HANDOFF.md

When using `/dispatch`, HANDOFF.md includes a `## Plan` section with checklist items:

```markdown
## Plan
<!-- Worker: update markers in-place as you progress -->
- [ ] Parse input CSV and validate schema
- [ ] Map columns to target format
- [ ] Handle date format normalization
- [ ] Generate output JSON
- [ ] Validate against schema
```

### Marker Semantics

| Marker | Meaning | When Worker Sets It |
|--------|---------|---------------------|
| `[ ]` | Pending | Initial state (set by primary) |
| `[x]` | Completed | Worker finished this step |
| `[?]` | Blocked | Worker needs clarification (IPC question written) |
| `[!]` | Error | Worker hit an unrecoverable error |

### How Workers Update

Workers update HANDOFF.md in-place via targeted Edit:
- Replace `- [ ] Step text` with `- [x] Step text`
- For blocked: `- [?] Step text (IPC: 001.question)`
- For errors: `- [!] Step text — error description`

### How Primary Reads Progress

Primary reads HANDOFF.md's `## Plan` section at any time. `/dispatch status` parses markers across all active workspaces and presents a dashboard.

---

## Context Dump (v2.1)

### CONTEXT.md Specification

When a worker cannot complete (IPC timeout, unrecoverable error, budget exhausted), it writes `CONTEXT.md` in the workspace before exiting:

```markdown
# Worker Context Dump

**Task ID:** worker-20260225-113000
**Dumped:** 2026-02-25T11:35:00Z
**Reason:** IPC timeout | error | budget exhausted

## Progress
Completed steps 1-3 of 5. Blocked on step 4.

## Current State
[Key state the worker holds at failure point]

## Blocking Issue
[What specifically stopped progress]

## How to Resume
1. Read this CONTEXT.md for state
2. Answer the blocking question if applicable
3. Start from the first unchecked Plan item
```

### Resume Flow

1. Primary reads `CONTEXT.md` to understand failure
2. If there's an unanswered question, primary answers it
3. New worker spawned with enhanced HANDOFF.md containing:
   - Original task + constraints
   - `## Previous Worker Context` section (from CONTEXT.md)
   - Already-completed Plan steps marked `[x]`
   - Pre-filled answer to blocking question
