---
name: iterm2-theme
description: Randomly apply a curated color scheme with transparency to the current iTerm2 session. Use when user wants to change terminal aesthetics.
async:
  mode: never
  require_sync:
    - visual feedback
---

# /iterm2-theme - iTerm2 Color Scheme Randomizer

Randomly applies a curated color scheme with transparency to the current iTerm2 session using proprietary escape sequences.

## Trigger

`/iterm2-theme` or `/theme`

## Usage

```
/iterm2-theme              # Random theme with default transparency (15%)
/iterm2-theme list          # Show all available themes
/iterm2-theme <name>        # Apply a specific theme
/iterm2-theme --alpha <N>   # Random theme with custom transparency (0-100)
/iterm2-theme reset         # Reset to iTerm2 default profile
```

## Implementation

<iterm2-theme>

### Parse Arguments

```
ARG1=$1   # Theme name, "list", "reset", or "--alpha"
ARG2=$2   # Alpha value if --alpha, or --alpha flag after name
ARG3=$3   # Alpha value if name + --alpha
```

### Color Themes

Each theme defines: `bg` (background), `fg` (foreground), `cursor`, `sel_bg` (selection background), `sel_fg` (selection foreground), `ansi_0`..`ansi_15` (16 ANSI colors), `alpha` (default transparency 0-100, 0=fully transparent).

**Curated themes:**

| # | Name | Vibe | Background | Default Alpha |
|---|------|------|------------|---------------|
| 1 | `midnight-aurora` | Deep blue + aurora greens | #0d1117 | 12 |
| 2 | `cyberpunk-neon` | Hot pink + electric blue | #0a0a1a | 15 |
| 3 | `forest-dusk` | Deep forest greens + amber | #0f1a0f | 18 |
| 4 | `ocean-depth` | Deep teal + coral | #051622 | 14 |
| 5 | `sunset-haze` | Warm oranges + purple | #1a0a1e | 16 |
| 6 | `arctic-frost` | Cool whites + ice blue | #0c1b2a | 10 |
| 7 | `volcanic-ember` | Dark red + orange glow | #1a0808 | 15 |
| 8 | `lavender-dream` | Soft purples + silver | #14101e | 20 |
| 9 | `tokyo-night` | Inspired by Tokyo Night | #1a1b26 | 12 |
| 10 | `copper-patina` | Warm bronze + verdigris | #1a1410 | 14 |
| 11 | `synthwave` | Retro 80s neon | #0e0e2c | 18 |
| 12 | `monochrome-silk` | Elegant grayscale | #111111 | 10 |
| 13 | `catppuccin-mocha` | Catppuccin warm pastels | #1e1e2e | 12 |
| 14 | `rose-pine` | Muted rose + pine | #191724 | 14 |
| 15 | `dracula-glass` | Dracula with glass effect | #1e1f29 | 20 |

### Execution Steps

1. **Determine theme**: If `list` -> display table and exit. If `reset` -> send reset sequence. If name given -> use that theme. Otherwise -> pick random from list.

2. **Determine alpha**: If `--alpha N` provided -> use N. Otherwise -> use theme's default alpha.

