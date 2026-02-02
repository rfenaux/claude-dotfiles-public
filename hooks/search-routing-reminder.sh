#!/bin/bash
# Search Routing Reminder - PreToolUse hook for Grep/Glob
# Reminds Claude to consider RAG search before pattern matching
# for semantic/conceptual queries

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
CHECK_PATH="${CWD:-$(pwd)}"
while [ "$CHECK_PATH" != "/" ]; do
    if [ -d "$CHECK_PATH/.rag" ]; then
        RAG_EXISTS=true
        break
    fi
    CHECK_PATH=$(dirname "$CHECK_PATH")
done

# Also check global lessons RAG
LESSONS_RAG="~/.claude/lessons/.rag"
MAIN_RAG="~/.claude/.rag"

if [ "$RAG_EXISTS" = true ] || [ -d "$LESSONS_RAG" ] || [ -d "$MAIN_RAG" ]; then
    cat << 'EOF'
[SEARCH_ROUTING_HINT]
RAG indexes are available. Consider the search tool hierarchy:
- **Conceptual/why/how questions** → rag_search FIRST (semantic)
- **Exact text match** → Grep (pattern)
- **File discovery** → Glob (names)

Available RAG indexes:
- ~/.claude/.rag (config, agents, skills, guides)
- ~/.claude/lessons/.rag (cross-project learnings)
- Project .rag/ (if exists in working directory)

For HubSpot/domain questions, also search lessons:
  rag_search("query", project_path="~/.claude/lessons")
EOF
fi

exit 0
