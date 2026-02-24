---
name: slack-sync-ritual
description: Sync decisions, blockers, and actions from Slack channels into CTM and project memory.
async:
  mode: never
  require_sync:
    - Slack MCP access (main session only)
    - CTM updates
    - user confirmation
---

# /slack-sync - Slack Sync Ritual

Bridge between Slack conversations and project documentation. Searches project Slack channels for decisions, blockers, and actions, then updates CTM context with confirmed items. Found in 3+ sessions across Rescue-Late and acme-corp projects.

**IMPORTANT**: Must run in main session — Slack MCP tools are not available to sub-agents. If invoked from a sub-agent context, inform user to run `/slack-sync` directly.

## Trigger

Invoke this skill when:
- User says `/slack-sync`, "sync Slack", "check Slack", "what happened on Slack?"
- Before status updates when team communicates via Slack
- After being away from project for >24h
- When decisions seem missing from CTM/DECISIONS.md

## Why This Exists

Team decisions made in Slack channels — agreements, approach choices, timeline confirmations — frequently don't make it into project documentation. This creates documentation drift where DECISIONS.md is stale and CTM is incomplete. Regular syncing closes this gap.

## Commands

| Command | Action |
|---------|--------|
| `/slack-sync` | Full 5-step sync ritual |
| `/slack-sync --channel #name` | Sync specific channel only |
| `/slack-sync --since 2d` | Only messages from last 2 days |
| `/slack-sync --decisions` | Extract decisions only |
| `/slack-sync --dry-run` | Show what would be synced without updating |

## Workflow

### Step 1: Search Slack
Search project-relevant Slack channels for messages since last sync. Use `slack_search_public` with project keywords and `after:` date filter.

### Step 2: Extract Decisions
Identify decision patterns in messages:
- "decided", "going with", "confirmed", "agreed", "let's do"
- Capture: decision text, who decided, when, thread context

### Step 3: Extract Blockers
Identify blocker patterns:
- "blocked", "waiting on", "can't proceed", "delayed", "stuck"
- Capture: what's blocked, who's blocking, since when

### Step 4: Update CTM
After user confirmation, add to CTM context:
- `ctm context add --decision "..."` for decisions
- `ctm context add --blocker "..."` for blockers

### Step 5: Flag Unconfirmed
Items with ambiguous context flagged as [NEEDS CONFIRMATION] for manual review.

## Output Format

```
Slack Sync (#channel-name, last 48h):
  Decisions: [N] found
    [1] "Going with Option B for pricing" (@person, date)
  Blockers: [M] found
    [1] "Waiting on API credentials" (since date)
  Actions: [K] found
    [1] "@person to send test data by Friday"

  Already in CTM: [X] skipped
  New to add: [Y]
  Add to CTM? [y/n/select]
```

## Integration

- **Slack MCP**: `slack_search_public`, `slack_read_channel`, `slack_read_thread`
- **`slack-ctm-sync` agent**: Agent wrapper for this skill's logic
- **CTM**: `ctm context add` for decisions/blockers
- **DECISIONS.md**: Records confirmed decisions
