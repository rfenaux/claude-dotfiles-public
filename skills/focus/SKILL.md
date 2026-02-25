---
name: focus
description: ADHD focus anchor - re-centering, task display, and topic parking
---

# /focus - ADHD Focus Anchor

Quick re-centering when you feel scattered or want to check what's parked.

## Commands

| Command | Action |
|---------|--------|
| `/focus` | Show current task + parked items |
| `/focus park <topic>` | Quickly park a thought without switching |
| `/focus clear` | Review and clear parked items |

## When User Invokes `/focus`

Display this format:

```
┌─────────────────────────────────────────────────────────────┐
│  FOCUS ANCHOR                                               │
├─────────────────────────────────────────────────────────────┤
│  CURRENT TASK: [CTM active task name]                       │
│  Progress: [X]%  |  Step: [current step from CTM]           │
├─────────────────────────────────────────────────────────────┤
│  PARKED IDEAS ([count]):                                    │
│  • [parked item 1]                                          │
│  • [parked item 2]                                          │
│  (none) ← if empty                                          │
├─────────────────────────────────────────────────────────────┤
│  NEXT ACTION: [what we were about to do]                    │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

1. Run `ctm status` to get active task
2. Run `ctm status --priority low` to get parked items (tasks starting with "parked:")
3. Format and display the anchor box
4. End with a gentle prompt: "Ready to continue, or want to switch focus?"

## `/focus park <topic>`

Quick-park without interrupting flow:

```bash
ctm spawn "parked: <topic>" --priority low
```

Response: "Parked: **<topic>**. Back to [current task]."

## `/focus clear`

Interactive review of parked items:

1. List all parked items with numbers
2. For each, ask: "Still want this? (keep/delete/promote)"
   - **keep** - Leave in parking lot
   - **delete** - Remove (`ctm complete <id>` with note "dropped")
   - **promote** - Make it a real task (`ctm spawn "<topic>" --priority medium`)
3. Show updated parking lot

## Auto-Invocation

This skill can be invoked by me when:
- User says "wait, what were we doing?"
- User says "I'm lost" or "where was I?"
- User returns after apparent break (>5 min gap in conversation)
- Conversation has had 3+ topic switches without completing anything

## Tone

Grounding, not judgmental. The parking lot is a feature, not a failure. Having ideas is good - capturing them lets us finish things.
