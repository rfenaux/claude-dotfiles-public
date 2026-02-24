#!/bin/bash
# enrich-project-memory.sh - Enrich per-project MEMORY.md with CTM context + lessons
#
# Called by SessionStart hook AFTER sync-memory.sh.
# Appends/replaces a "## Project Context (Auto-Generated)" section with:
#   1. CTM decisions, blockers, next_actions from matching task
#   2. High-confidence lessons (approved, >= 0.8) matching project tags
#   3. DECISIONS.md fallback if no CTM match
#
# Safeguards: idempotent, fail-silent, 24h cooldown, .bak backup, 200-line limit

set -euo pipefail

# --- Configuration ---
PROJECTS_DIR="$HOME/.claude/projects"
CTM_TASKS_DIR="$HOME/.claude/ctm/tasks"
LESSONS_FILE="$HOME/.claude/lessons/lessons.jsonl"
MAX_LINES=200
COOLDOWN_HOURS=24
MIN_CONFIDENCE=0.8
MAX_LESSONS=3
MARKER="## Project Context (Auto-Generated)"

# --- Path encoding (handles both Claude Code native and sync-memory.sh formats) ---
get_project_memory_file() {
    # Claude Code native encoding: replaces both / and spaces with -
    local native_encoded
    native_encoded=$(echo "$PWD" | sed 's|[/ ]|-|g' | sed 's|^-||')
    local native_path="$PROJECTS_DIR/-$native_encoded/memory/MEMORY.md"

    # sync-memory.sh encoding: replaces only / with - (preserves spaces)
    local legacy_encoded
    legacy_encoded=$(echo "$PWD" | sed 's|/|-|g' | sed 's|^-||')
    local legacy_path="$PROJECTS_DIR/-$legacy_encoded/memory/MEMORY.md"

    # Prefer native encoding (what Claude Code actually reads)
    if [[ -f "$native_path" ]]; then
        echo "$native_path"
    elif [[ -f "$legacy_path" ]]; then
        echo "$legacy_path"
    else
        # Default to native encoding for new files
        echo "$native_path"
    fi
}

# --- Extract project keywords from PWD + CTM tags for lesson matching ---
get_project_keywords() {
    # Extract meaningful directory names from PWD
    # e.g., ${HOME}/Documents/Projects - Pro/Huble/Rescue-Claude
    # yields: huble rescue claude
    local dir_name
    dir_name=$(basename "$PWD")
    local parent_name
    parent_name=$(basename "$(dirname "$PWD")")

    # Base keywords from directory names
    local base_keywords
    base_keywords=$(echo "$dir_name $parent_name" \
        | tr '[:upper:]' '[:lower:]' \
        | sed 's/[-_. ]/ /g' \
        | tr ' ' '\n' \
        | grep -v '^$' \
        | grep -v '^pro$' \
        | grep -v '^projects$' \
        | grep -v '^documents$' \
        | grep -v '^users$')

    # Domain keyword inference (known associations)
    local domain_keywords=""
    if echo "$base_keywords" | grep -qi 'huble'; then
        domain_keywords="hubspot api integration"
    fi

    # Combine and deduplicate
    echo "$base_keywords $domain_keywords" \
        | tr ' ' '\n' \
        | grep -v '^$' \
        | sort -u
}

