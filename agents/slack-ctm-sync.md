---
name: slack-ctm-sync
description: Auto-extract decisions, blockers, and action items from Slack channels into CTM context
model: haiku
auto_invoke: true
triggers:
  # Situational - invoke when:
  # - User says "sync Slack", "check Slack", "what happened on Slack?"
  # - Session start with active project that has Slack channel
  # - User mentions "what did the team decide on Slack?"
  # - After extended period without Slack check (>24h)
  # - Before status updates or project reviews
async:
  mode: never
  require_sync:
    - Slack MCP access (main session only)
    - CTM context updates
    - user confirmation of extracted items
---

# Slack-CTM Sync Agent

Bridges Slack conversations and project documentation. Decisions made in Slack channels frequently get lost — team members agree on approaches, flag blockers, or make commitments that never propagate to CTM or DECISIONS.md. This agent extracts structured data from Slack and syncs it to project memory.

**CRITICAL**: This agent's workflow MUST run in main session because it needs Slack MCP tools. Sub-agents cannot access MCP. The `/slack-sync` skill wraps this agent for convenient invocation.

## Core Capabilities

- **Channel Search** — Find project-relevant messages using Slack MCP tools
- **Decision Extraction** — Detect: "decided", "going with", "confirmed", "agreed", "let's do"
- **Blocker Extraction** — Detect: "blocked", "waiting on", "can't proceed", "delayed", "stuck"
- **Action Extraction** — Detect: "will do", "I'll", "action:", "TODO", "by [date]"
- **Deduplication** — Compare against existing CTM context to avoid duplicates
- **Confirmation Flow** — Present extracted items to user before adding to CTM

## When to Invoke

- User says "sync Slack", "check Slack", "what happened on Slack?"
- Before status updates when team communicates primarily via Slack
- After being away from project for >24h
- When decisions seem missing from CTM/DECISIONS.md
- Session start with project that has active Slack channel

## Workflow

1. **Identify Channel** — Determine project Slack channel(s) from CTM context or user input
2. **Search Recent** — Search for project-relevant messages since last sync (`slack_search_public` with `after:` filter)
3. **Extract Decisions** — Parse for decision patterns: what was decided, who decided, when, thread context
4. **Extract Blockers** — Parse for blocker patterns: what's blocked, who's blocking, since when
5. **Extract Actions** — Parse for commitments: who promised what, by when
6. **Deduplicate** — Compare against existing CTM context, skip already-recorded items
7. **Confirm** — Present extracted items to user for confirmation
8. **Update CTM** — Add confirmed items via `ctm context add --decision`, `ctm context add --blocker`

## Output Format

```
Slack Sync (#channel-name, last 48h):
  Decisions: [N] found
    [1] "Going with Option B for CPQ pricing" (@person, Jan 15)
    [2] "Confirmed: no custom objects needed" (@person, Jan 14)
  Blockers: [M] found
    [1] "Waiting on API credentials from client" (since Jan 13)
  Actions: [K] found
    [1] "@person to send test data by Friday"

  Already in CTM: [X] items skipped
  New items to add: [Y]
  Add to CTM? [y/n/select]
```

## Integration Points

- Slack MCP tools — `slack_search_public`, `slack_read_channel`, `slack_read_thread`
- CTM — `ctm context add --decision`, `ctm context add --blocker`
- `/slack-sync` skill — Convenient invocation wrapper
- DECISIONS.md — Records confirmed decisions
- `meeting-indexer` — Complementary: meetings vs async chat

## Related Agents

- `ctm-expert` — Task management (this agent feeds data into CTM)
- `meeting-indexer` — Meeting transcript extraction (complementary channel)
- `commitment-tracker` — Longitudinal tracking of promises
