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
  BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'
  DIM='\033[2m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; DIM=''; NC=''
fi

CURRENT_STEP=0
TOTAL_STEPS=8

info()    { echo -e "  ${BLUE}i${NC} $*"; }
success() { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}!${NC} $*"; }
error()   { echo -e "  ${RED}✗${NC} $*" >&2; }
fatal()   { error "$*"; exit 1; }
# Lowercase helper (macOS ships bash 3.2 which lacks ${var,,})
lc() { echo "$1" | tr '[:upper:]' '[:lower:]'; }
divider() { echo -e "  ${DIM}────────────────────────────────────────────────${NC}"; }
step() {
  CURRENT_STEP=$((CURRENT_STEP + 1))
  echo ""
  divider
  echo -e "  ${BOLD}${CYAN}[$CURRENT_STEP/$TOTAL_STEPS]${NC} ${BOLD}$*${NC}"
  echo ""
}

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

  What is this?
  Claude Code is Anthropic's AI coding assistant for the terminal.
  This installer adds a configuration layer on top: 144 AI agents,
  persistent memory, local semantic search, and 60+ automations
  that make Claude Code dramatically more capable.

Usage: bash install.sh [options]

Options:
  --yes           Accept all defaults, skip optional prompts (non-interactive)
  --prefix PATH   Install to a custom location (default: ~/.claude)
  --no-deps       Skip installing Python/CLI dependencies
  --help          Show this help

Examples:
  bash install.sh                          # Guided interactive install
  bash install.sh --yes                    # Accept all defaults
  bash install.sh --prefix ~/my-claude     # Custom install path
  bash install.sh --yes --no-deps          # Minimal quick install
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
  echo -e "${BOLD}${BLUE}"
  echo "   ╔═══════════════════════════════════════════════════════════╗"
  echo "   ║                                                           ║"
  echo "   ║     ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗     ║"
  echo "   ║    ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝     ║"
  echo "   ║    ██║     ██║     ███████║██║   ██║██║  ██║█████╗       ║"
  echo "   ║    ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝       ║"
  echo "   ║    ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗     ║"
  echo "   ║     ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝     ║"
  echo "   ║                                                           ║"
  echo "   ║          C O D E   D O T F I L E S                       ║"
  echo "   ║                                                           ║"
  echo "   ╚═══════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
  echo -e "  ${DIM}Production-grade configuration for Claude Code${NC}"
  echo ""
  echo -e "  ${GREEN}■${NC} 144 specialized AI agents    ${GREEN}■${NC} 60+ automation hooks"
  echo -e "  ${GREEN}■${NC} 56 slash command skills       ${GREEN}■${NC} Self-healing infrastructure"
  echo -e "  ${GREEN}■${NC} Persistent task memory (CTM)  ${GREEN}■${NC} Local semantic search (RAG)"
  echo ""
  echo -e "  ${DIM}This installer will guide you through 8 steps.${NC}"
  echo -e "  ${DIM}Each step explains what it does before doing it.${NC}"
  echo -e "  ${DIM}You can press Enter to accept defaults at every prompt.${NC}"
  echo ""

  if [ "$YES_MODE" = false ]; then
    ask "Ready to begin?" "Y"
    if [[ "$(lc "$REPLY")" =~ ^n ]]; then
      echo ""
      info "No problem. Run this script again when you're ready."
      exit 0
    fi
  fi
}

# ─────────────────────────────────────────────────────────────
# Prerequisites check
# ─────────────────────────────────────────────────────────────
check_prerequisites() {
  step "Checking prerequisites"
  echo -e "  ${DIM}Making sure your machine has the tools this config needs.${NC}"
  echo ""
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
    if [[ "$(lc "$REPLY")" =~ ^n ]] || [ -z "$REPLY" ]; then
      fatal "Please install prerequisites and re-run install.sh"
    fi
  fi
}