# --- Check cooldown ---
check_cooldown() {
    local memory_file="$1"
    local comment_line

    # Look for the enrichment timestamp comment
    comment_line=$(grep -o '<!-- Last enriched: [^>]*-->' "$memory_file" 2>/dev/null || echo "")
    if [[ -z "$comment_line" ]]; then
        return 0  # No previous enrichment, proceed
    fi

    # Extract timestamp
    local last_enriched
    last_enriched=$(echo "$comment_line" | sed 's/.*Last enriched: \(.*\) -->/\1/')

    # Compare with current time (macOS date)
    local last_epoch current_epoch diff_hours
    last_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$last_enriched" "+%s" 2>/dev/null || echo "0")
    current_epoch=$(date "+%s")
    diff_hours=$(( (current_epoch - last_epoch) / 3600 ))

    if [[ $diff_hours -lt $COOLDOWN_HOURS ]]; then
        # Check if CTM tasks were updated since last enrichment
        local ctm_updated=false
        for task_file in "$CTM_TASKS_DIR"/*.json; do
            [[ -f "$task_file" ]] || continue
            if [[ "$task_file" -nt "$memory_file" ]]; then
                ctm_updated=true
                break
            fi
        done

        if [[ "$ctm_updated" == "false" ]]; then
            return 1  # Still in cooldown and no CTM changes
        fi
    fi

    return 0  # Proceed with enrichment
}

# --- Extract CTM context for current project ---
extract_ctm_context() {
    local project_dir_name
    project_dir_name=$(basename "$PWD" | tr '[:upper:]' '[:lower:]')

    local decisions="" blockers="" next_actions=""
    local matched=false

    for task_file in "$CTM_TASKS_DIR"/*.json; do
        [[ -f "$task_file" ]] || continue

        # Check if task matches current project
        local task_project task_name task_status
        task_project=$(jq -r '.context.project // .project // ""' "$task_file" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        task_name=$(jq -r '.name // .task.title // ""' "$task_file" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        task_status=$(jq -r '.status // .state.status // ""' "$task_file" 2>/dev/null)

        # Skip non-active tasks
        [[ "$task_status" == "active" || "$task_status" == "in_progress" ]] || continue

        # Match by project field or task name containing project dir name
        if [[ "$task_project" == *"$project_dir_name"* ]] || [[ "$task_name" == *"$project_dir_name"* ]]; then
            matched=true

            # Extract recent_decisions (array of strings)
            decisions=$(jq -r '
                (.recent_decisions // [])[:5][] // empty
            ' "$task_file" 2>/dev/null | sed 's/^D: //' || echo "")

            # Also check decisions array (objects with .decision field)
            if [[ -z "$decisions" ]]; then
                decisions=$(jq -r '
                    (.decisions // [])[:5][] | .decision // empty
                ' "$task_file" 2>/dev/null || echo "")
            fi

            # Extract blockers
            blockers=$(jq -r '
                (.blockers // [])[] // empty
            ' "$task_file" 2>/dev/null || echo "")

            # Extract next_actions
            next_actions=$(jq -r '
                (.next_actions // [])[:3][] // empty
            ' "$task_file" 2>/dev/null || echo "")

            break  # Use first matching task
        fi
    done

    if [[ "$matched" == "true" ]]; then
        # Write to temp files (avoids multiline prefix parsing issues)
        local tmpdir="${TMPDIR:-/tmp}/enrich-memory-$$"
        mkdir -p "$tmpdir"
        echo "$decisions" > "$tmpdir/decisions"
        echo "$blockers" > "$tmpdir/blockers"
        echo "$next_actions" > "$tmpdir/next_actions"
        echo "$tmpdir"
        return 0
    fi

    return 1  # No CTM match
}

# --- Extract DECISIONS.md fallback ---
extract_decisions_md() {
    local decisions_file="$PWD/.claude/context/DECISIONS.md"
    [[ -f "$decisions_file" ]] || return 1

    # Extract non-superseded decisions (lines not starting with ~~ and containing decision patterns)
    grep -E '^\s*[-*]\s+' "$decisions_file" \
        | grep -v '~~' \
        | grep -v 'Superseded' \
        | head -5 \
        | sed 's/^\s*[-*]\s*//' \
        || return 1
}

