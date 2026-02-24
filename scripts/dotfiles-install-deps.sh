#!/bin/bash
# dotfiles-install-deps.sh - Install all dependencies for Claude Code configuration
# Run this after cloning the dotfiles repo on a new machine

set -e

echo "=== Claude Code Dependencies Installer ==="
echo ""

# Detect OS
OS="$(uname -s)"
if [ "$OS" != "Darwin" ]; then
    echo "WARNING: This script is designed for macOS. Some commands may not work."
fi

# Track what was installed
INSTALLED=()
SKIPPED=()
FAILED=()

check_and_install() {
    local name="$1"
    local check_cmd="$2"
    local install_cmd="$3"

    echo -n "Checking $name... "
    if eval "$check_cmd" &>/dev/null; then
        echo "already installed"
        SKIPPED+=("$name")
    else
        echo "installing..."
        if eval "$install_cmd"; then
            INSTALLED+=("$name")
        else
            echo "FAILED to install $name"
            FAILED+=("$name")
        fi
    fi
}

# 1. Homebrew
echo ""
echo "--- Package Manager ---"
check_and_install "Homebrew" \
    "command -v brew" \
    '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'

# 2. Ollama (for RAG embeddings)
echo ""
echo "--- RAG Dependencies ---"
check_and_install "Ollama" \
    "command -v ollama" \
    "brew install ollama"

# Pull embedding model if Ollama is installed
if command -v ollama &>/dev/null; then
    echo -n "Checking mxbai-embed-large model... "
    if ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
        echo "already pulled"
        SKIPPED+=("mxbai-embed-large model")
    else
        echo "pulling..."
        if ollama pull mxbai-embed-large; then
            INSTALLED+=("mxbai-embed-large model")
        else
            FAILED+=("mxbai-embed-large model")
        fi
    fi
fi

# 3. Python packages
echo ""
echo "--- Python Dependencies ---"

# Check if pip is available
if command -v pip3 &>/dev/null; then
    PIP="pip3"
elif command -v pip &>/dev/null; then
    PIP="pip"
else
    echo "WARNING: pip not found. Skipping Python packages."
    FAILED+=("Python packages (pip not found)")
    PIP=""
fi

if [ -n "$PIP" ]; then
    PYTHON_PACKAGES="python-pptx python-docx pandas openpyxl lancedb"

    # Use --user flag to avoid PEP 668 externally-managed-environment errors
    # Also use --break-system-packages as fallback for Homebrew Python
    PIP_FLAGS="--user --quiet"

    # Test if --user works, otherwise try --break-system-packages
    if ! $PIP install --user --dry-run pip &>/dev/null 2>&1; then
        PIP_FLAGS="--break-system-packages --quiet"
    fi

    for pkg in $PYTHON_PACKAGES; do
        check_and_install "Python: $pkg" \
            "$PIP show $pkg" \
            "$PIP install $pkg $PIP_FLAGS"
    done
fi

# 4. Bun (for rag-dashboard and some scripts)
echo ""
echo "--- JavaScript Runtime ---"
check_and_install "Bun" \
    "command -v bun" \
    "curl -fsSL https://bun.sh/install | bash"

# 5. uv (for MCP servers)
echo ""
echo "--- Python Project Manager ---"
check_and_install "uv" \
    "command -v uv" \
    "brew install uv"

# 6. MCP Server virtual environments
if command -v uv &>/dev/null; then
    echo ""
    echo "--- MCP Servers ---"

    # RAG server
    if [ -d "$HOME/.claude/mcp-servers/rag-server" ]; then
        echo -n "Setting up rag-server venv... "
        if [ -d "$HOME/.claude/mcp-servers/rag-server/.venv" ]; then
            echo "already exists"
            SKIPPED+=("rag-server venv")
        else
            if (cd "$HOME/.claude/mcp-servers/rag-server" && uv sync 2>/dev/null); then
                echo "done"
                INSTALLED+=("rag-server venv")
            else
                echo "FAILED"
                FAILED+=("rag-server venv")
            fi
        fi
    fi

    # Fathom server
    if [ -d "$HOME/.claude/mcp-servers/fathom" ] && [ -f "$HOME/.claude/mcp-servers/fathom/pyproject.toml" ]; then
        echo -n "Setting up fathom server venv... "
        if [ -d "$HOME/.claude/mcp-servers/fathom/.venv" ]; then
            echo "already exists"
            SKIPPED+=("fathom venv")
        else
            if (cd "$HOME/.claude/mcp-servers/fathom" && uv sync 2>/dev/null); then
                echo "done"
                INSTALLED+=("fathom venv")
            else
                echo "FAILED"
                FAILED+=("fathom venv")
            fi
        fi
    fi
fi

# 7. Node modules for rag-dashboard
if [ -d "$HOME/.claude/rag-dashboard" ] && command -v bun &>/dev/null; then
    echo ""
    echo "--- RAG Dashboard ---"
    echo -n "Installing rag-dashboard dependencies... "
    if (cd "$HOME/.claude/rag-dashboard" && bun install --silent 2>/dev/null); then
        echo "done"
        INSTALLED+=("rag-dashboard node_modules")
    else
        echo "skipped (may already exist)"
        SKIPPED+=("rag-dashboard node_modules")
    fi
fi

# Summary
echo ""
echo "=== Installation Summary ==="
echo ""

if [ ${#INSTALLED[@]} -gt 0 ]; then
    echo "Installed (${#INSTALLED[@]}):"
    for item in "${INSTALLED[@]}"; do
        echo "  ✓ $item"
    done
    echo ""
fi

if [ ${#SKIPPED[@]} -gt 0 ]; then
    echo "Already present (${#SKIPPED[@]}):"
    for item in "${SKIPPED[@]}"; do
        echo "  • $item"
    done
    echo ""
fi

if [ ${#FAILED[@]} -gt 0 ]; then
    echo "Failed (${#FAILED[@]}):"
    for item in "${FAILED[@]}"; do
        echo "  ✗ $item"
    done
    echo ""
    echo "Some dependencies failed to install. Please install them manually."
    exit 1
fi

echo "All dependencies ready!"
echo ""
echo "Next steps:"
echo "  1. Run: ~/.claude/scripts/validate-setup.sh --quick"
echo "  2. Start Claude Code in any project directory"
