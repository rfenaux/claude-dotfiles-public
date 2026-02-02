# PRD: performance-expert

## Overview

**Agent Name:** `performance-expert`
**Purpose:** Technical expert for Claude Code performance optimization and resource management
**Model:** Haiku (fast diagnostics) or Sonnet (complex analysis)

## Problem Statement

Users need guidance on optimizing Claude Code performance:
- Resource profiles and load management
- Model selection for cost/speed optimization
- Token optimization cascades
- Agent spawning strategies
- Context window management

## Key Capabilities

### 1. Resource Management
- Configure resource profiles (balanced/performance/conservative)
- Monitor system load with check-load.sh
- Recommend profile switches
- Manage agent spawning limits

### 2. Model Selection Optimization
- Guide model selection by task type:
  - Haiku: exploration, file lookups, RAG + synthesis
  - Sonnet: implementation, reviews, planning
  - Opus: architecture, complex integration
- Estimate token usage
- Recommend cost-effective approaches

### 3. Token Optimization
- Implement cascade pattern: Codex → Gemini → Claude
- Delegate bulk analysis to external models
- Use Gemini for >200K context
- Reserve Claude for tool-dependent tasks

### 4. Performance Diagnostics
- Identify bottlenecks
- Analyze context window usage
- Recommend /clear points
- Optimize parallel vs sequential execution

## Tools Required

- Bash (run diagnostics, check-load.sh)
- Read (analyze configs)
- Write (update profiles)
- Edit (optimize settings)

## Resource Profiles

| Profile | Max Agents | Load Threshold | Use Case |
|---------|------------|----------------|----------|
| balanced | 4 | 8.0 | Default - general work |
| performance | 6 | 12.0 | Focused Claude sessions |
| conservative | 3 | 4.8 | Running other apps |

## Load-Aware Spawning Rules

| Status | Action |
|--------|--------|
| OK | Spawn freely (parallel allowed) |
| CAUTION | Sequential only - wait for completion |
| HIGH_LOAD | Work inline - no new agents |
| Limit reached | Queue work - don't spawn |

## Token Optimization Cascade

```
1. codex-delegate (default)
   ↓ (quota exceeded or unavailable)
2. gemini-delegate (fallback)
   ↓ (needs Claude tools)
3. Claude (final)
```

## Trigger Patterns

- "optimize Claude Code performance"
- "reduce token usage"
- "which model should I use"
- "too many agents running"
- "context window full"

## Scripts Reference

```bash
~/.claude/scripts/check-load.sh          # Check current load
~/.claude/scripts/switch-profile.sh      # Change profile
~/.claude/scripts/detect-device.sh       # Device info
```

## Integration Points

- Reads ~/.claude/RESOURCE_MANAGEMENT.md
- Uses codex-delegate and gemini-delegate agents
- Coordinates with agent spawning decisions
- Works with reasoning-duo/trio for validation

## Success Metrics

- Response latency optimized
- Token costs reduced
- Agent limits respected
- System load managed
