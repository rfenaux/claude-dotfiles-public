#!/bin/zsh
# iTerm2 Theme Applicator - applies color schemes via proprietary escape sequences
# Usage: apply-theme.sh [theme_name|list|reset|random] [alpha_percent]
# Requires: zsh (macOS default), iTerm2

set -euo pipefail

# Find the controlling TTY - escape sequences must go directly to the terminal,
# not stdout (which Claude Code captures). Walk up the process tree to find it.
find_tty() {
  local pid=$$
  local found_tty=""
  for _ in 1 2 3 4 5; do
    found_tty=$(ps -o tty= -p "$pid" 2>/dev/null | tr -d ' ')
    if [[ -n "$found_tty" && "$found_tty" != "??" ]]; then
      echo "/dev/$found_tty"
      return 0
    fi
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
    [[ -z "$pid" ]] && break
  done
  # Fallback: try /dev/tty
  if [[ -w /dev/tty ]]; then
    echo "/dev/tty"
    return 0
  fi
  return 1
}

TTY_DEV=$(find_tty) || { echo "ERROR|Cannot find TTY device" >&2; exit 1; }

set_color() { printf "\033]1337;SetColors=%s=%s\007" "$1" "$2" > "$TTY_DEV" }
set_alpha() { printf "\033]1337;SetBackgroundAlpha=%s\007" "$1" > "$TTY_DEV" }

# All theme names
THEME_NAMES=(
  midnight-aurora cyberpunk-neon forest-dusk ocean-depth sunset-haze
  arctic-frost volcanic-ember lavender-dream tokyo-night copper-patina
  synthwave monochrome-silk catppuccin-mocha rose-pine dracula-glass
)

