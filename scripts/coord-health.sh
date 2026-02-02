#!/usr/bin/env bash
# coord-health.sh - Health check for coordination system
# Part of Multi-Session Coordination System (Phase 2)
#
# Usage: coord-health.sh <project_path> [--json] [--fix]
#
# Options:
#   --json   Output as JSON
#   --fix    Attempt to fix issues automatically
#
# Checks:
#   1. Log file writable
#   2. Snapshot valid and parseable
#   3. No stale locks
#   4. Log not corrupted
#   5. Log size within limits
#
# Exit codes:
#   0 - All healthy
#   1 - Issues found (see output)
#   2 - Critical issues (coordination may not work)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULTS_FILE="$HOME/.claude/coordination-defaults.json"

if [[ -f "$DEFAULTS_FILE" ]]; then
  MAX_EVENTS=$(jq -r '.log.max_events // 1000' "$DEFAULTS_FILE")
  STALE_THRESHOLD=$(jq -r '.heartbeat.stale_threshold_sec // 120' "$DEFAULTS_FILE")
else
  MAX_EVENTS=1000
  STALE_THRESHOLD=120
fi

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

JSON_OUTPUT=false
FIX_ISSUES=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    --fix)
      FIX_ISSUES=true
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

if [[ $# -lt 1 ]]; then
  echo "Usage: coord-health.sh <project_path> [--json] [--fix]" >&2
  exit 1
fi

PROJECT_PATH="$1"

# ─────────────────────────────────────────────────────────────────────────────
# Setup
# ─────────────────────────────────────────────────────────────────────────────

COORD_DIR="$PROJECT_PATH/.agent-workspaces"
LOG_FILE="$COORD_DIR/coord.log"
SNAPSHOT_FILE="$COORD_DIR/coord-snapshot.json"

# Track results
declare -a CHECKS=()
declare -a ISSUES=()
declare -a FIXED=()
OVERALL_STATUS="healthy"

add_check() {
  local name="$1"
  local status="$2"
  local message="$3"

  CHECKS+=("$name:$status:$message")

  if [[ "$status" == "fail" || "$status" == "critical" ]]; then
    ISSUES+=("$name: $message")
    if [[ "$status" == "critical" ]]; then
      OVERALL_STATUS="critical"
    elif [[ "$OVERALL_STATUS" != "critical" ]]; then
      OVERALL_STATUS="unhealthy"
    fi
  fi
}

add_fixed() {
  local issue="$1"
  FIXED+=("$issue")
}

# ─────────────────────────────────────────────────────────────────────────────
# Check 1: Coordination directory exists
# ─────────────────────────────────────────────────────────────────────────────

if [[ ! -d "$COORD_DIR" ]]; then
  add_check "directory" "warn" "Coordination not initialized"

  if [[ "$FIX_ISSUES" == true ]]; then
    mkdir -p "$COORD_DIR"
    add_fixed "Created coordination directory"
    add_check "directory" "pass" "Created coordination directory"
  fi
else
  add_check "directory" "pass" "Coordination directory exists"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 2: Log file writable
# ─────────────────────────────────────────────────────────────────────────────

if [[ -d "$COORD_DIR" ]]; then
  if [[ -f "$LOG_FILE" ]]; then
    if [[ -w "$LOG_FILE" ]]; then
      add_check "log_writable" "pass" "Log file is writable"
    else
      add_check "log_writable" "critical" "Log file is not writable"

      if [[ "$FIX_ISSUES" == true ]]; then
        chmod u+w "$LOG_FILE" 2>/dev/null && add_fixed "Fixed log file permissions"
      fi
    fi
  else
    add_check "log_writable" "pass" "No log file yet (will be created)"
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 3: Log not corrupted
# ─────────────────────────────────────────────────────────────────────────────

if [[ -f "$LOG_FILE" ]]; then
  CORRUPT_LINES=0
  TOTAL_LINES=$(wc -l < "$LOG_FILE" | tr -d ' ')

  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" ]] && continue
    if ! echo "$line" | jq -e . >/dev/null 2>&1; then
      ((CORRUPT_LINES++))
    fi
  done < "$LOG_FILE"

  if [[ $CORRUPT_LINES -eq 0 ]]; then
    add_check "log_integrity" "pass" "All $TOTAL_LINES log entries valid"
  elif [[ $CORRUPT_LINES -lt 5 ]]; then
    add_check "log_integrity" "warn" "$CORRUPT_LINES/$TOTAL_LINES entries corrupted"
  else
    add_check "log_integrity" "fail" "$CORRUPT_LINES/$TOTAL_LINES entries corrupted"
  fi
else
  add_check "log_integrity" "pass" "No log file to check"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 4: Snapshot valid
# ─────────────────────────────────────────────────────────────────────────────

if [[ -f "$SNAPSHOT_FILE" ]]; then
  if jq -e . "$SNAPSHOT_FILE" >/dev/null 2>&1; then
    VERSION=$(jq -r '.version // "unknown"' "$SNAPSHOT_FILE")
    add_check "snapshot_valid" "pass" "Snapshot valid (v$VERSION)"
  else
    add_check "snapshot_valid" "fail" "Snapshot JSON is invalid"

    if [[ "$FIX_ISSUES" == true ]]; then
      rm -f "$SNAPSHOT_FILE"
      "$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" --force >/dev/null 2>&1
      add_fixed "Rebuilt snapshot from log"
    fi
  fi
else
  add_check "snapshot_valid" "pass" "No snapshot yet (will be created)"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 5: Log size within limits
# ─────────────────────────────────────────────────────────────────────────────

if [[ -f "$LOG_FILE" ]]; then
  EVENT_COUNT=$(wc -l < "$LOG_FILE" | tr -d ' ')
  UTIL=$(( (EVENT_COUNT * 100) / MAX_EVENTS ))

  if [[ $EVENT_COUNT -ge $MAX_EVENTS ]]; then
    add_check "log_size" "warn" "Log at capacity ($EVENT_COUNT/$MAX_EVENTS) - rotation needed"

    if [[ "$FIX_ISSUES" == true ]]; then
      "$SCRIPT_DIR/coord-rotate.sh" "$PROJECT_PATH" --force >/dev/null 2>&1
      add_fixed "Rotated log file"
    fi
  elif [[ $UTIL -ge 80 ]]; then
    add_check "log_size" "warn" "Log at ${UTIL}% capacity ($EVENT_COUNT/$MAX_EVENTS)"
  else
    add_check "log_size" "pass" "Log at ${UTIL}% capacity ($EVENT_COUNT/$MAX_EVENTS)"
  fi
else
  add_check "log_size" "pass" "No log file yet"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 6: No stale locks
# ─────────────────────────────────────────────────────────────────────────────

if [[ -f "$SNAPSHOT_FILE" ]]; then
  # Rebuild to ensure fresh data
  "$SCRIPT_DIR/coord-rebuild.sh" "$PROJECT_PATH" >/dev/null 2>&1 || true

  STALE_CHECK=$("$SCRIPT_DIR/coord-heartbeat.sh" "$PROJECT_PATH" --check-stale --json 2>/dev/null || echo '{"stale_locks":[]}')
  STALE_COUNT=$(echo "$STALE_CHECK" | jq '.stale_locks | length')

  if [[ $STALE_COUNT -eq 0 ]]; then
    add_check "stale_locks" "pass" "No stale locks"
  else
    add_check "stale_locks" "warn" "$STALE_COUNT stale lock(s) detected"

    if [[ "$FIX_ISSUES" == true ]]; then
      "$SCRIPT_DIR/coord-heartbeat.sh" "$PROJECT_PATH" --cleanup >/dev/null 2>&1
      add_fixed "Released stale locks"
    fi
  fi
else
  add_check "stale_locks" "pass" "No locks to check"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Check 7: Lock file not stuck
# ─────────────────────────────────────────────────────────────────────────────

LOCK_FILE="$COORD_DIR/coord.log.lock"
if [[ -f "$LOCK_FILE" ]]; then
  # Check if lock is older than 5 minutes (stuck)
  LOCK_AGE=$(( $(date +%s) - $(stat -f %m "$LOCK_FILE" 2>/dev/null || stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0) ))

  if [[ $LOCK_AGE -gt 300 ]]; then
    add_check "lock_file" "warn" "Lock file is ${LOCK_AGE}s old (possibly stuck)"

    if [[ "$FIX_ISSUES" == true ]]; then
      rm -f "$LOCK_FILE"
      add_fixed "Removed stuck lock file"
    fi
  else
    add_check "lock_file" "pass" "Lock file OK"
  fi
else
  add_check "lock_file" "pass" "No lock file issues"
fi

# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
  # Build checks array
  CHECKS_JSON="[]"
  for check in "${CHECKS[@]}"; do
    NAME="${check%%:*}"
    REST="${check#*:}"
    STATUS="${REST%%:*}"
    MESSAGE="${REST#*:}"

    CHECKS_JSON=$(echo "$CHECKS_JSON" | jq \
      --arg name "$NAME" \
      --arg status "$STATUS" \
      --arg message "$MESSAGE" \
      '. + [{name: $name, status: $status, message: $message}]')
  done

  ISSUES_JSON=$(printf '%s\n' "${ISSUES[@]}" 2>/dev/null | jq -R . | jq -s '.' || echo '[]')
  FIXED_JSON=$(printf '%s\n' "${FIXED[@]}" 2>/dev/null | jq -R . | jq -s '.' || echo '[]')

  jq -nc \
    --arg overall "$OVERALL_STATUS" \
    --argjson checks "$CHECKS_JSON" \
    --argjson issues "$ISSUES_JSON" \
    --argjson fixed "$FIXED_JSON" \
    '{
      overall_status: $overall,
      checks: $checks,
      issues: $issues,
      fixed: $fixed
    }'
else
  # Human-readable output
  echo "Coordination Health Check"
  echo "========================="
  echo ""

  for check in "${CHECKS[@]}"; do
    NAME="${check%%:*}"
    REST="${check#*:}"
    STATUS="${REST%%:*}"
    MESSAGE="${REST#*:}"

    case "$STATUS" in
      pass)     ICON="✓" ;;
      warn)     ICON="⚠" ;;
      fail)     ICON="✗" ;;
      critical) ICON="✗" ;;
      *)        ICON="?" ;;
    esac

    printf "  %s %-15s %s\n" "$ICON" "$NAME" "$MESSAGE"
  done

  echo ""

  if [[ ${#FIXED[@]} -gt 0 ]]; then
    echo "Fixed issues:"
    for fix in "${FIXED[@]}"; do
      echo "  ✓ $fix"
    done
    echo ""
  fi

  case "$OVERALL_STATUS" in
    healthy)
      echo "Status: HEALTHY"
      ;;
    unhealthy)
      echo "Status: ISSUES FOUND"
      echo "Run with --fix to attempt automatic repair"
      ;;
    critical)
      echo "Status: CRITICAL"
      echo "Coordination may not function correctly"
      ;;
  esac
fi

# Exit code based on status
case "$OVERALL_STATUS" in
  healthy)   exit 0 ;;
  unhealthy) exit 1 ;;
  critical)  exit 2 ;;
esac
