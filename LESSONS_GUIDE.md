# Learned Lessons System Guide

> Automatic extraction of experiential knowledge from conversations

## Overview

The Learned Lessons system extracts reusable knowledge from Claude Code conversations - technical patterns, user preferences, strategies, and anti-patterns. Lessons are globally available across all projects.

## What Gets Captured

| Type | Description | Example |
|------|-------------|---------|
| **Technical** | API quirks, tool behaviors, workarounds | "Ollama timeouts on >500 token chunks" |
| **Preferences** | User communication/workflow preferences | "Always propose phased approach" |
| **Strategies** | Problem-solving approaches that work | "Check API docs before trial-and-error" |
| **Anti-patterns** | Things NOT to do | "Never use Read tool on XLSX files" |

## How It Works

```
Tool success/failure during session
       ↓
[post-tool-learning.sh / failure-learning.sh]
       ↓
Dedup check via confidence.py check-and-merge
       ↓
Duplicate found? → Increment occurrences, boost confidence (SONA)
New lesson?      → Auto-approve at confidence 0.70, append to JSONL
       ↓
Periodic compilation → compiled/{tag}.md summaries
```

**Fully automated.** Lessons are auto-approved on first capture (confidence 0.70) and auto-promoted on recurrence via SONA success formula. No manual review required.

Batch extraction from conversation transcripts also auto-approves. The `review/` directory is available for manual override only.

## Storage Structure

```
~/.claude/lessons/
├── lessons.jsonl        # Approved lessons (SSOT)
├── index.json           # Statistics and metadata
├── compiled/            # Domain-grouped summaries (auto-generated)
│   ├── INDEX.md         # Compilation index
│   ├── hubspot.md       # HubSpot domain lessons
│   ├── rag.md           # RAG domain lessons
│   └── ...              # One per tag with 5+ lessons
├── scripts/
│   ├── confidence.py    # SONA formulas + check-and-merge dedup
│   ├── compile-lessons.py  # Compilation engine
│   └── migrate-lessons.py  # One-time migration (run once)
├── review/              # Manual override only (auto-approve is default)
├── pending/             # Legacy (hooks now write to JSONL directly)
├── archive/             # Rejected/superseded lessons
└── .rag/                # RAG embeddings (approved + compiled)
```

## Lesson Signals Detected

The extractor looks for:
- **Iteration struggles**: Errors → workarounds, multiple tool retries
- **Clarification cycles**: Misunderstandings corrected, preferences revealed
- **Breakthroughs**: "Works!", "Figured it out", "The trick is..."
- **User preferences**: "I prefer...", "I always...", "My style is..."

## Commands

```bash
cc lessons stats           # Statistics
cc lessons show <id>       # View lesson details
cc lessons search "query"  # Semantic search (approved only)
cc lessons list [type]     # List approved lessons
cc lessons archive         # View rejected lessons
cc health                  # System health check

# Confidence management
python3 ~/.claude/lessons/scripts/confidence.py feedback <id> --success|--failure
python3 ~/.claude/lessons/scripts/confidence.py decay
python3 ~/.claude/lessons/scripts/confidence.py show <id>
python3 ~/.claude/lessons/scripts/confidence.py check-and-merge  # stdin: JSON
python3 ~/.claude/lessons/scripts/confidence.py batch-promote

# Compilation
python3 ~/.claude/lessons/scripts/compile-lessons.py  # Generate domain summaries
```

## Confidence Scoring

| Score | Meaning | Surfacing |
|-------|---------|-----------|
| ≥0.8 | Validated multiple times (auto-promoted by recurrence) | Always shown |
| 0.70 | First capture (auto-approved) | Shown when relevant |
| 0.5-0.7 | Decayed or legacy | Lower priority |
| <0.5 | Low confidence | Not surfaced |

**Auto-promotion:** Each recurrence applies SONA success: `conf = min(0.99, conf + 0.05 * (1-conf))`. A lesson seen 3 times reaches 0.786, 6 times reaches 0.858.

**Occurrence tracking:** Each lesson has an `occurrences` counter. Duplicates are detected by title similarity (>60% word overlap) or error signature match, then merged.

## Global Availability

Lessons are RAG-indexed independently of any project. All agents can query via:

```bash
rag_search("query", "~/.claude/lessons")
```

## Automatic Surfacing (CTM Integration)

Lessons are automatically surfaced on session start based on context from:

1. **CTM Task Context** (primary) - Active/recent task title + tags from `~/.claude/ctm/index.json`
2. **Directory Context** (secondary) - Path detection (HubSpot, Enterprise, etc.)

```
Session Start
    │
    └─→ lesson-surfacer.sh
        ├─→ Read CTM tasks → extract keywords (title + tags)
        ├─→ Detect directory context
        ├─→ Combine → search lessons.jsonl
        └─→ Surface top 3 matches in session context
```

**Example output:**
```markdown
### Relevant Lessons for This Context

**HubSpot Payments unavailable in sandbox**
  HubSpot Payments is not supported in sandbox accounts...
  _Tags: hubspot, commerce-hub, sandbox_

_Source: CTM task | Query: "integration hubspot api workflows..."_
```

The system automatically connects what you're working on (CTM) with what you've learned (Lessons).

## CTM Bidirectional Integration (v2.0)

Lessons now track which CTM task they were learned during:

```bash
# New fields in lesson JSON:
# - ctm_task_id: active CTM agent when lesson was captured
# - ctm_task_ids: all CTM tasks where this lesson appeared (union on merge)

# Query lessons by task
python3 ~/.claude/lessons/scripts/confidence.py task-lessons <task-id>

# Apply SONA feedback when a task completes
python3 ~/.claude/lessons/scripts/confidence.py task-feedback <task-id> --success|--failure

# Query lessons by tags (for task switch surfacing)
python3 ~/.claude/lessons/scripts/confidence.py by-tags <tag1,tag2> --min-conf 0.8 --limit 5
```

## Lesson Archival (TTL)

Stale lessons are archived automatically:
- **Threshold:** confidence < 0.40 AND last activity > 90 days
- **Frequency:** Monthly (30-day cooldown)
- **Destination:** `archive/low-confidence/archived-{date}.jsonl`

```bash
python3 ~/.claude/lessons/scripts/archive-stale.py --dry-run  # Preview
python3 ~/.claude/lessons/scripts/archive-stale.py             # Execute
python3 ~/.claude/lessons/scripts/archive-stale.py --force     # Skip cooldown
```

## Known Limitations

| Limitation | Status | Notes |
|------------|--------|-------|
| No surfacing metrics | Planned | Can't measure which lessons get used |
| Error signature tracking is grep-based | Known | MD5 of tool+error, not semantic |
| Lesson-analyzer review queue undocumented | Known | `review/` dir exists but no CLI workflow |
| No lesson versioning / supersession | Known | Can't mark lesson A replaced by B |
| Cold-start for new users | Inherent | ~20+ sessions needed before useful patterns emerge |

## When to Query Lessons Manually

- Starting work in a domain with past experience (HubSpot, APIs, etc.)
- Encountering errors or unexpected behavior
- Before implementing patterns that might have known gotchas
