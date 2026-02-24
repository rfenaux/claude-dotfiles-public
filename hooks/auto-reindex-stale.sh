#!/usr/bin/env bash
# auto-reindex-stale.sh - Auto-reindex stale RAG indexes at SessionStart
# Hook: SessionStart, once: true
# Budget: Detection <200ms inline, reindex in background
# Rate limit: 1 reindex per path per 24h

set +e  # fail-silent: hooks must not abort on error

CONFIG="$HOME/.claude/config/self-healing.json"
LOG_DIR="$HOME/.claude/logs/self-healing"
LOG_FILE="$LOG_DIR/reindex.jsonl"
LOCK_PREFIX="/tmp/claude-reindex"

[[ -d "$LOG_DIR" ]] || mkdir -p "$LOG_DIR"

# Read config
if [[ ! -f "$CONFIG" ]]; then
  exit 0
fi

ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('enabled', False))" 2>/dev/null || echo "false")
[[ "$ENABLED" != "True" && "$ENABLED" != "true" ]] && exit 0

RAG_ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('rag_reindex',{}).get('enabled', True))" 2>/dev/null || echo "true")
[[ "$RAG_ENABLED" != "True" && "$RAG_ENABLED" != "true" ]] && exit 0

STALENESS_DAYS=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('rag_reindex',{}).get('staleness_days', 7))" 2>/dev/null || echo 7)
FILE_THRESHOLD=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('rag_reindex',{}).get('file_change_threshold', 10))" 2>/dev/null || echo 10)
RATE_LIMIT_H=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('rag_reindex',{}).get('rate_limit_h', 24))" 2>/dev/null || echo 24)

# Consume stdin
cat > /dev/null

# Ollama pre-flight (required for reindex)
if ! curl -sf --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
  exit 0
fi

# Check each monitored path
check_and_reindex() {
  local path="$1"
  local expanded_path="${path/#\~/$HOME}"
  local rag_dir="$expanded_path/.rag"
  local activity_log="$rag_dir/.index_activity.log"

  # Skip if no .rag/ directory
  [[ -d "$rag_dir" ]] || return 0

  # Rate limit: 1 per path per RATE_LIMIT_H hours
  local path_hash
  path_hash=$(echo -n "$expanded_path" | md5 -q 2>/dev/null || echo -n "$expanded_path" | md5sum 2>/dev/null | cut -d' ' -f1)
  local lock_file="${LOCK_PREFIX}-${path_hash}.lock"

  if [[ -f "$lock_file" ]]; then
    local lock_age=$(( $(date +%s) - $(stat -f %m "$lock_file" 2>/dev/null || echo 0) ))
    local rate_sec=$(( RATE_LIMIT_H * 3600 ))
    [[ $lock_age -lt $rate_sec ]] && return 0
  fi

  local needs_reindex=false
  local reason=""

  # Check 1: Activity log age
  if [[ -f "$activity_log" ]]; then
    local log_age_days=$(( ($(date +%s) - $(stat -f %m "$activity_log" 2>/dev/null || echo 0)) / 86400 ))
    if [[ $log_age_days -gt $STALENESS_DAYS ]]; then
      needs_reindex=true
      reason="index ${log_age_days} days old (threshold: ${STALENESS_DAYS})"
    fi
  fi

  # Check 2: Modified files since last index
  if [[ "$needs_reindex" == "false" && -f "$activity_log" ]]; then
    local modified_count
    modified_count=$(find "$expanded_path" -newer "$activity_log" \
      \( -name "*.md" -o -name "*.txt" -o -name "*.json" -o -name "*.py" -o -name "*.js" \) \
      ! -path "*/.git/*" ! -path "*/.rag/*" ! -path "*/node_modules/*" ! -path "*/__pycache__/*" \
      ! -path "*/conversation-history/*" \
      2>/dev/null | wc -l | tr -d ' ')

    if [[ $modified_count -gt $FILE_THRESHOLD ]]; then
      needs_reindex=true
      reason="${modified_count} files modified (threshold: ${FILE_THRESHOLD})"
    fi
  fi

  if [[ "$needs_reindex" == "true" ]]; then
    local ts
    ts=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    printf '{"ts":"%s","path":"%s","reason":"%s","action":"reindex"}\n' \
      "$ts" "$expanded_path" "$reason" >> "$LOG_FILE" 2>/dev/null

    # Reindex in background using CLI (MCP-free)
    touch "$lock_file"
    (
      cd "$expanded_path"
      python3 -m rag_mcp_server.cli reindex "$expanded_path" > /dev/null 2>&1
      printf '{"ts":"%s","path":"%s","action":"reindex","result":"completed"}\n' \
        "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$expanded_path" >> "$LOG_FILE" 2>/dev/null
    ) &
  fi
}

# Background all checks
{
  check_and_reindex "~/.claude/lessons"
  check_and_reindex "~/.claude"
  check_and_reindex "~/.claude/observations"
} &

exit 0
