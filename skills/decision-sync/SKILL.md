---
name: decision-sync
description: Reconcile decisions between conversation files and DECISIONS.md to prevent documentation drift
trigger: /decision-sync
model: haiku
tools:
  - Read
  - Grep
  - Glob
  - Edit
context: fork
---

# decision-sync

Reconcile decisions between conversation files and DECISIONS.md to prevent documentation drift.

## Trigger

Invoke when:
- User says "decision sync", "/decision-sync", "sync decisions", "reconcile decisions"
- Hook detects decision drift (conversation files have resolved items, DECISIONS.md shows pending)
- User asks "what decisions have been made?" or "is X still a blocker?"
- After discovering that documented blockers are actually resolved

## Description

This skill scans for decision-related keywords in conversation files (*.txt) and compares them against the project's DECISIONS.md. It surfaces discrepancies where decisions were made in conversations but not back-propagated to documentation.

## Workflow

### Step 1: Discover Conversation Files

Scan for `.txt` files in project root and `input/` directories:
- Files matching `YYYY-MM-DD-*.txt` (Claude session exports)
- Files matching `transcript*.txt` (meeting transcripts)
- Files matching `*conversation*.txt`

### Step 2: Extract Decisions

Search for decision patterns:
```
- "resolved" / "all resolved" / "yes resolved"
- "decided" / "we decided" / "decision:"
- "confirmed" / "confirming"
- "Question X: yes"
- "agreed" / "signed off"
```

Extract surrounding context (±5 lines) for each match.

### Step 3: Compare Against DECISIONS.md

Read `.claude/context/DECISIONS.md` and identify:
- Items marked "PENDING" or "Awaiting"
- Items with dates older than conversation files
- Topics mentioned in conversations but not in DECISIONS.md

### Step 4: Generate Reconciliation Report

Output a table showing:
| Decision Topic | DECISIONS.md Status | Conversation Status | Source File | Recommended Action |
|----------------|---------------------|---------------------|-------------|-------------------|

### Step 5: Offer Updates

Ask user:
> "Found X decisions in conversations that may update DECISIONS.md. Would you like me to update?"

If yes, update DECISIONS.md with:
- Change status from PENDING to RESOLVED
- Add date and source reference
- Move to appropriate section

## Example Output

```
## Decision Sync Report

### Discrepancies Found: 2

| Topic | DECISIONS.md | Conversations | Source |
|-------|--------------|---------------|--------|
| InforLN Credentials | ⏳ PENDING | ✅ "yes all resolved" | 2025-12-18-honestly-*.txt |
| Webhooks vs Polling | ⏳ PENDING | ✅ "webhooks" | 2025-12-18-honestly-*.txt |

### Recommended Updates

1. **InforLN Credentials** → Mark as RESOLVED (Dec 2025)
2. **Sync Mechanism** → Update to "Webhooks decided" (Dec 2025)

Would you like me to update DECISIONS.md?
```

## Files Modified

- `.claude/context/DECISIONS.md` - Updates status, adds resolution dates

## Notes

- Always preserve original decision context when updating
- Add "Source: [filename]" reference for traceability
- Don't delete PENDING items, change status to RESOLVED with date
