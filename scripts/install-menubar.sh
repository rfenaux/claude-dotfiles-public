#!/usr/bin/env bash
# Install Claude Code Menu Bar Status Display
set -euo pipefail

PYTHON="${HOME}/.pyenv/versions/3.11.7/bin/python3"
MENUBAR_SCRIPT="$HOME/.claude/scripts/claude-menubar.py"
PLIST_DST="$HOME/Library/LaunchAgents/com.claude.menubar.plist"
LABEL="com.claude.menubar"
LOG_DIR="$HOME/.claude/logs"

echo "=== Claude Menu Bar Installer ==="
echo ""

# 1. Check Python
if [[ ! -x "$PYTHON" ]]; then
  echo "Python not found at $PYTHON"
  exit 1
fi
echo "Python: $PYTHON"

# 2. Install rumps
if "$PYTHON" -c "import rumps" 2>/dev/null; then
  echo "rumps: already installed"
else
  echo "Installing rumps..."
  "$PYTHON" -m pip install --quiet rumps || { echo "Failed to install rumps"; exit 1; }
  echo "rumps: installed"
fi

# 3. Check script
if [[ ! -f "$MENUBAR_SCRIPT" ]]; then
  echo "Menu bar script not found: $MENUBAR_SCRIPT"
  exit 1
fi
chmod +x "$MENUBAR_SCRIPT"
echo "Script: $MENUBAR_SCRIPT"

# 4. Log dir
mkdir -p "$LOG_DIR"

# 5. Unload if running
if launchctl list 2>/dev/null | grep -q "$LABEL"; then
  echo "Unloading existing service..."
  launchctl unload "$PLIST_DST" 2>/dev/null || true
fi

# 6. Create plist
cat > "$PLIST_DST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>$MENUBAR_SCRIPT</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
        <key>HOME</key>
        <string>${HOME}</string>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/menubar.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/menubar.log</string>
    <key>ProcessType</key>
    <string>Interactive</string>
    <key>ThrottleInterval</key>
    <integer>30</integer>
</dict>
</plist>
PLISTEOF
echo "Plist: $PLIST_DST"

# 7. Load
echo "Loading service..."
launchctl load "$PLIST_DST" || { echo "Failed to load service"; exit 1; }
sleep 2

if launchctl list 2>/dev/null | grep -q "$LABEL"; then
  echo "Service loaded successfully"
else
  echo "Service may not be running — check: tail -f $LOG_DIR/menubar.log"
fi

echo ""
echo "=== Done ==="
echo "Menu bar icon should appear shortly."
echo "Logs: tail -f $LOG_DIR/menubar.log"
echo "Uninstall: launchctl unload $PLIST_DST && rm $PLIST_DST"
