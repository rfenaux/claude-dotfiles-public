#!/bin/bash
# device-check.sh - SessionStart hook for device detection
# Checks if current device matches stored profile, prompts if new

set +e  # fail-silent: hooks must not abort on error

# TEMPORARILY DISABLED - will revisit later
# To re-enable: remove the early exit below
exit 0

DETECT_SCRIPT="$HOME/.claude/scripts/detect-device.sh"

# Skip if script doesn't exist
[[ ! -x "$DETECT_SCRIPT" ]] && exit 0

# Silent check - exit 0 if known device, exit 1 if new
if "$DETECT_SCRIPT" --check 2>/dev/null; then
    # Known device - show brief status
    if command -v jq &>/dev/null; then
        PROFILE_FILE="$HOME/.claude/machine-profile.json"
        if [[ -f "$PROFILE_FILE" ]]; then
            profile=$(jq -r '.active_profile' "$PROFILE_FILE")
            chip=$(jq -r '.hardware.chip' "$PROFILE_FILE")
            max_agents=$(jq -r ".profiles.$profile.max_parallel_agents // .limits.max_parallel_agents" "$PROFILE_FILE")
            echo "Device: $chip | Profile: $profile | Max agents: $max_agents"
        fi
    fi
else
    # New device detected - show prompt
    "$DETECT_SCRIPT"
fi

exit 0
