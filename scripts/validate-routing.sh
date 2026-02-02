#!/bin/bash
# validate-routing.sh - Check CLAUDE.md routing references are valid
# Run: ~/.claude/scripts/validate-routing.sh
# Or add to validate-setup.sh for comprehensive checks

set -euo pipefail

CLAUDE_MD="$HOME/.claude/CLAUDE.md"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0
checked=0

echo "=== CLAUDE.md Routing Reference Validator ==="
echo ""

# Check CLAUDE.md exists
if [[ ! -f "$CLAUDE_MD" ]]; then
    echo -e "${RED}ERROR: CLAUDE.md not found at $CLAUDE_MD${NC}"
    exit 1
fi

# Extract all file references (patterns: `~/.claude/...` or `~/.claude/...`)
echo "Checking file references..."
echo ""

# Find all ~/.claude/*.md references
while IFS= read -r line; do
    # Extract file path from the line
    file_ref=$(echo "$line" | grep -oE '~/.claude/[^`\)\ ]+\.md' | head -1)

    if [[ -n "$file_ref" ]]; then
        # Expand ~ to $HOME
        full_path="${file_ref/#\~/$HOME}"
        ((checked++))

        if [[ -f "$full_path" ]]; then
            # Check if line contains a section reference like → "Section Name"
            if echo "$line" | grep -qE '→.*"[^"]+"'; then
                section=$(echo "$line" | grep -oE '→.*"[^"]+"' | sed 's/→.*"\([^"]*\)"/\1/')
                # Check if section exists in file
                if grep -q "## $section\|### $section\|# $section" "$full_path" 2>/dev/null; then
                    echo -e "${GREEN}✓${NC} $file_ref → \"$section\""
                else
                    echo -e "${YELLOW}⚠${NC} $file_ref exists but section \"$section\" not found"
                    ((warnings++))
                fi
            else
                echo -e "${GREEN}✓${NC} $file_ref"
            fi
        else
            echo -e "${RED}✗${NC} $file_ref - FILE NOT FOUND"
            ((errors++))
        fi
    fi
done < <(grep -E '~/.claude/[^`]*\.md' "$CLAUDE_MD" | sort -u)

echo ""

# Check project-relative references
echo "Checking project-relative references..."
while IFS= read -r ref; do
    if [[ -n "$ref" ]]; then
        ((checked++))
        # These are template references, just validate format
        echo -e "${GREEN}✓${NC} $ref (template reference)"
    fi
done < <(grep -oE 'project/[^`\)\ ]+' "$CLAUDE_MD" | sort -u | head -10)

echo ""

# Summary
echo "=== Summary ==="
echo "References checked: $checked"
echo -e "Valid: ${GREEN}$((checked - errors - warnings))${NC}"
if [[ $warnings -gt 0 ]]; then
    echo -e "Warnings: ${YELLOW}$warnings${NC} (section not found in file)"
fi
if [[ $errors -gt 0 ]]; then
    echo -e "Errors: ${RED}$errors${NC} (file not found)"
    echo ""
    echo -e "${RED}ACTION REQUIRED: Fix broken references in CLAUDE.md${NC}"
    exit 1
else
    echo ""
    echo -e "${GREEN}All routing references valid!${NC}"
    exit 0
fi
