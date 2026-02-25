#!/usr/bin/env bash
# status-line.sh - Claude Code 2-line status line with usage limits
#
# Line 1: Account | Model | 5h bar | 7d bar | Ctx%
# Line 2: Git M/D/S/U/↑/↓/⚠ | ~/path | time | #session
#
# Reads JSON from stdin. Calls status-line-usage.py for API limits.

set -o pipefail

# ANSI colors
RST='\033[0m'
GRN='\033[92m'
YLW='\033[33m'
RED='\033[91m'
GRY='\033[90m'

input=$(cat)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Helpers ---

threshold_color() {
    local pct="${1:-0}"
    if [ "$pct" -ge 80 ] 2>/dev/null; then echo "$RED"
    elif [ "$pct" -ge 50 ] 2>/dev/null; then echo "$YLW"
    else echo "$GRN"
    fi
}

render_bar() {
    local pct="${1:-0}"
    local width=10
    local filled=$((pct * width / 100))
    [ "$filled" -gt "$width" ] && filled=$width
    local empty=$((width - filled))
    local color
    color=$(threshold_color "$pct")
    local bar="${color}"
    for ((i=0; i<filled; i++)); do bar+="━"; done
    for ((i=0; i<empty; i++)); do bar+="░"; done
    bar+="${RST}"
    echo "$bar"
}

colorize_stat() {
    local label="$1" value="$2" hi_color="${3:-$YLW}"
    if [ "$value" -eq 0 ] 2>/dev/null; then
        printf "${GRY}%s:%s${RST}" "$label" "$value"
    else
        printf "${hi_color}%s:%s${RST}" "$label" "$value"
    fi
}

# --- Account ---
acct="${CLAUDE_ACCOUNT_NAME:-Primary}"
# Override based on config dir patterns if accounts.json exists
if [ -f "${HOME}/.claude/config/accounts.json" ]; then
    _dir_name=$(basename "${CLAUDE_CONFIG_DIR:-$HOME/.claude}")
    _acct_match=$(python3 -c "
import json,sys
try:
    accts=json.load(open('${HOME}/.claude/config/accounts.json'))
    for a in accts:
        if a.get('dir_pattern','') and '${_dir_name}'.find(a['dir_pattern'])>=0:
            print(a.get('display',''));sys.exit(0)
except: pass
" 2>/dev/null)
    [ -n "$_acct_match" ] && acct="$_acct_match"
fi

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // .model.name // "?"' 2>/dev/null | sed 's/Claude //' | sed 's/ //')

# --- Context window (v2.1.6: use used_percentage directly) ---
ctx_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' 2>/dev/null)
ctx_pct=${ctx_pct%.*}  # truncate decimal
[ -z "$ctx_pct" ] || [ "$ctx_pct" = "null" ] && ctx_pct=0
ctx_color=$(threshold_color "$ctx_pct")

# --- 2x pricing alert (v2.0.88: exceeds_200k_tokens) ---
exceeds_200k=$(echo "$input" | jq -r '.exceeds_200k_tokens // false' 2>/dev/null)
cost_warn=""
if [ "$exceeds_200k" = "true" ]; then
    cost_warn="${RED}\$\$${RST} "
fi

# --- Session ID ---
sid=$(echo "$input" | jq -r '.session_id // ""' 2>/dev/null)
sid_short="$sid"

# --- Working directory ---
dir=$(echo "$input" | jq -r '.workspace.current_dir // empty' 2>/dev/null)
[ -z "$dir" ] && dir=$(pwd)
dir="${dir/#$HOME/~}"

# --- Usage limits (cached Python call) ---
usage_out="?|?|?|?|?"
if [ -f "$SCRIPT_DIR/status-line-usage.py" ]; then
    usage_out=$(python3 "$SCRIPT_DIR/status-line-usage.py" 2>/dev/null || echo "$usage_out")
fi

IFS='|' read -r fh_pct fh_rem sd_pct sd_rem opus_pct <<< "$usage_out"

# Build 5h and 7d displays
if [ "$fh_pct" = "?" ]; then
    fh_display="5h ??????????  ?%"
else
    fh_bar=$(render_bar "$fh_pct")
    fh_color=$(threshold_color "$fh_pct")
    fh_display="5h ${fh_bar} ${fh_color}${fh_pct}%${RST} (${fh_rem})"
fi

if [ "$sd_pct" = "?" ]; then
    sd_display="7d ??????????  ?%"
else
    sd_bar=$(render_bar "$sd_pct")
    sd_color=$(threshold_color "$sd_pct")
    sd_display="7d ${sd_bar} ${sd_color}${sd_pct}%${RST}"
fi

# --- Git status ---
git_line=""
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    git_status_output=$(git status --porcelain 2>/dev/null)
    if [ -n "$git_status_output" ]; then
        modified=$(git diff --name-only --diff-filter=M 2>/dev/null | wc -l | tr -d ' ')
        deleted=$(git diff --name-only --diff-filter=D 2>/dev/null | wc -l | tr -d ' ')
        staged=$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
        untracked=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
    else
        modified=0; deleted=0; staged=0; untracked=0
    fi

    ahead=0; behind=0
    if git rev-parse --abbrev-ref @{u} >/dev/null 2>&1; then
        ahead=$(git rev-list @{u}..HEAD --count 2>/dev/null || echo 0)
        behind=$(git rev-list HEAD..@{u} --count 2>/dev/null || echo 0)
    fi

    conflicts=$(git diff --name-only --diff-filter=U 2>/dev/null | wc -l | tr -d ' ')

    git_line="$(colorize_stat M $modified) $(colorize_stat D $deleted) $(colorize_stat S $staged) $(colorize_stat U $untracked) $(colorize_stat ↑ $ahead) $(colorize_stat ↓ $behind) $(colorize_stat ⚠ $conflicts $RED)"
else
    git_line="${GRY}no git${RST}"
fi

# --- Time ---
local_time=$(date +"%H:%M")

# --- Assemble output ---

# Line 1: Account | Model | 5h bar | 7d bar | Ctx%
line1="${acct} | ${model} | ${fh_display} | ${sd_display} | ${cost_warn}${ctx_color}Ctx:${ctx_pct}%${RST}"

# Line 2: Git stats | path | time | session
line2="${git_line} | ${GRN}${dir}${RST} | ${GRY}${local_time}${RST} | ${GRY}#${sid_short}${RST}"

echo -e "$line1"
echo -e "$line2"
