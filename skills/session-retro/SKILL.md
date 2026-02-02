---
name: session-retro
description: Automate session retrospective analysis using parallel workers. Analyzes time segments, extracts chronology, decisions, and improvements.
async:
  mode: optional
  optimal_for:
    - large session analysis
    - multi-file review
---

# /session-retro - Session Retrospective

Automated retrospective analysis of Claude sessions. Spawns parallel workers to analyze different time segments and synthesizes into a structured report.

## Trigger

Invoke this skill when:
- User says "/session-retro", "analyze session", "retrace chronologically"
- User says "retrospective", "what did we accomplish"
- User wants to understand what happened in a long session
- User asks "review our conversation", "summarize our work"

## Why This Exists

Meta-analysis identified recurring pattern of manual session analysis. This skill automates the process using parallel workers for efficiency.

## Behavior

### 1. Session Identification
Determine session source:
- Current session: Use conversation context
- By ID: Find in `~/.claude/projects/*/sessions-index.json`
- By date: Filter session files by timestamp

### 2. Parallel Analysis
Spawn 4 worker agents to analyze different aspects:

| Worker | Focus | Output |
|--------|-------|--------|
| **Chronology** | Timeline of activities | Ordered list with timestamps |
| **Decisions** | Choices and trade-offs | Decision log format |
| **Documents** | Files created/modified | File inventory |
| **Improvements** | Agent/config suggestions | Actionable recommendations |

Each worker uses `model: haiku` for efficiency.

### 3. Synthesis
Aggregate worker outputs into structured report:

```markdown
# Session Retrospective: [Session ID/Date]

## Timeline
- [HH:MM] Task started: X
- [HH:MM] Decision: Y
- [HH:MM] Deliverable: Z

## Decisions Made
| # | Decision | Context | Recorded |
|---|----------|---------|----------|
| 1 | ... | ... | ✅/❌ |

## Documents Created/Modified
| File | Action | Purpose |
|------|--------|---------|
| ... | Created | ... |

## Recommendations
1. [Improvement 1]
2. [Improvement 2]
```

## Commands

```bash
/session-retro                    # Analyze current session
/session-retro <session-id>       # Analyze specific session
/session-retro --date 2026-01-29  # Analyze by date
/session-retro --project <name>   # Analyze project sessions
```

## Delegation Pattern

Uses CDP with `context: fork`:
```
Primary → Worker[Chronology] ─┐
       → Worker[Decisions]  ──┼→ Synthesis
       → Worker[Documents]  ──┤
       → Worker[Improvements]─┘
```

## Files

| Path | Purpose |
|------|---------|
| `~/.claude/projects/*/sessions-index.json` | Session registry |
| `~/.claude/projects/*/*.jsonl` | Session transcripts |
| `project/conversation-history/*.md` | Exported conversations |

## Example

```
User: /session-retro

Claude: [Auto-invoking session-retro based on: retrospective]

Analyzing current session...
Spawning 4 parallel workers for analysis.

# Session Retrospective: 2026-01-29 Meta-Analysis

## Timeline
- 09:00 Started meta-analysis of 703 conversation files
- 09:45 Spawned 7 parallel workers for pattern analysis
- 10:30 Synthesized findings into final report
- 11:00 Created PRD and task list
- 11:30 Applied 6 CLAUDE.md additions

## Decisions Made
| # | Decision | Context | Recorded |
|---|----------|---------|----------|
| 1 | Use parallel workers for analysis | Efficiency optimization | ❌ |
| 2 | Add 6 sections to CLAUDE.md | Based on findings | ✅ |

## Documents Created/Modified
| File | Action | Purpose |
|------|--------|---------|
| PRD-meta-analysis-config-optimizations.md | Created | Implementation spec |
| CLAUDE.md | Modified | Added 6 optimization sections |
| META_ANALYSIS_FINAL_REPORT.md | Created | Analysis synthesis |

## Recommendations
1. Create /checkpoint skill (in progress)
2. Add checkpoint reminder hook
3. Increase manual checkpoint usage to 10+/week
```
