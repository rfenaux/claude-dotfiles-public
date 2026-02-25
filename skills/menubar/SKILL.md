---
name: menubar
description: Manage macOS menu bar status app from within Claude sessions
---

# /menubar — Claude Menubar App Control

Manage the macOS menu bar status app from within Claude sessions.

## Usage

| Command | Action |
|---------|--------|
| `/menubar` | Show menubar app status (running? PID?) |
| `/menubar start` | Start the menubar app |
| `/menubar stop` | Stop the menubar app |
| `/menubar restart` | Stop + start |
| `/menubar config` | Show current configuration |
| `/menubar config set <key> <value>` | Update a config value |

## Instructions

When the user runs `/menubar` or `/menubar <subcommand>`, execute the appropriate action:

### `/menubar` (no args) — Status

```bash
# Check if running
PID=$(pgrep -f "claude-menubar.py" 2>/dev/null)
if [ -n "$PID" ]; then
  echo "Menubar: RUNNING (PID $PID)"
else
  echo "Menubar: STOPPED"
fi
```

Report the result to the user.

### `/menubar start`

```bash
# Check if already running
PID=$(pgrep -f "claude-menubar.py" 2>/dev/null)
if [ -n "$PID" ]; then
  echo "Already running (PID $PID)"
else
  nohup python3 ~/.claude/scripts/claude-menubar.py > /tmp/claude-menubar.log 2>&1 &
  sleep 1
  NEW_PID=$(pgrep -f "claude-menubar.py" 2>/dev/null)
  echo "Started (PID $NEW_PID)"
fi
```

### `/menubar stop`

```bash
pkill -f "claude-menubar.py" 2>/dev/null && echo "Stopped" || echo "Not running"
```

### `/menubar restart`

```bash
pkill -f "claude-menubar.py" 2>/dev/null
sleep 1
nohup python3 ~/.claude/scripts/claude-menubar.py > /tmp/claude-menubar.log 2>&1 &
sleep 1
NEW_PID=$(pgrep -f "claude-menubar.py" 2>/dev/null)
echo "Restarted (PID $NEW_PID)"
```

### `/menubar config`

Read and display `~/.claude/config/menubar-config.json` formatted as a table showing:
- Icon: enabled, thresholds
- Notifications: enabled, cooldown, sound, each type's status
- Menu: max sessions, show agents, quick actions

### `/menubar config set <key> <value>`

Update a value in `~/.claude/config/menubar-config.json` using dot-notation keys.

Examples:
- `/menubar config set notifications.sound false`
- `/menubar config set icon.thresholds.yellow 75`
- `/menubar config set menu.max_sessions_shown 10`

Use Python to traverse the JSON, update the value, and write back:

```python
import json
config_path = Path.home() / ".claude" / "config" / "menubar-config.json"
with open(config_path) as f:
    config = json.load(f)

# Navigate dot-notation key
keys = key.split(".")
obj = config
for k in keys[:-1]:
    obj = obj[k]
obj[keys[-1]] = parsed_value  # auto-parse bool/int/float/str

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)
```

After any config change, suggest: "Restart the menubar to apply: `/menubar restart`"
