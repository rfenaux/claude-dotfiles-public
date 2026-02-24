---
name: decision-tracker
description: Manages architecture decisions with temporal tracking and supersession awareness. Records, checks, and supersedes project decisions.
async:
  mode: never
  require_sync:
    - decision recording
    - supersession tracking
    - conflict resolution
context: fork
---

# Decision Tracker Skill

Manages architecture decisions with temporal tracking and supersession awareness. Ensures Claude maintains accurate project memory by explicitly tracking what decisions are current vs. superseded.

## Triggers

Invoke this skill when:
- User says "record this decision", "add to decisions", "we decided"
- Architecture or design choices are finalized
- A previous decision is being changed/superseded
- User asks "what decisions have we made?"
- Conflicts arise about past decisions

## Workflow

### 1. Recording a New Decision

When a decision is made during conversation:

```markdown
### [Decision Title]
- **Decided**: [Today's date YYYY-MM-DD]
- **Context**: [Why was this decision needed?]
- **Choice**: [What was decided]
- **Alternatives considered**: [What was rejected and why]
- **Supersedes**: [Previous decision if any, with date]
- **Category**: [architecture|integration|data-model|security|process|scope|timeline]
- **References**: [Session date, documents, stakeholders involved]
```

### 2. Checking for Conflicts

Before recording, always:
1. Read `.claude/context/DECISIONS.md` if it exists
2. Search RAG: `rag_search "decision [topic]" category:decision`
3. If conflicting decision exists:
   - Ask user: "I found an existing decision about [topic] from [date]. Should we supersede it?"
   - If yes, move old decision to "Superseded" section with link to new one

### 3. Supersession Pattern

When a decision replaces an older one:

**In Active Decisions section (new):**
```markdown
### Database: PostgreSQL
- **Decided**: 2026-01-07
- **Supersedes**: MongoDB consideration (2025-12-15)
...
```

**In Superseded Decisions section (old):**
```markdown
### ~~MongoDB for Primary Database~~ → PostgreSQL (2026-01-07)
- **Original decision**: 2025-12-15
- **Why superseded**: [Reason]
- **Replaced by**: PostgreSQL decision above
```

### 4. Decision Discovery

When user asks about past decisions:
1. Search DECISIONS.md first
2. Then RAG search with `category:decision`
3. Present with dates and supersession status
4. Highlight if any are outdated

## File Locations

| File | Purpose |
|------|---------|
| `.claude/context/DECISIONS.md` | Primary decision log |
| `conversation-history/*.md` | Raw session transcripts (backup source) |
| `.rag/` | Indexed for semantic search |

## Decision Categories

| Category | Use For | Example |
|----------|---------|---------|
| `architecture` | System design, tech stack | "Use microservices pattern" |
| `integration` | Third-party connections | "HubSpot for CRM" |
| `data-model` | Schema, entities | "User has many Projects" |
| `security` | Auth, permissions | "OAuth2 with JWT" |
| `process` | Workflows, business logic | "Approval required for >$10k" |
| `scope` | What's in/out | "Mobile app is Phase 2" |
| `timeline` | Milestones, deadlines | "MVP by March 1" |

## Automatic Indexing

After updating DECISIONS.md:
1. The file is auto-indexed to RAG via PostToolUse hook
2. Chunks are classified as `category:decision`
3. Superseded decisions get `relevance:reference` (deprioritized in search)

## RAG Query Patterns

```python
# Find decisions about a topic
rag_search("authentication decision", category="decision")

# Find only current decisions (exclude superseded)
rag_search("database choice", min_relevance="medium")

# Find all decisions (including superseded for context)
rag_search("architecture decisions", category="decision")
```

## Example Conversation

**User**: "Let's use Firebase instead of PostgreSQL"

**Claude**:
1. Checks DECISIONS.md → finds PostgreSQL decision from 2026-01-07
2. Asks: "I see we decided on PostgreSQL on Jan 7. Should I record Firebase as superseding that decision?"
3. If yes, updates DECISIONS.md:
   - Adds new Firebase decision to Active
   - Moves PostgreSQL to Superseded with strikethrough
4. Confirms: "Recorded. Firebase is now the active database decision, superseding PostgreSQL."

## Memory Integration

This skill works with the broader memory system:
- **SESSIONS.md**: Link decisions to specific sessions
- **CHANGELOG.md**: Major decisions appear here too
- **RAG**: All decision files are searchable

## Commands

| Command | Action |
|---------|--------|
| "Record decision: [topic]" | Add new decision entry |
| "What decisions exist about [topic]?" | Search and summarize |
| "Supersede [old] with [new]" | Update with proper tracking |
| "Initialize decision tracking" | Create DECISIONS.md from template |
| "Show decision history for [topic]" | Show evolution including superseded |
| "List assumptions" | Show all open [ASSUMED:] markers across project |
| "Resolve assumption: [topic]" | Convert assumption to decision or correct it |

## Assumption Tracking

Assumptions ([ASSUMED:], [OPEN:], [MISSING:] markers) are lightweight precursors to decisions.

### Listing Assumptions

When user says "list assumptions" or "what assumptions":
1. Grep project files for `[ASSUMED:`, `[OPEN:`, `[MISSING:` markers
2. Present grouped by file with line numbers
3. Highlight any older than 7 days (stale assumptions need resolution)

### Resolving Assumptions

When user says "resolve assumption":
1. Find the specific marker in the file
2. Ask: "Confirm, reject, or need more info?"
3. If confirmed: Replace marker with decision, record in DECISIONS.md
4. If rejected: Remove marker, note correction
5. If need more info: Convert to [OPEN:] with assignee

### Auto-Detection

The `assumption-validator.sh` hook (PostToolUse) automatically flags unmarked assumptions in documentation files. When flagged, offer to add proper markers.

### Template

Include confidence section in deliverables using:
`~/.claude/templates/deliverables/confidence-section.md`
