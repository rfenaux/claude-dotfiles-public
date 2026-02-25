# Context Management

## Memory Flush (Pre-Compaction)

Before compaction, extract:
- **Decisions** -> DECISIONS.md or CTM context
- **Learnings** -> CTM learnings
- **Open questions** -> CTM agent context

Respond with `NO_PERSIST` if nothing to extract.

## Tool Result Pruning

| Tool | TTL | Strategy |
|------|-----|----------|
| Read | 30 min | Soft-trim (first/last 300 chars) |
| Grep | 45 min | Soft-trim |
| Glob | 30 min | Hard-clear (placeholder only) |
| Bash | 60 min | Soft-trim |
| WebFetch | 120 min | Soft-trim |

**Protected:** Last 3 assistant messages + their tool results never pruned.

## Context Inspection

| Command | Shows |
|---------|-------|
| `/context` | Quick summary + top consumers |
| `/context list` | All injected content with sizes |
| `/context detail` | Full breakdown by category |
| `/context trim` | Pruning recommendations |

## MCP Session Scope (Critical)

**MCP tools ONLY work in main session.** Sub-agents cannot access ANY MCP tools.

| Agent Type | MCP Access |
|------------|------------|
| Main session | Full |
| Task sub-agents | NONE |
| Plan agents | NONE |
| Workers (CDP) | NONE |

**Before delegating:** Does task need MCP tools? If yes -> keep in main session.

## Token Optimization Cascade

```
1. codex-delegate (bulk code ops) -> 2. gemini-delegate (>1M only) -> 3. Claude (1M native)
```

**Cost awareness:** >200K input tokens = 2x pricing. Delegate bulk work to Codex/Gemini.

## CDP (Cognitive Delegation Protocol)

Primary writes `HANDOFF.md` -> Spawns agent -> Agent writes `OUTPUT.md` -> Primary reads result.
**Depth limit:** Max 3 levels. **Load-aware:** Check `check-load.sh` before spawning.

## Past Conversation Access

**I DO have access.** Sources: `project/conversation-history/` (RAG) | `~/.claude/projects/*/sessions-index.json` (Read)
