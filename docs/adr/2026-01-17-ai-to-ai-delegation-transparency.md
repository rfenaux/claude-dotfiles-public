# ADR: AI-to-AI Delegation Transparency & Orchestration

> **Status**: Accepted
> **Date**: 2026-01-17
> **Deciders**: Raphaël Fenaux, Claude
> **Tags**: delegation, orchestration, CDP, multi-agent

## Context

Claude Code uses multiple AI systems for task delegation:
- **Claude → Claude** (sub-agents via Task tool)
- **Claude → Codex** (OpenAI CLI for code tasks)
- **Claude → Gemini** (Google CLI for bulk analysis)
- **Claude ↔ Codex** (reasoning-duo for collaborative problem-solving)

Prior to this decision, delegated AIs received prompts as if from a human. They had no context about:
1. Being in a delegation chain
2. Receiving work from another AI
3. Having a human as the ultimate stakeholder

Additionally, there were no controls on:
- How deep delegation chains could go (sub-agents spawning sub-agents)
- Whether to spawn based on system performance

## Decision

### 1. AI-to-AI Transparency

All delegation prompts now include explicit context about the AI-to-AI nature:

**For task delegation:**
```
[AI-TO-AI DELEGATION]
From: Claude (Anthropic) | To: [Target AI]
Chain: Human → Claude → You
Style: Be direct and technical. Skip explanations meant for humans.
```

**For collaborative reasoning:**
```
[AI-TO-AI COLLABORATION]
From: Claude (Anthropic) | To: Codex (OpenAI)
Mode: Reasoning Duo - Collaborative problem-solving
Your role: Challenge my assumptions, propose alternatives.
```

### 2. Depth Tracking (Max 3 Levels)

Sub-agents can delegate to their own sub-agents, but with limits:

```
Human
└── Primary (depth=0)     ← can spawn
    └── L1 (depth=1)      ← can spawn
        └── L2 (depth=2)  ← can spawn
            └── L3 (depth=3) ← CANNOT spawn
```

Depth is included in delegation preamble:
```
Max-Depth: 3 | Your-Depth: 2 | Can-Spawn: YES
```

### 3. Load-Aware Spawning

Before spawning, check system performance:

```bash
~/.claude/scripts/check-load.sh --status-only
```

| Status | Load Average | Spawning Policy |
|--------|--------------|-----------------|
| `OK` | < 5.0 | Parallel allowed |
| `CAUTION` | 5.0-10.0 | Sequential only |
| `HIGH_LOAD` | > 10.0 | Work inline |

## Rationale

### Why Transparency?

| Benefit | Impact |
|---------|--------|
| **Honesty** | Accurate representation of the interaction |
| **Efficiency** | Target AI skips human-oriented scaffolding |
| **Better reasoning-duo** | True peer debate when both know they're AIs |
| **Accountability** | Clear chain: Human → Primary → Sub-agent |
| **Calibrated output** | Target knows output is for AI synthesis |

### Why Depth Limits?

- **Prevent runaway chains**: Without limits, agents could spawn indefinitely
- **Maintain oversight**: Human can trace delegation max 3 levels deep
- **Resource management**: Deeper chains consume more context/tokens
- **Debugging**: Easier to trace issues in bounded chains

### Why Load-Aware Spawning?

- **Device protection**: Raphael's Mac shouldn't be overwhelmed
- **Graceful degradation**: High load → sequential → inline
- **User experience**: Prevent system slowdowns during heavy work
- **Cost efficiency**: Avoid spawning when system already strained

## Alternatives Considered

### 1. No Transparency (Rejected)
- Keep prompts as if from human
- **Rejected because**: Dishonest, inefficient, prevents true peer dialogue in reasoning-duo

### 2. Unlimited Depth (Rejected)
- Allow infinite delegation chains
- **Rejected because**: Risk of runaway spawning, hard to debug, resource exhaustion

### 3. No Load Checking (Rejected)
- Always spawn regardless of system state
- **Rejected because**: Poor user experience, potential system instability

### 4. Depth Limit of 2 (Considered)
- More conservative limit
- **Not chosen because**: 3 levels provides useful flexibility without excessive complexity

## Consequences

### Positive
- Clearer AI-to-AI communication
- More efficient (terse) responses from delegated AIs
- Bounded delegation prevents runaway chains
- System performance considered before spawning
- Better reasoning-duo debates with peer framing

### Negative
- Slightly longer prompts (preamble overhead)
- Depth=3 agents must work inline (can't delegate)
- Load checking adds small latency before spawning

### Neutral
- Scoring system updated (CDP/ACP now includes orchestration)
- Documentation expanded (CDP v1.2)

## Implementation

### Files Modified
- `~/.claude/agents/codex-delegate.md` - AI-to-AI preamble
- `~/.claude/agents/gemini-delegate.md` - AI-to-AI preamble
- `~/.claude/agents/reasoning-duo.md` - Collaboration context
- `~/.claude/CDP_PROTOCOL.md` - v1.2 with depth & load sections
- `~/.claude/AGENT_STANDARDS.md` - Section 12 updated
- `~/.claude/CONFIGURATION_GUIDE.md` - CDP section expanded
- `~/.claude/SCORING.md` - v3.0.1 with orchestration scoring

### Files Created
- `~/.claude/scripts/check-load.sh` - Performance monitor

### Scoring Impact
Category 9 (Advanced Features) → CDP/ACP protocols:
- Full (3 pts): CDP + ACP + depth tracking + check-load.sh
- Partial (2 pts): CDP + ACP docs only
- Basic (1 pt): CDP doc only

## References

- CDP Protocol: `~/.claude/CDP_PROTOCOL.md`
- Agent Standards: `~/.claude/AGENT_STANDARDS.md`
- Configuration Guide: `~/.claude/CONFIGURATION_GUIDE.md`
- Scoring System: `~/.claude/SCORING.md`
