---
name: session-context
description: Manage session-scoped context injected via rules/ auto-load. Add, list, preview, clear, or check conflicts for temporary system prompt additions.
context: fork
---

# /session-context - Session Context Manager

Manage temporary session-scoped context that gets auto-injected into the system prompt via `~/.claude/rules/session-context.md`.

## Usage

| Command | Action |
|---------|--------|
| `/session-context add "text"` | Append inline text to session context |
| `/session-context add-file /path/to/file.md` | Append file contents |
| `/session-context list` | Show current appends |
| `/session-context preview` | Preview full injected content |
| `/session-context clear` | Clear all session context |
| `/session-context check-conflicts` | Check for contradictions with CLAUDE.md |

## How It Works

1. Appends are written to `~/.claude/rules/session-context.md`
2. Claude Code auto-loads all `rules/*.md` files into the system prompt
3. On session end, the file is automatically deleted (SessionEnd hook)

## Implementation

Run the session context manager script:

```bash
~/.claude/scripts/session-context.sh "$@"
```

Read the script output and report results to user.
