#!/bin/bash
# Context Preflight Hook
# Auto-runs RAG search for question-like prompts when .rag exists
# Triggered by UserPromptSubmit hook

# Read hook input from stdin
HOOK_INPUT=$(cat)
USER_MESSAGE=$(echo "$HOOK_INPUT" | jq -r '.user_prompt // empty')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')

# Skip if no message or CWD
[ -z "$USER_MESSAGE" ] || [ "$USER_MESSAGE" = "null" ] && exit 0
[ -z "$CWD" ] || [ "$CWD" = "null" ] && exit 0

# Only for project directories
if [[ ! "$CWD" =~ ^~/Documents/(Projects|Docs) ]]; then
    exit 0
fi

# Find .rag folder (traverse up)
RAG_DIR=""
PROJECT_ROOT="$CWD"
CHECK_PATH="$CWD"
while [ "$CHECK_PATH" != "/" ]; do
    if [ -d "$CHECK_PATH/.rag" ]; then
        RAG_DIR="$CHECK_PATH/.rag"
        PROJECT_ROOT="$CHECK_PATH"
        break
    fi
    CHECK_PATH=$(dirname "$CHECK_PATH")
done

# Skip if no RAG folder
[ -z "$RAG_DIR" ] && exit 0

# ============================================
# QUESTION DETECTION
# Check if the message looks like a question about the project
# ============================================

# Convert to lowercase for matching
MSG_LOWER=$(echo "$USER_MESSAGE" | tr '[:upper:]' '[:lower:]')

# Skip short messages (likely commands)
[ ${#USER_MESSAGE} -lt 20 ] && exit 0

# Skip if message starts with common non-question patterns
case "$MSG_LOWER" in
    "fix "*|"create "*|"write "*|"add "*|"remove "*|"delete "*|"update "*|"commit"*|"push"*|"run "*|"test "*|"build"*)
        exit 0
        ;;
esac

# Check for question indicators
IS_QUESTION=false

# Explicit question patterns
if echo "$MSG_LOWER" | grep -qE "(^(what|where|how|why|when|which|who|can you|could you|is there|are there|do we|does|did|should|would|have we|has|explain|tell me|show me|find|search|look for|describe)|\\?)"; then
    IS_QUESTION=true
fi

# Project-specific question patterns
if echo "$MSG_LOWER" | grep -qE "(about (the|this|our) (project|code|system|architecture|decision|implementation)|in (the|this) (codebase|repo|project)|previously|before|last time|earlier|we discussed|we decided|requirement|stakeholder)"; then
    IS_QUESTION=true
fi

# Skip if not a question
[ "$IS_QUESTION" = "false" ] && exit 0

# ============================================
# AUTO RAG SEARCH
# Run search and output context
# ============================================

# Extract key terms from the question (remove stop words, get nouns/verbs)
SEARCH_QUERY=$(echo "$USER_MESSAGE" | head -c 500)

# Run RAG search via MCP server
RESULT=$(~/.local/bin/uv run --directory ~/.claude/mcp-servers/rag-server python -c "
import sys
import json
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
from rag_server.server import rag_search

query = '''$SEARCH_QUERY'''
project_path = '$PROJECT_ROOT'

try:
    results = rag_search(query, project_path, top_k=5)

    if results and results.get('results'):
        hits = results['results']
        if hits:
            print('<context-preflight>')
            print('RAG found relevant context for your question:')
            print('')
            for i, hit in enumerate(hits[:3], 1):
                source = hit.get('source', 'unknown')
                text = hit.get('text', '')[:500]
                score = hit.get('score', 0)
                print(f'{i}. [{source}] (relevance: {score:.2f})')
                print(f'   {text[:200]}...')
                print('')
            print('</context-preflight>')
except Exception as e:
    pass  # Silent fail
" 2>/dev/null)

# Output result if we got hits
if [ -n "$RESULT" ]; then
    echo "$RESULT"
fi

exit 0
