#!/usr/bin/env bash
# Log compaction events for dashboard visualization
# Event: PreCompact | Budget: <3s | Fail-silent
set +e  # fail-silent: hooks must not abort on error

LOG="$HOME/.claude/observations/compaction-log.jsonl"
mkdir -p "$(dirname "$LOG")"

# Count current session observations as proxy for context activity
COUNT=0
[[ -f "$HOME/.claude/observations/active-session.jsonl" ]] && \
  COUNT=$(wc -l < "$HOME/.claude/observations/active-session.jsonl" | tr -d ' ')

python3 -c "
import json
from datetime import datetime
entry = {
    'ts': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
    'event': 'pre_compact',
    'observation_count': int('$COUNT')
}
print(json.dumps(entry, separators=(',', ':')))
" >> "$LOG" 2>/dev/null || true

exit 0
