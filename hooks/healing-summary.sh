#!/usr/bin/env bash
# healing-summary.sh - Surface self-healing activity at SessionStart
# Hook: SessionStart, once: true
# Budget: <100ms, fail-silent
# Only outputs if there's something to report

set +e  # fail-silent: hooks must not abort on error

LOG_DIR="$HOME/.claude/logs/self-healing"

# Consume stdin
cat > /dev/null

# No log dir = nothing to report
[[ -d "$LOG_DIR" ]] || exit 0

# Check if any log files exist and have content
has_data=false
for f in "$LOG_DIR"/*.jsonl; do
  [[ -f "$f" ]] && [[ -s "$f" ]] && has_data=true && break
done
[[ "$has_data" == "true" ]] || exit 0

# Analyze last 7 days in Python (fast, single pass)
python3 << 'PYEOF'
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import Counter

LOG_DIR = Path.home() / ".claude" / "logs" / "self-healing"
cutoff = datetime.now(timezone.utc) - timedelta(days=7)
parts = []

def recent_entries(path):
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                ts_str = d.get("ts", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts >= cutoff:
                        entries.append(d)
            except (json.JSONDecodeError, ValueError):
                continue
    return entries

# Service restarts
svc_entries = recent_entries(LOG_DIR / "services.jsonl")
restarts = Counter()
for e in svc_entries:
    if e.get("result") == "success":
        restarts[e.get("service", "?")] += 1

if restarts:
    svc_parts = [f"{svc} {n}x" for svc, n in restarts.items()]
    parts.append(f"Services restarted: {', '.join(svc_parts)}")

# RAG reindexes
reindex_entries = recent_entries(LOG_DIR / "reindex.jsonl")
reindexed = [e.get("path", "?").replace(str(Path.home()), "~")
             for e in reindex_entries if e.get("result") == "completed"]
if reindexed:
    parts.append(f"RAG reindexed: {', '.join(set(reindexed))}")

# Decision syncs
decision_entries = recent_entries(LOG_DIR / "decision-sync.jsonl")
synced = sum(e.get("total_updated", 0) for e in decision_entries if "total_updated" in e)
if synced:
    parts.append(f"Decisions auto-synced: {synced}")

# Failure escalations
esc_entries = recent_entries(LOG_DIR / "failure-escalation.jsonl")
if esc_entries:
    parts.append(f"Failures escalated: {len(esc_entries)}")

# Import fixes
fix_entries = recent_entries(LOG_DIR / "import-fixes.jsonl")
if fix_entries:
    parts.append(f"Imports fixed: {len(fix_entries)}")

# Only output if something happened
if parts:
    print(f"[Self-Heal] Last 7d: {'; '.join(parts)}")

PYEOF

exit 0