# Get theme data by name -> sets T_* variables
load_theme() {
  case "$1" in
    midnight-aurora)
      T_BG=0d1117 T_FG=e2e8f0 T_SELBG=1f3a5f T_SELFG=f0f6fc T_CURBG=58a6ff T_CURFG=0d1117
      T_BLACK=484f58 T_RED=ff7b72 T_GREEN=3fb950 T_YELLOW=d29922 T_BLUE=58a6ff T_MAGENTA=bc8cff T_CYAN=39d2c0 T_WHITE=e2e8f0
      T_BR_BLACK=8b949e T_BR_RED=ffa198 T_BR_GREEN=56d364 T_BR_YELLOW=e3b341 T_BR_BLUE=79c0ff T_BR_MAGENTA=d2a8ff T_BR_CYAN=56d4dd T_BR_WHITE=f8fafc
      T_ALPHA=6 T_VIBE="Deep blue + aurora greens" ;;
    cyberpunk-neon)
      T_BG=0a0a1a T_FG=eeeeff T_SELBG=3d1f5c T_SELFG=ff79c6 T_CURBG=ff2975 T_CURFG=0a0a1a
      T_BLACK=2a2a3a T_RED=ff2975 T_GREEN=05ffa1 T_YELLOW=f1fa8c T_BLUE=00b4d8 T_MAGENTA=bd93f9 T_CYAN=8be9fd T_WHITE=eeeeff
      T_BR_BLACK=5a5a6a T_BR_RED=ff6eb4 T_BR_GREEN=69ff94 T_BR_YELLOW=ffffa5 T_BR_BLUE=48cae4 T_BR_MAGENTA=d6bcfa T_BR_CYAN=a4f4fd T_BR_WHITE=ffffff
      T_ALPHA=8 T_VIBE="Hot pink + electric blue" ;;
    forest-dusk)
      T_BG=0f1a0f T_FG=dce0c8 T_SELBG=2d4a2d T_SELFG=f0f0e0 T_CURBG=a3be8c T_CURFG=0f1a0f
      T_BLACK=2e3429 T_RED=d06060 T_GREEN=a3be8c T_YELLOW=ebcb8b T_BLUE=5e81ac T_MAGENTA=b48ead T_CYAN=8fbcbb T_WHITE=dce0c8
      T_BR_BLACK=6a7560 T_BR_RED=d08770 T_BR_GREEN=b5d19c T_BR_YELLOW=f0d9a0 T_BR_BLUE=81a1c1 T_BR_MAGENTA=c9a4c0 T_BR_CYAN=a3d1cf T_BR_WHITE=f4f7f0
      T_ALPHA=8 T_VIBE="Deep forest greens + amber" ;;
    ocean-depth)
      T_BG=051622 T_FG=d8e8f4 T_SELBG=0e3b5e T_SELFG=f0f8ff T_CURBG=1282a2 T_CURFG=ffffff
      T_BLACK=0a2944 T_RED=e74c3c T_GREEN=2ecc71 T_YELLOW=f39c12 T_BLUE=1282a2 T_MAGENTA=9b59b6 T_CYAN=1abc9c T_WHITE=d8e8f4
      T_BR_BLACK=2a6090 T_BR_RED=ff6b6b T_BR_GREEN=55efc4 T_BR_YELLOW=feca57 T_BR_BLUE=48dbfb T_BR_MAGENTA=c39bd3 T_BR_CYAN=48dbfb T_BR_WHITE=f0f6fa
      T_ALPHA=7 T_VIBE="Deep teal + coral" ;;
    sunset-haze)
      T_BG=1a0a1e T_FG=f0e0d4 T_SELBG=3d1f4a T_SELFG=fff4ee T_CURBG=ff6b6b T_CURFG=1a0a1e
      T_BLACK=2d1633 T_RED=ff6b6b T_GREEN=95e6a0 T_YELLOW=ffd93d T_BLUE=6c5ce7 T_MAGENTA=fd79a8 T_CYAN=81ecec T_WHITE=f0e0d4
      T_BR_BLACK=5a3868 T_BR_RED=ff9b9b T_BR_GREEN=a8e6cf T_BR_YELLOW=ffe69a T_BR_BLUE=a29bfe T_BR_MAGENTA=fab1c0 T_BR_CYAN=a8e6e6 T_BR_WHITE=fff6f0
      T_ALPHA=8 T_VIBE="Warm oranges + purple" ;;
    arctic-frost)
      T_BG=0c1b2a T_FG=e8edf4 T_SELBG=2e3440 T_SELFG=f8fafc T_CURBG=88c0d0 T_CURFG=0c1b2a
      T_BLACK=2e3440 T_RED=bf616a T_GREEN=a3be8c T_YELLOW=ebcb8b T_BLUE=81a1c1 T_MAGENTA=b48ead T_CYAN=88c0d0 T_WHITE=e8edf4
      T_BR_BLACK=616e7c T_BR_RED=d08770 T_BR_GREEN=a3be8c T_BR_YELLOW=ebcb8b T_BR_BLUE=5e81ac T_BR_MAGENTA=b48ead T_BR_CYAN=8fbcbb T_BR_WHITE=f8fafc
      T_ALPHA=5 T_VIBE="Cool whites + ice blue" ;;
    volcanic-ember)
      T_BG=1a0808 T_FG=f0d4c8 T_SELBG=3d1515 T_SELFG=fff0e8 T_CURBG=ff4500 T_CURFG=ffffff
      T_BLACK=2d1010 T_RED=ff4500 T_GREEN=7cba3a T_YELLOW=ffb347 T_BLUE=4a90d9 T_MAGENTA=c76b98 T_CYAN=5bc0be T_WHITE=f0d4c8
      T_BR_BLACK=5a3030 T_BR_RED=ff6a33 T_BR_GREEN=98d35e T_BR_YELLOW=ffc97a T_BR_BLUE=6ab0f3 T_BR_MAGENTA=e08bab T_BR_CYAN=7dd3d1 T_BR_WHITE=fff4ee
      T_ALPHA=7 T_VIBE="Dark red + orange glow" ;;
    lavender-dream)
      T_BG=14101e T_FG=e4ddf0 T_SELBG=2d2540 T_SELFG=f8f4ff T_CURBG=9d8ec7 T_CURFG=14101e
      T_BLACK=1e1830 T_RED=e06c75 T_GREEN=98c379 T_YELLOW=e5c07b T_BLUE=7c9dec T_MAGENTA=c678dd T_CYAN=56b6c2 T_WHITE=e4ddf0
      T_BR_BLACK=504870 T_BR_RED=e88e94 T_BR_GREEN=afd49b T_BR_YELLOW=ecd19e T_BR_BLUE=9bb4f0 T_BR_MAGENTA=d49ee5 T_BR_CYAN=7bc8d2 T_BR_WHITE=f8f4ff
      T_ALPHA=10 T_VIBE="Soft purples + silver" ;;
    tokyo-night)
      T_BG=1a1b26 T_FG=c8d0f0 T_SELBG=33467c T_SELFG=e0e8ff T_CURBG=c0caf5 T_CURFG=1a1b26
      T_BLACK=15161e T_RED=f7768e T_GREEN=9ece6a T_YELLOW=e0af68 T_BLUE=7aa2f7 T_MAGENTA=bb9af7 T_CYAN=7dcfff T_WHITE=c8d0f0
      T_BR_BLACK=565f89 T_BR_RED=ff9e9e T_BR_GREEN=b9f27c T_BR_YELLOW=ffc777 T_BR_BLUE=89b4ff T_BR_MAGENTA=c9a8ff T_BR_CYAN=b4f9f8 T_BR_WHITE=e8f0ff
      T_ALPHA=6 T_VIBE="Inspired by Tokyo Night" ;;
    copper-patina)
      T_BG=1a1410 T_FG=e4d8c0 T_SELBG=3a2e22 T_SELFG=f8f0e0 T_CURBG=c08040 T_CURFG=1a1410
      T_BLACK=2a2018 T_RED=cc6633 T_GREEN=669966 T_YELLOW=c08040 T_BLUE=557799 T_MAGENTA=996688 T_CYAN=5f9ea0 T_WHITE=e4d8c0
      T_BR_BLACK=5a4e40 T_BR_RED=e08050 T_BR_GREEN=88bb88 T_BR_YELLOW=d4a060 T_BR_BLUE=77aabb T_BR_MAGENTA=bb88aa T_BR_CYAN=7fbfbf T_BR_WHITE=f8f0e0
      T_ALPHA=7 T_VIBE="Warm bronze + verdigris" ;;
    synthwave)
      T_BG=0e0e2c T_FG=ece0ff T_SELBG=2a1f5e T_SELFG=ff00ff T_CURBG=ff2cf1 T_CURFG=0e0e2c
      T_BLACK=1a1a40 T_RED=fe4450 T_GREEN=72f1b8 T_YELLOW=fede5d T_BLUE=2ee2fa T_MAGENTA=ff7edb T_CYAN=03edf9 T_WHITE=ece0ff
      T_BR_BLACK=4a4a70 T_BR_RED=ff6b7a T_BR_GREEN=92ffd0 T_BR_YELLOW=fff490 T_BR_BLUE=6ef5ff T_BR_MAGENTA=ffa8e8 T_BR_CYAN=40f4ff T_BR_WHITE=faf4ff
      T_ALPHA=9 T_VIBE="Retro 80s neon" ;;
    monochrome-silk)
      T_BG=111111 T_FG=dddddd T_SELBG=333333 T_SELFG=ffffff T_CURBG=bbbbbb T_CURFG=111111
      T_BLACK=1a1a1a T_RED=aaaaaa T_GREEN=bbbbbb T_YELLOW=cccccc T_BLUE=999999 T_MAGENTA=aaaaaa T_CYAN=bbbbbb T_WHITE=dddddd
      T_BR_BLACK=555555 T_BR_RED=cccccc T_BR_GREEN=dddddd T_BR_YELLOW=eeeeee T_BR_BLUE=bbbbbb T_BR_MAGENTA=cccccc T_BR_CYAN=dddddd T_BR_WHITE=f5f5f5
      T_ALPHA=5 T_VIBE="Elegant grayscale" ;;
    catppuccin-mocha)
      T_BG=1e1e2e T_FG=e0e8ff T_SELBG=45475a T_SELFG=f0f4ff T_CURBG=f5e0dc T_CURFG=1e1e2e
      T_BLACK=45475a T_RED=f38ba8 T_GREEN=a6e3a1 T_YELLOW=f9e2af T_BLUE=89b4fa T_MAGENTA=cba6f7 T_CYAN=94e2d5 T_WHITE=e0e8ff
      T_BR_BLACK=6c7086 T_BR_RED=f38ba8 T_BR_GREEN=a6e3a1 T_BR_YELLOW=f9e2af T_BR_BLUE=89b4fa T_BR_MAGENTA=cba6f7 T_BR_CYAN=94e2d5 T_BR_WHITE=f0f4ff
      T_ALPHA=6 T_VIBE="Catppuccin warm pastels" ;;
    rose-pine)
      T_BG=191724 T_FG=eceaf8 T_SELBG=403d52 T_SELFG=f8f6ff T_CURBG=ebbcba T_CURFG=191724
      T_BLACK=26233a T_RED=eb6f92 T_GREEN=31748f T_YELLOW=f6c177 T_BLUE=9ccfd8 T_MAGENTA=c4a7e7 T_CYAN=9ccfd8 T_WHITE=eceaf8
      T_BR_BLACK=7a7696 T_BR_RED=eb6f92 T_BR_GREEN=31748f T_BR_YELLOW=f6c177 T_BR_BLUE=9ccfd8 T_BR_MAGENTA=c4a7e7 T_BR_CYAN=9ccfd8 T_BR_WHITE=f8f6ff
      T_ALPHA=7 T_VIBE="Muted rose + pine" ;;
    dracula-glass)
      T_BG=1e1f29 T_FG=f8f8f2 T_SELBG=44475a T_SELFG=ffffff T_CURBG=f8f8f2 T_CURFG=282a36
      T_BLACK=21222c T_RED=ff5555 T_GREEN=50fa7b T_YELLOW=f1fa8c T_BLUE=6272a4 T_MAGENTA=bd93f9 T_CYAN=8be9fd T_WHITE=f8f8f2
      T_BR_BLACK=626480 T_BR_RED=ff6e6e T_BR_GREEN=69ff94 T_BR_YELLOW=ffffa5 T_BR_BLUE=8694c7 T_BR_MAGENTA=d6acff T_BR_CYAN=a4ffff T_BR_WHITE=ffffff
      T_ALPHA=10 T_VIBE="Dracula with glass effect" ;;
    *)
      echo "ERROR|Unknown theme: $1" >&2
      echo "Available: ${THEME_NAMES[*]}" >&2
      return 1 ;;
  esac
}

