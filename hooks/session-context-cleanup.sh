#!/usr/bin/env bash
# SessionEnd hook: clear session-scoped context
SESSION_CONTEXT="$HOME/.claude/rules/session-context.md"
[[ -f "$SESSION_CONTEXT" ]] && rm "$SESSION_CONTEXT"
exit 0
