#!/usr/bin/env bash
# Claude Code Status Writer — PostToolUse hook
# Writes ~/.claude/status.json for statusline, dashboard, and Barista consumption
# Budget: <80ms | Atomic: writes .tmp then mv

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "update-status" || exit 0
start_timing "update-status"

# Per-session status directory
STATUS_DIR="$HOME/.claude/status"
mkdir -p "$STATUS_DIR"
PYTHON_CMD="$(command -v python3 2>/dev/null || echo /usr/bin/python3)"

# Privacy mode check
if [[ "${CLAUDE_BARISTA_ENABLED:-true}" == "false" ]]; then
  echo '{"version":"1.1.0","disabled":true}' > "$STATUS_DIR/disabled.json"
  ln -sf "$STATUS_DIR/disabled.json" "$HOME/.claude/status.json"
  exit 0
fi

INPUT=$(cat)

# --- Extract session_id first (needed for per-session file path) ---
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"' 2>/dev/null)
STATUS_FILE="${STATUS_DIR}/${SESSION_ID}.json"
CTX_PCT=$(echo "$INPUT" | jq -r '.context_window.used_percentage // 0' 2>/dev/null | cut -d. -f1)
CTX_USAGE=$(echo "$INPUT" | jq -r '.context_window.current_usage // 0' 2>/dev/null)
CTX_TOTAL=$(echo "$INPUT" | jq -r '.context_window.context_window_size // 200000' 2>/dev/null)

# --- CTM active task (single file reads) ---
CTM_SCHEDULER="$HOME/.claude/ctm/scheduler.json"
TASK_NAME="Idle"
TASK_ID=""
TASK_STATUS="idle"
TASK_PROGRESS=0

if [[ -f "$CTM_SCHEDULER" ]]; then
  TASK_ID=$(jq -r '.active_agent // ""' "$CTM_SCHEDULER" 2>/dev/null)
  if [[ -n "$TASK_ID" && "$TASK_ID" != "null" ]]; then
    CTM_INDEX="$HOME/.claude/ctm/index.json"
    if [[ -f "$CTM_INDEX" ]]; then
      TASK_NAME=$(jq -r ".agents[\"$TASK_ID\"].title // \"Task\"" "$CTM_INDEX" 2>/dev/null)
      TASK_STATUS=$(jq -r ".agents[\"$TASK_ID\"].status // \"active\"" "$CTM_INDEX" 2>/dev/null)
    fi
    TASK_PROGRESS=$(jq -r '.session.progress // 0' "$CTM_SCHEDULER" 2>/dev/null)
  fi
fi

# --- Agent count (fast ls + wc) ---
AGENT_DIR="$HOME/.agent-workspaces"
AGENT_COUNT=0
AGENT_NAMES="[]"

