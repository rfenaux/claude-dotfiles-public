# Feature Requests: Token Optimization for Claude Code

> Created: 2026-01-19 | Author: the author | Context: Session analyzing token overhead

## Executive Summary

A "hi" message costs ~53k tokens before any actual conversation. This document proposes architectural changes to reduce baseline context overhead by 60-70% through lazy-loading patterns.

**Core Insight:** Human memory doesn't load everything at once — it uses cue-based retrieval. Claude Code should work the same way.

```
Current:  Load ALL → Process request → Respond
Proposed: Load INDEX → Match cues → Fetch relevant → Respond
```

---

## Feature Request #1: Lazy-Loading Memory Files (CLAUDE.md)

### Problem

All `CLAUDE.md` files in the directory hierarchy load immediately into context:
- `~/.claude/CLAUDE.md` (~9.5k tokens)
- Parent directory CLAUDE.md files
- Project CLAUDE.md

**Total:** 10-18k tokens before conversation starts.

### Current Behavior

```
Session Start
    ↓
Load ALL CLAUDE.md content into system prompt
    ↓
User sends "hi"
    ↓
18k tokens already consumed
```

### Proposed Behavior

```
Session Start
    ↓
Load CLAUDE.md INDEX only (~500 tokens)
    ↓
User sends "hi"
    ↓
No additional fetch needed
    ↓
User asks about "timestamps"
    ↓
Fetch TIMESTAMPS section on demand
```

### Suggested Implementation

**Index file structure:**
```yaml
# CLAUDE.md.index
sections:
  partnership:
    triggers: ["partner", "working together", "the user"]
    file: CLAUDE.md#partnership
    tokens: 200
  timestamps:
    triggers: ["timestamp", "time format", "_HH:MM_"]
    file: CLAUDE.md#timestamps
    tokens: 150
  memory_system:
    triggers: ["RAG", "memory", "CTM", "remember"]
    file: RAG_GUIDE.md
    tokens: 2000
  agents:
    triggers: ["agent", "delegate", "sub-agent"]
    file: AGENTS_INDEX.md
    tokens: 1500
```

**Fetch logic:**
1. Parse user message for trigger keywords
2. Fetch matching sections
3. Inject into context for this turn only
4. Cache for session duration

### Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Baseline memory | 10-18k | 0.5-1k | **~15k tokens** |
| Per-turn overhead | 0 | 0.2-2k | Acceptable |

---

## Feature Request #2: Lazy-Loading Agent Definitions in Task Tool

### Problem

The `Task` tool description embeds ALL agent descriptions (~82 agents = ~8k tokens), even though most sessions use 0-3 agents.

### Current Behavior

```json
{
  "name": "Task",
  "description": "Launch a new agent...\n\nAvailable agents:\n- agent1: 50 tokens of description\n- agent2: 45 tokens...\n[82 agents × ~40 tokens = 3.3k tokens]"
}
```

### Proposed Behavior

**Option A: Summary List**
```json
{
  "name": "Task",
  "description": "Launch a new agent. Available: agent1, agent2, ... (82 total). Use subagent_type parameter.",
  "dynamic_schema": {
    "subagent_type": {
      "fetch_on_use": true,
      "source": "~/.claude/agents/"
    }
  }
}
```

**Option B: Category Grouping**
```json
{
  "name": "Task",
  "description": "Launch agent by category:\n- HubSpot (12 agents)\n- Documentation (8 agents)\n- Analysis (6 agents)\n...\nSpecify category or agent name in subagent_type."
}
```

### Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Task tool | ~8k | ~0.5k | **~7.5k tokens** |

---

## Feature Request #3: Lazy-Loading Skill Definitions

### Problem

The `Skill` tool embeds all skill descriptions (~44 skills = ~2.6k tokens).

### Proposed Solution

Same as agents — summary list or category grouping with on-demand fetch.

### Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Skill tool | ~2.6k | ~0.3k | **~2.3k tokens** |

---

## Feature Request #4: Sub-Agent Context Inheritance Control

### Problem

Sub-agents spawned via Task tool inherit the full parent context, including the entire CLAUDE.md. For simple tasks like "find files matching X", this is wasteful.

### Current Workaround

