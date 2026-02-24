#!/bin/bash
# assumption-validator.sh — PostToolUse hook for Write|Edit
# Scans written content for unmarked assumptions
# Output: Warning text if violations found, empty if clean

# Only process Write and Edit
TOOL="$TOOL_NAME"
if [[ "$TOOL" != "Write" && "$TOOL" != "Edit" ]]; then
    exit 0
fi

# Extract file path from tool input
FILE_PATH=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('file_path',''))" 2>/dev/null)

# Guard: exit if extraction failed
if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Skip non-text files and config files
case "$FILE_PATH" in
    *.json|*.py|*.sh|*.js|*.ts|*.css|*.html|*.yml|*.yaml)
        exit 0  # Skip code/config files
        ;;
    *.md|*.txt|*.rst|*.adoc)
        # Process documentation files
        ;;
    *)
        exit 0  # Skip unknown types
        ;;
esac

# Skip if file is in hooks/scripts/config (internal infra)
case "$FILE_PATH" in
    */.claude/hooks/*|*/.claude/scripts/*|*/.claude/config/*|*/.claude/settings.json)
        exit 0
        ;;
esac

# Run assumption detector on the file
DETECTOR="${HOME}/.claude/scripts/assumption-detector.py"
if [[ ! -f "$DETECTOR" ]]; then
    exit 0
fi

# Guard: check if file exists and is readable
if [[ ! -f "$FILE_PATH" || ! -r "$FILE_PATH" ]]; then
    exit 0
fi

# Run detector, suppress stderr, timeout after 1 second
RESULT=$(timeout 1s python3 "$DETECTOR" "$FILE_PATH" 2>/dev/null)
EXIT_CODE=$?

# Guard: exit if detector failed or timed out
if [[ $EXIT_CODE -ne 0 ]]; then
    exit 0
fi

# Extract violation count safely
VIOLATIONS=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('total_violations', 0))
except:
    print(0)
" 2>/dev/null)

# Guard: handle extraction failure
if [[ -z "$VIOLATIONS" ]]; then
    VIOLATIONS=0
fi

# Only output if violations found
if [[ "$VIOLATIONS" -gt 0 ]]; then
    # Extract summary of up to 5 violations
    SUMMARY=$(echo "$RESULT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    violations = data.get('violations', [])[:5]
    for v in violations:
        line = v.get('line', '?')
        indicator = v.get('indicator', '?')
        marker = v.get('suggested_marker', '[ASSUMED:]')
        print(f'  Line {line}: \"{indicator}\" → {marker}')
except:
    pass
" 2>/dev/null)

    # Output warning (injected into Claude's context)
    echo "[CONFIDENCE CHECK] $VIOLATIONS unmarked assumption(s) detected in $FILE_PATH:"
    if [[ -n "$SUMMARY" ]]; then
        echo "$SUMMARY"
    fi
    echo "Consider adding [ASSUMED:], [OPEN:], or [MISSING:] markers."
fi

exit 0
