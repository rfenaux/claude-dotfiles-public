#!/usr/bin/env bash
# session-metrics-collector.sh - Collect session efficiency metrics at SessionEnd
# Hook: SessionEnd (after session-compressor.sh)
# Budget: <2s, fail-silent
# Captures: tool counts, search hit rate, hot files, agent spawns, duration

set +e  # fail-silent: hooks must not abort on error

CONFIG="$HOME/.claude/config/self-improvement.json"
METRICS_DIR="$HOME/.claude/metrics"
METRICS_FILE="$METRICS_DIR/sessions.jsonl"
OBS_FILE="$HOME/.claude/observations/active-session.jsonl"

[[ -d "$METRICS_DIR" ]] || mkdir -p "$METRICS_DIR"

# Read config
if [[ -f "$CONFIG" ]]; then
  ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('enabled', True))" 2>/dev/null || echo "true")
  [[ "$ENABLED" != "True" && "$ENABLED" != "true" ]] && exit 0
fi

# Consume stdin
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo "unknown")

# No observations = nothing to measure
[[ -f "$OBS_FILE" ]] || exit 0

# Collect metrics in background
{
  python3 << 'PYEOF'
import json
import sys
import os
from datetime import datetime, timezone
from collections import Counter, defaultdict

OBS_FILE = os.path.expanduser("~/.claude/observations/active-session.jsonl")
METRICS_FILE = os.path.expanduser("~/.claude/metrics/sessions.jsonl")

if not os.path.exists(OBS_FILE):
    sys.exit(0)

entries = []
with open(OBS_FILE, 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue

if not entries:
    sys.exit(0)

# Tool usage counts
tool_counts = Counter()
for e in entries:
    tool_counts[e.get('tool', 'unknown')] += 1

# Search effectiveness: Grep/Glob with non-empty output
search_tools = ['Grep', 'Glob']
search_total = sum(1 for e in entries if e.get('tool') in search_tools)
search_hits = sum(1 for e in entries if e.get('tool') in search_tools
                  and e.get('output', '') and len(str(e.get('output', ''))) > 20)
search_hit_rate = round(search_hits / search_total, 2) if search_total > 0 else None

# Hot files (most frequently accessed)
file_counts = Counter()
for e in entries:
    files = e.get('files', [])
    if isinstance(files, list):
        for f in files:
            if f:
                file_counts[f] += 1
hot_files = [f for f, c in file_counts.most_common(5)]

# Agent spawns (Task tool usage)
agent_spawns = sum(1 for e in entries if e.get('tool') == 'Task')

# MCP tool success (any mcp__ tool)
mcp_total = sum(1 for e in entries if str(e.get('tool', '')).startswith('mcp__'))
mcp_success = sum(1 for e in entries if str(e.get('tool', '')).startswith('mcp__')
                  and e.get('output', '') and 'error' not in str(e.get('output', '')).lower()[:100])
mcp_success_rate = round(mcp_success / mcp_total, 2) if mcp_total > 0 else None

# Session duration estimate (first to last entry timestamp)
timestamps = []
for e in entries:
    ts = e.get('ts', '')
    if ts:
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            timestamps.append(dt)
        except (ValueError, TypeError):
            pass

duration_min = None
if len(timestamps) >= 2:
    duration_min = round((max(timestamps) - min(timestamps)).total_seconds() / 60, 1)

# Tool calls per minute
tools_per_min = round(len(entries) / duration_min, 1) if duration_min and duration_min > 0 else None

# Build metrics record
metrics = {
    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "session_id": os.environ.get("CLAUDE_SESSION_ID", "unknown"),
    "total_tool_calls": len(entries),
    "tool_counts": dict(tool_counts.most_common(10)),
    "search_total": search_total,
    "search_hit_rate": search_hit_rate,
    "hot_files": hot_files,
    "agent_spawns": agent_spawns,
    "mcp_total": mcp_total,
    "mcp_success_rate": mcp_success_rate,
    "duration_min": duration_min,
    "tools_per_min": tools_per_min,
    "projects": list(set(e.get('project', '') for e in entries if e.get('project')))
}

# Append to JSONL
with open(METRICS_FILE, 'a') as f:
    f.write(json.dumps(metrics, separators=(',', ':')) + '\n')

PYEOF
} &

exit 0
