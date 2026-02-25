#!/bin/bash
# Configurable paths — single source of truth
# Override any of these via environment variables (e.g., in ~/.zshrc)

# Where projects live (used by init-project, client-onboard, CTM auto-enable)
export PROJECTS_DIR="${PROJECTS_DIR:-$HOME/Projects}"

# Organization wiki (optional — skip features that need it if unset)
export ORG_WIKI_PATH="${ORG_WIKI_PATH:-}"

# Fathom transcript sync output
export FATHOM_OUTPUT_DIR="${FATHOM_OUTPUT_DIR:-$HOME/fathom-transcripts}"

# Fathom internal domains to exclude (comma-separated)
export FATHOM_INTERNAL_DOMAINS="${FATHOM_INTERNAL_DOMAINS:-}"

# FSD template location (optional — functional-spec-generator uses this)
export FSD_TEMPLATE_PATH="${FSD_TEMPLATE_PATH:-}"

# Slide deck theme location (optional — slide-deck-creator uses this)
export SLIDE_THEME_PATH="${SLIDE_THEME_PATH:-}"

# Account display name for status line
export CLAUDE_ACCOUNT_NAME="${CLAUDE_ACCOUNT_NAME:-Primary}"

# Multi-account failover config (optional)
export CLAUDE_ACCOUNTS_CONFIG="${CLAUDE_ACCOUNTS_CONFIG:-$HOME/.claude/config/accounts.json}"
