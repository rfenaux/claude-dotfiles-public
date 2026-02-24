---
name: post-mortem-analyzer
description: Analyze archived project conversations to extract failure points, root causes, and actionable lessons learned.
async:
  mode: never
  require_sync:
    - analysis review
    - lessons extraction approval
---

# /post-mortem - Post-Mortem Analyzer

Retrospective analysis tool for completed or archived projects. Reads conversation history to identify failure points, extract root causes, compare against successful project patterns, and generate actionable lessons-learned reports. Found in archived project analysis (A8) and ISMS consultant recovery (A5).

## Trigger

Invoke this skill when:
- User says `/post-mortem`, "post-mortem", "what went wrong?", "retrospective"
- Archived project needs analysis
- After project completion for lessons extraction
- When inherited project shows patterns of failure

## Why This Exists

Project failures and successes contain valuable patterns, but extracting them manually from dozens of conversation files is impractical. Automated analysis produces structured lessons that feed into the learned lessons system, improving future project outcomes.

## Commands

| Command | Action |
|---------|--------|
| `/post-mortem` | Full 5-step analysis |
| `/post-mortem --project <path>` | Analyze specific project |
| `/post-mortem --failures` | Focus on failure points only |
| `/post-mortem --lessons` | Extract lessons only (skip detailed analysis) |
| `/post-mortem --compare` | Compare against successful project patterns |

## Workflow

### Step 1: Read History
Load archived project files: conversation history, session summaries, DECISIONS.md, SESSIONS.md, CTM snapshots.

### Step 2: Identify Failure Points
Detect patterns of trouble:
- Missed deadlines (decision dates vs actual delivery)
- Scope changes (additions not in original SOW)
- Blocker accumulation (growing unresolved blockers over time)
- Communication breakdowns (same topic discussed 3+ times without resolution)
- Rework cycles (deliverable revised more than twice)

### Step 3: Extract Root Causes
For each failure point, trace to root cause:
- Insufficient discovery (requirements gaps)
- Unclear requirements (ambiguity not resolved early)
- Resource constraints (understaffed, overcommitted)
- External dependencies (client delays, partner blockers)
- Technical limitations (platform constraints discovered late)
- Scope creep (gradual expansion without commercial adjustment)

### Step 4: Compare Patterns
Match against known success patterns from comparable projects:
- Use `comparable-project-finder` for similar past projects
- Identify: what successful projects did differently at the same decision points

### Step 5: Generate Report
Produce post-mortem with actionable recommendations and lessons for the learned lessons system.

## Output Format

```markdown
# Post-Mortem: [Project Name]
> Period: [dates] | Sessions: [N] | Outcome: [result]

## Executive Summary
[What happened and why, in 2 paragraphs]

## Failure Points
| # | Event | Date | Root Cause | Impact |
|---|-------|------|-----------|--------|

## Root Cause Analysis
### [Root Cause Category]
- Evidence: [specific examples]
- Contributing factors: [context]
- Comparable: [similar issue in past project]

## Lessons Learned
| # | Lesson | Confidence | Tags |
|---|--------|-----------|------|

## Recommendations
- Process: [what to change]
- Tools: [what to add/improve]
- People: [roles/communication changes]
```

## Integration

- **RAG**: Search archived project documents
- **Lessons system**: Auto-capture extracted lessons (`~/.claude/lessons/`)
- **`comparable-project-finder`**: Find similar past projects
- **`project-chronicle-generator`**: Timeline feeds into analysis
