#!/usr/bin/env bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# usage-tracker.sh - Track agent/skill invocation counts
# Hooks: SubagentStart (agent tracking), PostToolUse on Skill (skill tracking)
# Budget: <10ms — just increment a file counter

INPUT=$(cat)
STATS_DIR="$HOME/.claude/stats/usage"

# Detect hook event from input structure
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
AGENT_TYPE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('agent_type',''))" 2>/dev/null || echo "")
SKILL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('skill',''))" 2>/dev/null || echo "")

{
  mkdir -p "$STATS_DIR/agent" "$STATS_DIR/skill"

  if [[ -n "$AGENT_TYPE" && "$AGENT_TYPE" != "general-purpose" ]]; then
    # SubagentStart event — track agent type
    COUNT_FILE="$STATS_DIR/agent/${AGENT_TYPE}.count"
    COUNT=0
    [[ -f "$COUNT_FILE" ]] && COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
    echo $((COUNT + 1)) > "$COUNT_FILE"
    date +%s > "$STATS_DIR/agent/${AGENT_TYPE}.last"
  fi

  if [[ "$TOOL_NAME" == "Skill" && -n "$SKILL_NAME" ]]; then
    # PostToolUse on Skill — track skill usage
    # Normalize skill name (strip prefix like "ms-office-suite:")
    SKILL_BASE="${SKILL_NAME##*:}"
    COUNT_FILE="$STATS_DIR/skill/${SKILL_BASE}.count"
    COUNT=0
    [[ -f "$COUNT_FILE" ]] && COUNT=$(cat "$COUNT_FILE" 2>/dev/null || echo 0)
    echo $((COUNT + 1)) > "$COUNT_FILE"
    date +%s > "$STATS_DIR/skill/${SKILL_BASE}.last"
  fi
} &

exit 0
