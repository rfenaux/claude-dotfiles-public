# MCP Fast-Fail Rule

MCP tool failures are binary (connected or not) — retrying wastes time.

## 1-Attempt Only

If an MCP tool call fails → pivot immediately to fallback. Do NOT:
- Retry the same MCP tool
- Try variations of the tool call
- Spawn a sub-agent to retry (they also lack MCP access)
- Debug or investigate MCP connectivity

## Fallback Table

| MCP Server | Tools | Fallback |
|------------|-------|----------|
| rag-server | `rag_index`, `rag_reindex`, `rag_search`, `rag_list`, `rag_remove` | `python3 -m rag_mcp_server.cli <cmd>` |
| slack (remote) | `slack_*` | No CLI fallback — tell user to restart session |
| mermaid-chart | `mermaid_*` | Write `.mmd` file directly |
| Others | Varies | Inform user, don't debug |

## Session Scope

**MCP tools ONLY work in main session.** Never available to:
- Task sub-agents (forked context)
- Plan agents
- Worker agents (CDP)

Before delegating: does task need MCP? If yes → keep in main session.