if [[ -d "$AGENT_DIR" ]]; then
  # Only count agents without OUTPUT.md (i.e. still active, not completed)
  AGENT_COUNT=0
  ACTIVE_NAMES=""
  for d in "$AGENT_DIR"/*/; do
    [[ -d "$d" ]] || continue
    name=$(basename "$d")
    [[ "$name" == .* ]] && continue
    [[ -f "$d/OUTPUT.md" ]] && continue
    AGENT_COUNT=$((AGENT_COUNT + 1))
    ACTIVE_NAMES="${ACTIVE_NAMES}${name}"$'\n'
  done
  if [[ -n "$ACTIVE_NAMES" ]]; then
    AGENT_NAMES=$(printf '%s' "$ACTIVE_NAMES" | head -5 | jq -R . 2>/dev/null | jq -s . 2>/dev/null || echo "[]")
  fi
fi

# --- Load status (lightweight inline check, no subprocess) ---
LOAD_PROFILE="balanced"
LOAD_STATUS="OK"
LOAD_AVG="0.0"

PROFILE_FILE="$HOME/.claude/machine-profile.json"
if [[ -f "$PROFILE_FILE" ]]; then
  LOAD_PROFILE=$(jq -r '.active_profile // "balanced"' "$PROFILE_FILE" 2>/dev/null || echo "balanced")
  THRESHOLD_OK=$(jq -r ".profiles.$LOAD_PROFILE.load_ok // .thresholds.load_ok // 8.0" "$PROFILE_FILE" 2>/dev/null || echo "8.0")
else
  THRESHOLD_OK=8.0
fi

# Quick 1-min load average (fast, no subprocess)
LOAD_AVG=$(sysctl -n vm.loadavg 2>/dev/null | awk '{print $2}' || echo "0.0")

# Determine status via awk (faster than bc)
LOAD_STATUS=$(awk "BEGIN {if ($LOAD_AVG < $THRESHOLD_OK) print \"OK\"; else if ($LOAD_AVG < $THRESHOLD_OK * 1.5) print \"CAUTION\"; else print \"HIGH_LOAD\"}")

# --- Write atomically ---
cat > "${STATUS_FILE}.tmp" << STATUSEOF
{
  "version": "1.1.0",
  "updated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "session_id": "$SESSION_ID",
  "task": {
    "name": $(echo "$TASK_NAME" | jq -R .),
    "id": "$TASK_ID",
    "progress": ${TASK_PROGRESS:-0},
    "status": "$TASK_STATUS"
  },
  "context": {
    "current_tokens": ${CTX_USAGE:-0},
    "total_tokens": ${CTX_TOTAL:-200000},
    "percentage": ${CTX_PCT:-0}
  },
  "agents": {
    "active": ${AGENT_COUNT:-0},
    "names": ${AGENT_NAMES:-[]}
  },
  "load": {
    "profile": "$LOAD_PROFILE",
    "status": "$LOAD_STATUS",
    "load_avg": ${LOAD_AVG:-0.0}
  }
}
STATUSEOF

mv "${STATUS_FILE}.tmp" "$STATUS_FILE" || record_failure "update-status"

# --- Backward-compat symlink ---
ln -sf "$STATUS_FILE" "$HOME/.claude/status.json"

# --- Aggregator: build index.json + cleanup stale files (<20ms) ---
"$PYTHON_CMD" -c "
import json, os, glob, time

status_dir = '$STATUS_DIR'
now = time.time()

sessions = []
stale_count = 0
total_agents = 0
max_ctx = 0
load_data = {}

for f in glob.glob(os.path.join(status_dir, '*.json')):
    bn = os.path.basename(f)
    if bn in ('index.json', 'disabled.json', 'menubar-state.json'):
        continue
    try:
        age = now - os.path.getmtime(f)
        if age > 600:  # 10 min cleanup (was 30 — dead sessions linger too long)
            os.unlink(f)
            continue
        with open(f) as fh:
            d = json.load(fh)
        if d.get('disabled'):
            continue
        is_stale = age > 300  # 5 min stale
        if is_stale:
            stale_count += 1
        ctx_pct = d.get('context', {}).get('percentage', 0)
        agents = d.get('agents', {}).get('active', 0)
        total_agents += agents
        if ctx_pct > max_ctx:
            max_ctx = ctx_pct
        load_data = d.get('load', load_data)
        sessions.append({
            'session_id': d.get('session_id', bn.replace('.json', '')),
            'task': d.get('task', {}).get('name', 'Idle'),
            'context_pct': ctx_pct,
            'agents': agents,
            'status': 'stale' if is_stale else 'active',
            'updated_at': d.get('updated_at', ''),
        })
    except Exception:
        continue

sessions.sort(key=lambda s: s.get('updated_at', ''), reverse=True)
index = {
    'updated_at': sessions[0]['updated_at'] if sessions else '',
    'sessions': sessions,
    'summary': {
        'total_sessions': len(sessions),
        'active_sessions': len(sessions) - stale_count,
        'stale_sessions': stale_count,
        'total_agents': total_agents,
        'max_context_pct': max_ctx,
        'load': load_data,
    }
}
tmp = os.path.join(status_dir, 'index.json.tmp')
with open(tmp, 'w') as fh:
    json.dump(index, fh, separators=(',', ':'))
os.rename(tmp, os.path.join(status_dir, 'index.json'))
" 2>/dev/null || true

end_timing "update-status"

exit 0