3. **Apply colors via iTerm2 escape sequences**:

   iTerm2 proprietary escape sequences use this format:
   ```
   \033]1337;SetColors=key=RRGGBB\007
   ```

   Keys: `bg`, `fg`, `bold`, `link`, `selbg`, `selfg`, `curbg`, `curfg`, `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, `br_black`, `br_red`, `br_green`, `br_yellow`, `br_blue`, `br_magenta`, `br_cyan`, `br_white`

   **Apply transparency** via:
   ```
   \033]1337;SetBackgroundAlpha=0.85\007
   ```
   (where 0.85 = 15% transparency, formula: `(100 - alpha_percent) / 100`)

4. **Build and execute the script**:

   Create a bash script that sends all escape sequences:

   ```bash
   #!/bin/bash
   # iTerm2 color scheme applicator

   set_color() {
     printf "\033]1337;SetColors=%s=%s\007" "$1" "$2"
   }

   set_alpha() {
     printf "\033]1337;SetBackgroundAlpha=%s\007" "$1"
   }

   # Apply each color key
   set_color bg RRGGBB
   set_color fg RRGGBB
   set_color selbg RRGGBB
   set_color selfg RRGGBB
   set_color curbg RRGGBB
   set_color curfg RRGGBB
   set_color black RRGGBB
   set_color red RRGGBB
   set_color green RRGGBB
   set_color yellow RRGGBB
   set_color blue RRGGBB
   set_color magenta RRGGBB
   set_color cyan RRGGBB
   set_color white RRGGBB
   set_color br_black RRGGBB
   set_color br_red RRGGBB
   set_color br_green RRGGBB
   set_color br_yellow RRGGBB
   set_color br_blue RRGGBB
   set_color br_magenta RRGGBB
   set_color br_cyan RRGGBB
   set_color br_white RRGGBB

   # Apply transparency
   set_alpha 0.85
   ```

5. **Display confirmation**:

   ```
   Theme: [name] applied
   ├─ Background: #RRGGBB
   ├─ Foreground: #RRGGBB
   ├─ Transparency: XX%
   └─ Palette: [vibe description]

   Tip: /iterm2-theme to roll again, /iterm2-theme reset to restore defaults
   ```

### Theme Definitions (Full Color Values)

Use these exact hex values (without #) when generating the script:

**1. midnight-aurora**
```
bg=0d1117  fg=c9d1d9  selbg=1f3a5f  selfg=e6edf3  curbg=58a6ff  curfg=0d1117
black=484f58  red=ff7b72  green=3fb950  yellow=d29922  blue=58a6ff  magenta=bc8cff  cyan=39d2c0  white=c9d1d9
br_black=6e7681  br_red=ffa198  br_green=56d364  br_yellow=e3b341  br_blue=79c0ff  br_magenta=d2a8ff  br_cyan=56d4dd  br_white=f0f6fc
```

**2. cyberpunk-neon**
```
bg=0a0a1a  fg=e0e0ff  selbg=3d1f5c  selfg=ff79c6  curbg=ff2975  curfg=0a0a1a
black=2a2a3a  red=ff2975  green=05ffa1  yellow=f1fa8c  blue=00b4d8  magenta=bd93f9  cyan=8be9fd  white=e0e0ff
br_black=4a4a5a  br_red=ff6eb4  br_green=69ff94  br_yellow=ffffa5  br_blue=48cae4  br_magenta=d6bcfa  br_cyan=a4f4fd  br_white=f8f8ff
```

**3. forest-dusk**
```
bg=0f1a0f  fg=c4c9a5  selbg=2d4a2d  selfg=e8e8d0  curbg=a3be8c  curfg=0f1a0f
black=2e3429  red=c25d5d  green=a3be8c  yellow=ebcb8b  blue=5e81ac  magenta=b48ead  cyan=8fbcbb  white=c4c9a5
br_black=4c5646  br_red=d08770  br_green=b5d19c  br_yellow=f0d9a0  br_blue=81a1c1  br_magenta=c9a4c0  br_cyan=a3d1cf  br_white=eceff4
```

**4. ocean-depth**
```
bg=051622  fg=bcd4e6  selbg=0e3b5e  selfg=e0f0ff  curbg=1282a2  curfg=ffffff
black=0a2944  red=e74c3c  green=2ecc71  yellow=f39c12  blue=1282a2  magenta=9b59b6  cyan=1abc9c  white=bcd4e6
br_black=1a4a6e  br_red=ff6b6b  br_green=55efc4  br_yellow=feca57  br_blue=48dbfb  br_magenta=c39bd3  br_cyan=48dbfb  br_white=dfe6e9
```

**5. sunset-haze**
```
bg=1a0a1e  fg=e8d5c4  selbg=3d1f4a  selfg=ffeedd  curbg=ff6b6b  curfg=1a0a1e
black=2d1633  red=ff6b6b  green=95e6a0  yellow=ffd93d  blue=6c5ce7  magenta=fd79a8  cyan=81ecec  white=e8d5c4
br_black=4a2d55  br_red=ff9b9b  br_green=a8e6cf  br_yellow=ffe69a  br_blue=a29bfe  br_magenta=fab1c0  br_cyan=a8e6e6  br_white=ffeef0
```

**6. arctic-frost**
```
bg=0c1b2a  fg=d8dee9  selbg=2e3440  selfg=eceff4  curbg=88c0d0  curfg=0c1b2a
black=2e3440  red=bf616a  green=a3be8c  yellow=ebcb8b  blue=81a1c1  magenta=b48ead  cyan=88c0d0  white=d8dee9
br_black=4c566a  br_red=d08770  br_green=a3be8c  br_yellow=ebcb8b  br_blue=5e81ac  br_magenta=b48ead  br_cyan=8fbcbb  br_white=eceff4
```

**7. volcanic-ember**
```
bg=1a0808  fg=e8c4b8  selbg=3d1515  selfg=ffe0d0  curbg=ff4500  curfg=ffffff
black=2d1010  red=ff4500  green=7cba3a  yellow=ffb347  blue=4a90d9  magenta=c76b98  cyan=5bc0be  white=e8c4b8
br_black=4a2020  br_red=ff6a33  br_green=98d35e  br_yellow=ffc97a  br_blue=6ab0f3  br_magenta=e08bab  br_cyan=7dd3d1  br_white=ffeee6
```

**8. lavender-dream**
```
bg=14101e  fg=d0c8e0  selbg=2d2540  selfg=efe8ff  curbg=9d8ec7  curfg=14101e
black=1e1830  red=e06c75  green=98c379  yellow=e5c07b  blue=7c9dec  magenta=c678dd  cyan=56b6c2  white=d0c8e0
br_black=3a3350  br_red=e88e94  br_green=afd49b  br_yellow=ecd19e  br_blue=9bb4f0  br_magenta=d49ee5  br_cyan=7bc8d2  br_white=efe8ff
```

**9. tokyo-night**
```
bg=1a1b26  fg=a9b1d6  selbg=33467c  selfg=c0caf5  curbg=c0caf5  curfg=1a1b26
black=15161e  red=f7768e  green=9ece6a  yellow=e0af68  blue=7aa2f7  magenta=bb9af7  cyan=7dcfff  white=a9b1d6
br_black=414868  br_red=ff9e9e  br_green=b9f27c  br_yellow=ffc777  br_blue=89b4ff  br_magenta=c9a8ff  br_cyan=b4f9f8  br_white=c0caf5
```

**10. copper-patina**
```
bg=1a1410  fg=d4c5a9  selbg=3a2e22  selfg=f0e6d0  curbg=c08040  curfg=1a1410
black=2a2018  red=cc6633  green=669966  yellow=c08040  blue=557799  magenta=996688  cyan=5f9ea0  white=d4c5a9
br_black=4a3a2e  br_red=e08050  br_green=88bb88  br_yellow=d4a060  br_blue=77aabb  br_magenta=bb88aa  br_cyan=7fbfbf  br_white=f0e6d0
```

**11. synthwave**
```
bg=0e0e2c  fg=e0d0ff  selbg=2a1f5e  selfg=ff00ff  curbg=ff2cf1  curfg=0e0e2c
black=1a1a40  red=fe4450  green=72f1b8  yellow=fede5d  blue=2ee2fa  magenta=ff7edb  cyan=03edf9  white=e0d0ff
br_black=3a3a60  br_red=ff6b7a  br_green=92ffd0  br_yellow=fff490  br_blue=6ef5ff  br_magenta=ffa8e8  br_cyan=40f4ff  br_white=f5f0ff
```

**12. monochrome-silk**
```
bg=111111  fg=cccccc  selbg=333333  selfg=ffffff  curbg=aaaaaa  curfg=111111
black=1a1a1a  red=999999  green=aaaaaa  yellow=bbbbbb  blue=888888  magenta=999999  cyan=aaaaaa  white=cccccc
br_black=444444  br_red=bbbbbb  br_green=cccccc  br_yellow=dddddd  br_blue=aaaaaa  br_magenta=bbbbbb  br_cyan=cccccc  br_white=eeeeee
```

**13. catppuccin-mocha**
```
bg=1e1e2e  fg=cdd6f4  selbg=45475a  selfg=cdd6f4  curbg=f5e0dc  curfg=1e1e2e
black=45475a  red=f38ba8  green=a6e3a1  yellow=f9e2af  blue=89b4fa  magenta=cba6f7  cyan=94e2d5  white=cdd6f4
br_black=585b70  br_red=f38ba8  br_green=a6e3a1  br_yellow=f9e2af  br_blue=89b4fa  br_magenta=cba6f7  br_cyan=94e2d5  br_white=a6adc8
```

**14. rose-pine**
```
bg=191724  fg=e0def4  selbg=403d52  selfg=e0def4  curbg=ebbcba  curfg=191724
black=26233a  red=eb6f92  green=31748f  yellow=f6c177  blue=9ccfd8  magenta=c4a7e7  cyan=9ccfd8  white=e0def4
br_black=6e6a86  br_red=eb6f92  br_green=31748f  br_yellow=f6c177  br_blue=9ccfd8  br_magenta=c4a7e7  br_cyan=9ccfd8  br_white=e0def4
```

**15. dracula-glass**
```
bg=1e1f29  fg=f8f8f2  selbg=44475a  selfg=f8f8f2  curbg=f8f8f2  curfg=282a36
black=21222c  red=ff5555  green=50fa7b  yellow=f1fa8c  blue=6272a4  magenta=bd93f9  cyan=8be9fd  white=f8f8f2
br_black=545763  br_red=ff6e6e  br_green=69ff94  br_yellow=ffffa5  br_blue=8694c7  br_magenta=d6acff  br_cyan=a4ffff  br_white=ffffff
```

### Reset Sequence

To reset to default iTerm2 profile:
```bash
# Reset all colors to profile defaults
printf "\033]1337;SetColors=preset=Default\007"
# Reset alpha to fully opaque
printf "\033]1337;SetBackgroundAlpha=1.0\007"
```

### Error Handling

- If not running in iTerm2 (check `$TERM_PROGRAM`), warn user but attempt anyway
- If theme name not found, list available themes and exit

</iterm2-theme>

## Notes

- Changes are session-only - closing the tab reverts to profile defaults
- Transparency requires "Background Image" or transparency support in iTerm2 Preferences
- Works with iTerm2 3.0+ (escape sequence support)
- Colors apply instantly, no restart needed
