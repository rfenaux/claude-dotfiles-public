# Async Routing Guide

> When to run agents synchronously vs asynchronously

## Overview

Agents can run **synchronously** (blocking, interactive) or **asynchronously** (background, parallel). The routing decision affects user experience and resource utilization.

## Decision Logic

Check agent frontmatter for `async.mode`:

| Mode | Behavior |
|------|----------|
| `always` | Run in background automatically |
| `never` | Run synchronously (blocking) |
| `auto` | Decide based on task + heuristics below |

## Auto Mode Heuristics

### Prefer Async When

- Task involves multiple files (>5)
- Task is analysis/summary (not creation)
- No mid-execution decisions needed
- Agent model is haiku
- Keywords in request: "bulk", "summarize all", "analyze these", "in background"

### Require Sync When

- Agent needs iterative feedback (ERD, BPMN, specs)
- High-stakes deliverables requiring validation
- User says "with me", "interactively", "sync"
- Keywords: "design", "create", "review"

## Override Syntax

User can force execution mode:
- `"in background"` / `"async"` → force background
- `"sync"` / `"interactively"` / `"with me"` → force synchronous

Example: `"run erd-generator in background"` overrides `mode: never`

## Announcement Format

When spawning agents, announce mode:
- Sync: `[Running {agent} synchronously]`
- Async: `[Running {agent} in background - will notify on completion]`

## Completion Notification

When async agent completes:
1. Announce: `[Agent {agent} completed - results in {workspace}/OUTPUT.md]`
2. If CTM active: `ctm context add --note "Agent completed: {summary}"`

## Agent Frontmatter Example

```yaml
---
name: new-agent-name
description: What this agent does...
model: sonnet
async:
  mode: auto          # always | never | auto
  prefer_background:  # when to favor async
    - bulk processing
    - analysis
  require_sync:       # when to force sync
    - user decisions
    - iterative feedback
---
```

## Mode Selection Guide

| Choose | When |
|--------|------|
| `always` | No user interaction needed (reports, data gen, conversions) |
| `never` | Requires feedback loops (design, specs, presentations) |
| `auto` | Context-dependent (most agents) |

## Full Specification

See `~/.claude/AGENT_STANDARDS.md` Section 11 for complete details.
