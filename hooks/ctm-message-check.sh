#!/bin/bash
# ctm-message-check.sh - Check for unread CTM messages at session start
# Part of: OpenClaw Phase 3 (MA-E, agent reply loops)
# Created: 2026-02-14
# Event: SessionStart (once: true)
#
# Checks the messaging inbox for unread messages and surfaces them.
# Lightweight alternative to a background daemon.

set +e  # fail-silent: hooks must not abort on error

MSG_DIR="$HOME/.claude/ctm/messages"
[ ! -d "$MSG_DIR" ] && exit 0

# Count unread messages (files with "read": false or missing "read" field)
UNREAD=0
SENDERS=""

shopt -s nullglob
for msg_file in "$MSG_DIR"/*.json; do
    [ ! -f "$msg_file" ] && continue

    IS_READ=$(python3 -c "
import json, sys
try:
    with open('$msg_file') as f:
        msg = json.load(f)
    if not msg.get('read', False):
        print(msg.get('sender', 'unknown'))
except:
    pass
" 2>/dev/null)

    if [ -n "$IS_READ" ]; then
        UNREAD=$((UNREAD + 1))
        SENDERS="${SENDERS:+$SENDERS, }$IS_READ"
    fi
done

if [ "$UNREAD" -gt 0 ]; then
    echo "[CTM Messages] $UNREAD unread from: $SENDERS. Use 'ctm receive --unread' to view."
fi

exit 0
