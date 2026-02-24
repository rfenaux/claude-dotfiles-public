#!/usr/bin/env bash
# claude-pick.sh - Interactive persona picker for Claude Code sessions
#
# Usage:
#   cla                    Interactive fzf picker (or numbered menu fallback)
#   cla architect          Direct launch by key
#   cla vanilla            Launch without any agent
#   cla -c                 Continue last session (passes through to claude)
#   cla architect -c       Combine: persona + continue
#
# Respects CLAUDE_CONFIG_DIR for multi-account setups.
# Config: $CLAUDE_CONFIG_DIR/config/personas.json (or ~/.claude/config/personas.json)

_claude_pick() {
  local config_dir="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
  local personas_file="$config_dir/config/personas.json"

  # Dependency check
  if ! command -v jq &>/dev/null; then
    echo "❌ jq required. Install: brew install jq"
    return 1
  fi

  # Fallback if no personas config
  if [[ ! -f "$personas_file" ]]; then
    echo "⚠ No personas.json found at $personas_file — launching vanilla Claude"
    claude "$@"
    return
  fi

  # Check if first arg is a persona key (not a claude flag)
  local direct_key=""
  local pass_args=("$@")
  if [[ ${1:-} != "" && ${1:-} != -* ]]; then
    direct_key="$1"
    pass_args=("${@:2}")
  fi

  # --- Direct key mode ---
  if [[ -n "$direct_key" ]]; then
    local match
    match=$(jq -r --arg key "$direct_key" '.personas[] | select(.key == $key)' "$personas_file")

    if [[ -z "$match" ]]; then
      echo "⚠ Unknown persona: $direct_key"
      echo "  Available: $(jq -r '[.personas[].key] | join(", ")' "$personas_file")"
      return 1
    fi

    local agent label icon
    agent=$(echo "$match" | jq -r '.agent')
    label=$(echo "$match" | jq -r '.label')
    icon=$(echo "$match" | jq -r '.icon')

    echo "$icon → $label"
    if [[ -n "$agent" ]]; then
      claude --agent "$agent" "${pass_args[@]}"
    else
      claude "${pass_args[@]}"
    fi
    return
  fi

  # --- Interactive mode ---

  # Build selection list: "key | icon label | description"
  local items
  items=$(jq -r '.personas[] | "\(.key)\t\(.icon) \(.label)\t\(.description)"' "$personas_file")

  if command -v fzf &>/dev/null; then
    # fzf mode
    local selected
    selected=$(echo "$items" \
      | awk -F'\t' '{printf "%-12s  %-35s  %s\n", $1, $2, $3}' \
      | fzf --prompt="🎭 Persona: " \
            --height=40% \
            --header="Pick a session persona (ESC = cancel)" \
            --no-multi)

    [[ -z "$selected" ]] && { echo "Cancelled."; return 0; }

    # Extract key (first word)
    local key
    key=$(echo "$selected" | awk '{print $1}')
    _claude_pick "$key" "${pass_args[@]}"
  else
    # Numbered menu fallback
    echo "🎭 Choose persona:"
    echo ""

    local i=1
    local keys=()
    local default_idx=1
    while IFS=$'\t' read -r key label desc; do
      local is_default=""
      if jq -e --arg key "$key" '.personas[] | select(.key == $key and .default == true)' "$personas_file" &>/dev/null; then
        is_default=" ★"
        default_idx=$i
      fi
      printf "  %d) %-35s %s%s\n" "$i" "$label" "$desc" "$is_default"
      keys+=("$key")
      ((i++))
    done <<< "$items"

    echo ""
    printf "  Pick [1-%d, Enter = %d default]: " "${#keys[@]}" "$default_idx"
    read -r choice

    if [[ -z "$choice" ]]; then
      choice=$default_idx
    fi

    if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice >= 1 && choice <= ${#keys[@]} )); then
      _claude_pick "${keys[$((choice-1))]}" "${pass_args[@]}"
    else
      echo "Invalid choice."
      return 1
    fi
  fi
}

# Public function
cla() { _claude_pick "$@"; }
