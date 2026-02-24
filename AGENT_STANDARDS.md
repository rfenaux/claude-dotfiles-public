# Agent Standards & Cross-Cutting Patterns

Standard patterns that ALL agents should follow. Reference this file in agent prompts.

---

## 1. RAG Integration (MANDATORY)

Every agent should check for RAG and use project context:

```markdown
## BEFORE STARTING

1. **Check RAG availability**: Does `.rag/` folder exist?
2. **If RAG available**, search for relevant context:
   - Past similar deliverables
   - Project-specific decisions (DECISIONS.md)
   - Requirements and constraints
   - Comparable project lessons
3. **Use RAG results** to inform recommendations
4. **Cite RAG sources** in output: `(Source: [filename], [date])`
```

**RAG Search Patterns by Agent Type:**

| Agent Type | Search Queries |
|------------|----------------|
| ERD/Data Model | "data model", "entities", "SSOT", "relationships" |
| BPMN/Process | "business process", "workflow", "automation" |
| Architecture | "integration", "system architecture", "API" |
| Specification | "requirements", "decisions", "constraints" |
| Discovery | "discovery", "stakeholders", "current state" |
| Risk | "risks", "blockers", "dependencies" |
| Commercial | "budget", "ROI", "investment", "cost" |

---

## 2. Error Handling (MANDATORY)

All agents must handle errors gracefully:

```markdown
## ERROR HANDLING

**If missing required input:**
- State clearly: "Cannot proceed without [specific input]"
- Request specific information needed
- Provide example of required format

**If ambiguous requirement:**
- Ask clarifying question with 2-3 specific options
- Don't guess or assume - surface the ambiguity

**If outside scope:**
- State: "This task requires [other agent name]"
- Suggest: "Would you like me to invoke [agent]?"

**If knowledge gap:**
- State: "This requires domain knowledge outside my specialization"
- Suggest: "Consider invoking [hubspot-specialist / solution-architect]"

**NEVER:**
- Proceed silently with assumptions
- Hallucinate capabilities or data
- Guess at unknown information
```

---

## 3. Output Quality Standards (MANDATORY)

Self-validate before delivering any output:

```markdown
## QUALITY CHECKLIST (Self-Validate Before Delivery)

- [ ] All facts cited to sources (KB, RAG, documentation)
- [ ] No hallucinated capabilities or data
- [ ] Tier/version/platform specified where relevant
- [ ] Quantified where possible (not just qualitative)
- [ ] Actionable recommendations (not vague advice)
- [ ] Complete (all required sections present)
- [ ] Professional formatting (headers, tables, lists)
- [ ] Clear next steps provided
```

---

## 4. Output Format Standards

All agents should use consistent output formatting:

```markdown
## OUTPUT FORMAT

**File Naming:** [CLIENT]_[DELIVERABLE-TYPE]_v[VERSION]_[DATE].md
Example: Cognita_ERD_v1.2_2024-12-15.md

**File Header:**
```yaml
---
Client: [Client Name]
Deliverable: [Deliverable Type]
Version: [X.X]
Date: [YYYY-MM-DD]
Author: [Name or "Claude Agent"]
Status: Draft | Review | Approved
---
```

**Content Structure:**
1. Executive Summary (what, why, key points)
2. Detailed Content (core deliverable)
3. Assumptions and Constraints
4. Next Steps or Recommendations
5. Version History (what changed)
```

---

## 5. Cross-Agent Collaboration

Agents should reference related agents for workflow continuity:

```markdown
## RELATED AGENTS

When your task connects to other specialized work:

| Your Task | Related Agent | When to Reference |
|-----------|---------------|-------------------|
| Data model | erd-generator | Before/after property mapping |
| Business process | bpmn-specialist | Before solution spec |
| Integration design | system-architecture-visualizer | After requirements |
| Technical spec | solution-spec-writer | After architecture |
| Presentation | slide-deck-creator | After deliverables ready |

**Workflow Suggestion Pattern:**
"This [deliverable] should be used with [agent-name] for [next step]."
```

---

## 6. HubSpot Context (for CRM Agents)

Agents working with HubSpot should include platform-specific guidance:

```markdown
## HUBSPOT CONTEXT

**Always specify:**
- HubSpot tier required (Free/Starter/Pro/Enterprise)
- API version (v3 preferred, v4 for new features)
- Object type limitations (custom objects = Enterprise only)
- Rate limits (100 requests/10 seconds for Private Apps)

**Key patterns:**
- Association labels for custom relationships
- Lifecycle stage vs. Lead status usage
- Calculated properties vs. workflows for computed fields
- SSOT designation for each property

**Reference:** Invoke `hubspot-specialist` for detailed platform questions.
```

---

## 7. Effort Estimation (RECOMMENDED)

Include effort estimates when generating deliverables:

```markdown
## EFFORT ESTIMATION

Provide estimate before starting based on:
- Input complexity (simple/medium/complex)
- Number of systems/objects/processes
- Level of detail required

**Typical Ranges:**
| Complexity | Time Estimate |
|------------|---------------|
| Simple | 1-2 hours |
| Medium | 2-4 hours |
| Complex | 4-8 hours |

State: "Estimated effort: [X hours] based on [complexity factors]"
```

---

## 8. Agent Context Protocol (ACP)

For agents that may run in parallel:

```markdown
## AGENT CONTEXT PROTOCOL

**If running as parallel agent:**

1. Create workspace: `.agent-workspaces/{task-id}/`
2. Create files:
   - `AGENT_STATE.md` - Current task and position
   - `PROGRESS.md` - Subtask checklist
   - `SOURCES.md` - Files read with excerpts
3. Update files every 3-5 tool calls
4. Signal completion: `OUTPUT.md`

**See:** ~/.claude/AGENT_CONTEXT_PROTOCOL.md for full specification.
```

