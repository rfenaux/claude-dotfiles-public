#!/bin/bash
# rag-cascade-inject.sh - Auto-inject RAG results for questions
# Part of Claude Code 2.1.x Feature Adoption (PRD-claude-code-2.1-feature-adoption)
#
# Returns additionalContext with RAG search results when question patterns detected
# Hook type: PreToolUse (triggers on Read to catch file access after questions)

set -e

HOOK_INPUT=$(cat)
TOOL_NAME=$(echo "$HOOK_INPUT" | jq -r '.tool_name // empty')
SESSION_ID=$(echo "$HOOK_INPUT" | jq -r '.session_id // empty')
CWD=$(echo "$HOOK_INPUT" | jq -r '.cwd // empty')

# Marker file to track questions asked this session
QUESTION_MARKER="/tmp/claude-rag-cascade-${SESSION_ID:-$$}"

# Only trigger on first Read after a question (avoid flooding)
# This hook works in conjunction with the existing search-routing-reminder.sh

# Check if RAG is available
RAG_AVAILABLE=false
LESSONS_RAG="~/.claude/lessons/.rag"
MAIN_RAG="~/.claude/.rag"
PROJECT_RAG="${CWD}/.rag"

if [ -d "$LESSONS_RAG" ] || [ -d "$MAIN_RAG" ]; then
    RAG_AVAILABLE=true
fi

# Exit early if no RAG available
if [ "$RAG_AVAILABLE" = false ]; then
    exit 0
fi

# This hook injects context into the model via additionalContext
# The model will see this information alongside the tool result

# Get the last few user messages to detect question patterns
# Since we don't have direct access to conversation, we rely on patterns
# The key insight: this hook runs, so we should add helpful context

# Construct helpful RAG reminder as additionalContext
# This is more efficient than running RAG searches in the hook
# (which would be slow and might not match the actual question)

cat << 'CONTEXT_JSON'
{
  "additionalContext": "[RAG CONTEXT AVAILABLE]\nBefore answering conceptual questions (how/why/what), search these RAG indexes:\n\n1. Lessons (cross-project knowledge):\n   rag_search(query, project_path=\"~/.claude/lessons\")\n\n2. Claude config (agents, skills, guides):\n   rag_search(query, project_path=\"~/.claude\")\n\n3. Project-specific (if .rag/ exists):\n   rag_search(query, project_path=\"<current_project>\")\n\nSearch order: Lessons → Config → Project → Grep/Glob"
}
CONTEXT_JSON

exit 0
