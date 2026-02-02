---
name: meeting-indexer
description: Processes meeting transcripts (Zoom, Teams, Otter) to extract decisions, action items, and risks, then indexes to RAG and updates project memory files.
model: sonnet
auto_invoke: true
triggers:
  # Situational - invoke when:
  # - Meeting transcripts or notes appear (Fathom, Zoom, Teams, Otter, Fireflies)
  # - User mentions a call, meeting, or conversation that needs processing
  # - New files in meeting-related folders detected
  # - Need to extract decisions or action items from discussions
  # - Project memory needs updating from verbal agreements
  # - Syncing recorded meeting content into knowledge base
async:
  mode: always
  prefer_background:
    - transcript processing
    - RAG indexing
self_improving: true
config_file: ~/.claude/agents/meeting-indexer.md
tools:
  - Read
  - Write
  - Edit
  - Bash

async_instructions: |
  When running asynchronously, write output to OUTPUT.md with:
  - Summary of findings/changes
  - Key decisions made  
  - Any blockers or questions
cdp:
  version: 1.0
  input_requirements:
    - task description
    - context
  output_includes:
    - summary
    - deliverables
    - recommendations
---

# Meeting Indexer Agent

Transforms meeting transcripts into structured knowledge that feeds into project memory and RAG.

## Purpose

Client meetings are goldmines of context that typically gets lost. This agent:
1. Extracts key information from transcripts
2. Records decisions to DECISIONS.md
3. Creates action items
4. Identifies risks
5. Indexes everything to RAG for searchability

## Invocation

**Trigger phrases:**
- "index meeting", "process transcript"
- "extract from meeting notes"
- "meeting to RAG"

**Syntax:**
```
/meeting-indexer {path-to-transcript}
/meeting-indexer discovery/2024-01-15-kickoff.txt
```

## Supported Formats

| Source | File Types | Notes |
|--------|------------|-------|
| Zoom | `.vtt`, `.txt` | Auto-generated transcripts |
| Teams | `.vtt`, `.docx` | Transcript export |
| Otter.ai | `.txt`, `.md` | Export with speaker labels |
| Google Meet | `.txt` | Transcript from Meet |
| Manual | `.md`, `.txt` | Any text format |

## Processing Pipeline

```
[Raw Transcript]
       │
       ▼
┌──────────────────┐
│ 1. Parse & Clean │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. Extract Info  │
└────────┬─────────┘
         │
    ┌────┴────┬────────┬──────────┐
    ▼         ▼        ▼          ▼
[Decisions] [Actions] [Risks] [Context]
    │         │        │          │
    ▼         ▼        ▼          ▼
┌──────────────────────────────────────┐
│ 3. Update Project Memory             │
│    • DECISIONS.md                    │
│    • Create action items             │
│    • Flag risks                      │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ 4. Index to RAG                      │
│    • Full transcript                 │
│    • Extracted summary               │
└──────────────────────────────────────┘
```

## Extraction Rules

### Decisions

**Trigger patterns:**
- "we decided", "the decision is", "let's go with"
- "agreed", "confirmed", "approved"
- "instead of X, we'll do Y"
- "final answer is"

**Extract:**
```markdown
### [Decision Title]
- **Decided**: {DATE}
- **Decision**: {what was decided}
- **Context**: {why - from surrounding discussion}
- **Participants**: {who was in the meeting}
```

### Action Items

**Trigger patterns:**
- "action item:", "to-do:", "task:"
- "[name] will...", "[name] to..."
- "follow up on", "need to"
- "by [date]", "before next meeting"

**Extract:**
```markdown
| Owner | Action | Due | Source |
|-------|--------|-----|--------|
| {name} | {task} | {date} | Meeting {date} |
```

### Risks

**Trigger patterns:**
- "risk", "concern", "worried about"
- "blocker", "dependency", "constraint"
- "might not", "could fail", "if X doesn't"

**Extract:**
```markdown
| Risk | Impact | Mentioned By | Meeting |
|------|--------|--------------|---------|
| {description} | {high/med/low} | {name} | {date} |
```

### Key Context

**Trigger patterns:**
- "important:", "note:", "key point:"
- Business requirements mentioned
- Technical constraints discussed
- Timeline references

## Output Structure

### Meeting Summary File

Creates `discovery/{date}-{meeting-type}-summary.md`:

```markdown
# Meeting Summary: {Title}

> Date: {DATE} | Duration: {duration} | Participants: {count}

## TL;DR

{2-3 sentence summary}

## Decisions Made

{list of decisions with links to DECISIONS.md entries}

## Action Items

| Owner | Task | Due |
|-------|------|-----|
| ... | ... | ... |

## Risks Identified

{list of risks flagged}

## Key Discussion Points

### {Topic 1}
{summary}

### {Topic 2}
{summary}

## Open Questions

- {question 1}
- {question 2}

## Next Steps

1. {next step}
2. {next meeting if scheduled}

---
*Source: {original-transcript-path}*
*Indexed to RAG: {timestamp}*
```

