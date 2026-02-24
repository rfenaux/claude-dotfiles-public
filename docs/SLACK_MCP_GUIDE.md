# Slack MCP Integration - Usage Guide

## Availability Check (Do This First)

Slack is a **remote MCP integration** with an Anthropic-controlled feature flag (`tengu_claudeai_mcp_connectors`). It is NOT always available. **Check before using.**

**How to check:** Look for any tool matching `slack_` in the available tools list. The tool names follow the pattern `mcp__<dynamic-uuid>__slack_<action>` where the UUID changes per session.

```
If slack tools ARE available   → Use them directly (see Usage below)
If slack tools are NOT available → Tell the user:
  "Slack remote MCP isn't loaded this session (Anthropic feature flag).
   Options: restart the session, or I can search other sources."
```

**Do NOT** waste time debugging, checking .mcp.json, or reading config files. The flag is server-side and cannot be changed locally.

### Why it sometimes doesn't work

- `tengu_claudeai_mcp_connectors` is an A/B feature flag controlled by Anthropic's servers
- It's cached in `~/.claude/.claude.json` but you CANNOT change it - it refreshes each session
- The flag can be `true` in one session and `false` in the next
- Multi-account setups (Huble/FoW) may get different flag values
- **There is no local fix.** Restarting the session is the only workaround.

---

## How It Works

Slack is authorized via the claude.ai account (Settings > Integrations > Slack). When the feature flag is enabled, tools are automatically injected into the Claude Code session.

The UUID in the tool name is dynamic - don't hardcode it.

---

## Available Tools

### Search

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `slack_search_public` | Search messages across public channels | `query`, `limit`, `sort` (timestamp/score), `sort_dir` (asc/desc) |
| `slack_search_users` | Search for users by name/email | `query` |

### Channels

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `slack_list_channels` | List channels (public + joined private) | `limit`, `cursor` |
| `slack_get_channel_history` | Read recent messages from a channel | `channel_id`, `limit`, `oldest`, `latest` |
| `slack_get_channel_info` | Get channel metadata (topic, purpose, members) | `channel_id` |

### Messages

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `slack_get_thread_replies` | Get all replies in a thread | `channel_id`, `thread_ts` |
| `slack_send_message` | Post a message to a channel | `channel_id`, `text` |
| `slack_update_message` | Edit an existing message | `channel_id`, `ts`, `text` |

### Users

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `slack_read_user_profile` | Get user profile (name, title, email, etc.) | `user_id` |
| `slack_get_users` | List workspace users | `cursor`, `limit` |

### Reactions

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `slack_add_reaction` | Add emoji reaction to a message | `channel_id`, `timestamp`, `reaction` |

---

## Usage Patterns

### Search for recent messages about a topic
```
slack_search_public(query="project update", limit=5, sort="timestamp", sort_dir="desc")
```

### Search with Slack operators (same as Slack search bar)
```
slack_search_public(query="from:@username in:#project-channel after:2026-01-01")
slack_search_public(query="has:link in:#general budget")
```

### Read a specific channel's history
```
# First find the channel
slack_list_channels(limit=100)
# Then read it
slack_get_channel_history(channel_id="C0EXAMPLE01", limit=20)
```

### Get thread context
```
# Use the message_ts from search results as thread_ts
slack_get_thread_replies(channel_id="C090R9ZM24E", thread_ts="1770124889.309119")
```

### Look up a user
```
slack_search_users(query="soraya")
slack_read_user_profile(user_id="U05DH55B3GW")
```

---

## Tips

- `sort="timestamp"` + `sort_dir="desc"` = most recent first (usually what you want)
- Search results include `Context before` and `Context after` for surrounding messages
- `message_ts` is the unique message identifier - use it for threads, reactions, updates
- Channel IDs start with `C` (channels) or `D` (DMs) or `G` (group DMs)
- The `query` parameter supports full Slack search syntax: `from:`, `in:`, `has:`, `before:`, `after:`, `during:`, etc.

---

## Important

- This is READ + WRITE. `slack_send_message` actually posts. **Always confirm before sending.**
- Private channels you haven't joined are NOT searchable.
- DMs are NOT searchable via `slack_search_public`.

---

## Local Fallback (If Needed)

If the remote MCP becomes permanently unreliable, a local Slack MCP can be set up with a bot token. This requires creating a Slack App in the workspace (needs admin approval at Huble).

```bash
claude mcp add slack -- npx -y @modelcontextprotocol/server-slack
# Requires SLACK_BOT_TOKEN (xoxb-...) in env
# Scopes needed: channels:history, channels:read, chat:write, search:read, users:read
```

Slack's official MCP (mcp.slack.com/sse) exists but is partner-only (not self-serve).
