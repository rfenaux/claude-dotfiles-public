#!/usr/bin/env bash
# circuit-breaker.sh - Shared library for hook failure protection
# Source this in hooks: . ~/.claude/hooks/lib/circuit-breaker.sh
# Then call: check_circuit "hook-name" || exit 0
#
# Threshold: 3 failures in 5 minutes → skip for 30 minutes
# Auto-resets after cooldown period

CIRCUIT_DIR="/tmp/claude-circuit"

check_circuit() {
  local hook_name="${1:?hook name required}"
  local failure_file="$CIRCUIT_DIR/${hook_name}.failures"
  local trip_file="$CIRCUIT_DIR/${hook_name}.tripped"

  mkdir -p "$CIRCUIT_DIR"

  # Check if circuit is tripped
  if [[ -f "$trip_file" ]]; then
    local trip_age=$(( $(date +%s) - $(stat -f %m "$trip_file" 2>/dev/null || echo 0) ))
    if [[ $trip_age -lt 1800 ]]; then
      # Still in cooldown (30 min)
      return 1
    fi
    # Cooldown expired — reset
    rm -f "$trip_file" "$failure_file"
  fi

  return 0
}

record_failure() {
  local hook_name="${1:?hook name required}"
  local failure_file="$CIRCUIT_DIR/${hook_name}.failures"
  local trip_file="$CIRCUIT_DIR/${hook_name}.tripped"

  mkdir -p "$CIRCUIT_DIR"

  # Append timestamp
  echo "$(date +%s)" >> "$failure_file"

  # Count failures in last 5 minutes
  local cutoff=$(( $(date +%s) - 300 ))
  local recent=0
  while IFS= read -r ts; do
    [[ $ts -ge $cutoff ]] && recent=$((recent + 1))
  done < "$failure_file"

  # Trip if threshold exceeded
  if [[ $recent -ge 3 ]]; then
    touch "$trip_file"
    # Truncate failure log
    echo "$(date +%s)" > "$failure_file"
  fi
}

# --- Timing Telemetry ---
# Usage: start_timing "hook-name" at top, end_timing "hook-name" before exit
TIMING_DIR="/tmp/claude-hook-timing"

start_timing() {
  local hook_name="${1:?hook name required}"
  mkdir -p "$TIMING_DIR" 2>/dev/null
  # Use perl for sub-second precision (macOS date lacks %N)
  perl -MTime::HiRes=time -e 'print time()' > "$TIMING_DIR/${hook_name}.start" 2>/dev/null
}

end_timing() {
  local hook_name="${1:?hook name required}"
  local start_file="$TIMING_DIR/${hook_name}.start"
  [[ -f "$start_file" ]] || return 0

  local start_ts=$(cat "$start_file" 2>/dev/null)
  local end_ts=$(perl -MTime::HiRes=time -e 'print time()' 2>/dev/null)
  rm -f "$start_file"

  [[ -z "$start_ts" || -z "$end_ts" ]] && return 0

  # Calculate duration in ms using perl (bash can't do float math)
  local duration_ms=$(perl -e "printf('%d', ($end_ts - $start_ts) * 1000)" 2>/dev/null)

  # Log if over 100ms (slow hook threshold)
  if [[ -n "$duration_ms" && "$duration_ms" -gt 100 ]] 2>/dev/null; then
    printf '{"hook":"%s","ms":%s,"ts":"%s"}\n' \
      "$hook_name" "$duration_ms" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      >> "$TIMING_DIR/slow-hooks.jsonl" 2>/dev/null
  fi
}
