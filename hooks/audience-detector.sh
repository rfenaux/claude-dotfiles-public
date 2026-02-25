#!/bin/bash
set +e  # Never use set -e in hooks — non-zero exits kill the hook
# audience-detector.sh — UserPromptSubmit hook
# Detects audience from user prompt keywords and writes profile to session file
# Output: Injects detected audience context for Claude
# Performance budget: <50ms

SESSION_ID="${CLAUDE_SESSION_ID:-unknown}"
AUDIENCE_FILE="/tmp/claude-audience-${SESSION_ID}.txt"
PROFILES_CONFIG="${HOME}/.claude/config/audience-profiles.json"

# Skip if config missing
if [[ ! -f "$PROFILES_CONFIG" ]]; then
    exit 0
fi

# Get user prompt from stdin or TOOL_INPUT
PROMPT="${TOOL_INPUT:-}"
if [[ -z "$PROMPT" ]]; then
    exit 0
fi

# Lowercase for matching
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Manual override detection (instant classification, 10 points)
if echo "$PROMPT_LOWER" | grep -qi "for executives\|for leadership\|for the CEO\|for the board"; then
    echo "executive" > "$AUDIENCE_FILE"
    echo "[AUDIENCE: Executive] Adapt output: business impact first, no code, concise (max 1 page), include ROI/metrics."
    exit 0
fi
if echo "$PROMPT_LOWER" | grep -qi "explain technically\|for developers\|technical detail"; then
    echo "technical" > "$AUDIENCE_FILE"
    echo "[AUDIENCE: Technical] Adapt output: include code snippets, file paths, trade-offs, full detail."
    exit 0
fi
if echo "$PROMPT_LOWER" | grep -qi "for the team\|step by step\|how-to guide\|as a runbook"; then
    echo "operational" > "$AUDIENCE_FILE"
    echo "[AUDIENCE: Operational] Adapt output: numbered steps, checklists, tips/warnings, moderate jargon."
    exit 0
fi
if echo "$PROMPT_LOWER" | grep -qi "in simple terms\|explain simply\|ELI5\|without jargon\|in plain english"; then
    echo "non_technical" > "$AUDIENCE_FILE"
    echo "[AUDIENCE: Non-Technical] Adapt output: analogies, no acronyms, short sentences, concrete examples."
    exit 0
fi

# Keyword scoring (fast grep-based)
EXEC_SCORE=0
TECH_SCORE=0
OPS_SCORE=0
NONTECH_SCORE=0

# Executive keywords
for kw in "executive summary" "board" "roi" "strategic" "high-level" "bottom line" "investment" "stakeholder" "business case"; do
    echo "$PROMPT_LOWER" | grep -qi "$kw" && EXEC_SCORE=$((EXEC_SCORE + 1))
done

# Technical keywords
for kw in "implementation" "api" "code" "architecture" "schema" "endpoint" "function" "debug" "deploy" "refactor" "migration" "database" "query" "sdk"; do
    echo "$PROMPT_LOWER" | grep -qi "\b${kw}\b" && TECH_SCORE=$((TECH_SCORE + 1))
done

# Operational keywords
for kw in "process" "workflow" "sop" "training" "onboarding" "guide" "handover" "documentation" "runbook"; do
    echo "$PROMPT_LOWER" | grep -qi "$kw" && OPS_SCORE=$((OPS_SCORE + 1))
done

# Non-technical keywords
for kw in "basics" "overview" "layman" "non-technical"; do
    echo "$PROMPT_LOWER" | grep -qi "$kw" && NONTECH_SCORE=$((NONTECH_SCORE + 1))
done

# Find winner (min 2 matches required)
MAX_SCORE=0
WINNER="mixed"

if [[ $EXEC_SCORE -ge 2 && $EXEC_SCORE -gt $MAX_SCORE ]]; then
    MAX_SCORE=$EXEC_SCORE; WINNER="executive"
fi
if [[ $TECH_SCORE -ge 2 && $TECH_SCORE -gt $MAX_SCORE ]]; then
    MAX_SCORE=$TECH_SCORE; WINNER="technical"
fi
if [[ $OPS_SCORE -ge 2 && $OPS_SCORE -gt $MAX_SCORE ]]; then
    MAX_SCORE=$OPS_SCORE; WINNER="operational"
fi
if [[ $NONTECH_SCORE -ge 2 && $NONTECH_SCORE -gt $MAX_SCORE ]]; then
    MAX_SCORE=$NONTECH_SCORE; WINNER="non_technical"
fi

# Write detected profile
echo "$WINNER" > "$AUDIENCE_FILE"

# Only inject context if NOT mixed (mixed = no strong signal, don't clutter context)
case "$WINNER" in
    executive)
        echo "[AUDIENCE: Executive] Adapt output: business impact first, no code, concise (max 1 page), include ROI/metrics."
        ;;
    technical)
        echo "[AUDIENCE: Technical] Adapt output: include code snippets, file paths, trade-offs, full detail."
        ;;
    operational)
        echo "[AUDIENCE: Operational] Adapt output: numbered steps, checklists, tips/warnings, moderate jargon."
        ;;
    non_technical)
        echo "[AUDIENCE: Non-Technical] Adapt output: analogies, no acronyms, short sentences, concrete examples."
        ;;
    *)
        # Mixed: no injection (don't pollute context when no clear signal)
        ;;
esac

exit 0
