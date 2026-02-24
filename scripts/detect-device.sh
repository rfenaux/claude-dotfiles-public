#!/bin/bash
# detect-device.sh - Detect device and manage machine profiles
#
# Usage:
#   detect-device.sh              # Check device, prompt if new
#   detect-device.sh --check      # Silent check, exit 0 if known device
#   detect-device.sh --generate   # Generate profile for current device
#   detect-device.sh --info       # Show current device info
#
# Called by session-start hook to ensure optimized settings per machine

set -euo pipefail

PROFILE_FILE="$HOME/.claude/machine-profile.json"
DEVICES_DIR="$HOME/.claude/devices"

# Detect hardware info
detect_hardware() {
    local chip=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Chip:" | awk -F': ' '{print $2}' || echo "Unknown")
    local cores=$(sysctl -n hw.ncpu 2>/dev/null || echo "0")
    local perf_cores=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Total Number of Cores" | grep -oE '[0-9]+ performance' | grep -oE '[0-9]+' || echo "0")
    local eff_cores=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Total Number of Cores" | grep -oE '[0-9]+ efficiency' | grep -oE '[0-9]+' || echo "0")
    local memory=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Memory:" | awk -F': ' '{print $2}' | grep -oE '[0-9]+' || echo "0")
    local model=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Model Name:" | awk -F': ' '{print $2}' || echo "Unknown")
    local serial=$(system_profiler SPHardwareDataType 2>/dev/null | grep "Serial Number" | awk -F': ' '{print $2}' || echo "unknown")

    # Create device fingerprint (hash of serial for privacy)
    local fingerprint=$(echo "$serial" | shasum -a 256 | cut -c1-12)

    echo "$chip|$cores|$perf_cores|$eff_cores|$memory|$model|$fingerprint"
}

# Generate recommended thresholds based on hardware
recommend_thresholds() {
    local cores=$1
    local memory=$2

    # Load thresholds scale with core count
    local load_ok=$(echo "scale=1; $cores * 0.8" | bc)
    local load_caution=$(echo "scale=1; $cores * 1.5" | bc)
    local load_high=$(echo "scale=1; $cores * 2.0" | bc)

    # Agent limits based on memory (roughly 1 agent per 4GB, min 2, max 6)
    local max_agents=$((memory / 4))
    [[ $max_agents -lt 2 ]] && max_agents=2
    [[ $max_agents -gt 6 ]] && max_agents=6

    echo "$load_ok|$load_caution|$load_high|$max_agents"
}

# Check if current device matches profile
check_device() {
    if [[ ! -f "$PROFILE_FILE" ]]; then
        return 1
    fi

    local current_hw=$(detect_hardware)
    local current_fingerprint=$(echo "$current_hw" | cut -d'|' -f7)

    if ! command -v jq &>/dev/null; then
        # Without jq, just assume match if profile exists
        return 0
    fi

    local profile_fingerprint=$(jq -r '.hardware.fingerprint // "none"' "$PROFILE_FILE" 2>/dev/null)

    if [[ "$current_fingerprint" == "$profile_fingerprint" ]]; then
        return 0
    else
        return 1
    fi
}

# Show device info
show_info() {
    local hw=$(detect_hardware)
    local chip=$(echo "$hw" | cut -d'|' -f1)
    local cores=$(echo "$hw" | cut -d'|' -f2)
    local perf=$(echo "$hw" | cut -d'|' -f3)
    local eff=$(echo "$hw" | cut -d'|' -f4)
    local mem=$(echo "$hw" | cut -d'|' -f5)
    local model=$(echo "$hw" | cut -d'|' -f6)
    local fp=$(echo "$hw" | cut -d'|' -f7)

    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ DEVICE INFORMATION                                         │"
    echo "├─────────────────────────────────────────────────────────────┤"
    printf "│ Model:       %-46s │\n" "$model"
    printf "│ Chip:        %-46s │\n" "$chip"
    printf "│ Cores:       %-46s │\n" "$cores ($perf P + $eff E)"
    printf "│ Memory:      %-46s │\n" "${mem}GB"
    printf "│ Fingerprint: %-46s │\n" "$fp"
    echo "└─────────────────────────────────────────────────────────────┘"
}

