#!/bin/bash
# lesson-surfacer.sh - Surface relevant lessons and pending analyses on session start
#
# Runs on: SessionStart hook
# Purpose:
#   1. Check for pending lesson analyses (flag for Claude to process)
#   2. Surface contextually relevant lessons from existing knowledge base
#
# Output is added to Claude's context via hook system.

set -e

LESSONS_DIR="$HOME/.claude/lessons"
PENDING_DIR="$LESSONS_DIR/pending"
INDEX_FILE="$LESSONS_DIR/index.json"

# ============================================
# SECTION 1: Check for lessons pending review
# ============================================

REVIEW_DIR="$LESSONS_DIR/review"
REVIEW_COUNT=0
REVIEW_INFO=""

if [ -d "$REVIEW_DIR" ]; then
    REVIEW_COUNT=$(find "$REVIEW_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [ "$REVIEW_COUNT" -gt 0 ]; then
        REVIEW_INFO=$(cat << EOF

## Lessons Pending Approval

**$REVIEW_COUNT lesson(s)** awaiting your review.

Run \`cc lessons review\` to approve or reject.

EOF
)
    fi
fi

# ============================================
# SECTION 1b: Check for pending analyses
# ============================================

PENDING_COUNT=0
PENDING_INFO=""

if [ -d "$PENDING_DIR" ]; then
    PENDING_COUNT=$(find "$PENDING_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')

    if [ "$PENDING_COUNT" -gt 0 ]; then
        PENDING_INFO=$(cat << EOF

## Conversations Queued for Analysis

**$PENDING_COUNT conversation(s)** queued for lesson extraction.

Ask Claude to "analyze pending lessons" to process them.

EOF
)
    fi
fi

# ============================================
# SECTION 2: Get lesson statistics
# ============================================

STATS_INFO=""
if [ -f "$INDEX_FILE" ]; then
    TOTAL=$(jq -r '.stats.total // 0' "$INDEX_FILE" 2>/dev/null)
    ACTIVE=$(jq -r '.stats.active // 0' "$INDEX_FILE" 2>/dev/null)
    CONFLICTED=$(jq -r '.stats.conflicted // 0' "$INDEX_FILE" 2>/dev/null)

    if [ "$TOTAL" -gt 0 ]; then
        STATS_INFO=$(cat << EOF

## Learned Lessons Available

**$ACTIVE active lessons** in knowledge base.
EOF
)
        if [ "$CONFLICTED" -gt 0 ]; then
            STATS_INFO="$STATS_INFO
**$CONFLICTED conflicts** need review (\`/lessons conflicts\`)."
        fi
    fi
fi

# ============================================
# SECTION 3: Context-aware lesson surfacing
# ============================================

# Try to detect context from CWD, recent activity, AND CTM tasks
CWD=$(pwd)
CONTEXT_HINT=""
CTM_CONTEXT=""

# ---- CTM Task Context (NEW) ----
# Extract keywords from active CTM tasks (title + tags)
CTM_INDEX="$HOME/.claude/ctm/index.json"
if [ -f "$CTM_INDEX" ]; then
    # Get active task titles and tags
    CTM_CONTEXT=$(jq -r '
        .agents | to_entries[] |
        select(.value.status == "active" or .value.status == "paused") |
        .value.title + " " + (.value.tags // [] | join(" "))
    ' "$CTM_INDEX" 2>/dev/null | tr '\n' ' ' | xargs)

    # If no active tasks, get most recently active one
    if [ -z "$CTM_CONTEXT" ]; then
        CTM_CONTEXT=$(jq -r '
            [.agents | to_entries[] | .value | {title, tags, last_active}] |
            sort_by(.last_active) | reverse | .[0] |
            .title + " " + (.tags // [] | join(" "))
        ' "$CTM_INDEX" 2>/dev/null | xargs)
    fi
fi

# ---- Directory Context ----
DIR_CONTEXT=""
if [[ "$CWD" =~ [Hh]ub[Ss]pot ]] || [[ "$CWD" =~ [Rr]escue ]]; then
    DIR_CONTEXT="hubspot api integration workflows"
elif [[ "$CWD" =~ \.claude ]]; then
    DIR_CONTEXT="claude code configuration agents"
elif [[ "$CWD" =~ [Cc]ognita ]]; then
    DIR_CONTEXT="<project> crm project"
elif [[ "$CWD" =~ [Pp]rojects.*[Pp]ro ]]; then
    # Professional projects - extract project name
    PROJECT_NAME=$(basename "$CWD" | tr '-' ' ')
    DIR_CONTEXT="$PROJECT_NAME project implementation"
fi

# Combine contexts (CTM takes priority, directory adds context)
if [ -n "$CTM_CONTEXT" ] && [ -n "$DIR_CONTEXT" ]; then
    CONTEXT_HINT="$CTM_CONTEXT $DIR_CONTEXT"
elif [ -n "$CTM_CONTEXT" ]; then
    CONTEXT_HINT="$CTM_CONTEXT"
elif [ -n "$DIR_CONTEXT" ]; then
    CONTEXT_HINT="$DIR_CONTEXT"
fi

# Clean up context hint (remove duplicates, limit length)
if [ -n "$CONTEXT_HINT" ]; then
    CONTEXT_HINT=$(echo "$CONTEXT_HINT" | tr '[:upper:]' '[:lower:]' | tr -s ' ' | head -c 200)
fi

RELEVANT_LESSONS=""
LESSONS_FILE="$LESSONS_DIR/lessons.jsonl"
CONTEXT_SOURCE=""

# Track context source for output
if [ -n "$CTM_CONTEXT" ]; then
    CONTEXT_SOURCE="CTM task"
elif [ -n "$DIR_CONTEXT" ]; then
    CONTEXT_SOURCE="directory"
fi

# Only search if we have context and lessons exist
if [ -n "$CONTEXT_HINT" ] && [ -f "$LESSONS_FILE" ]; then

    # Method 1: Fast grep-based search on lessons.jsonl (primary)
    # This is faster than RAG for keyword matching and works without Ollama
    SEARCH_RESULT=$(python3 << PYEOF
import json
import sys
import re

context = '''$CONTEXT_HINT'''
keywords = set(context.lower().split())
# Remove common stopwords
stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'project', 'implementation'}
keywords = keywords - stopwords

if not keywords:
    sys.exit(0)

matches = []
try:
    with open('$LESSONS_FILE', 'r') as f:
        for line in f:
            if not line.strip():
                continue
            try:
                lesson = json.loads(line)
                if lesson.get('status') != 'approved':
                    continue

                # Score based on keyword matches in title, tags, category, lesson text
                score = 0
                title = lesson.get('title', '').lower()
                tags = ' '.join(lesson.get('tags', [])).lower()
                category = lesson.get('category', '').lower()
                content = lesson.get('lesson', '').lower()

                searchable = f"{title} {tags} {category} {content}"

                for kw in keywords:
                    if kw in searchable:
                        # Weight: title matches worth more
                        if kw in title:
                            score += 3
                        if kw in tags:
                            score += 2
                        if kw in category:
                            score += 2
                        if kw in content:
                            score += 1

                if score > 0:
                    matches.append({
                        'score': score,
                        'title': lesson.get('title', 'Untitled'),
                        'lesson': lesson.get('lesson', '')[:150],
                        'tags': lesson.get('tags', []),
                        'confidence': lesson.get('confidence', 0)
                    })
            except json.JSONDecodeError:
                continue

    # Sort by score, take top 3
    matches.sort(key=lambda x: (-x['score'], -x['confidence']))
    for m in matches[:3]:
        tags_str = ', '.join(m['tags'][:3]) if m['tags'] else ''
        print(f"**{m['title']}**")
        print(f"  {m['lesson']}...")
        if tags_str:
            print(f"  _Tags: {tags_str}_")
        print()

except Exception as e:
    pass
PYEOF
2>/dev/null) || true

    # Method 2: RAG semantic search (fallback if grep found nothing and RAG is available)
    if [ -z "$SEARCH_RESULT" ] && [ -d "$LESSONS_DIR/.rag" ]; then
        SEARCH_RESULT=$("$HOME/.local/bin/uv" run --directory "$HOME/.claude/mcp-servers/rag-server" python -c "
import sys
import json
sys.path.insert(0, '~/.claude/mcp-servers/rag-server/src')
try:
    from rag_server.server import rag_search
    results = rag_search(
        query='$CONTEXT_HINT',
        project_path='$LESSONS_DIR',
        top_k=3
    )
    if results.get('results'):
        for r in results['results'][:3]:
            text = r.get('text', '')[:200]
            print(f'- {text}...')
except Exception as e:
    pass
" 2>/dev/null || true)
    fi

    if [ -n "$SEARCH_RESULT" ]; then
        RELEVANT_LESSONS=$(cat << EOF

### Relevant Lessons for This Context

$SEARCH_RESULT
_Source: $CONTEXT_SOURCE | Query: "${CONTEXT_HINT:0:80}..."_
EOF
)
    fi
fi

# ============================================
# OUTPUT
# ============================================

# Only output if we have something to show
if [ -n "$REVIEW_INFO" ] || [ -n "$PENDING_INFO" ] || [ -n "$STATS_INFO" ] || [ -n "$RELEVANT_LESSONS" ]; then
    echo ""
    echo "---"
    echo "$REVIEW_INFO"
    echo "$STATS_INFO"
    echo "$RELEVANT_LESSONS"
    echo "$PENDING_INFO"
    echo "---"
fi

exit 0
