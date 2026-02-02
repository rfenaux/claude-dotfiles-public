#!/bin/bash
# inbox-init.sh - Initialize inbox structure in a project or globally
# Usage: inbox-init.sh [--global]

set -euo pipefail

TEMPLATE_PATH="$HOME/.claude/templates/INBOX_RULES_TEMPLATE.md"
GLOBAL_INBOX="$HOME/.claude/inbox"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}═══ $1 ═══${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}→${NC} $1"
}

# Check if --global flag is passed
if [[ "${1:-}" == "--global" ]]; then
    INBOX_PATH="$GLOBAL_INBOX"
    RULES_FILE="$INBOX_PATH/INBOX_RULES.md"
    IS_GLOBAL=true
else
    INBOX_PATH="$(pwd)/00-inbox"
    RULES_FILE="$INBOX_PATH/INBOX_RULES.md"
    IS_GLOBAL=false
fi

# Check if inbox already exists
if [[ -d "$INBOX_PATH" ]]; then
    echo "Inbox already exists at: $INBOX_PATH"
    echo "Use '/inbox' to process files."
    exit 0
fi

# Create inbox directory
print_header "Initializing Inbox"

mkdir -p "$INBOX_PATH"
print_success "Created: $INBOX_PATH"

# Copy rules template
if [[ -f "$TEMPLATE_PATH" ]]; then
    cp "$TEMPLATE_PATH" "$RULES_FILE"
    print_success "Created: INBOX_RULES.md (from template)"
else
    # Create minimal rules file if template missing
    cat > "$RULES_FILE" << 'EOF'
# Inbox Rules Configuration

## Configuration

```yaml
auto_move: true
confidence_threshold: 0.9
logging: true
```

## Rules

See ~/.claude/templates/INBOX_RULES_TEMPLATE.md for full documentation.

## Fallback

```yaml
fallback:
  destination: 06-staging/to-review/
  action: move_to_staging
```
EOF
    print_success "Created: INBOX_RULES.md (minimal)"
    print_info "Note: Full template not found at $TEMPLATE_PATH"
fi

# Create log file
echo '{"version":"1.0","entries":[]}' > "$INBOX_PATH/.inbox_log.json"
print_success "Created: .inbox_log.json"

# Create .gitignore for inbox (optional staging files)
cat > "$INBOX_PATH/.gitignore" << 'EOF'
# Temporary files in inbox
*.tmp
*.bak
.DS_Store

# Log file (local only)
.inbox_log.json
EOF
print_success "Created: .gitignore"

# Global-specific setup
if [[ "$IS_GLOBAL" == true ]]; then
    # Create global-specific rules
    cat > "$RULES_FILE" << 'EOF'
# Global Inbox Rules (Claude Configuration)

> Drop Claude config files here for automatic routing.

## Configuration

```yaml
auto_move: true
confidence_threshold: 0.9
logging: true
```

## Rules

### Pattern Rules

```yaml
patterns:
  # Agents
  - pattern: "*-agent.md"
    destination: ~/.claude/agents/
    action: auto_move
    confidence: 0.95

  - pattern: "*_agent.md"
    destination: ~/.claude/agents/
    action: auto_move
    confidence: 0.95

  # PRDs
  - pattern: "PRD-*.md"
    destination: ~/.claude/prds/
    action: auto_move
    confidence: 0.95

  # Templates
  - pattern: "*_TEMPLATE.md"
    destination: ~/.claude/templates/
    action: auto_move
    confidence: 0.95

  # Guides
  - pattern: "*_GUIDE.md"
    destination: ~/.claude/docs/
    action: auto_move
    confidence: 0.90

  - pattern: "*_REFERENCE.md"
    destination: ~/.claude/docs/
    action: auto_move
    confidence: 0.90
```

### Extension Rules

```yaml
extensions:
  # Shell scripts (likely hooks or utilities)
  - extensions: [.sh]
    destination: ~/.claude/scripts/
    action: suggest
    confidence: 0.70
```

## Fallback

```yaml
fallback:
  destination: ~/.claude/inbox/uncategorized/
  action: move_to_staging
```
EOF
    print_success "Updated rules for global inbox"

    # Create uncategorized fallback folder
    mkdir -p "$INBOX_PATH/uncategorized"
    print_success "Created: uncategorized/ (fallback folder)"
fi

# Summary
echo ""
print_header "Inbox Ready"
echo ""
echo "Location: $INBOX_PATH"
echo ""
echo "Next steps:"
echo "  1. Drop files into $INBOX_PATH"
echo "  2. Run /inbox to process them"
echo "  3. Edit INBOX_RULES.md to customize routing"
echo ""

if [[ "$IS_GLOBAL" == true ]]; then
    echo "Global routing destinations:"
    echo "  • *-agent.md → ~/.claude/agents/"
    echo "  • PRD-*.md → ~/.claude/prds/"
    echo "  • *_TEMPLATE.md → ~/.claude/templates/"
    echo "  • *_GUIDE.md → ~/.claude/docs/"
fi
