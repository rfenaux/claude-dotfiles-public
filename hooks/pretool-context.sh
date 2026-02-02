#!/bin/bash
# PreToolUse Context Injection Hook
# Returns: {"additionalContext": "..."} to inject into model context
# Created: 2026-01-17 | Claude Code 2.1+ feature

# Check if disabled via environment
[[ "${CLAUDE_CONTEXT_INJECTION:-on}" == "off" ]] && exit 0

TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
PROJECT_PATH="${PWD}"

# Only inject for Edit/Write tools (Bash excluded to avoid noise)
case "$TOOL_NAME" in
  Edit|Write)
    ;;
  *)
    exit 0
    ;;
esac

CONTEXT=""

# Add CTM task context if available
if [[ -f ~/.claude/scripts/ctm-context.sh ]]; then
  CTM_CONTEXT=$(~/.claude/scripts/ctm-context.sh 2>/dev/null || true)
  if [[ -n "$CTM_CONTEXT" && "$CTM_CONTEXT" != "null" ]]; then
    CONTEXT+="## Active Task\n$CTM_CONTEXT\n\n"
  fi
fi

# Add recent decisions (last 3) if file exists and has content
if [[ -f "$PROJECT_PATH/.claude/context/DECISIONS.md" ]]; then
  # Get last 3 decision headers with their content
  RECENT_DECISIONS=$(grep -A 3 "^### " "$PROJECT_PATH/.claude/context/DECISIONS.md" 2>/dev/null | tail -15 || true)
  if [[ -n "$RECENT_DECISIONS" ]]; then
    CONTEXT+="## Recent Decisions\n$RECENT_DECISIONS\n"
  fi
fi

# Add implicit requirements from <username>-patterns.json if relevant
PATTERNS_FILE="$HOME/.claude/<username>-patterns.json"
if [[ -f "$PATTERNS_FILE" ]]; then
  # Detect project type from path or file extensions
  PROJECT_TYPE=""
  if [[ "$PROJECT_PATH" == *"hubspot"* ]] || grep -qir "hubspot" "$PROJECT_PATH"/*.md 2>/dev/null; then
    PROJECT_TYPE="any HubSpot work"
  elif [[ -f "$PROJECT_PATH/package.json" ]] || [[ -f "$PROJECT_PATH/setup.py" ]]; then
    PROJECT_TYPE="any script"
  fi

  if [[ -n "$PROJECT_TYPE" ]]; then
    REQUIREMENTS=$(jq -r --arg type "$PROJECT_TYPE" '.implicit_requirements[$type] // [] | .[]' "$PATTERNS_FILE" 2>/dev/null | head -4)
    if [[ -n "$REQUIREMENTS" ]]; then
      CONTEXT+="## Implicit Requirements ($PROJECT_TYPE)\n"
      while IFS= read -r req; do
        CONTEXT+="• $req\n"
      done <<< "$REQUIREMENTS"
      CONTEXT+="\n"
    fi
  fi
fi

# Output JSON if we have context to inject
if [[ -n "$CONTEXT" ]]; then
  # Escape for JSON (handle newlines and quotes)
  ESCAPED=$(echo -e "$CONTEXT" | jq -Rs .)
  echo "{\"additionalContext\": $ESCAPED}"
fi
