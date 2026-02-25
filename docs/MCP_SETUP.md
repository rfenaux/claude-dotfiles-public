# MCP Connector Setup

MCP (Model Context Protocol) connectors let Claude Code directly access external services. These are configured per-project in `.mcp.json` files.

## Google Workspace

Access Gmail, Google Drive, Calendar, Docs, and Sheets directly from Claude.

```bash
claude mcp add google-workspace -- npx @anthropic-ai/google-workspace-mcp
```

Then authenticate when prompted in your next Claude session.

## Slack

Slack is an Anthropic-hosted connector enabled through Claude Code settings. When available, it provides `slack_search_public`, `slack_read_channel`, `slack_send_message`, and other tools.

**Availability:** Controlled by Anthropic feature flag. If tools don't appear, restart your Claude session.

## Fathom (Meeting Transcripts)

Access meeting transcripts and action items from Fathom.

```bash
claude mcp add fathom -- npx @anthropic-ai/fathom-mcp
```

Requires a Fathom API key. Set `FATHOM_API_KEY` in your shell profile.

## Mermaid Chart

Render Mermaid diagrams to images.

```bash
claude mcp add mermaid-chart -- npx @anthropic-ai/mermaid-chart-mcp
```

## Custom MCP Servers

Add any MCP server to your project:

```bash
# stdio transport
claude mcp add <name> -- <command> [args...]

# HTTP transport (preferred over deprecated SSE)
claude mcp add <name> --transport http --url <endpoint>
```

## Important Notes

- **MCP tools only work in the main session** — sub-agents and task agents cannot access MCP tools
- **Fast-fail rule** — if an MCP tool fails, use the CLI fallback immediately (don't retry)
- **Per-project config** — `.mcp.json` is project-specific. Copy between projects as needed
