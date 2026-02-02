---
name: action-extractor
description: Use when Fathom MCP tools are called, user says "extract tasks", "analyze meeting", "process transcript", "what actions from", or when emails/transcripts need task extraction. Auto-invokes after mcp__fathom__ calls.
context: fork
agent: general-purpose
async:
  mode: auto
  prefer_background:
    - large transcript processing
    - batch email analysis
  require_sync:
    - task review and confirmation
    - interactive extraction
---

# Action Extractor

Extract actionable tasks and discussion topics from meeting transcripts and emails.

## When This Runs

**Auto-invoke (no user action needed):**
- After any `mcp__fathom__get_meeting` or `mcp__fathom__get_transcript` call
- After `mcp__fathom__list_meetings` if user selects meetings to process

**Manual trigger phrases:**
- "extract tasks from [meeting/email]"
- "analyze this meeting"
- "what actions came out of..."
- "process this transcript"
- "follow-ups from [source]"

## Input Sources

| Source | How to Provide | Format |
|--------|----------------|--------|
| Fathom meeting | Auto-detected from MCP call | JSON with transcript |
| Email file | Path to `.eml`, `.msg`, or `.txt` | Standard email format |
| Pasted transcript | Direct text in conversation | Plain text |
| Meeting notes | Path to `.md`, `.txt` file | Any text format |

## Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                      INPUT RECEIVED                          │
│  (Fathom transcript / Email / Meeting notes)                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    1. DETECT SOURCE TYPE                     │
│  Fathom JSON → Email file → Pasted text → File path         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. EXTRACT INFORMATION                    │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │  TASKS   │  │ TOPICS   │  │DECISIONS │  │ DEADLINES│    │
│  │          │  │          │  │          │  │          │    │
│  │ • Owner  │  │ • Subject│  │ • What   │  │ • Date   │    │
│  │ • Action │  │ • Context│  │ • Why    │  │ • Task   │    │
│  │ • Due    │  │ • Status │  │ • Who    │  │ • Owner  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                              ▼
┌─────────────────────────┐    ┌─────────────────────────────┐
│   3A. CREATE CTM TASKS  │    │   3B. GENERATE SUMMARY      │
│                         │    │                             │
│ ctm spawn "task"        │    │ • Markdown file             │
│   --deadline +Nd        │    │ • Structured sections       │
│   --blocked-by <id>     │    │ • Cross-linked to CTM       │
└─────────────────────────┘    └─────────────────────────────┘
              │                              │
              └──────────────┬───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. OUTPUT TO USER                         │
│  • Summary displayed inline                                  │
│  • CTM task IDs listed                                       │
│  • Markdown file path (if created)                          │
└─────────────────────────────────────────────────────────────┘
```

## Extraction Patterns

### Tasks / Action Items

**Trigger phrases:**
- "[Name] will...", "[Name] to..."
- "action item:", "to-do:", "task:"
- "follow up on...", "need to..."
- "can you...", "please...", "make sure to..."
- "by [date]", "before [event]", "deadline:"

**Extract:**
| Field | Source |
|-------|--------|
| Owner | Name mentioned or "TBD" |
| Action | The task itself |
| Due | Explicit date or inferred from context |
| Context | Surrounding discussion |
| Confidence | HIGH/MEDIUM/LOW based on clarity |

### Topics Requiring Action

**Trigger phrases:**
- "we need to discuss...", "open question:"
- "pending:", "waiting on...", "blocked by..."
- "revisit", "circle back", "follow up"
- Questions ending with "?" that weren't answered

**Extract:**
| Field | Source |
|-------|--------|
| Topic | Subject matter |
| Status | OPEN / PENDING / BLOCKED |
| Blocker | What's blocking (if any) |
| Next step | Suggested action |

### Decisions (for reference)

**Trigger phrases:**
- "we decided...", "agreed:", "confirmed:"
- "let's go with...", "the plan is..."
- "instead of X, we'll Y"

**Action:** Log to DECISIONS.md via `decision-tracker` skill.

## CTM Integration

Tasks are created with smart defaults and **source tracking**:

```bash
# From Fathom transcript
ctm spawn "Review API spec" --deadline +3d --switch false \
    --source fathom-transcript --source-ref "meeting_493906762" \
    --extracted-by "action-extractor"

# From email
ctm spawn "Send proposal" --deadline +2d \
    --source email --source-ref "email_thread_xyz" \
    --extracted-by "action-extractor"

# Blocked task
ctm spawn "Deploy to staging" --blocked-by <api-task-id> \
    --source fathom-transcript --source-ref "meeting_123"

