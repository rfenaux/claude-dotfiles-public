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
Conversation ends
       ↓
[save-conversation.sh] saves transcript
       ↓
[lesson-extractor.sh] scores for lesson signals
       ↓ (if score ≥ 3)
[analyze-lessons.py] calls Anthropic API (background)
       ↓
Extracted lessons → ~/.claude/lessons/review/
       ↓
[User runs: cc lessons review]
       ↓
Approve → lessons.jsonl + RAG indexed
Reject  → archive/
```

**Fully automated extraction.** Manual approval still required.

The extraction uses `claude --print` (non-interactive mode) with Haiku by default. Runs in background after each substantive conversation. Uses existing Claude Code auth.

## Storage Structure

```
~/.claude/lessons/
├── lessons.jsonl        # Approved lessons (SSOT)
├── index.json           # Statistics and metadata
├── review/              # Extracted lessons awaiting approval
├── pending/             # Conversations queued for analysis
├── archive/             # Rejected/superseded lessons
└── .rag/                # RAG embeddings (approved only)
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
cc lessons review          # Interactive approval workflow
cc lessons queue           # Conversations awaiting analysis
cc lessons extract <file>  # Manual extraction from file
cc lessons approve <id>    # Approve specific lesson
cc lessons reject <id>     # Reject specific lesson
cc lessons show <id>       # View lesson details
cc lessons search "query"  # Semantic search (approved only)
cc lessons list [type]     # List approved lessons
cc lessons archive         # View rejected lessons
cc health                  # System health check
```

## Confidence Scoring

| Score | Meaning | Surfacing |
|-------|---------|-----------|
| ≥0.8 | Validated multiple times | Always shown |
| 0.7-0.8 | Seen once, high confidence | Shown when relevant |
| 0.5-0.7 | Tentative | Pending validation |
| <0.5 | Low confidence | Not surfaced |

## Global Availability

Lessons are RAG-indexed independently of any project. All agents can query via:

```bash
rag_search("query", "~/.claude/lessons")
```

## Automatic Surfacing (CTM Integration)

Lessons are automatically surfaced on session start based on context from:

1. **CTM Task Context** (primary) - Active/recent task title + tags from `~/.claude/ctm/index.json`
2. **Directory Context** (secondary) - Path detection (HubSpot, <PROJECT>, etc.)

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

## When to Query Lessons Manually

- Starting work in a domain with past experience (HubSpot, APIs, etc.)
- Encountering errors or unexpected behavior
- Before implementing patterns that might have known gotchas