# ─────────────────────────────────────────────────────────────
# Ask install path (if not set via --prefix)
# ─────────────────────────────────────────────────────────────
ask_install_path() {
  step "Install location"

  echo -e "  ${DIM}Claude Code reads its configuration from a folder on your machine.${NC}"
  echo -e "  ${DIM}The default location is ~/.claude — you almost certainly want this.${NC}"
  echo ""

  if [ "$PREFIX_SET" = true ] || [ "$YES_MODE" = true ]; then
    info "Install path: ${BOLD}$INSTALL_PREFIX${NC}"
    return
  fi
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

  echo ""
  warn "Existing installation detected: $INSTALL_PREFIX"
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
  step "Copying files"
  echo -e "  ${DIM}Copying agents, skills, hooks, and config to your install folder.${NC}"
  echo ""
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
  step "Setting permissions"
  echo -e "  ${DIM}Making scripts runnable. This is a one-time setup step.${NC}"
  echo ""

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
  step "Settings"
  echo -e "  ${DIM}Creating your settings file. This controls hooks, permissions, and behavior.${NC}"
  echo ""

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
  step "Installing dependencies"
  echo -e "  ${DIM}Installing Python packages and CLI tools that hooks and scripts need.${NC}"
  echo -e "  ${DIM}Includes: jq (JSON processing), ripgrep (fast search), fd (file finder).${NC}"
  echo ""

  if [ "$SKIP_DEPS" = true ]; then
    info "Skipping dependency install (--no-deps)"
    return
  fi

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
  step "Optional extras"

  echo -e "  ${DIM}These are nice-to-have features. Everything works without them.${NC}"
  echo ""

  if [ "$YES_MODE" = true ]; then
    info "Skipping optional setup (--yes mode)"
    return
  fi

  echo -e "  ${BOLD}Ollama — Local AI Search${NC}"
  echo ""
  echo "  Think of this as a search engine that lives on your machine."
  echo "  It lets you ask questions like \"what did we decide about auth?\""
  echo "  and get answers from your project files and past sessions."
  echo ""
  echo "  Ollama runs locally — your data never leaves your machine."
  echo "  Requires ~700MB disk space. Can be set up later if you skip."
  echo ""
  ask "Install Ollama for local semantic search?" "Y"

  if [[ "$(lc "$REPLY")" =~ ^y ]]; then
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

  echo ""
  echo -e "  ${BOLD}API Keys (optional)${NC}"
  echo ""
  echo "  This config includes agents that can call OpenAI (Codex) and Google"
  echo "  (Gemini) alongside Claude for complex reasoning tasks."
  echo ""
  echo "  Without these keys, everything still works — you just won't have"
  echo "  multi-model agents. Most users skip this and add them later."
  echo ""

  # Detect shell rc file
  local shell_rc="$HOME/.zshrc"
  if [[ "${SHELL:-}" == *"bash"* ]] || [ -f "$HOME/.bashrc" ] && [ ! -f "$HOME/.zshrc" ]; then
    shell_rc="$HOME/.bashrc"
  fi

  ask "Do you have an OpenAI API key? (get one at platform.openai.com — paid)" "N"
  if [[ "$(lc "$REPLY")" =~ ^y ]]; then
    ask "Paste your OpenAI API key" ""
    if [ -n "$REPLY" ] && [[ "$REPLY" == sk-* ]]; then
      echo "export OPENAI_API_KEY=\"$REPLY\"" >> "$shell_rc"
      success "OPENAI_API_KEY added to $shell_rc"
    else
      warn "Skipped (invalid or empty key)"
    fi
  fi

  ask "Do you have a Google API key? (get one at aistudio.google.com — free tier available)" "N"
  if [[ "$(lc "$REPLY")" =~ ^y ]]; then
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
  step "Validating installation"
  echo -e "  ${DIM}Running a quick health check to make sure everything is in order.${NC}"
  echo ""

  local validator="$INSTALL_PREFIX/scripts/validate-setup.sh"
  if [ -x "$validator" ]; then
    "$validator" --quick || warn "Some checks flagged. Run validate-setup.sh for details."
  else
    warn "validate-setup.sh not found — skipping validation"
  fi
}

# ─────────────────────────────────────────────────────────────
# Summary + next steps
# ─────────────────────────────────────────────────────────────
print_summary() {
  # Count what was installed
  local agent_count hook_count skill_count rule_count
  agent_count=$(find "$INSTALL_PREFIX/agents" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  hook_count=$(find "$INSTALL_PREFIX/hooks" -name "*.sh" -o -name "*.py" -o -name "*.mjs" 2>/dev/null | wc -l | tr -d ' ')
  skill_count=$(find "$INSTALL_PREFIX/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l | tr -d ' ')
  rule_count=$(find "$INSTALL_PREFIX/rules" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

  local ollama_status="Not installed"
  command -v ollama &>/dev/null && ollama_status="Installed"

  echo ""
  echo ""
  echo -e "${BOLD}${GREEN}"
  echo "   ╔═══════════════════════════════════════════════════════════╗"
  echo "   ║                                                           ║"
  echo "   ║              Installation complete!                       ║"
  echo "   ║                                                           ║"
  echo "   ╚═══════════════════════════════════════════════════════════╝"
  echo -e "${NC}"
  echo -e "  ${DIM}┌─────────────────────────────────────────────────────┐${NC}"
  echo -e "  ${DIM}│${NC}  Installed to:  ${BOLD}$INSTALL_PREFIX${NC}"
  echo -e "  ${DIM}│${NC}"
  echo -e "  ${DIM}│${NC}  ${GREEN}■${NC} Agents:  $agent_count     ${GREEN}■${NC} Skills:  $skill_count"
  echo -e "  ${DIM}│${NC}  ${GREEN}■${NC} Hooks:   $hook_count     ${GREEN}■${NC} Rules:   $rule_count"
  echo -e "  ${DIM}│${NC}  ${GREEN}■${NC} Ollama:  $ollama_status"
  if [ "$MERGE_MODE" = true ]; then
  echo -e "  ${DIM}│${NC}  ${BLUE}i${NC} Mode:    Merge (existing files preserved)"
  fi
  echo -e "  ${DIM}└─────────────────────────────────────────────────────┘${NC}"
}

print_next_steps() {
  print_summary
  echo ""
  echo -e "  ${BOLD}Get started:${NC}"
  echo ""
  echo -e "  ${CYAN}1.${NC} Restart your terminal       ${DIM}(loads new env variables)${NC}"
  echo -e "  ${CYAN}2.${NC} Go to a project              ${DIM}cd /your/project${NC}"
  echo -e "  ${CYAN}3.${NC} Start Claude Code             ${DIM}claude${NC}"
  echo ""
  divider
  echo ""
  echo -e "  ${BOLD}Try in your first session:${NC}"
  echo ""
  echo -e "  ${CYAN}/ctm spawn \"my first task\"${NC}    Track work across sessions"
  echo -e "  ${CYAN}/enhance${NC}                       See prompt enhancement"
  echo -e "  ${CYAN}/config-audit${NC}                  Verify your setup"
  echo ""
  divider
  echo ""
  echo -e "  ${BOLD}Documentation:${NC}  ${DIM}$INSTALL_PREFIX/CONFIGURATION_GUIDE.md${NC}"
  echo -e "  ${BOLD}Full check:${NC}     ${DIM}$INSTALL_PREFIX/scripts/validate-setup.sh${NC}"
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
