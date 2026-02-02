#!/bin/bash
# switch-profile.sh - Switch between resource management profiles
#
# Usage:
#   switch-profile.sh                    # Show current profile
#   switch-profile.sh balanced           # Switch to balanced
#   switch-profile.sh performance        # Switch to performance
#   switch-profile.sh conservative       # Switch to conservative
#   switch-profile.sh --list             # List all profiles

set -euo pipefail

PROFILE_FILE="$HOME/.claude/machine-profile.json"

if [[ ! -f "$PROFILE_FILE" ]]; then
    echo "Error: Machine profile not found at $PROFILE_FILE"
    exit 1
fi

if ! command -v jq &>/dev/null; then
    echo "Error: jq required but not installed. Run: brew install jq"
    exit 1
fi

show_current() {
    local current=$(jq -r '.active_profile' "$PROFILE_FILE")
    local desc=$(jq -r ".profiles.$current.description // \"No description\"" "$PROFILE_FILE")
    local ollama_model=$(jq -r ".profiles.$current.ollama_model // \"nomic-embed-text\"" "$PROFILE_FILE")
    echo "Current profile: $current"
    echo "  → $desc"
    echo "  → Embedding model: $ollama_model"
}

list_profiles() {
    local current=$(jq -r '.active_profile' "$PROFILE_FILE")
    echo "Available profiles:"
    echo ""
    jq -r '.profiles | to_entries[] | "  \(.key): \(.value.description)"' "$PROFILE_FILE" | while read line; do
        local name=$(echo "$line" | cut -d: -f1 | tr -d ' ')
        if [[ "$name" == "$current" ]]; then
            echo "$line ← active"
        else
            echo "$line"
        fi
    done
}

switch_profile() {
    local new_profile=$1

    # Check if profile exists
    if ! jq -e ".profiles.$new_profile" "$PROFILE_FILE" >/dev/null 2>&1; then
        echo "Error: Profile '$new_profile' not found"
        echo ""
        list_profiles
        exit 1
    fi

    # Update the profile
    local tmp=$(mktemp)
    jq ".active_profile = \"$new_profile\"" "$PROFILE_FILE" > "$tmp" && mv "$tmp" "$PROFILE_FILE"

    local desc=$(jq -r ".profiles.$new_profile.description" "$PROFILE_FILE")
    local max_agents=$(jq -r ".profiles.$new_profile.max_parallel_agents // .limits.max_parallel_agents" "$PROFILE_FILE")
    local load_ok=$(jq -r ".profiles.$new_profile.load_ok // .thresholds.load_ok" "$PROFILE_FILE")
    local ollama_model=$(jq -r ".profiles.$new_profile.ollama_model // \"nomic-embed-text\"" "$PROFILE_FILE")

    echo "✓ Switched to profile: $new_profile"
    echo "  → $desc"
    echo "  → Max parallel agents: $max_agents"
    echo "  → Load threshold (OK): $load_ok"
    echo "  → Embedding model: $ollama_model"
    echo ""
    echo "⚠ Note: Restart Claude Code to use new embedding model."
}

case "${1:-}" in
    "")
        show_current
        ;;
    --list|-l)
        list_profiles
        ;;
    *)
        switch_profile "$1"
        ;;
esac
