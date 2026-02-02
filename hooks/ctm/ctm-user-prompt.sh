#!/bin/bash
# CTM User Prompt Hook
# Checks user input for triggers that suggest context switching

set -e

CTM_DIR="$HOME/.claude/ctm"
CTM_LIB="$CTM_DIR/lib"
LOG_FILE="$CTM_DIR/logs/hooks.log"

mkdir -p "$CTM_DIR/logs"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [user-prompt] $1" >> "$LOG_FILE"
}

# Read the hook input (contains user prompt)
HOOK_INPUT=$(cat)

# Extract user message from hook input
USER_MESSAGE=$(echo "$HOOK_INPUT" | jq -r '.user_prompt // .message // empty' 2>/dev/null || echo "")

if [ -z "$USER_MESSAGE" ]; then
    # Try to get from stdin directly if jq parsing failed
    USER_MESSAGE="$HOOK_INPUT"
fi

# Skip if empty or too short
if [ ${#USER_MESSAGE} -lt 5 ]; then
    exit 0
fi

log "Checking triggers for: ${USER_MESSAGE:0:50}..."

# Check if CTM is initialized
if [ ! -f "$CTM_DIR/index.json" ]; then
    exit 0
fi

# Run trigger detection
cd "$CTM_LIB"
RESULT=$(python3 << EOF
import sys
import json
sys.path.insert(0, '.')

try:
    from triggers import detect_triggers, TriggerMatch
    from scheduler import get_scheduler
    from agents import get_agent

    user_input = """$USER_MESSAGE"""

    matches = detect_triggers(user_input)

    if not matches:
        sys.exit(0)

    # Get current active agent
    scheduler = get_scheduler()
    current_id = scheduler.get_active()

    # Find high-confidence actionable matches
    for m in matches:
        if m.confidence > 0.7:
            if m.type == "switch" and m.agent_id and m.agent_id != current_id:
                agent = get_agent(m.agent_id)
                if agent:
                    print(f"[CTM] Detected: '{m.matched_text}' → Switch to [{m.agent_id}] {agent.task['title']}")
                    break
            elif m.type == "complete":
                if current_id:
                    agent = get_agent(current_id)
                    if agent:
                        print(f"[CTM] Detected completion signal → Mark [{current_id}] complete?")
                break
            elif m.type == "escalate":
                print(f"[CTM] Detected urgency signal → Consider priority escalation")
                break

except Exception as e:
    # Silent fail - don't interrupt user flow
    pass
EOF
2>/dev/null) || true

if [ -n "$RESULT" ]; then
    echo "$RESULT"
    log "Trigger output: $RESULT"
fi
