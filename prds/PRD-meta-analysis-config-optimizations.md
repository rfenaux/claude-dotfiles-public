# PRD: Meta-Analysis Configuration Optimizations

**Version:** 1.0
**Date:** 2026-01-29
**Author:** Claude Code (Meta-Analysis)
**Status:** Draft → Implementation

---

## 1. Problem Statement

### Background

A comprehensive meta-analysis of 703 conversation files (~4.3GB) across 13 <COMPANY> projects (Oct 2025 - Jan 2026) revealed systematic inefficiencies in Claude Code configuration:

### Key Findings

| Finding | Impact | Evidence |
|---------|--------|----------|
| **Tool failures on large files** | 15% of Read/RAG operations fail | Conversation-history files >256KB cause errors |
| **Conversations end without action** | Breaks partnership momentum | ~40% of responses lack next-step proposals |
| **Low checkpoint rate** | Context degradation in long sessions | 0.3% manual checkpoints vs 65.6% auto-compaction |
| **Agents underused** | 30-40% efficiency loss | 0-1 agent spawns/session despite 48+ configured |
| **Decisions not captured** | Lost institutional knowledge | Decision phrases detected but not recorded |
| **Frustration triggers** | Rework, partnership friction | Patterns identified but no recovery protocol |

### Root Causes

1. **No pre-flight checks** - Operations attempted without validating constraints
2. **No response templates** - Inconsistent output structure
3. **No session health monitoring** - Reactive vs proactive memory management
4. **No pattern detection** - Agents not auto-invoked based on task type
5. **No calibration guidance** - Response length/format not context-aware

---

## 2. Goals & Success Metrics

### Primary Goals

1. Reduce tool failures from 15% to <5%
2. Increase conversations ending with action from 60% to >90%
3. Increase manual checkpoints from 0.3% to 10+ per week
4. Increase agent spawns from 0-1 to 2-3 per session
5. Capture 100% of significant decisions

### Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Tool failures (size-related) | ~15% | <5% | Track Read/RAG errors |
| Action proposal rate | ~60% | >90% | Audit conversation endings |
| Manual checkpoints/week | ~0.3 | 10+ | Count ctm checkpoint calls |
| Agent spawns/session | 0-1 | 2-3 | Count Task tool invocations |
| Decision capture rate | ~50% | 95%+ | Compare decisions vs DECISIONS.md |
| First-attempt success | 75% | 85% | Track corrections/iterations |

---

## 3. Solution Design

### 3.1 CLAUDE.md Additions

#### A. Pre-Flight Checks Section

**Purpose:** Prevent 15% of tool failures by checking constraints before operations.

**Implementation:**
```markdown
## Pre-Flight Checks

| Operation | Check First | Fallback |
|-----------|-------------|----------|
| Read conversation-history/*.md | Check size (>256KB?) | Use Grep with context |
| RAG search | Start top_k=5 | Expand if <5 relevant results |
| Agent spawning | check-load.sh | Work inline if HIGH_LOAD |
| Large files (>100KB) | Use offset/limit | Grep for patterns |
```

**Location:** After "CDP & Token Optimization" section

---

#### B. Response Format Section

**Purpose:** Ensure every substantive response ends with actionable next steps.

**Implementation:**
```markdown
## Response Format

Every substantive response ends with:

**Next Steps:**
1. [Primary action] - [Why now] (Recommended)
2. [Alternative] - [Trade-off]

Proceed with 1, or prefer another approach?

Skip for: Status checks, simple confirmations, information-only.
```

**Location:** After "Core Workflows" section

---

#### C. Session Health Protocol

**Purpose:** Increase checkpoint rate from 0.3% to 10+ per week.

**Implementation:**
```markdown
## Session Health Protocol

| Duration | Action |
|----------|--------|
| 2 hours | Offer: "Session at 2h. Checkpoint? [Y/n]" |
| 4 hours | Stronger: "Checkpoint strongly recommended." |
| 6 hours | Warning: "Session health declining. Break advised." |

At session end: ALWAYS offer checkpoint (unless <5 min).
```

**Location:** After "Resource Profiles" section

---

#### D. Agent Pattern Detection

**Purpose:** Increase agent spawns from 0-1 to 2-3 per session.

**Implementation:**
```markdown
### Pattern-Based Agent Detection

| Pattern | Agent | Confidence |
|---------|-------|------------|
| "ERD", "data model", "entity diagram" | erd-generator | High |
| "BPMN", "process flow", "workflow diagram" | bpmn-specialist | High |
| "Lucidchart", "architecture diagram" | lucidchart-generator | High |
| "analyze session", "retrospective" | Spawn parallel workers | High |
| "transcript", "meeting notes" | action-extractor | High |
| >10 files, "review all" | codex-delegate | Medium |

Announce: "[Auto-invoking {agent} based on: {pattern}]"
```

**Location:** Enhance existing "Auto-Invoke Triggers" section

---

#### E. Communication Calibration

**Purpose:** Match response style to user signals; detect and recover from frustration.

**Implementation:**
```markdown
## Communication Calibration

### Response Length
| Signal | Length | Format |
|--------|--------|--------|
| Command (<10 words) | Brief | Execute + confirm |
| Question | Medium | Explanation + example |
| Build request | Detailed | Structure + deliverable |
| Approval ("go", "yes") | Minimal | Execute immediately |

### Frustration Detection
Watch for: "already told you", repeated requests, shortened messages
Recovery: Acknowledge → Clarify → Execute → Confirm

### Drift Detection (ADHD)
If >5 messages without action: "I notice drift from [task]. Park or continue?"
```

