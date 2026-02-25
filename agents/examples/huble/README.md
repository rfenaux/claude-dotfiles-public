# Huble-Specific Agents (Examples)

These agents are specific to Huble Digital's internal processes and wiki. They're included as examples of how to create organization-specific agents that route to internal knowledge bases.

To use these:
1. Copy to `~/.claude/agents/`
2. Set `ORG_WIKI_PATH` in `config/paths.sh` to point to your organization's knowledge base
3. Update the agent content to reference your organization's processes

These agents demonstrate the pattern of:
- Internal wiki routing (methodology, sales, operations, HR, dev)
- RAG search against organization-specific indexes
- Domain-specific expertise backed by indexed documentation
