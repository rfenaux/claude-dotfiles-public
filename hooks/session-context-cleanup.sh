#!/usr/bin/env bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# SessionEnd hook: clear session-scoped context
SESSION_CONTEXT="$HOME/.claude/rules/session-context.md"
[[ -f "$SESSION_CONTEXT" ]] && rm "$SESSION_CONTEXT"
exit 0
