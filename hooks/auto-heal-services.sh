#!/usr/bin/env bash
# auto-heal-services.sh - Auto-restart down services at SessionStart
# Hook: SessionStart, once: true
# Budget: <10s total (background), fail-silent
# Rate limit: 1 restart per service per 60min

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "auto-heal-services" || exit 0

CONFIG="$HOME/.claude/config/self-healing.json"
LOG_DIR="$HOME/.claude/logs/self-healing"
LOG_FILE="$LOG_DIR/services.jsonl"
LOCK_PREFIX="/tmp/claude-heal"

[[ -d "$LOG_DIR" ]] || mkdir -p "$LOG_DIR"

# Read config (fail-silent if missing)
if [[ ! -f "$CONFIG" ]]; then
  exit 0
fi

ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('enabled', False))" 2>/dev/null || echo "false")
[[ "$ENABLED" != "True" && "$ENABLED" != "true" ]] && exit 0

# Consume stdin (hook input)
cat > /dev/null

# Run healing in background
{
  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  log_event() {
    local service="$1" action="$2" result="$3"
    printf '{"ts":"%s","service":"%s","action":"%s","result":"%s"}\n' \
      "$TS" "$service" "$action" "$result" >> "$LOG_FILE" 2>/dev/null
  }

  check_rate_limit() {
    local service="$1" base_min="$2"
    local lock_file="${LOCK_PREFIX}-${service}.lock"
    local attempts_file="${LOCK_PREFIX}-${service}.attempts"
    local max_attempts=5

    # Check attempt ceiling
    local attempts=0
    [[ -f "$attempts_file" ]] && attempts=$(cat "$attempts_file" 2>/dev/null || echo 0)
    if [[ $attempts -ge $max_attempts ]]; then
      log_event "$service" "restart" "ceiling_reached"
      return 1  # Stop trying after max attempts
    fi

    # Exponential backoff: base * 2^attempts (cap at 1440 min = 24h)
    local delay_min=$(( base_min * (1 << attempts) ))
    [[ $delay_min -gt 1440 ]] && delay_min=1440

    if [[ -f "$lock_file" ]]; then
      local lock_age=$(( $(date +%s) - $(stat -f %m "$lock_file" 2>/dev/null || echo 0) ))
      local delay_sec=$(( delay_min * 60 ))
      if [[ $lock_age -lt $delay_sec ]]; then
        log_event "$service" "restart" "rate_limited"
        return 1  # Still in backoff window
      fi
    fi
    return 0
  }

  set_rate_limit() {
    local service="$1"
    touch "${LOCK_PREFIX}-${service}.lock"
    # Increment attempt counter
    local attempts_file="${LOCK_PREFIX}-${service}.attempts"
    local attempts=0
    [[ -f "$attempts_file" ]] && attempts=$(cat "$attempts_file" 2>/dev/null || echo 0)
    echo $(( attempts + 1 )) > "$attempts_file"
  }

  reset_attempts() {
    local service="$1"
    rm -f "${LOCK_PREFIX}-${service}.attempts"
  }

  # --- Ollama ---
  OLLAMA_ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['services']['ollama'].get('enabled', True))" 2>/dev/null || echo "true")
  if [[ "$OLLAMA_ENABLED" == "True" || "$OLLAMA_ENABLED" == "true" ]]; then
    if ! curl -sf --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
      if check_rate_limit "ollama" 60; then
        log_event "ollama" "restart" "attempting"
        if brew services restart ollama > /dev/null 2>&1; then
          sleep 5
          if curl -sf --max-time 2 http://localhost:11434/api/tags > /dev/null 2>&1; then
            log_event "ollama" "restart" "success"
            set_rate_limit "ollama"
            reset_attempts "ollama"
          else
            log_event "ollama" "restart" "failed_verify"
          fi
        else
          log_event "ollama" "restart" "failed_cmd"
          record_failure "auto-heal-services"
        fi
      else
        : # rate_limited already logged by check_rate_limit
      fi
    fi
  fi

  # --- Dashboard ---
  DASH_ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['services']['dashboard'].get('enabled', True))" 2>/dev/null || echo "true")
  if [[ "$DASH_ENABLED" == "True" || "$DASH_ENABLED" == "true" ]]; then
    if ! curl -sf --max-time 2 http://localhost:8420/ > /dev/null 2>&1; then
      if check_rate_limit "dashboard" 60; then
        log_event "dashboard" "restart" "attempting"
        DASH_SCRIPT="$HOME/.claude/rag-dashboard/start.sh"
        if [[ -x "$DASH_SCRIPT" ]] && "$DASH_SCRIPT" > /dev/null 2>&1; then
          sleep 3
          if curl -sf --max-time 2 http://localhost:8420/ > /dev/null 2>&1; then
            log_event "dashboard" "restart" "success"
            set_rate_limit "dashboard"
            reset_attempts "dashboard"
          else
            log_event "dashboard" "restart" "failed_verify"
          fi
        else
          log_event "dashboard" "restart" "failed_cmd"
          record_failure "auto-heal-services"
        fi
      else
        : # rate_limited already logged by check_rate_limit
      fi
    fi
  fi

  # --- RAG MCP ---
  RAG_ENABLED=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['services']['rag_mcp'].get('enabled', True))" 2>/dev/null || echo "true")
  if [[ "$RAG_ENABLED" == "True" || "$RAG_ENABLED" == "true" ]]; then
    if ! pgrep -f "rag_server" > /dev/null 2>&1; then
      if check_rate_limit "rag_mcp" 60; then
        log_event "rag_mcp" "restart" "attempting"
        RAG_SCRIPT="$HOME/.claude/scripts/restart-rag-server.sh"
        if [[ -x "$RAG_SCRIPT" ]] && "$RAG_SCRIPT" > /dev/null 2>&1; then
          log_event "rag_mcp" "restart" "success"
          set_rate_limit "rag_mcp"
          reset_attempts "rag_mcp"
        else
          log_event "rag_mcp" "restart" "failed_cmd"
          record_failure "auto-heal-services"
        fi
      else
        : # rate_limited already logged by check_rate_limit
      fi
    fi
  fi

} &

exit 0
