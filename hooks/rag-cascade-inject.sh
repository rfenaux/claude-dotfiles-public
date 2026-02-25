#!/bin/bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# rag-cascade-inject.sh - Auto-RAG injection on question prompts
# Detects questions in user messages and injects RAG search guidance
#
# Part of: CC 2.1 Feature Adoption (P0, QW-1)
# Created: 2026-02-14
# Event: UserPromptSubmit
#
# Returns additionalContext to prompt Claude to search RAG before answering.
# Lightweight (~50ms) - no actual RAG query, just contextual guidance.

HOOK_INPUT=$(cat)

# Extract user message
USER_MSG=$(echo "$HOOK_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('message', data.get('content', '')))
except:
    pass
" 2>/dev/null)

[ -z "$USER_MSG" ] && exit 0

# Skip short messages, commands, approvals
MSG_LEN=${#USER_MSG}
[ "$MSG_LEN" -lt 15 ] && exit 0
[[ "$USER_MSG" == /* ]] && exit 0
[[ "$USER_MSG" =~ ^(go|yes|y|no|n|ok|sure|original|proceed|approved)$ ]] && exit 0
# Skip ctm commands
[[ "$USER_MSG" == ctm* ]] && exit 0

# Detect question patterns (case-insensitive)
IS_QUESTION=$(echo "$USER_MSG" | python3 -c "
import sys, re
msg = sys.stdin.read().strip().lower()
patterns = [
    r'^(how|why|what|where|when|which|who|does|can|is|are|do|should|could|would|have|has|did|was|were)\b',
    r'^(explain|describe|tell me|show me|find|search|look|check|remind me|remember)\b',
    r'\?$'
]
if any(re.search(p, msg) for p in patterns):
    print('yes')
" 2>/dev/null)

[ "$IS_QUESTION" != "yes" ] && exit 0

# Check for RAG indexes
CWD=$(echo "$HOOK_INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('cwd', ''))
except:
    pass
" 2>/dev/null <<< "$HOOK_INPUT" 2>/dev/null)
CWD="${CWD:-$(pwd)}"

HAS_PROJECT_RAG=false
CHECK="$CWD"
while [ "$CHECK" != "/" ] && [ -n "$CHECK" ]; do
    if [ -d "$CHECK/.rag" ]; then
        HAS_PROJECT_RAG=true
        break
    fi
    CHECK=$(dirname "$CHECK")
done

HAS_LESSONS_RAG=false
[ -d "$HOME/.claude/lessons/.rag" ] && HAS_LESSONS_RAG=true

HAS_CONFIG_RAG=false
[ -d "$HOME/.claude/.rag" ] && HAS_CONFIG_RAG=true

HAS_HUBLE_RAG=false
[ -d "$HOME/projects/huble-wiki/.rag" ] && HAS_HUBLE_RAG=true

# Only inject if RAG indexes exist
if [ "$HAS_PROJECT_RAG" = true ] || [ "$HAS_LESSONS_RAG" = true ] || [ "$HAS_CONFIG_RAG" = true ] || [ "$HAS_HUBLE_RAG" = true ]; then
    # Build index list
    INDEXES=""
    [ "$HAS_LESSONS_RAG" = true ] && INDEXES="lessons"
    [ "$HAS_CONFIG_RAG" = true ] && INDEXES="${INDEXES:+$INDEXES, }config"
    [ "$HAS_HUBLE_RAG" = true ] && INDEXES="${INDEXES:+$INDEXES, }huble-wiki"
    [ "$HAS_PROJECT_RAG" = true ] && INDEXES="${INDEXES:+$INDEXES, }project"

    cat << EOF
{"additionalContext": "[RAG-CASCADE] Question detected. Search RAG BEFORE answering — available indexes: $INDEXES. Use rag_search with relevant terms from the user's question."}
EOF
fi

exit 0
