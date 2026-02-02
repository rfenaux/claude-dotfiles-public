# PRD: agent-coordination-expert

## Overview

**Agent Name:** `agent-coordination-expert`
**Purpose:** Technical expert for multi-agent coordination and orchestration
**Model:** Sonnet (complex reasoning + orchestration)

## Problem Statement

Users need guidance on coordinating multiple Claude Code agents:
- CDP (Cognitive Delegation Protocol) implementation
- Parent-child agent relationships
- Context passing between agents
- Load-aware spawning strategies
- Result aggregation patterns

## Key Capabilities

### 1. CDP Implementation
- Design agent handoff patterns
- Create HANDOFF.md specifications
- Process OUTPUT.md results
- Manage depth limits (max 3 levels)

### 2. Orchestration Patterns
- Parallel agent execution
- Sequential workflow chains
- Fan-out/fan-in patterns
- Error handling and recovery

### 3. Load-Aware Coordination
- Check system load before spawning
- Respect agent limits per profile
- Queue work when at capacity
- Avoid killing running agents

### 4. Context Management
- Pass context via HANDOFF.md
- Aggregate results from OUTPUT.md
- Maintain session coherence
- Handle cross-agent state

## Tools Required

- Task (spawn agents)
- Read (HANDOFF.md, OUTPUT.md)
- Write (coordination files)
- Bash (check-load.sh)

## CDP Protocol

### Agent Spawning Pattern

```
Primary Agent
    │
    ├── Writes HANDOFF.md (context + instructions)
    │
    ├── Spawns Sub-Agent via Task tool
    │
    ├── Sub-Agent executes
    │
    ├── Sub-Agent writes OUTPUT.md (results)
    │
    └── Primary reads OUTPUT.md
```

### HANDOFF.md Structure

```markdown
# Task Handoff

## Context
- Project: [project path]
- Goal: [task goal]
- Constraints: [any limitations]

## Input
[Input data or file references]

## Expected Output
[What the sub-agent should produce]

## Notes
[Any additional context]
```

### OUTPUT.md Structure

```markdown
# Task Output

## Summary
[Brief summary of what was done]

## Results
[Actual output/deliverables]

## Decisions Made
[Any decisions during execution]

## Issues Encountered
[Problems or blockers]
```

## Depth Limits

| Level | Can Spawn | Notes |
|-------|-----------|-------|
| L1 (Primary) | Yes | Can spawn L2 |
| L2 | Yes | Can spawn L3 |
| L3 | No | Terminal - work inline |

## Load-Aware Spawning

```bash
# Check before spawning
~/.claude/scripts/check-load.sh --can-spawn

# Returns:
# OK - spawn freely
# CAUTION - sequential only
# HIGH_LOAD - work inline
```

## Coordination Patterns

### Parallel Execution
```
Primary
├── Agent A (background)
├── Agent B (background)
└── Agent C (background)
    └── Wait for all, aggregate results
```

### Sequential Chain
```
Primary → Agent A → Agent B → Agent C
    └── Pass context through chain
```

### Fan-Out/Fan-In
```
Primary
├── Spawn 5 workers (fan-out)
└── Aggregate 5 results (fan-in)
```

## Trigger Patterns

- "coordinate multiple agents"
- "set up agent delegation"
- "CDP best practices"
- "parallel agent execution"
- "agent orchestration help"

## Integration Points

- Uses CDP_PROTOCOL.md for patterns
- Coordinates with `reasoning-duo/trio` agents
- Works with `codex-delegate`, `gemini-delegate`
- Respects RESOURCE_MANAGEMENT.md limits

## Success Metrics

- Clean agent handoffs
- Proper context passing
- Load limits respected
- Results properly aggregated