# --- Extract matching lessons ---
extract_lessons() {
    [[ -f "$LESSONS_FILE" ]] || return 1

    local keywords
    keywords=$(get_project_keywords)
    [[ -n "$keywords" ]] || return 1

    # Build jq tag-matching filter from keywords
    local keyword_array
    keyword_array=$(echo "$keywords" | jq -R -s 'split("\n") | map(select(length > 0))')

    # Filter: approved, confidence >= threshold, tags match any keyword
    jq -r --argjson keywords "$keyword_array" --argjson min_conf "$MIN_CONFIDENCE" '
        select(.status == "approved")
        | select(.confidence >= $min_conf)
        | select(
            (.tags // []) as $tags |
            ($keywords | any(. as $kw | $tags | any(. | test($kw; "i"))))
        )
        | "[L] " + .title
    ' "$LESSONS_FILE" 2>/dev/null \
        | head -"$MAX_LESSONS" \
        || return 1
}

# --- Generate the enrichment block ---
generate_enrichment() {
    local timestamp
    timestamp=$(date "+%Y-%m-%dT%H:%M:%S")

    local output=""
    output+="$MARKER"$'\n'
    output+="<!-- Last enriched: $timestamp -->"$'\n'

    # Try CTM first
    local ctm_tmpdir decisions="" blockers="" next_actions=""
    if ctm_tmpdir=$(extract_ctm_context 2>/dev/null); then
        decisions=$(cat "$ctm_tmpdir/decisions" 2>/dev/null || echo "")
        blockers=$(cat "$ctm_tmpdir/blockers" 2>/dev/null || echo "")
        next_actions=$(cat "$ctm_tmpdir/next_actions" 2>/dev/null || echo "")
        rm -rf "$ctm_tmpdir" 2>/dev/null
    fi

    # Decisions section (CTM or DECISIONS.md fallback)
    local has_decisions=false
    if [[ -n "$decisions" ]]; then
        output+=$'\n'"### Active Decisions"$'\n'
        while IFS= read -r line; do
            [[ -n "$line" ]] && output+="- $line"$'\n' && has_decisions=true
        done <<< "$decisions"
    else
        # Fallback to DECISIONS.md
        local fallback_decisions
        if fallback_decisions=$(extract_decisions_md 2>/dev/null) && [[ -n "$fallback_decisions" ]]; then
            output+=$'\n'"### Active Decisions"$'\n'
            while IFS= read -r line; do
                [[ -n "$line" ]] && output+="- $line"$'\n' && has_decisions=true
            done <<< "$fallback_decisions"
        fi
    fi

    # Lessons section
    local lessons has_lessons=false
    if lessons=$(extract_lessons 2>/dev/null) && [[ -n "$lessons" ]]; then
        output+=$'\n'"### Known Patterns"$'\n'
        while IFS= read -r line; do
            [[ -n "$line" ]] && output+="- $line"$'\n' && has_lessons=true
        done <<< "$lessons"
    fi

    # Blockers section
    local has_blockers=false
    if [[ -n "$blockers" ]]; then
        output+=$'\n'"### Current Blockers"$'\n'
        while IFS= read -r line; do
            [[ -n "$line" ]] && output+="- $line"$'\n' && has_blockers=true
        done <<< "$blockers"
    fi

    # Next actions section
    if [[ -n "$next_actions" ]]; then
        output+=$'\n'"### Next Actions"$'\n'
        while IFS= read -r line; do
            [[ -n "$line" ]] && output+="- $line"$'\n'
        done <<< "$next_actions"
    fi

    # Only output if we have at least one section with content
    if [[ "$has_decisions" == "true" || "$has_lessons" == "true" || "$has_blockers" == "true" ]]; then
        echo "$output"
        return 0
    fi

    return 1  # Nothing to enrich
}

# --- Merge enrichment into MEMORY.md ---
merge_into_memory() {
    local memory_file="$1"
    local enrichment="$2"

    [[ -f "$memory_file" ]] || return 1

    # Create backup
    cp "$memory_file" "${memory_file}.bak"

    # Check if auto-generated section already exists
    if grep -q "^$MARKER" "$memory_file"; then
        # Replace existing section: everything from MARKER to end of file
        # (auto-generated section is always at the end)
        local line_num
        line_num=$(grep -n "^$MARKER" "$memory_file" | head -1 | cut -d: -f1)

        # Keep everything before the marker
        head -n $((line_num - 1)) "$memory_file" > "${memory_file}.tmp"

        # Remove trailing blank lines
        sed -e :a -e '/^\n*$/{$d;N;ba' -e '}' "${memory_file}.tmp" > "${memory_file}.tmp2"
        mv "${memory_file}.tmp2" "${memory_file}.tmp"

        # Append separator and new enrichment
        echo "" >> "${memory_file}.tmp"
        echo "---" >> "${memory_file}.tmp"
        echo "" >> "${memory_file}.tmp"
        echo "$enrichment" >> "${memory_file}.tmp"

        mv "${memory_file}.tmp" "$memory_file"
    else
        # Append new section at end
        echo "" >> "$memory_file"
        echo "---" >> "$memory_file"
        echo "" >> "$memory_file"
        echo "$enrichment" >> "$memory_file"
    fi

    # Enforce line limit
    local line_count
    line_count=$(wc -l < "$memory_file" | tr -d ' ')

    if [[ $line_count -gt $MAX_LINES ]]; then
        # Trim: remove lines from auto-generated section (keep header + first entries)
        local marker_line
        marker_line=$(grep -n "^$MARKER" "$memory_file" | head -1 | cut -d: -f1)
        local available=$((MAX_LINES - marker_line + 1))

        if [[ $available -lt 5 ]]; then
            # Not enough room for enrichment - remove it entirely
            head -n $((marker_line - 1)) "$memory_file" > "${memory_file}.tmp"
            mv "${memory_file}.tmp" "$memory_file"
            echo "[Memory-Enrich] WARNING: MEMORY.md too long for enrichment ($line_count lines), removed auto section"
        else
            # Keep only first $available lines of enrichment
            {
                head -n $((marker_line - 1)) "$memory_file"
                tail -n +$marker_line "$memory_file" | head -n $available
            } > "${memory_file}.tmp"
            mv "${memory_file}.tmp" "$memory_file"
            echo "[Memory-Enrich] Trimmed enrichment to fit $MAX_LINES line limit"
        fi
    fi

    # Clean up backup if successful
    rm -f "${memory_file}.bak"
}

# --- Main ---
main() {
    # Check prerequisites
    command -v jq >/dev/null 2>&1 || { echo "[Memory-Enrich] jq not found, skipping"; exit 0; }

    local memory_file
    memory_file=$(get_project_memory_file)

    [[ -f "$memory_file" ]] || { exit 0; }  # No project memory, nothing to enrich

    # Check cooldown
    if ! check_cooldown "$memory_file"; then
        exit 0  # Within cooldown, skip
    fi

    # Generate enrichment content
    local enrichment
    if enrichment=$(generate_enrichment); then
        merge_into_memory "$memory_file" "$enrichment"
        echo "[Memory-Enrich] Enriched project memory with CTM context + lessons"
    fi
}

main "$@"
