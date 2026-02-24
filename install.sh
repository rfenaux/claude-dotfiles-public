#!/usr/bin/env bash
# install.sh - Interactive installer for claude-dotfiles-public
# Usage: bash install.sh [--yes] [--prefix PATH] [--no-deps] [--help]
#
# Flags:
#   --yes          Accept all defaults (non-interactive). Skips optional prompts.
#   --prefix PATH  Install to PATH instead of ~/.claude
#   --no-deps      Skip running dotfiles-install-deps.sh
#   --help         Show this help

set -uo pipefail

# ─────────────────────────────────────────────────────────────
# Color helpers (with NO_COLOR / dumb terminal fallback)
# ─────────────────────────────────────────────────────────────
if [ -t 1 ] && [ "${NO_COLOR:-}" = "" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; NC=''
fi

info()    { echo -e "  ${BLUE}i${NC} $*"; }
success() { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}!${NC} $*"; }
error()   { echo -e "  ${RED}✗${NC} $*" >&2; }
fatal()   { error "$*"; exit 1; }
header()  { echo -e "\n${BOLD}${CYAN}▶ $*${NC}"; }

ask() {
  # ask "prompt" "default"  -> result in $REPLY
  local prompt="$1" default="${2:-}"
  if [ "$YES_MODE" = true ]; then
    REPLY="$default"
    return
  fi
  if [ -n "$default" ]; then
    printf "  ${BOLD}?${NC} %s [%s]: " "$prompt" "$default"
  else
    printf "  ${BOLD}?${NC} %s: " "$prompt"
  fi
  read -r REPLY
  REPLY="${REPLY:-$default}"
}

# ─────────────────────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────────────────────
YES_MODE=false
INSTALL_PREFIX="$HOME/.claude"
SKIP_DEPS=false
PREFIX_SET=false

show_help() {
  cat <<EOF
Claude Code Dotfiles Installer

Usage: bash install.sh [options]

Options:
  --yes           Non-interactive: accept all defaults, skip optional prompts
  --prefix PATH   Install location (default: ~/.claude)
  --no-deps       Skip dependency installation (dotfiles-install-deps.sh)
  --help          Show this help

Examples:
  bash install.sh                          # Interactive install to ~/.claude
  bash install.sh --yes                    # Non-interactive, all defaults
  bash install.sh --prefix ~/my-claude     # Custom install path
  bash install.sh --yes --no-deps          # Quick install, skip deps
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yes|-y)      YES_MODE=true ;;
    --prefix)      shift; INSTALL_PREFIX="${1%/}"; PREFIX_SET=true ;;
    --no-deps)     SKIP_DEPS=true ;;
    --help|-h)     show_help; exit 0 ;;
    *)             fatal "Unknown argument: $1. Run with --help for usage." ;;
  esac
  shift
done

# Resolve repo dir to absolute path (works regardless of how script is invoked)
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

# ─────────────────────────────────────────────────────────────
# Welcome banner
# ─────────────────────────────────────────────────────────────
print_banner() {
  echo ""
  echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${BLUE}║         Claude Code Dotfiles Installer                   ║${NC}"
  echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo "  This will install a production-grade Claude Code configuration:"
  echo ""
  echo "  • 144 specialized AI agents (HubSpot, APIs, diagrams, reasoning…)"
  echo "  • 56 slash command skills  (/ctm, /enhance, /pm-spec, /brand-extract…)"
  echo "  • 60+ session automation hooks"
  echo "  • CTM — cognitive task manager with multi-session memory"
  echo "  • RAG — local semantic search across your project files"
  echo "  • Self-healing infrastructure"
  echo ""
}