# Parse args
THEME_NAME="${1:-random}"
ALPHA_OVERRIDE="${2:-}"

# Handle list
if [[ "$THEME_NAME" == "list" ]]; then
  echo "Available iTerm2 themes:"
  echo ""
  for name in "${THEME_NAMES[@]}"; do
    load_theme "$name"
    printf "  %-20s  #%-6s  %2s%% alpha  %s\n" "$name" "$T_BG" "$T_ALPHA" "$T_VIBE"
  done
  echo ""
  echo "Usage: /iterm2-theme <name> | /iterm2-theme --alpha <N>"
  exit 0
fi

# Handle reset
if [[ "$THEME_NAME" == "reset" ]]; then
  printf "\033]1337;SetColors=preset=Default\007" > "$TTY_DEV"
  set_alpha "1.0"
  echo "RESET|default|100"
  exit 0
fi

# Handle random
if [[ "$THEME_NAME" == "random" ]]; then
  RANDOM_IDX=$((RANDOM % ${#THEME_NAMES[@]} + 1))
  THEME_NAME="${THEME_NAMES[$RANDOM_IDX]}"
fi

# Handle --alpha as first arg
if [[ "$THEME_NAME" == "--alpha" ]]; then
  ALPHA_OVERRIDE="$ALPHA_OVERRIDE"
  RANDOM_IDX=$((RANDOM % ${#THEME_NAMES[@]} + 1))
  THEME_NAME="${THEME_NAMES[$RANDOM_IDX]}"
fi

# Load theme
load_theme "$THEME_NAME"

# Apply all colors
set_color bg "$T_BG"
set_color fg "$T_FG"
set_color selbg "$T_SELBG"
set_color selfg "$T_SELFG"
set_color curbg "$T_CURBG"
set_color curfg "$T_CURFG"
set_color black "$T_BLACK"
set_color red "$T_RED"
set_color green "$T_GREEN"
set_color yellow "$T_YELLOW"
set_color blue "$T_BLUE"
set_color magenta "$T_MAGENTA"
set_color cyan "$T_CYAN"
set_color white "$T_WHITE"
set_color br_black "$T_BR_BLACK"
set_color br_red "$T_BR_RED"
set_color br_green "$T_BR_GREEN"
set_color br_yellow "$T_BR_YELLOW"
set_color br_blue "$T_BR_BLUE"
set_color br_magenta "$T_BR_MAGENTA"
set_color br_cyan "$T_BR_CYAN"
set_color br_white "$T_BR_WHITE"

# Calculate and apply alpha
ALPHA_PCT="${ALPHA_OVERRIDE:-$T_ALPHA}"
ALPHA_FLOAT=$(echo "scale=2; (100 - $ALPHA_PCT) / 100" | bc)
set_alpha "$ALPHA_FLOAT"

# Output result
echo "APPLIED|$THEME_NAME|#$T_BG|#$T_FG|$ALPHA_PCT|$T_VIBE"