We built a wrapper script that:
1. Sets `CLAUDE_MAIN_SESSION=true` for main sessions
2. SessionStart hook checks for this env var
3. Sub-agents (no env var) get swapped to slim CLAUDE.md

### Proposed Native Solution

```yaml
# In Task tool parameters
Task:
  subagent_type: "Explore"
  prompt: "Find all TypeScript files"
  context_inheritance: "minimal"  # NEW PARAMETER
```

**Options:**
- `full` — Inherit everything (current behavior)
- `minimal` — Only system prompt + tool definitions
- `none` — Fresh context, only the prompt
- `custom` — Specify which CLAUDE.md sections to include

### Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Per sub-agent | ~9.5k | ~1.5k | **~8k per agent** |
| Session with 5 agents | ~47.5k | ~7.5k | **~40k tokens** |

---

## Feature Request #5: Project-Scoped Tool Defaults

### Problem

All MCP servers load globally regardless of project type:
- GitHub MCP: 4.5k tokens (26 tools)
- Fathom MCP: 2.6k tokens (12 tools)
- RAG MCP: 2k tokens (8 tools)

A HubSpot consulting project doesn't need GitHub tools.

### Current Workaround

Project-level `.mcp.json` overrides global config (this works today).

### Proposed Enhancement

**Auto-detection based on project type:**
```yaml
# ~/.claude/project-profiles.yaml
profiles:
  git-repo:
    detect: [".git/"]
    enable: ["github-mcp", "rag-server"]
  consulting:
    detect: ["knowledge-base/", ".solarc/"]
    enable: ["rag-server", "fathom-mcp"]
  default:
    enable: ["rag-server"]
```

### Impact

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Consulting project | 9.1k | 2k | **~7k tokens** |

---

## Feature Request #6: Usage-Based Tool Pruning

### Problem

Tools/agents/skills you never use still load every session.

### Proposed Solution

Track usage over time and suggest pruning:

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Token Optimization Suggestions                          │
│                                                             │
│  These tools haven't been used in 30+ sessions:             │
│  - mcp__fathom__create_webhook (214 tokens)                 │
│  - mcp__github__fork_repository (152 tokens)                │
│  - agent: mermaid-converter (38 tokens)                     │
│                                                             │
│  Disable to save ~400 tokens? [y/n/never ask]               │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

1. Track tool invocations in `~/.claude/usage-stats.json`
2. After N sessions, analyze patterns
3. Suggest disabling unused tools (user opt-in)
4. Provide easy re-enable command

### Impact

Variable — depends on user's actual usage patterns. Estimated 1-5k tokens for power users with many unused tools.

---

## Summary: Total Potential Savings

| Feature | Tokens Saved | Complexity |
|---------|--------------|------------|
| Lazy-load CLAUDE.md | ~15k | Medium |
| Lazy-load agents | ~7.5k | Medium |
| Lazy-load skills | ~2.3k | Low |
| Sub-agent context control | ~8k per agent | Low |
| Project-scoped tools | ~7k | Low (exists) |
| Usage-based pruning | ~1-5k | High |
| **Total** | **~40-45k** | - |

**Current baseline:** ~53k tokens for "hi"
**Optimized baseline:** ~10-15k tokens for "hi"
**Reduction:** ~70%

---

## Appendix: The Brain Analogy

Human memory architecture that inspired these requests:

```
┌─────────────────────────────────────────────────────────────┐
│  HUMAN MEMORY                    PROPOSED CLAUDE CODE       │
├─────────────────────────────────────────────────────────────┤
│  Index/Tags always loaded        CLAUDE.md.index (~500 tok) │
│  Full memories fetched on cue    Sections fetched on match  │
│  Recent memories cached          Session cache              │
│  Unused memories pruned          Usage-based suggestions    │
│  Context-dependent recall        Project-type detection     │
└─────────────────────────────────────────────────────────────┘
```

The current architecture is like a human who recites their entire autobiography before every conversation. The proposed architecture matches how human working memory actually functions.

---

## Related Files

- `~/.claude/docs/CLAUDE_WRAPPER.md` — Our workaround implementation
- `~/.claude/CLAUDE.md.slim` — Slim version we created
- `~/.claude/CLAUDE.md.full` — Full version backup

---

**Submitted by:** the author
**Date:** 2026-01-19
**Claude Code Version:** 2.1+
**Model:** Claude Opus 4.5