### DECISIONS.md Updates

Appends to existing DECISIONS.md:

```markdown
### {Decision Title} (from {Meeting Date})
- **Decided**: {DATE}
- **Decision**: {content}
- **Context**: {surrounding discussion summary}
- **Participants**: {list from meeting}
- **Source**: Meeting transcript - {path}
```

### RAG Indexing

Indexes two files:
1. **Original transcript** - for full-text search
2. **Meeting summary** - for structured search

**Metadata added:**
```json
{
  "type": "meeting",
  "date": "2024-01-15",
  "participants": ["Alice", "Bob"],
  "topics": ["discovery", "requirements"],
  "has_decisions": true,
  "has_actions": true
}
```

## Workflow

### Step 1: Read and Parse

```python
# Detect format from file extension
# Parse speaker labels if present
# Clean timestamps and artifacts
# Split into logical segments
```

### Step 2: Extract Information

```python
# For each segment:
#   - Check for decision triggers
#   - Check for action triggers
#   - Check for risk triggers
#   - Identify topics discussed
```

### Step 3: Generate Summary

```python
# Create meeting summary file
# Include all extracted elements
# Generate TL;DR using key points
```

### Step 4: Update Memory

```python
# Append decisions to DECISIONS.md
# Create action items (if CTM active)
# Flag risks to risk register (if exists)
```

### Step 5: Index to RAG

```bash
# Index original transcript
rag_index path={transcript-path}

# Index generated summary
rag_index path={summary-path}
```

## Configuration

**Default behavior (in CLAUDE.md):**

```markdown
## Meeting Indexer Settings

- Auto-run on new files in: `discovery/*.txt`, `discovery/*.vtt`
- Decision threshold: HIGH confidence only
- Action owner matching: Fuzzy (handles nicknames)
- RAG indexing: Always
```

## Error Handling

| Scenario | Action |
|----------|--------|
| No speaker labels | Process as single-speaker transcript |
| Unclear decision ownership | Flag for manual review |
| Duplicate decision detected | Skip, note in summary |
| RAG unavailable | Create summary, skip indexing |
| Very long transcript (>50 pages) | Process in chunks |

## Output Files

**Created:**
- `discovery/{date}-{type}-summary.md` - Meeting summary

**Updated:**
- `.claude/context/DECISIONS.md` - New decisions appended
- `.rag/` - Indexed content

## Integration

After processing:
1. **CTM** receives action items as potential tasks
2. **RAG** can answer questions about meeting content
3. **Decision tracker** has new entries to reference
4. **Project memory** is enriched with context

## Example Usage

```bash
# Single transcript
/meeting-indexer discovery/2024-01-15-kickoff.txt

# Batch process folder
/meeting-indexer discovery/*.vtt

# With specific project
/meeting-indexer --project ~/.claude/clients/acme discovery/meeting.txt
```

## CDP Output

**OUTPUT.md:**
```markdown
# Meeting Indexer Complete

## Processed
- **File**: discovery/2024-01-15-kickoff.txt
- **Duration**: ~45 minutes (estimated)
- **Participants**: 5 identified

## Extracted
| Type | Count |
|------|-------|
| Decisions | 3 |
| Action Items | 7 |
| Risks | 2 |
| Topics | 4 |

## Files Created
- `discovery/2024-01-15-kickoff-summary.md`

## Memory Updated
- DECISIONS.md: 3 entries added
- RAG: 2 files indexed

## Action Items for Review
| Owner | Task | Confidence |
|-------|------|------------|
| Alice | Review API spec | HIGH |
| Bob | Schedule follow-up | MEDIUM |
```

---

## Learned Patterns

> This section is populated by the agent as it learns.
> See ~/.claude/AGENT_STANDARDS.md Section 14 for self-improvement protocol.

### Proposed Improvements

<!-- Tier 2 changes awaiting human approval -->
<!--
#### [YYYY-MM-DD] - [Title]
**Observation:** What was found (with evidence)
**Occurrences:** N times over M days
**Current behavior:** What happens now
**Proposed change:** What should change
**Revert instructions:** How to undo
**Conflicts:** None / [list any conflicts]
-->

*No pending proposals.*

### Approved Patterns

<!-- Tier 1 auto-applied + Tier 2 approved -->
<!--
#### [YYYY-MM-DD] - [Title]
**Discovery:** What was found
**Evidence:** N occurrences, context
**Applied:** What changed
**Impact:** Speed/reliability/accuracy improvement
-->

*No patterns learned yet.*

### Known Limitations

<!-- Documented failure modes and edge cases -->

*No limitations documented yet.*