---

## 9. Model Selection Guidance

Agents should understand when to delegate to different models:

| Model | Use For | Cost |
|-------|---------|------|
| **Haiku** | Simple lookups, data transformation, status reports | $ |
| **Sonnet** | Standard implementation, documentation, analysis | $$ |
| **Opus** | Complex reasoning, architecture, strategic decisions | $$$$$ |

**Announce model selection:** `[Using Sonnet for: ERD generation]`

---

## 10. Ethical Boundaries

All agents must respect these boundaries:

```markdown
## ETHICAL BOUNDARIES

**I will NOT:**
- Proceed with designs that exclude accessibility considerations
- Generate content that misrepresents data or capabilities
- Create documentation that obscures risks or limitations
- Recommend solutions solely to increase project scope/cost
- Hallucinate product features or capabilities

**I will ALWAYS:**
- Surface risks even when uncomfortable
- Recommend simpler solutions when appropriate
- Acknowledge uncertainty explicitly
- Preserve user decision-making authority
- Cite sources for factual claims
```

---

## Quick Reference

**Before any task:**
1. ✅ Check RAG (`.rag/` folder?)
2. ✅ Understand scope and constraints
3. ✅ Identify related agents for workflow

**During task:**
1. ✅ Follow output format standards
2. ✅ Handle errors gracefully
3. ✅ Include HubSpot context if relevant

**Before delivery:**
1. ✅ Run quality checklist
2. ✅ Provide effort estimate
3. ✅ Suggest next steps

---

## 11. Async Execution Patterns

Agents can run synchronously (blocking) or asynchronously (background) based on task characteristics.

### Frontmatter Schema

Add `async` block to agent frontmatter:

```yaml
---
name: agent-name
description: ...
model: sonnet
async:
  mode: auto              # always | never | auto
  prefer_background:      # conditions favoring async
    - bulk
    - parallel
    - multiple files
  require_sync:           # conditions requiring sync
    - interactive
    - user confirmation
---
```

### Mode Definitions

| Mode | Behavior |
|------|----------|
| `always` | Always run in background (no user interaction needed) |
| `never` | Always run synchronously (requires user interaction) |
| `auto` | Claude decides based on task + hints (default) |

### Decision Matrix

| Factor | Favor Async | Favor Sync |
|--------|-------------|------------|
| **User interaction** | None during execution | Questions/approvals needed |
| **Feedback loops** | None (input → output) | Multiple (propose → refine) |
| **Artifact stakes** | Analysis, summaries | Deliverables, decisions |
| **Iteration count** | 0 (one-shot) | 2+ (iterative) |
| **Output urgency** | Can review later | Needs immediate attention |

### Override Syntax

Users can force sync/async at invocation:

```
"run X in background" / "async" → force background execution
"run X sync" / "interactively" / "with me" → force synchronous
```

### Notification on Completion

When async agent completes:
1. Write results to `.agent-workspaces/{task-id}/OUTPUT.md`
2. Announce: `[Agent {name} completed - results in {workspace}/OUTPUT.md]`
3. If CTM active: Add context note about completion

### Integration with ACP

Async agents follow Agent Context Protocol:
- Create workspace: `.agent-workspaces/{task-id}/`
- Update `PROGRESS.md` every 3-5 tool calls
- Signal completion with `OUTPUT.md`

See `~/.claude/AGENT_CONTEXT_PROTOCOL.md` for full specification.

---

## 12. Cognitive Delegation Protocol (CDP) — MANDATORY

All sub-agents MUST follow CDP when spawned via Task tool. This is the **native behavior** for delegation.

### Protocol Overview

```
PRIMARY                              SUB-AGENT
   │                                     │
   │  HANDOFF.md (input)                 │
   │ ────────────────────────────────────▶
   │                                     │ Execute task
   │ ◀────────────────────────────────────│
   │  OUTPUT.md (return)                 │
```

### Agent Requirements

**On startup:**
1. Read `HANDOFF.md` in workspace
2. Understand task, context, constraints
3. Stay within scope defined in handoff

**During execution:**
1. Use `WORK.md` for scratchpad (optional)
2. Don't narrate steps — just work
3. Stay focused on deliverables

**On completion:**
1. Write `OUTPUT.md` with required format
2. Set status: `completed`, `blocked`, or `needs-input`
3. Include all files created/modified

### OUTPUT.md Required Format

```markdown
# Task Complete: [Title]

**Status:** completed | blocked | needs-input
**Duration:** [time]
**Agent:** [agent-name]

## Summary
[1-3 sentences — what was accomplished]

## Deliverables
| File | Description |
|------|-------------|
| `path/to/file` | What it does |

## Decisions Made
- **[Decision]**: [Rationale]

## For Primary
[Critical info main conversation needs]

## Files Modified
- `path/to/file` — What changed
```

### Frontmatter CDP Declaration

Agents should declare CDP compliance:

```yaml
---
name: agent-name
cdp:
  version: 1.0
  input_requirements:
    - task description
    - key files
  output_includes:
    - summary
    - deliverables
    - decisions
---
```

### Key Principles

1. **Isolation**: All work stays in agent context — don't pollute primary
2. **Minimal returns**: Only essential info in OUTPUT.md
3. **Scope discipline**: Only do what HANDOFF.md specifies
4. **Clean completion**: OUTPUT.md must be standalone and complete

**Full specification:** `~/.claude/CDP_PROTOCOL.md`

---

*Last Updated: 2026-01-08*
*Applies to: All 55 agents in ~/.claude/agents/*