# ─────────────────────────────────────────────────────────────
# Prerequisites check
# ─────────────────────────────────────────────────────────────
check_prerequisites() {
  header "Checking prerequisites"
  local missing=0

  # claude CLI
  if command -v claude &>/dev/null; then
    local ver; ver=$(claude --version 2>/dev/null | head -1 || echo "installed")
    success "claude CLI — $ver"
  else
    warn "claude CLI not found"
    info "  Install: https://claude.ai/claude-code"
    info "  Or: npm install -g @anthropic-ai/claude-code"
    missing=$((missing + 1))
  fi

  # python3 3.11+
  if command -v python3 &>/dev/null; then
    local py_ver; py_ver=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0.0")
    local py_major; py_major=$(echo "$py_ver" | cut -d. -f1)
    local py_minor; py_minor=$(echo "$py_ver" | cut -d. -f2)
    if [ "$py_major" -ge 3 ] && [ "$py_minor" -ge 11 ] 2>/dev/null; then
      success "Python $py_ver"
    else
      warn "Python $py_ver found, but 3.11+ required"
      info "  Install: https://python.org  or  brew install python@3.12"
      missing=$((missing + 1))
    fi
  else
    warn "python3 not found (required for RAG and hooks)"
    info "  Install: https://python.org  or  brew install python@3.12"
    missing=$((missing + 1))
  fi

  # git
  if command -v git &>/dev/null; then
    success "git — $(git --version | awk '{print $3}')"
  else
    warn "git not found"
    info "  Install: brew install git  or  apt install git"
    missing=$((missing + 1))
  fi

  if [ $missing -gt 0 ]; then
    echo ""
    warn "$missing prerequisite(s) missing."
    ask "Continue anyway? (some features may not work)" "N"
    if [[ "${REPLY,,}" =~ ^n ]] || [ -z "$REPLY" ]; then
      fatal "Please install prerequisites and re-run install.sh"
    fi
  fi
}

# ─────────────────────────────────────────────────────────────
# Ask install path (if not set via --prefix)
# ─────────────────────────────────────────────────────────────
ask_install_path() {
  if [ "$PREFIX_SET" = true ] || [ "$YES_MODE" = true ]; then
    info "Install path: ${BOLD}$INSTALL_PREFIX${NC}"
    return
  fi

  header "Install location"
  echo "  Default: $HOME/.claude"
  echo "  (This is where Claude Code looks for configuration by default)"
  echo ""
  ask "Install path" "$HOME/.claude"
  INSTALL_PREFIX="${REPLY%/}"
}

# ─────────────────────────────────────────────────────────────
# Handle existing installation
# ─────────────────────────────────────────────────────────────
MERGE_MODE=false
handle_existing() {
  if [ ! -d "$INSTALL_PREFIX" ]; then
    return
  fi

  header "Existing installation detected"
  warn "Directory already exists: $INSTALL_PREFIX"
  echo ""

  if [ "$YES_MODE" = true ]; then
    info "Using merge mode (--yes): existing files preserved, new files added"
    MERGE_MODE=true
    return
  fi

  echo "  Options:"
  echo "  [b] Backup existing to $INSTALL_PREFIX.backup.$(date +%Y%m%d-%H%M%S)"
  echo "  [m] Merge — add new files, preserve your existing customizations"
  echo "  [a] Abort"
  echo ""
  ask "Your choice" "m"

  case "${REPLY:0:1}" in
    B|b)
      local backup="${INSTALL_PREFIX}.backup.$(date +%Y%m%d-%H%M%S)"
      info "Creating backup at $backup…"
      cp -r "$INSTALL_PREFIX" "$backup"
      success "Backup created: $backup"
      MERGE_MODE=false
      ;;
    M|m)
      info "Merge mode: existing files will be preserved"
      MERGE_MODE=true
      ;;
    *)
      fatal "Aborted."
      ;;
  esac
}

