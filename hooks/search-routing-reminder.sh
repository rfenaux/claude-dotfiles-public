#!/bin/bash
# Search Routing Reminder - PreToolUse hook for Grep/Glob
# Uses additionalContext (v2.1.9) to inject RAG search guidance
# into the model's context when RAG indexes are available

# Circuit breaker: skip if too many recent failures
. "$HOME/.claude/hooks/lib/circuit-breaker.sh" 2>/dev/null
check_circuit "search-routing-reminder" || exit 0

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')

# Only process Grep and Glob
case "$TOOL_NAME" in
    Grep|Glob)
        ;;
    *)
        exit 0
        ;;
esac

# Determine if this is a project with RAG
RAG_EXISTS=false
PROJECT_RAG=""
CHECK_PATH="${CWD:-$(pwd)}"
while [ "$CHECK_PATH" != "/" ]; do
    if [ -d "$CHECK_PATH/.rag" ]; then
        RAG_EXISTS=true
        PROJECT_RAG="$CHECK_PATH/.rag"
        break
    fi
    CHECK_PATH=$(dirname "$CHECK_PATH")
done

# Also check global RAG indexes
LESSONS_RAG="${HOME}/.claude/lessons/.rag"
MAIN_RAG="${HOME}/.claude/.rag"
ORG_WIKI_RAG="${ORG_WIKI_PATH:+${ORG_WIKI_PATH}/.rag}"

if [ "$RAG_EXISTS" = true ] || [ -d "$LESSONS_RAG" ] || [ -d "$MAIN_RAG" ] || [ -n "$ORG_WIKI_RAG" -a -d "$ORG_WIKI_RAG" ]; then
    # Build available indexes list
    INDEXES="~/.claude/.rag (config/agents/skills/guides)"
    [ -d "$LESSONS_RAG" ] && INDEXES="$INDEXES, ~/.claude/lessons/.rag (cross-project learnings)"
    [ -n "$ORG_WIKI_RAG" ] && [ -d "$ORG_WIKI_RAG" ] && INDEXES="$INDEXES, ${ORG_WIKI_PATH}/.rag (organization wiki)"
    [ -n "$PROJECT_RAG" ] && INDEXES="$INDEXES, project .rag/ ($PROJECT_RAG)"

    # v2.1.9: Return JSON with additionalContext for model injection
    cat << EOF
{
  "additionalContext": "RAG indexes available: $INDEXES. For conceptual/why/how queries, use rag_search FIRST (semantic) before pattern-matching with Grep/Glob. Search order: 1) rag_search lessons 2) rag_search config 3) rag_search org-wiki (if set) 4) rag_search project 5) Grep/Glob for exact matches."
}
EOF
fi

exit 0
