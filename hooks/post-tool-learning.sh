#!/usr/bin/env bash
# PostToolLearning Hook - captures successful tool patterns as auto-approved lessons
# PostToolUse hook for Write|Edit|Bash
# Budget: <50ms, async background, fail-silent.
# v2: Auto-approve at 0.70, dedup via check-and-merge, write to JSONL.

set +e  # fail-silent: hooks must not abort on error

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "post-tool-learning" || exit 0

LESSONS_FILE="$HOME/.claude/lessons/lessons.jsonl"
CONFIDENCE_PY="$HOME/.claude/lessons/scripts/confidence.py"

# Read hook input from stdin
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

# Rate limit: max 5 per session
COUNT_FILE="/tmp/claude-ptl-count-${SESSION_ID}"
COUNT=0
[[ -f "$COUNT_FILE" ]] && COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
[[ "$COUNT" -ge 5 ]] && exit 0

# Async background processing
{
  TOOL_OUTPUT=$(echo "$INPUT" | python3 -c "import sys,json; print(str(json.load(sys.stdin).get('tool_output',''))[:500])" 2>/dev/null || echo "")
  TOOL_INPUT_STR=$(echo "$INPUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin).get('tool_input',{}))[:500])" 2>/dev/null || echo "{}")
  CWD=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null || echo "$PWD")
  OUTPUT_LEN=${#TOOL_OUTPUT}
  SIGNAL=""

  case "$TOOL_NAME" in
    Write)
      [[ $OUTPUT_LEN -gt 0 ]] && SIGNAL="new_file_created"
      ;;
    Edit)
      [[ $OUTPUT_LEN -gt 100 ]] && SIGNAL="significant_edit"
      ;;
    Bash)
      [[ $OUTPUT_LEN -gt 50 ]] && SIGNAL="successful_command"
      ;;
  esac

  if [[ -n "$SIGNAL" ]]; then
    TS=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    LESSON_JSON=$(python3 -c "
import json, sys
candidate = {
    'type': 'tool_success',
    'tool': sys.argv[1],
    'signal': sys.argv[2],
    'title': f'{sys.argv[2]}: {sys.argv[1]} in {sys.argv[5].split(\"/\")[-1] if \"/\" in sys.argv[5] else sys.argv[5]}',
    'context': {
        'input_preview': sys.argv[3][:200],
        'output_preview': sys.argv[4][:200]
    },
    'tags': [sys.argv[1].lower(), sys.argv[2].replace('_','-')],
    'project': sys.argv[5],
    'ctm_task_id': sys.argv[8] if sys.argv[8] else None,
    'ctm_task_ids': [sys.argv[8]] if sys.argv[8] else [],
    'session_id': sys.argv[6],
    'timestamp': sys.argv[7],
    'status': 'approved',
    'confidence': 0.70,
    'approved_at': sys.argv[7],
    'occurrences': 1,
    'metadata': {'seen_count': 1, 'last_seen': sys.argv[7]}
}
print(json.dumps(candidate, separators=(',',':')))
" "$TOOL_NAME" "$SIGNAL" "$TOOL_INPUT_STR" "$TOOL_OUTPUT" "$CWD" "$SESSION_ID" "$TS" "$CTM_TASK_ID" 2>/dev/null)

    if [[ -n "$LESSON_JSON" ]]; then
      # Check for duplicate and merge, or append as new
      RESULT=$(echo "$LESSON_JSON" | python3 "$CONFIDENCE_PY" check-and-merge 2>/dev/null || echo "NEW")
      if [[ "$RESULT" == "NEW" ]]; then
        echo "$LESSON_JSON" >> "$LESSONS_FILE" || record_failure "post-tool-learning"
      fi
      # Increment counter
      echo $(( COUNT + 1 )) > "$COUNT_FILE"
    fi
  fi
} &

exit 0
