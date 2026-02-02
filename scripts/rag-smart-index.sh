#!/bin/bash
# RAG Smart Index
# Wrapper for rag_index that excludes common junk and provides summaries
# Run: ~/.claude/scripts/rag-smart-index.sh /path/to/project
# Run: ~/.claude/scripts/rag-smart-index.sh /path/to/project --dry-run

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Default exclusions (common junk patterns)
EXCLUDE_DIRS=(
    "node_modules"
    ".git"
    ".svn"
    ".hg"
    "__pycache__"
    ".pytest_cache"
    ".mypy_cache"
    ".ruff_cache"
    "venv"
    ".venv"
    "env"
    ".env"
    "build"
    "dist"
    "target"
    ".next"
    ".nuxt"
    ".output"
    "coverage"
    ".coverage"
    ".nyc_output"
    ".turbo"
    ".cache"
    ".parcel-cache"
    ".webpack"
    ".rag"
    ".claude"
    "vendor"
    "Pods"
    ".gradle"
    ".idea"
    ".vscode"
    "*.egg-info"
    ".tox"
    ".nox"
)

EXCLUDE_FILES=(
    "*.pyc"
    "*.pyo"
    "*.so"
    "*.dylib"
    "*.dll"
    "*.exe"
    "*.o"
    "*.a"
    "*.class"
    "*.jar"
    "*.war"
    "*.lock"
    "package-lock.json"
    "yarn.lock"
    "pnpm-lock.yaml"
    "Cargo.lock"
    "poetry.lock"
    "*.min.js"
    "*.min.css"
    "*.map"
    "*.chunk.js"
    "*.bundle.js"
    ".DS_Store"
    "Thumbs.db"
    "*.log"
    "*.bak"
    "*.swp"
    "*.swo"
)

INCLUDE_EXTENSIONS=(
    "md"
    "txt"
    "pdf"
    "docx"
    "doc"
    "html"
    "htm"
    "json"
    "yaml"
    "yml"
    "toml"
    "xml"
    "csv"
    "py"
    "js"
    "ts"
    "tsx"
    "jsx"
    "go"
    "rs"
    "java"
    "kt"
    "swift"
    "rb"
    "php"
    "sh"
    "bash"
    "zsh"
    "sql"
    "graphql"
    "proto"
    "tf"
    "hcl"
)

# Functions
print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_section() {
    echo ""
    echo -e "${BOLD}▶ $1${NC}"
}

info() {
    echo -e "  ${CYAN}ℹ${NC} $1"
}

success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

warn() {
    echo -e "  ${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "  ${RED}✗${NC} $1"
}

usage() {
    echo "Usage: rag-smart-index.sh <path> [options]"
    echo ""
    echo "Options:"
    echo "  --dry-run     Show what would be indexed without indexing"
    echo "  --verbose     Show all files being processed"
    echo "  --include-code  Include source code files (default: docs only)"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  rag-smart-index.sh ./docs"
    echo "  rag-smart-index.sh /project --dry-run"
    echo "  rag-smart-index.sh . --include-code --verbose"
}

# Parse arguments
TARGET_PATH=""
DRY_RUN=false
VERBOSE=false
INCLUDE_CODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --include-code)
            INCLUDE_CODE=true
            shift
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            usage
            exit 1
            ;;
        *)
            TARGET_PATH="$1"
            shift
            ;;
    esac
done

# Validate input
if [ -z "$TARGET_PATH" ]; then
    error "No path provided"
    usage
    exit 1
fi

if [ ! -e "$TARGET_PATH" ]; then
    error "Path does not exist: $TARGET_PATH"
    exit 1
fi

# Resolve to absolute path
TARGET_PATH=$(cd "$(dirname "$TARGET_PATH")" && pwd)/$(basename "$TARGET_PATH")

# Build find exclusions
build_find_excludes() {
    local excludes=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        excludes="$excludes -path '*/$dir' -prune -o -path '*/$dir/*' -prune -o"
    done
    echo "$excludes"
}

# Build file extension filter
build_extension_filter() {
    local filter=""
    local extensions=("md" "txt" "pdf" "docx" "html" "htm" "json" "yaml" "yml" "xml")

    if [ "$INCLUDE_CODE" = true ]; then
        extensions+=("py" "js" "ts" "tsx" "jsx" "go" "rs" "java" "rb" "sh" "sql")
    fi

    for i in "${!extensions[@]}"; do
        if [ $i -eq 0 ]; then
            filter="-name '*.${extensions[$i]}'"
        else
            filter="$filter -o -name '*.${extensions[$i]}'"
        fi
    done
    echo "$filter"
}

# Main
print_header "RAG Smart Index"

print_section "Configuration"
info "Target path: ${BOLD}$TARGET_PATH${NC}"
info "Dry run: $DRY_RUN"
info "Include code: $INCLUDE_CODE"

print_section "Scanning files..."

# Build the find command
FIND_CMD="find '$TARGET_PATH' -type d \\( -name 'node_modules' -o -name '.git' -o -name '__pycache__' -o -name 'venv' -o -name '.venv' -o -name 'build' -o -name 'dist' -o -name '.next' -o -name 'coverage' -o -name '.rag' -o -name '.claude' -o -name 'vendor' -o -name '.cache' \\) -prune -o -type f \\( -name '*.md' -o -name '*.txt' -o -name '*.pdf' -o -name '*.docx' -o -name '*.html' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml'"

