---
name: rename-smart
description: Smart session renaming with timestamp + AI-generated title. Auto-invoked after N messages, at PreCompact, SessionEnd, or manually via /rename-smart.
argument-hint: [force]
async:
  mode: never
  require_sync:
    - title generation
    - user confirmation
---

# Smart Session Rename

Generates intelligent session names combining creation timestamp and a concise title summarizing the conversation.

## Trigger

This skill is invoked:
- **Automatically** after 3-5 user messages (via hook)
- **At PreCompact** when context is getting full
- **At SessionEnd** to ensure session is properly named
- **Manually** via `/rename-smart`

## Behavior

1. **Check if already renamed**: Skip if session already has a smart name (unless `force` argument)
2. **Get session creation time**: Extract from session metadata
3. **Generate title**: Analyze conversation to create 3-5 word summary
4. **Format name**: `YYYY-MM-DD_HHMM_title-with-dashes`
5. **Execute rename**: Use `/rename` command

## Name Format

```
2026-01-23_1318_context-audit-expert-implementation
│           │    │
│           │    └── 3-5 word summary (lowercase, dashes)
│           └── Time (HHMM) of first message
└── Date of first message
```

## Examples

| Conversation About | Generated Name |
|--------------------|----------------|
| Building ERD for CRM | `2026-01-23_0915_crm-erd-design` |
| Debugging API auth | `2026-01-23_1430_api-auth-debugging` |
| HubSpot migration planning | `2026-01-23_1100_hubspot-migration-planning` |

## Implementation

When this skill is invoked, Claude should:

1. **Check rename state file** (`~/.claude/session-rename-state.json`):
   ```json
   {
     "renamed_sessions": ["session-id-1", "session-id-2"]
   }
   ```

2. **If not renamed (or force=true)**:
   - Read the conversation context
   - Identify the main topic/task
   - Generate a 3-5 word title (lowercase, use dashes)
   - Get session creation timestamp
   - Format: `YYYY-MM-DD_HHMM_title-here`

3. **Execute rename** via script:
   ```bash
   ~/.claude/scripts/rename-session.sh <session-id> "2026-01-23_1318_title-here"
   ```

   Or if session ID unknown, use `/rename` command directly.

4. **Update state file** with session ID

## Skip Conditions

Do NOT rename if:
- Session already has a timestamped name (matches `^\d{4}-\d{2}-\d{2}_\d{4}_`)
- Session has fewer than 3 user messages (unless at PreCompact/SessionEnd)
- Session ID is in `renamed_sessions` list (unless force=true)

## Manual Override

```
/rename-smart           # Normal - skip if already renamed
/rename-smart force     # Force rename even if already done
```