# Generate new profile for current device
generate_profile() {
    local hw=$(detect_hardware)
    local chip=$(echo "$hw" | cut -d'|' -f1)
    local cores=$(echo "$hw" | cut -d'|' -f2)
    local perf=$(echo "$hw" | cut -d'|' -f3)
    local eff=$(echo "$hw" | cut -d'|' -f4)
    local mem=$(echo "$hw" | cut -d'|' -f5)
    local model=$(echo "$hw" | cut -d'|' -f6)
    local fp=$(echo "$hw" | cut -d'|' -f7)

    local thresholds=$(recommend_thresholds "$cores" "$mem")
    local load_ok=$(echo "$thresholds" | cut -d'|' -f1)
    local load_caution=$(echo "$thresholds" | cut -d'|' -f2)
    local load_high=$(echo "$thresholds" | cut -d'|' -f3)
    local max_agents=$(echo "$thresholds" | cut -d'|' -f4)

    # Choose Ollama model based on memory
    local ollama_model="mxbai-embed-large"
    local ollama_recommended="mxbai-embed-large"
    if [[ $mem -ge 32 ]]; then
        ollama_model="mxbai-embed-large"
        ollama_recommended="snowflake-arctic-embed"
    fi

    # Backup existing profile if present
    if [[ -f "$PROFILE_FILE" ]]; then
        mkdir -p "$DEVICES_DIR"
        local old_fp=$(jq -r '.hardware.fingerprint // "unknown"' "$PROFILE_FILE" 2>/dev/null || echo "unknown")
        cp "$PROFILE_FILE" "$DEVICES_DIR/profile-$old_fp-$(date +%Y%m%d).json" 2>/dev/null || true
    fi

    cat > "$PROFILE_FILE" << EOF
{
  "\$schema": "Machine profile for Claude Code resource management",
  "generated": "$(date +%Y-%m-%d)",
  "hardware": {
    "model": "$model",
    "chip": "$chip",
    "cores": {
      "total": $cores,
      "performance": ${perf:-0},
      "efficiency": ${eff:-0}
    },
    "memory_gb": $mem,
    "gpu": "$chip (integrated, shared memory)",
    "storage_type": "SSD",
    "fingerprint": "$fp"
  },
  "thresholds": {
    "load_ok": $load_ok,
    "load_caution": $load_caution,
    "load_high": $load_high,
    "memory_free_warn_percent": 20,
    "memory_free_critical_percent": 10
  },
  "limits": {
    "max_parallel_agents": $max_agents,
    "max_background_shells": 5,
    "agent_spawn_cooldown_ms": 2000
  },
  "ollama": {
    "model": "$ollama_model",
    "recommended_upgrade": "$ollama_recommended",
    "num_parallel": 2,
    "gpu_layers": -1
  },
  "profiles": {
    "balanced": {
      "description": "Default - good balance of speed and resource usage",
      "max_parallel_agents": $max_agents,
      "load_ok": $load_ok
    },
    "aggressive": {
      "description": "Higher limits - more agents, higher load tolerance",
      "max_parallel_agents": $((max_agents + 2)),
      "load_ok": $(echo "scale=1; $load_ok * 1.5" | bc)
    },
    "conservative": {
      "description": "Minimize resource usage, good for multitasking",
      "max_parallel_agents": $((max_agents > 2 ? max_agents - 1 : 2)),
      "load_ok": $(echo "scale=1; $load_ok * 0.6" | bc)
    }
  },
  "active_profile": "balanced"
}
EOF

    echo "✓ Generated optimized profile for $model ($chip, ${mem}GB)"
    echo "  → Max parallel agents: $max_agents"
    echo "  → Load threshold (OK): $load_ok"
    echo "  → Ollama model: $ollama_model"
}

# Prompt user for new device
prompt_new_device() {
    local hw=$(detect_hardware)
    local chip=$(echo "$hw" | cut -d'|' -f1)
    local mem=$(echo "$hw" | cut -d'|' -f5)
    local model=$(echo "$hw" | cut -d'|' -f6)

    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ 🖥️  NEW DEVICE DETECTED                                      │"
    echo "├─────────────────────────────────────────────────────────────┤"
    printf "│ %-59s │\n" "$model"
    printf "│ %-59s │\n" "$chip / ${mem}GB"
    echo "├─────────────────────────────────────────────────────────────┤"
    echo "│ Would you like to generate optimized resource settings?    │"
    echo "│ This will tune agent limits and load thresholds for this   │"
    echo "│ machine's hardware.                                        │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
    echo "Run: ~/.claude/scripts/detect-device.sh --generate"
    echo ""
}

# Main
case "${1:-}" in
    --check)
        if check_device; then
            exit 0
        else
            exit 1
        fi
        ;;
    --generate)
        generate_profile
        ;;
    --info)
        show_info
        ;;
    *)
        if check_device; then
            # Known device - show brief status
            if command -v jq &>/dev/null && [[ -f "$PROFILE_FILE" ]]; then
                local profile=$(jq -r '.active_profile' "$PROFILE_FILE")
                local chip=$(jq -r '.hardware.chip' "$PROFILE_FILE")
                echo "Device: $chip [profile: $profile]"
            fi
        else
            # Unknown device - prompt
            prompt_new_device
        fi
        ;;
esac