# ─────────────────────────────────────────────────────────────
# Copy files from repo to install prefix
# ─────────────────────────────────────────────────────────────
copy_files() {
  header "Copying files"
  mkdir -p "$INSTALL_PREFIX"

  local rsync_flags="-rq"
  local extra_flags=""
  if [ "$MERGE_MODE" = true ]; then
    extra_flags="--ignore-existing"
    info "Merge mode: only adding new files"
  else
    info "Full install to $INSTALL_PREFIX"
  fi

  rsync $rsync_flags $extra_flags \
    --exclude=".git" \
    --exclude="install.sh" \
    --exclude="README.md" \
    --exclude="~" \
    "$REPO_DIR/" "$INSTALL_PREFIX/"

  success "Files copied to $INSTALL_PREFIX"
}

# ─────────────────────────────────────────────────────────────
# Set executable permissions
# ─────────────────────────────────────────────────────────────
set_permissions() {
  header "Setting permissions"

  # Make all .sh and .py scripts executable
  find "$INSTALL_PREFIX/hooks" -name "*.sh" -o -name "*.py" 2>/dev/null | \
    xargs chmod +x 2>/dev/null || true
  find "$INSTALL_PREFIX/scripts" -name "*.sh" -o -name "*.py" 2>/dev/null | \
    xargs chmod +x 2>/dev/null || true
  find "$INSTALL_PREFIX/ctm/scripts" -type f 2>/dev/null | \
    xargs chmod +x 2>/dev/null || true
  find "$INSTALL_PREFIX/skills" -name "*.sh" 2>/dev/null | \
    xargs chmod +x 2>/dev/null || true

  success "Executable permissions set"
}

# ─────────────────────────────────────────────────────────────
# Bootstrap settings.json
# ─────────────────────────────────────────────────────────────
bootstrap_settings() {
  header "Settings"

  if [ -f "$INSTALL_PREFIX/settings.json" ]; then
    info "settings.json already exists — not overwritten"
    info "To reset: cp $INSTALL_PREFIX/settings.example.json $INSTALL_PREFIX/settings.json"
  elif [ -f "$INSTALL_PREFIX/settings.example.json" ]; then
    cp "$INSTALL_PREFIX/settings.example.json" "$INSTALL_PREFIX/settings.json"
    success "Created settings.json from settings.example.json"
  else
    warn "settings.example.json not found — settings.json not created"
  fi
}

# ─────────────────────────────────────────────────────────────
# Run dependency installer
# ─────────────────────────────────────────────────────────────
install_deps() {
  if [ "$SKIP_DEPS" = true ]; then
    info "Skipping dependency install (--no-deps)"
    return
  fi

  header "Installing dependencies"

  local deps_script="$INSTALL_PREFIX/scripts/dotfiles-install-deps.sh"
  if [ -x "$deps_script" ]; then
    bash "$deps_script"
  else
    warn "dotfiles-install-deps.sh not found or not executable — skipping"
    info "Run manually: $INSTALL_PREFIX/scripts/dotfiles-install-deps.sh"
  fi
}

# ─────────────────────────────────────────────────────────────
# Optional: Ollama for local RAG embeddings
# ─────────────────────────────────────────────────────────────
setup_ollama() {
  if [ "$YES_MODE" = true ]; then
    return
  fi

  header "Local AI Search (optional)"
  echo "  Ollama enables semantic search across your project files and past sessions."
  echo "  Requires ~700MB disk space. Can be set up later if you skip this step."
  echo ""
  ask "Install Ollama for local semantic search?" "Y"

  if [[ "${REPLY,,}" =~ ^y ]]; then
    if command -v ollama &>/dev/null; then
      success "Ollama already installed"
    else
      info "Installing Ollama…"
      if [[ "$(uname)" == "Darwin" ]]; then
        if command -v brew &>/dev/null; then
          brew install ollama 2>/dev/null || {
            warn "brew install failed, trying official installer"
            curl -fsSL https://ollama.ai/install.sh | sh
          }
        else
          curl -fsSL https://ollama.ai/install.sh | sh
        fi
      else
        curl -fsSL https://ollama.ai/install.sh | sh
      fi
    fi

    info "Pulling embedding model (mxbai-embed-large, ~700MB)…"
    if command -v ollama &>/dev/null; then
      if ollama pull mxbai-embed-large 2>/dev/null; then
        success "Embedding model ready"
      else
        warn "Model pull failed. Run later: ollama serve && ollama pull mxbai-embed-large"
      fi
    fi
  else
    info "Skipped. To enable later:"
    info "  brew install ollama && ollama serve"
    info "  ollama pull mxbai-embed-large"
  fi
}

