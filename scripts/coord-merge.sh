#!/usr/bin/env bash
# coord-merge.sh - Three-way merge for conflict resolution
# Part of Multi-Session Coordination System (Phase 3)
#
# Usage:
#   coord-merge.sh <base_file> <ours_file> <theirs_file> [--output <file>]
#   coord-merge.sh --detect <file1> <file2>
#
# Modes:
#   Default:    Attempt three-way merge
#   --detect:   Analyze if two changes can be auto-merged
#
# Options:
#   --output <file>   Write merged result to file (default: stdout)
#   --markers         Include conflict markers for overlapping changes
#   --ours-label      Label for "ours" side (default: OURS)
#   --theirs-label    Label for "theirs" side (default: THEIRS)
#   --json            Output analysis as JSON
#
# Exit codes:
#   0 - Merge successful (or clean --detect)
#   1 - Merge conflict (overlapping changes)
#   2 - File not found
#   3 - Invalid arguments

set -euo pipefail

# ─────────────────────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────────────────────

DETECT_MODE=false
OUTPUT_FILE=""
USE_MARKERS=false
OURS_LABEL="OURS"
THEIRS_LABEL="THEIRS"
JSON_OUTPUT=false

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --detect)
      DETECT_MODE=true
      shift
      ;;
    --output)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --markers)
      USE_MARKERS=true
      shift
      ;;
    --ours-label)
      OURS_LABEL="$2"
      shift 2
      ;;
    --theirs-label)
      THEIRS_LABEL="$2"
      shift 2
      ;;
    --json)
      JSON_OUTPUT=true
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 3
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL[@]}"

# ─────────────────────────────────────────────────────────────────────────────
# Detect mode: analyze if changes can be auto-merged
# ─────────────────────────────────────────────────────────────────────────────

if [[ "$DETECT_MODE" == true ]]; then
  if [[ $# -lt 2 ]]; then
    echo "Usage: coord-merge.sh --detect <file1> <file2>" >&2
    exit 3
  fi

  FILE1="$1"
  FILE2="$2"

  for f in "$FILE1" "$FILE2"; do
    if [[ ! -f "$f" ]]; then
      echo "Error: File not found: $f" >&2
      exit 2
    fi
  done

  # Use diff to find changed regions
  # We consider changes mergeable if they don't overlap

  # Get line counts
  LINES1=$(wc -l < "$FILE1" | tr -d ' ')
  LINES2=$(wc -l < "$FILE2" | tr -d ' ')

  # Generate diff
  DIFF_OUTPUT=$(diff "$FILE1" "$FILE2" 2>/dev/null || true)

  if [[ -z "$DIFF_OUTPUT" ]]; then
    # Files are identical
    if [[ "$JSON_OUTPUT" == true ]]; then
      jq -nc '{
        can_merge: true,
        reason: "files_identical",
        changes: 0
      }'
    else
      echo "Files are identical - no merge needed"
    fi
    exit 0
  fi

  # Count changes and check for complexity
  CHANGE_COUNT=$(echo "$DIFF_OUTPUT" | grep -c '^[0-9]' || echo 0)

  # Simple heuristic: if changes are non-overlapping, they can be merged
  # For now, we report the analysis and let the caller decide

  if [[ "$JSON_OUTPUT" == true ]]; then
    jq -nc \
      --argjson changes "$CHANGE_COUNT" \
      --argjson lines1 "$LINES1" \
      --argjson lines2 "$LINES2" \
      '{
        can_merge: ($changes < 5),
        reason: (if $changes < 5 then "few_changes" else "many_changes"),
        change_count: $changes,
        file1_lines: $lines1,
        file2_lines: $lines2,
        recommendation: (if $changes < 5 then "auto_merge_likely" else "manual_review_recommended")
      }'
  else
    echo "Change analysis:"
    echo "  File 1: $LINES1 lines"
    echo "  File 2: $LINES2 lines"
    echo "  Changes: $CHANGE_COUNT regions"

    if [[ $CHANGE_COUNT -lt 5 ]]; then
      echo "  Status: Auto-merge likely possible"
    else
      echo "  Status: Manual review recommended"
    fi
  fi

  exit 0
fi

# ─────────────────────────────────────────────────────────────────────────────
# Three-way merge mode
# ─────────────────────────────────────────────────────────────────────────────

