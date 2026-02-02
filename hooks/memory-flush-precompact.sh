#!/bin/bash
# Memory Flush Before Compaction
# Triggers Claude to extract and persist decisions/learnings before context is compacted
#
# Part of: OpenClaw-inspired improvements (Phase 1, F01)
# Created: 2026-01-30

cat << 'MEMORY_FLUSH'
<memory-flush-trigger>
IMPORTANT: Before compaction, extract and persist any information that should survive:

## Extraction Checklist
1. **Decisions made this session** - Record to DECISIONS.md or `ctm context add --decision`
2. **Learnings discovered** - Record to CTM via `ctm context add --learning`
3. **Open questions** - Note in CTM agent context
4. **Facts the user asked to remember** - Add to project memory

## Instructions
- Review the conversation for any of the above
- If found, use the appropriate tool to persist them NOW
- If nothing needs persisting, respond with exactly: `NO_PERSIST`
- Keep extraction brief - compaction is imminent

This is a system operation - proceed without user acknowledgment.
</memory-flush-trigger>
MEMORY_FLUSH