# ─────────────────────────────────────────────────────────────
# Optional: API keys for multi-model delegation
# ─────────────────────────────────────────────────────────────
setup_api_keys() {
  if [ "$YES_MODE" = true ]; then
    return
  fi

  header "Optional API Keys"
  echo "  These enable the multi-model reasoning agents (Claude + Codex + Gemini)."
  echo "  Both are optional — Claude Code works without them."
  echo ""

  # Detect shell rc file
  local shell_rc="$HOME/.zshrc"
  if [[ "${SHELL:-}" == *"bash"* ]] || [ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ]; then
    shell_rc="$HOME/.bashrc"
  fi

  ask "Do you have an OpenAI API key? (sk-...)" "N"
  if [[ "${REPLY,,}" =~ ^y ]]; then
    ask "Paste your OpenAI API key" ""
    if [ -n "$REPLY" ] && [[ "$REPLY" == sk-* ]]; then
      echo "export OPENAI_API_KEY=\"$REPLY\"" >> "$shell_rc"
      success "OPENAI_API_KEY added to $shell_rc"
    else
      warn "Skipped (invalid or empty key)"
    fi
  fi

  ask "Do you have a Google API key?" "N"
  if [[ "${REPLY,,}" =~ ^y ]]; then
    ask "Paste your Google API key" ""
    if [ -n "$REPLY" ]; then
      echo "export GOOGLE_API_KEY=\"$REPLY\"" >> "$shell_rc"
      success "GOOGLE_API_KEY added to $shell_rc"
    else
      warn "Skipped (empty key)"
    fi
  fi
}

# ─────────────────────────────────────────────────────────────
# Validate installation
# ─────────────────────────────────────────────────────────────
run_validation() {
  header "Validating installation"

  local validator="$INSTALL_PREFIX/scripts/validate-setup.sh"
  if [ -x "$validator" ]; then
    "$validator" --quick || warn "Some checks flagged. Run validate-setup.sh for details."
  else
    warn "validate-setup.sh not found — skipping validation"
  fi
}

# ─────────────────────────────────────────────────────────────
# First session instructions
# ─────────────────────────────────────────────────────────────
print_next_steps() {
  echo ""
  echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${GREEN}║  Installation complete!                                  ║${NC}"
  echo -e "${BOLD}${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
  echo ""
  echo -e "${BOLD}Next steps:${NC}"
  echo ""
  echo "  1. Restart your terminal (pick up new env variables)"
  echo "  2. Navigate to a project:  cd /your/project"
  echo "  3. Start Claude Code:      claude"
  echo ""
  echo -e "${BOLD}Try these in your first session:${NC}"
  echo ""
  echo "  /ctm spawn \"my first task\"    # start tracking your work"
  echo "  /enhance                       # see prompt enhancement in action"
  echo "  /config-audit                  # check your installation health"
  echo ""
  echo -e "${BOLD}Documentation:${NC}"
  echo "  $INSTALL_PREFIX/README.md"
  echo "  $INSTALL_PREFIX/CONFIGURATION_GUIDE.md"
  echo "  $INSTALL_PREFIX/AGENTS_INDEX.md"
  echo ""
  echo -e "${BOLD}Full validation:${NC}"
  echo "  $INSTALL_PREFIX/scripts/validate-setup.sh"
  echo ""
}

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
main() {
  print_banner
  check_prerequisites
  ask_install_path
  handle_existing
  copy_files
  set_permissions
  bootstrap_settings
  install_deps
  setup_ollama
  setup_api_keys
  run_validation
  print_next_steps
}

main "$@"
