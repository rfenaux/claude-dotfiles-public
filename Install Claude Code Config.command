#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Install Claude Code Config.command
#
# Double-click this file in Finder to download and install
# the Claude Code Dotfiles configuration automatically.
#
# What it does:
#   1. Downloads the latest config from GitHub (as a zip — no git needed)
#   2. Extracts it to a temporary folder
#   3. Launches the interactive installer
#   4. Cleans up the temporary download
#
# You can also run this from Terminal:
#   bash "Install Claude Code Config.command"
# ─────────────────────────────────────────────────────────────

set -uo pipefail

# ── Config ──────────────────────────────────────────────────
REPO_OWNER="rfenaux"
REPO_NAME="claude-dotfiles-public"
BRANCH="main"
DOWNLOAD_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}/archive/refs/heads/${BRANCH}.zip"
TEMP_DIR=""

# ── Colors ──────────────────────────────────────────────────
if [ -t 1 ] && [ "${NO_COLOR:-}" = "" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
  BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'
  DIM='\033[2m'; NC='\033[0m'
else
  RED=''; GREEN=''; YELLOW=''; BLUE=''; CYAN=''; BOLD=''; DIM=''; NC=''
fi

info()    { echo -e "  ${BLUE}i${NC} $*"; }
success() { echo -e "  ${GREEN}✓${NC} $*"; }
warn()    { echo -e "  ${YELLOW}!${NC} $*"; }
error()   { echo -e "  ${RED}✗${NC} $*" >&2; }
# Lowercase helper (macOS ships bash 3.2 which lacks ${var,,})
lc() { echo "$1" | tr '[:upper:]' '[:lower:]'; }

# ── Cleanup on exit ─────────────────────────────────────────
cleanup() {
  if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}
trap cleanup EXIT

# ── Main ────────────────────────────────────────────────────
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
echo -e "  ${DIM}One-click installer — downloads and configures everything.${NC}"
echo ""

# Check for curl
if ! command -v curl &>/dev/null; then
  error "curl is required but not found."
  error "On macOS, curl is pre-installed. If you're on Linux: apt install curl"
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 1
fi

# Check for unzip
if ! command -v unzip &>/dev/null; then
  error "unzip is required but not found."
  error "Install: brew install unzip  or  apt install unzip"
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 1
fi

echo -e "  This will:"
echo ""
echo -e "  ${CYAN}1.${NC} Download the latest config from GitHub      ${DIM}(~5 MB)${NC}"
echo -e "  ${CYAN}2.${NC} Run the guided installer                    ${DIM}(8 steps)${NC}"
echo -e "  ${CYAN}3.${NC} Clean up the download when done"
echo ""

printf "  ${BOLD}?${NC} Ready to start? [Y/n]: "
read -r REPLY
REPLY="${REPLY:-Y}"
if [[ "$(lc "$REPLY")" =~ ^n ]]; then
  echo ""
  info "No problem. Run this file again when you're ready."
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 0
fi

echo ""

# ── Step 1: Download ────────────────────────────────────────
info "Downloading from GitHub..."
TEMP_DIR=$(mktemp -d)
ZIP_FILE="$TEMP_DIR/dotfiles.zip"

if ! curl -fsSL -o "$ZIP_FILE" "$DOWNLOAD_URL"; then
  error "Download failed."
  error "Check your internet connection and try again."
  error "URL: $DOWNLOAD_URL"
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 1
fi

success "Downloaded $(du -h "$ZIP_FILE" | awk '{print $1}')"

# ── Step 2: Extract ─────────────────────────────────────────
info "Extracting..."
if ! unzip -q "$ZIP_FILE" -d "$TEMP_DIR"; then
  error "Failed to extract the download."
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 1
fi

# GitHub zips extract to repo-name-branch/
EXTRACTED_DIR="$TEMP_DIR/${REPO_NAME}-${BRANCH}"
if [ ! -d "$EXTRACTED_DIR" ]; then
  # Fallback: find the extracted directory
  EXTRACTED_DIR=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
fi

if [ ! -f "$EXTRACTED_DIR/install.sh" ]; then
  error "install.sh not found in the downloaded files."
  error "The repository structure may have changed."
  echo ""
  echo "Press any key to close..."
  read -n 1 -s
  exit 1
fi

success "Extracted to temporary folder"
echo ""

# ── Step 3: Launch installer ────────────────────────────────
info "Launching the installer..."
echo ""
echo -e "  ${DIM}────────────────────────────────────────────────${NC}"
echo ""

# Hand off to the real installer
bash "$EXTRACTED_DIR/install.sh" "$@"
INSTALL_EXIT=$?

echo ""

if [ $INSTALL_EXIT -eq 0 ]; then
  echo -e "  ${DIM}────────────────────────────────────────────────${NC}"
  echo ""
  success "All done! You can close this window."
  echo ""
  echo -e "  ${DIM}The temporary download has been cleaned up automatically.${NC}"
else
  warn "The installer exited with an error (code $INSTALL_EXIT)."
  warn "You can re-run this file to try again."
fi

echo ""
echo "Press any key to close..."
read -n 1 -s