# Task with context
ctm context add --note "From meeting: Client wants feature X by Q2"
```

**Source types:**
| Type | Use When |
|------|----------|
| `fathom-transcript` | Extracted from Fathom meeting |
| `email` | Extracted from email file |
| `claude-session` | Created during Claude conversation |
| `manual` | User-created outside extraction |

**Priority mapping:**
| Signal | CTM Priority |
|--------|--------------|
| "urgent", "ASAP", "critical" | --priority critical |
| "important", "high priority" | --priority high |
| "when you can", "low priority" | --priority low |
| Default | --priority normal |

## Output: Markdown Summary

Creates `{source-date}-action-summary.md`:

```markdown
# Action Summary: {Source Title}

> **Source:** {Fathom meeting / Email / File}
> **Date:** {YYYY-MM-DD}
> **Processed:** {timestamp}

## Tasks Created

| CTM ID | Owner | Task | Due | Priority |
|--------|-------|------|-----|----------|
| task-001 | Alice | Review API spec | +3d | high |
| task-002 | Bob | Schedule demo | +5d | normal |

## Topics Requiring Action

| Topic | Status | Next Step |
|-------|--------|-----------|
| Budget approval | PENDING | Awaiting CFO sign-off |
| Timeline concerns | OPEN | Discuss in next standup |

## Decisions Made

- **D-042:** Use HubSpot for CRM (logged to DECISIONS.md)

## Open Questions

- What's the fallback if API is delayed?
- Who owns the documentation?

## Raw Extraction Data

<details>
<summary>Full extraction details</summary>

{JSON of all extracted items with confidence scores}

</details>
```

## Email-Specific Handling

For email files (`.eml`, `.msg`, `.txt`):

**Parse:**
- Subject line → Meeting/topic context
- From/To/CC → Potential task owners
- Date → Reference timestamp
- Thread history → Additional context

**Special patterns:**
- "Can you...?" → Task for recipient
- "Please confirm..." → Confirmation task
- "Attached is..." → Review attachment task
- "By [date]..." → Deadline extraction

## Commands

```bash
# Process current Fathom meeting (after MCP call)
/action-extractor

# Process specific file
/action-extractor path/to/transcript.txt
/action-extractor path/to/email.eml

# Process without creating CTM tasks (summary only)
/action-extractor --summary-only

# Process with specific project context
/action-extractor --project /path/to/project
```

## Integration Points

| System | Integration |
|--------|-------------|
| **CTM** | Creates tasks with deadlines and dependencies |
| **RAG** | Indexes summary for future search |
| **DECISIONS.md** | Logs decisions via decision-tracker |
| **meeting-indexer** | Delegates heavy processing |
| **Fathom MCP** | Auto-triggers on meeting fetch |

## Confidence Thresholds

| Confidence | Action |
|------------|--------|
| HIGH (>0.8) | Auto-create CTM task |
| MEDIUM (0.5-0.8) | Create task, flag for review |
| LOW (<0.5) | Include in summary only, don't create task |

## Error Handling

| Scenario | Action |
|----------|--------|
| No actionable items found | Report "No tasks extracted" with summary |
| Unclear task owner | Set owner as "TBD", flag in summary |
| No deadline mentioned | Don't set deadline (CTM handles) |
| CTM unavailable | Generate summary only |
| Duplicate task detected | Skip, note in summary |

## Example: Fathom Meeting

```
[User fetches meeting via Fathom MCP]
mcp__fathom__get_meeting meeting_id="abc123"

[Skill auto-invokes]
Extracting actions from: "Q1 Planning Call"

Found:
- 3 tasks (2 HIGH, 1 MEDIUM confidence)
- 2 topics requiring action
- 1 decision

Creating CTM tasks...
✓ task-047: "Finalize budget proposal" (Alice, +5d)
✓ task-048: "Schedule stakeholder review" (Bob, +7d)
✓ task-049: "Draft timeline options" (TBD, no deadline)

Summary saved: 2026-01-23-q1-planning-action-summary.md
```

## Example: Email Thread

```
/action-extractor ~/Downloads/re-project-kickoff.eml

Extracting actions from email thread: "Re: Project Kickoff"

Found:
- 2 tasks
- 1 open question

Creating CTM tasks...
✓ task-050: "Send SOW draft" (You, +2d)
✓ task-051: "Confirm meeting time" (Client, blocked)

Summary saved: 2026-01-23-email-kickoff-action-summary.md
```