if [ "$INCLUDE_CODE" = true ]; then
    FIND_CMD="$FIND_CMD -o -name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.tsx' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.rb' -o -name '*.sh' -o -name '*.sql'"
fi

FIND_CMD="$FIND_CMD \\) -print"

# Execute find and collect files
FILES=$(eval $FIND_CMD 2>/dev/null | grep -v -E '(node_modules|__pycache__|\.git|\.rag|\.min\.|\.lock$|\.map$)' || true)

# Count and categorize (handle empty FILES gracefully)
if [ -z "$FILES" ]; then
    TOTAL_FILES=0
    MD_COUNT=0
    PDF_COUNT=0
    DOCX_COUNT=0
    CODE_COUNT=0
    OTHER_COUNT=0
else
    TOTAL_FILES=$(echo "$FILES" | wc -l | tr -d ' ')
    MD_COUNT=$(echo "$FILES" | grep '\.md$' | wc -l | tr -d ' ')
    PDF_COUNT=$(echo "$FILES" | grep '\.pdf$' | wc -l | tr -d ' ')
    DOCX_COUNT=$(echo "$FILES" | grep '\.docx$' | wc -l | tr -d ' ')
    CODE_COUNT=0

    if [ "$INCLUDE_CODE" = true ]; then
        CODE_COUNT=$(echo "$FILES" | grep -E '\.(py|js|ts|tsx|go|rs|java|rb|sh|sql)$' | wc -l | tr -d ' ')
    fi

    OTHER_COUNT=$((TOTAL_FILES - MD_COUNT - PDF_COUNT - DOCX_COUNT - CODE_COUNT))
fi

print_section "File Summary"
echo ""
echo -e "  ${BOLD}Documents to index:${NC}"
echo -e "    Markdown (.md):    ${GREEN}$MD_COUNT${NC}"
echo -e "    PDF (.pdf):        ${GREEN}$PDF_COUNT${NC}"
echo -e "    Word (.docx):      ${GREEN}$DOCX_COUNT${NC}"
if [ "$INCLUDE_CODE" = true ]; then
echo -e "    Code files:        ${GREEN}$CODE_COUNT${NC}"
fi
echo -e "    Other:             ${GREEN}$OTHER_COUNT${NC}"
echo -e "    ${BOLD}────────────────────${NC}"
echo -e "    ${BOLD}Total:             ${CYAN}$TOTAL_FILES${NC}"

if [ "$VERBOSE" = true ] && [ "$TOTAL_FILES" -gt 0 ]; then
    print_section "Files to index"
    echo "$FILES" | head -50
    if [ "$TOTAL_FILES" -gt 50 ]; then
        echo -e "  ${DIM}... and $((TOTAL_FILES - 50)) more${NC}"
    fi
fi

print_section "Exclusions applied"
info "Directories: node_modules, .git, __pycache__, venv, build, dist, .next, .rag, .claude, vendor, coverage"
info "Files: *.min.*, *.lock, *.map, *.pyc, *.log"

if [ "$TOTAL_FILES" -eq 0 ] || [ -z "$TOTAL_FILES" ]; then
    echo ""
    warn "No indexable files found in $TARGET_PATH"
    echo -e "  ${DIM}Try --include-code to include source files${NC}"
    exit 0
fi

# Dry run stops here
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo -e "${YELLOW}DRY RUN${NC} - No files were indexed"
    echo -e "Run without --dry-run to index these $TOTAL_FILES files"
    exit 0
fi

# Find project root (look for .rag directory)
find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.rag" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    # No .rag found, use target path's parent or target itself
    if [ -d "$TARGET_PATH" ]; then
        echo "$TARGET_PATH"
    else
        dirname "$TARGET_PATH"
    fi
}

PROJECT_ROOT=$(find_project_root "$TARGET_PATH")

print_section "Indexing..."
info "Project root: $PROJECT_ROOT"

# Check if RAG is initialized
if [ ! -d "$PROJECT_ROOT/.rag" ]; then
    warn "RAG not initialized in $PROJECT_ROOT"
    info "Initialize with: rag init (in Claude Code)"
    exit 1
fi

# Index using the RAG MCP server (via claude command or direct)
# We'll output the files to a temp list and let the user know to index via Claude
TEMP_FILE=$(mktemp)
echo "$FILES" > "$TEMP_FILE"

echo ""
info "Found $TOTAL_FILES files ready to index"
info "File list saved to: $TEMP_FILE"
echo ""
echo -e "${BOLD}To complete indexing, run in Claude Code:${NC}"
echo ""
echo -e "  ${CYAN}rag index $TARGET_PATH${NC}"
echo ""
echo -e "Or index specific files:"
while IFS= read -r file; do
    echo -e "  ${DIM}rag index \"$file\"${NC}"
done < <(echo "$FILES" | head -5)

if [ "$TOTAL_FILES" -gt 5 ]; then
    echo -e "  ${DIM}... ($((TOTAL_FILES - 5)) more files)${NC}"
fi

echo ""
success "Scan complete. Ready to index $TOTAL_FILES files."
