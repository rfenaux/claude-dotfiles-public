#!/usr/bin/env bash
# FailureLearning Hook - captures tool failures as auto-approved lessons
# PostToolUseFailure hook (all tools)
# Budget: <50ms, async background, fail-silent.
# v2: Auto-approve at 0.70 (0.75 for repeat failures), dedup via check-and-merge.

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "failure-learning" || exit 0

LESSONS_FILE="$HOME/.claude/lessons/lessons.jsonl"
CONFIDENCE_PY="$HOME/.claude/lessons/scripts/confidence.py"
LOGS_DIR="$HOME/.claude/logs"
CATALOG="$LOGS_DIR/failure-catalog.jsonl"
[[ -d "$LOGS_DIR" ]] || mkdir -p "$LOGS_DIR"

# Read hook input
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
[[ -z "$TOOL_NAME" ]] && exit 0

SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")

# Read active CTM task ID (for bidirectional CTM <-> Lessons linkage)
CTM_TASK_ID=""
CTM_SCHEDULER="$HOME/.claude/ctm/scheduler.json"
if [[ -f "$CTM_SCHEDULER" ]]; then
  CTM_TASK_ID=$(python3 -c "
import json, sys
d = json.load(open(sys.argv[1]))
aid = d.get('active_agent') or ''
if not aid and d.get('priority_queue'):
    aid = d['priority_queue'][0][0]
print(aid)
" "$CTM_SCHEDULER" 2>/dev/null || echo "")
fi

# Rate limit: max 10 per session
COUNT_FILE="/tmp/claude-fl-count-${SESSION_ID}"
COUNT=0
[[ -f "$COUNT_FILE" ]] && COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
[[ "$COUNT" -ge 10 ]] && exit 0

# Async background
{
  # Extract all fields in one python call for efficiency
  read -r TOOL_INPUT_STR TOOL_OUTPUT CWD < <(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)

# Input summary
inp = json.dumps(d.get('tool_input', {}))[:500]

# Error extraction: try multiple fields, pick first non-empty
error = ''
for field in ('tool_output', 'error', 'error_message', 'output', 'message'):
    val = d.get(field, '')
    if val:
        if isinstance(val, dict):
            error = json.dumps(val)[:500]
        else:
            error = str(val)[:500]
        break

# If still empty, check nested tool_output dict for error/stderr
if not error:
    to = d.get('tool_output', {})
    if isinstance(to, dict):
        for k in ('error', 'stderr', 'message', 'output'):
            if to.get(k):
                error = str(to[k])[:500]
                break

# If still empty, use input summary as fallback context
if not error:
    error = f'[no error captured] input: {inp[:200]}'

cwd = d.get('cwd', '')
# Tab-separated for read
print(f'{inp}\t{error}\t{cwd}')
" 2>/dev/null || echo "{}\t\t$PWD")
  # Split tab-separated output
  IFS=$'\t' read -r TOOL_INPUT_STR TOOL_OUTPUT CWD <<< "$TOOL_INPUT_STR"

  # Generate error signature
  ERROR_SIG=$(echo -n "${TOOL_NAME}:${TOOL_OUTPUT:0:200}" | md5 -q 2>/dev/null || echo -n "${TOOL_NAME}:${TOOL_OUTPUT:0:200}" | md5sum 2>/dev/null | cut -d' ' -f1 || echo "unknown")

  TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  CONFIDENCE="0.70"

  # Repeat failures (same signature 3+ times = higher confidence)
  if [[ -f "$CATALOG" ]]; then
    SIG_COUNT=$(grep -c "\"$ERROR_SIG\"" "$CATALOG" 2>/dev/null || echo 0)
    [[ "$SIG_COUNT" -ge 2 ]] && CONFIDENCE="0.75"
  fi

  # Build lesson JSON
  LESSON_JSON=$(python3 -c "
import json, sys
candidate = {
    'type': 'tool_failure',
    'tool': sys.argv[1],
    'title': f'Failure: {sys.argv[1]} - {sys.argv[3][:80]}',
    'input_summary': sys.argv[2][:500],
    'error': sys.argv[3][:500],
    'error_signature': sys.argv[4],
    'tags': [sys.argv[1].lower(), 'failure', 'debugging'],
    'project': sys.argv[5],
    'ctm_task_id': sys.argv[9] if sys.argv[9] else None,
    'ctm_task_ids': [sys.argv[9]] if sys.argv[9] else [],
    'session_id': sys.argv[6],
    'timestamp': sys.argv[7],
    'status': 'approved',
    'confidence': float(sys.argv[8]),
    'approved_at': sys.argv[7],
    'occurrences': 1,
    'metadata': {'seen_count': 1, 'last_seen': sys.argv[7]}
}
print(json.dumps(candidate, separators=(',',':')))
" "$TOOL_NAME" "$TOOL_INPUT_STR" "$TOOL_OUTPUT" "$ERROR_SIG" "$CWD" "$SESSION_ID" "$TS" "$CONFIDENCE" "$CTM_TASK_ID" 2>/dev/null)

  if [[ -n "$LESSON_JSON" ]]; then
    # Dedup check: merge or append
    RESULT=$(echo "$LESSON_JSON" | python3 "$CONFIDENCE_PY" check-and-merge 2>/dev/null || echo "NEW")
    if [[ "$RESULT" == "NEW" ]]; then
      echo "$LESSON_JSON" >> "$LESSONS_FILE" || record_failure "failure-learning"
    fi

    # Still log to failure catalog for signature tracking
    echo "$LESSON_JSON" >> "$CATALOG" 2>/dev/null

    # Increment counter
    echo $(( COUNT + 1 )) > "$COUNT_FILE"
  fi
} &

exit 0