if [[ $# -lt 3 ]]; then
  echo "Usage: coord-merge.sh <base_file> <ours_file> <theirs_file> [--output <file>]" >&2
  exit 3
fi

BASE_FILE="$1"
OURS_FILE="$2"
THEIRS_FILE="$3"

for f in "$BASE_FILE" "$OURS_FILE" "$THEIRS_FILE"; do
  if [[ ! -f "$f" ]]; then
    echo "Error: File not found: $f" >&2
    exit 2
  fi
done

# ─────────────────────────────────────────────────────────────────────────────
# Perform merge using git merge-file
# ─────────────────────────────────────────────────────────────────────────────

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

# Copy files to temp (git merge-file modifies in place)
cp "$OURS_FILE" "$TEMP_DIR/ours"
cp "$BASE_FILE" "$TEMP_DIR/base"
cp "$THEIRS_FILE" "$TEMP_DIR/theirs"

MERGE_RESULT="$TEMP_DIR/merged"

# Perform merge
# git merge-file exits:
#   0 - clean merge
#   >0 - number of conflicts
CONFLICT_COUNT=0

if [[ "$USE_MARKERS" == true ]]; then
  # Keep conflict markers
  git merge-file -p \
    -L "$OURS_LABEL" \
    -L "BASE" \
    -L "$THEIRS_LABEL" \
    "$TEMP_DIR/ours" "$TEMP_DIR/base" "$TEMP_DIR/theirs" > "$MERGE_RESULT" 2>/dev/null || CONFLICT_COUNT=$?
else
  # Try clean merge, fail on conflict
  if ! git merge-file -p \
    "$TEMP_DIR/ours" "$TEMP_DIR/base" "$TEMP_DIR/theirs" > "$MERGE_RESULT" 2>/dev/null; then
    CONFLICT_COUNT=$?
  fi
fi

# ─────────────────────────────────────────────────────────────────────────────
# Handle result
# ─────────────────────────────────────────────────────────────────────────────

if [[ $CONFLICT_COUNT -eq 0 ]]; then
  # Clean merge
  if [[ -n "$OUTPUT_FILE" ]]; then
    cp "$MERGE_RESULT" "$OUTPUT_FILE"

    if [[ "$JSON_OUTPUT" == true ]]; then
      jq -nc \
        --arg output "$OUTPUT_FILE" \
        '{status: "merged", conflicts: 0, output_file: $output}'
    else
      echo "Merged successfully to: $OUTPUT_FILE"
    fi
  else
    if [[ "$JSON_OUTPUT" == true ]]; then
      CONTENT=$(cat "$MERGE_RESULT" | jq -Rs .)
      jq -nc \
        --argjson content "$CONTENT" \
        '{status: "merged", conflicts: 0, content: $content}'
    else
      cat "$MERGE_RESULT"
    fi
  fi
  exit 0
else
  # Conflicts detected
  if [[ "$USE_MARKERS" == true ]]; then
    # Output with conflict markers
    if [[ -n "$OUTPUT_FILE" ]]; then
      cp "$MERGE_RESULT" "$OUTPUT_FILE"

      if [[ "$JSON_OUTPUT" == true ]]; then
        jq -nc \
          --argjson conflicts "$CONFLICT_COUNT" \
          --arg output "$OUTPUT_FILE" \
          '{status: "conflict_markers", conflicts: $conflicts, output_file: $output, message: "File contains conflict markers for manual resolution"}'
      else
        echo "Merge conflicts: $CONFLICT_COUNT"
        echo "Written with conflict markers to: $OUTPUT_FILE"
        echo "Edit the file to resolve conflicts manually"
      fi
    else
      if [[ "$JSON_OUTPUT" == true ]]; then
        CONTENT=$(cat "$MERGE_RESULT" | jq -Rs .)
        jq -nc \
          --argjson conflicts "$CONFLICT_COUNT" \
          --argjson content "$CONTENT" \
          '{status: "conflict_markers", conflicts: $conflicts, content: $content}'
      else
        cat "$MERGE_RESULT"
      fi
    fi
    exit 1
  else
    # No markers, just report conflict
    if [[ "$JSON_OUTPUT" == true ]]; then
      jq -nc \
        --argjson conflicts "$CONFLICT_COUNT" \
        '{status: "conflict", conflicts: $conflicts, message: "Files have overlapping changes that cannot be auto-merged"}'
    else
      echo "Error: Merge conflict detected ($CONFLICT_COUNT overlapping regions)" >&2
      echo "Use --markers to output with conflict markers for manual resolution" >&2
    fi
    exit 1
  fi
fi