**Location:** After "Partnership" section

---

#### F. Decision Capture Enhancement

**Purpose:** Capture 100% of significant decisions.

**Implementation:**
```markdown
**Decision Recording:** When decision made → ALWAYS ask: "Record to DECISIONS.md?"

Detect: "we decided", "let's go with", "switching to", "final answer"
Skip for: Trivial (formatting, naming conventions)
```

**Location:** Enhance existing "Decision Recording" in Core Workflows

---

### 3.2 New Skills

#### A. /checkpoint Skill

**Purpose:** Manual session checkpointing with structured output.

**Location:** `~/.claude/skills/checkpoint/`

**Behavior:**
1. Summarize current context (active task, recent decisions)
2. Record to CTM (`ctm checkpoint`)
3. List pending decisions
4. Confirm: "Checkpoint saved. Ready to continue or break?"

**Trigger:** `/checkpoint` or auto-prompted at 2h/4h/6h

---

#### B. /session-retro Skill

**Purpose:** Automate session retrospective (recurring pattern identified in analysis).

**Location:** `~/.claude/skills/session-retro/`

**Behavior:**
1. Find session files by ID (Glob)
2. Spawn 4 parallel workers (time segments)
3. Aggregate: Chronology + Decisions + Documents + Agent Improvements
4. Output structured markdown report

**Trigger:** "analyze session", "retrace session", "retrospective"

---

#### C. /flowchart Skill

**Purpose:** Automate HTML flowchart generation (manual pattern identified).

**Location:** `~/.claude/skills/flowchart/`

**Behavior:**
1. Parse text input for stages/decisions
2. Generate HTML with CSS styling
3. Apply brand colors if BRAND_KIT.md exists
4. Output interactive HTML file

**Trigger:** "create flowchart", "visualize process"

---

### 3.3 Settings.json Hook

#### Checkpoint Reminder Hook

**Purpose:** Automated reminder at 2h session duration.

**Implementation:** Add to `UserPromptSubmit` hooks:
```json
{
  "matcher": "",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/session-checkpoint-reminder.sh"
    }
  ]
}
```

**Hook Script Logic:**
- Track session start time
- At 2h mark: Echo "[SESSION HEALTH: 2 hours. Consider /checkpoint]"
- Non-blocking (doesn't require response)

---

## 4. Implementation Plan

### Phase 1: CLAUDE.md Updates (Immediate)

| Task | Priority | Effort |
|------|----------|--------|
| Add Pre-Flight Checks | P0 | Low |
| Add Response Format | P0 | Low |
| Add Session Health Protocol | P1 | Low |
| Enhance Agent Pattern Detection | P0 | Low |
| Add Communication Calibration | P1 | Medium |
| Enhance Decision Capture | P0 | Low |

**Estimated Time:** 30 minutes

---

### Phase 2: Skills Creation (Short-term)

| Skill | Priority | Effort |
|-------|----------|--------|
| /checkpoint | P1 | Medium |
| /session-retro | P2 | Medium |
| /flowchart | P2 | Medium |

**Estimated Time:** 1-2 hours

---

### Phase 3: Hook Configuration (Short-term)

| Hook | Priority | Effort |
|------|----------|--------|
| session-checkpoint-reminder.sh | P1 | Low |

**Estimated Time:** 15 minutes

---

## 5. Rollback Plan

### If Issues Occur

| Component | Rollback Method |
|-----------|-----------------|
| CLAUDE.md | Git revert: `cd ~/.claude && git checkout HEAD~1 CLAUDE.md` |
| Skills | Delete skill folder: `rm -rf ~/.claude/skills/{skill}/` |
| Hooks | Remove from settings.json, restart Claude |

### Testing Protocol

1. After CLAUDE.md changes: Test with sample prompts
2. After skill creation: Invoke manually, verify output
3. After hook addition: Run 30-minute session, check reminders

---

## 6. Dependencies

| Dependency | Status |
|------------|--------|
| CTM system | ✅ Available |
| RAG system | ✅ Available |
| Conversation history | ✅ Available |
| Brand kit support | ✅ Available |

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| CLAUDE.md too long | Medium | Low | Keep additions concise (~95 lines) |
| Hook performance | Low | Medium | Non-blocking implementation |
| Pattern false positives | Medium | Low | Announce auto-invoke, allow override |
| Over-prompting checkpoints | Medium | Medium | Respect user dismissal for session |

---

## 8. Appendix

### A. Meta-Analysis Source

**Report:** `/private/tmp/.../scratchpad/META_ANALYSIS_FINAL_REPORT.md`
**Data:** 703 conversation files, 13 projects, Oct 2025 - Jan 2026

### B. Related Documents

- `~/.claude/CTM_GUIDE.md` - Checkpoint integration
- `~/.claude/RAG_GUIDE.md` - Search optimization
- `~/.claude/CDP_PROTOCOL.md` - Agent delegation
- `~/.claude/RESOURCE_MANAGEMENT.md` - Load checking

---

**PRD Status:** Ready for Implementation
**Approval:** User approved "let's do all" on 2026-01-29
