#!/usr/bin/env bash
# persistent-ctl.sh — Control the Persistent Space Daemon
# Usage: persistent-ctl.sh {status|start|stop|restart|logs|queue|test}
set -euo pipefail

DAEMON_PY="$HOME/.claude/persistent/daemon.py"
PLIST_NAME="com.claude.persistent-space"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
SOCKET_PATH="$HOME/.claude/persistent/daemon.sock"
PID_FILE="$HOME/.claude/persistent/daemon.pid"
LOG_FILE="$HOME/.claude/logs/persistent-daemon.log"
QUEUE_FILE="$HOME/.claude/persistent/queue.json"
PYTHON="$(command -v python3 2>/dev/null || echo /usr/bin/python3)"

# --- Helpers ---

is_running() {
  if [[ -f "$PID_FILE" ]]; then
    local pid
    pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
      return 0
    fi
  fi
  return 1
}

ipc_command() {
  local cmd="$1"
  if [[ ! -S "$SOCKET_PATH" ]]; then
    echo "Error: Daemon not running (no socket)" >&2
    return 1
  fi
  # Use Python for reliable Unix socket communication
  "$PYTHON" -c "
import socket, sys
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
try:
    s.connect('$SOCKET_PATH')
    s.sendall(b'$cmd')
    data = s.recv(65536)
    print(data.decode('utf-8'))
except ConnectionRefusedError:
    print('{\"error\": \"Connection refused - daemon may be shutting down\"}')
finally:
    s.close()
"
}

# --- Commands ---

cmd_status() {
  if is_running; then
    local pid
    pid=$(cat "$PID_FILE")
    echo "Daemon: RUNNING (PID $pid)"

    # Get detailed status via IPC
    if [[ -S "$SOCKET_PATH" ]]; then
      local status
      status=$(ipc_command "status" 2>/dev/null || echo '{}')
      echo ""
      echo "$status" | "$PYTHON" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    q = d.get('queue', {})
    uptime = d.get('uptime_seconds', 0)
    h, m = divmod(uptime // 60, 60)
    print(f'  Uptime: {h}h {m}m')
    print(f'  Queue: {q.get(\"total\", 0)} total, {q.get(\"pending\", 0)} pending, {q.get(\"running\", 0)} running')
    print(f'  Completed: {q.get(\"completed\", 0)}, Failed: {q.get(\"failed\", 0)}')
except:
    print('  (Could not parse status)')
"
    fi
  else
    echo "Daemon: STOPPED"

    # Show queue stats even when stopped
    if [[ -f "$QUEUE_FILE" ]]; then
      local pending
      pending=$("$PYTHON" -c "
import json
with open('$QUEUE_FILE') as f:
    tasks = json.load(f).get('tasks', [])
pending = sum(1 for t in tasks if t.get('status') == 'pending')
print(f'{pending} pending task(s) in queue')
" 2>/dev/null || echo "Queue exists but unreadable")
      echo "  $pending"
    fi
  fi
}

cmd_start() {
  if is_running; then
    echo "Daemon already running (PID $(cat "$PID_FILE"))"
    return 0
  fi

  # Try launchd first
  if [[ -f "$PLIST_PATH" ]]; then
    echo "Starting via launchd..."
    launchctl load "$PLIST_PATH" 2>/dev/null || true
    sleep 2
    if is_running; then
      echo "Daemon started (PID $(cat "$PID_FILE"))"
    else
      echo "launchd load failed, starting directly..."
      _start_direct
    fi
  else
    _start_direct
  fi
}

_start_direct() {
  echo "Starting daemon directly..."
  nohup "$PYTHON" "$DAEMON_PY" >> "$LOG_FILE" 2>&1 &
  local pid=$!
  sleep 1
  if kill -0 "$pid" 2>/dev/null; then
    echo "Daemon started (PID $pid)"
  else
    echo "Error: Daemon failed to start. Check $LOG_FILE" >&2
    return 1
  fi
}

cmd_stop() {
  if ! is_running; then
    echo "Daemon not running"
    return 0
  fi

  local pid
  pid=$(cat "$PID_FILE")

  # Try graceful shutdown via IPC
  if [[ -S "$SOCKET_PATH" ]]; then
    echo "Sending shutdown via IPC..."
    ipc_command "shutdown" >/dev/null 2>&1 || true
    sleep 2
  fi

  # Check if still running
  if kill -0 "$pid" 2>/dev/null; then
    echo "Sending SIGTERM..."
    kill "$pid" 2>/dev/null || true
    sleep 2
  fi

  # Force kill if needed
  if kill -0 "$pid" 2>/dev/null; then
    echo "Force killing..."
    kill -9 "$pid" 2>/dev/null || true
  fi

  # Cleanup
  [[ -f "$PID_FILE" ]] && rm "$PID_FILE"
  [[ -S "$SOCKET_PATH" ]] && rm "$SOCKET_PATH"
  echo "Daemon stopped"
}

cmd_restart() {
  cmd_stop
  sleep 1
  cmd_start
}

cmd_logs() {
  local lines="${1:-50}"
  if [[ -f "$LOG_FILE" ]]; then
    tail -n "$lines" "$LOG_FILE"
  else
    echo "No log file found at $LOG_FILE"
  fi
}

cmd_queue() {
  if [[ ! -f "$QUEUE_FILE" ]]; then
    echo "No queue file found"
    return 0
  fi

  "$PYTHON" -c "
import json
from datetime import datetime

with open('$QUEUE_FILE') as f:
    data = json.load(f)

tasks = data.get('tasks', [])
if not tasks:
    print('Queue empty')
else:
    print(f'Queue: {len(tasks)} task(s)\n')
    for t in tasks:
        status = t.get('status', 'unknown')
        icon = {'pending': '⏳', 'running': '🔄', 'completed': '✅', 'failed': '❌'}.get(status, '❓')
        sched = t.get('trigger', {}).get('schedule', 'N/A')
        level = t.get('authorization', {}).get('level', '?')
        print(f'  {icon} {t[\"id\"]} | L{level} | {status} | {t.get(\"title\", \"untitled\")}')
        print(f'     Scheduled: {sched}')
        if t.get('result_path'):
            print(f'     Results: {t[\"result_path\"]}')
        print()
"
}

cmd_install() {
  echo "Installing launchd service..."

  mkdir -p "$(dirname "$PLIST_PATH")"

  cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON}</string>
        <string>${DAEMON_PY}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>60</integer>
    <key>StandardOutPath</key>
    <string>${LOG_FILE}</string>
    <key>StandardErrorPath</key>
    <string>${LOG_FILE}</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:${HOME}/.local/bin:${HOME}/.pyenv/shims</string>
    </dict>
</dict>
</plist>
PLIST

  echo "Created $PLIST_PATH"
  echo "Loading service..."
  launchctl load "$PLIST_PATH" 2>/dev/null || true
  sleep 2
  cmd_status
}

cmd_uninstall() {
  if [[ -f "$PLIST_PATH" ]]; then
    echo "Unloading service..."
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    rm "$PLIST_PATH"
    echo "Service uninstalled"
  else
    echo "Service not installed"
  fi
  cmd_stop
}

cmd_test() {
  echo "Running daemon self-test..."
  "$PYTHON" "$DAEMON_PY" --test
}

cmd_approvals() {
  local approvals_dir="$HOME/.claude/persistent/approvals"
  if [[ ! -d "$approvals_dir" ]]; then
    echo "No approvals directory found"
    return 0
  fi

  # Try IPC first (daemon may have fresher state)
  if [[ -S "$SOCKET_PATH" ]]; then
    ipc_command "approvals" 2>/dev/null | "$PYTHON" -c "
import sys, json
try:
    data = json.load(sys.stdin)
    approvals = data.get('approvals', [])
    if not approvals:
        print('No pending approvals')
    else:
        print(f'{len(approvals)} pending approval(s):\n')
        for a in approvals:
            print(f'  \u26a0\ufe0f  {a[\"task_id\"]}')
            print(f'     Title: {a.get(\"title\", \"untitled\")}')
            print(f'     Prompt: {a.get(\"prompt\", \"\")[:80]}...' if len(a.get('prompt', '')) > 80 else f'     Prompt: {a.get(\"prompt\", \"\")}')
            print(f'     Created: {a.get(\"created_at\", \"?\")}')
            print()
except:
    print('(Could not parse approvals from daemon)')
" && return 0
  fi

  # Fallback: read files directly
  "$PYTHON" -c "
import json, os, glob

approvals_dir = '$approvals_dir'
files = glob.glob(os.path.join(approvals_dir, '*.json'))
pending = []
for f in files:
    try:
        with open(f) as fh:
            d = json.load(fh)
        if d.get('status') == 'pending':
            pending.append(d)
    except:
        continue

if not pending:
    print('No pending approvals')
else:
    print(f'{len(pending)} pending approval(s):\n')
    for a in pending:
        print(f'  \u26a0\ufe0f  {a[\"task_id\"]}')
        print(f'     Title: {a.get(\"title\", \"untitled\")}')
        prompt = a.get('prompt', '')
        print(f'     Prompt: {prompt[:80]}...' if len(prompt) > 80 else f'     Prompt: {prompt}')
        print(f'     Created: {a.get(\"created_at\", \"?\")}')
        print()
"
}

cmd_approve() {
  local task_id="$1"
  if [[ -z "$task_id" ]]; then
    echo "Usage: persistent-ctl.sh approve <task-id>" >&2
    return 1
  fi

  # Try IPC first
  if [[ -S "$SOCKET_PATH" ]]; then
    local result
    result=$(ipc_command "approve $task_id" 2>/dev/null)
    echo "$result" | "$PYTHON" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('status') == 'approved':
        print(f'Approved: {d[\"task_id\"]}')
        print('Task will execute on next daemon poll cycle.')
    elif d.get('error'):
        print(f'Error: {d[\"error\"]}')
    else:
        print(json.dumps(d, indent=2))
except:
    print('(Unexpected response)')
" && return 0
  fi

  # Fallback: write approval file directly
  local approval_file="$HOME/.claude/persistent/approvals/${task_id}.json"
  if [[ ! -f "$approval_file" ]]; then
    echo "Error: No approval request found for $task_id" >&2
    return 1
  fi

  "$PYTHON" -c "
import json
from datetime import datetime

with open('$approval_file') as f:
    data = json.load(f)

data['status'] = 'approved'
data['approved_at'] = datetime.now().isoformat()

with open('$approval_file', 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f'Approved: $task_id')
print('Task will execute on next daemon poll cycle.')
"
}

cmd_deny() {
  local task_id="$1"
  if [[ -z "$task_id" ]]; then
    echo "Usage: persistent-ctl.sh deny <task-id>" >&2
    return 1
  fi

  # Try IPC first
  if [[ -S "$SOCKET_PATH" ]]; then
    local result
    result=$(ipc_command "deny $task_id" 2>/dev/null)
    echo "$result" | "$PYTHON" -c "
import sys, json
try:
    d = json.load(sys.stdin)
    if d.get('status') == 'denied':
        print(f'Denied: {d[\"task_id\"]}')
        print('Task will not be executed.')
    elif d.get('error'):
        print(f'Error: {d[\"error\"]}')
    else:
        print(json.dumps(d, indent=2))
except:
    print('(Unexpected response)')
" && return 0
  fi

  # Fallback: write denial directly
  local approval_file="$HOME/.claude/persistent/approvals/${task_id}.json"
  if [[ ! -f "$approval_file" ]]; then
    echo "Error: No approval request found for $task_id" >&2
    return 1
  fi

  "$PYTHON" -c "
import json
from datetime import datetime

with open('$approval_file') as f:
    data = json.load(f)

data['status'] = 'denied'
data['denied_at'] = datetime.now().isoformat()

with open('$approval_file', 'w') as f:
    json.dump(data, f, indent=2, default=str)

print(f'Denied: $task_id')
print('Task will not be executed.')
"
}

# --- Router ---

case "${1:-help}" in
  status)     cmd_status ;;
  start)      cmd_start ;;
  stop)       cmd_stop ;;
  restart)    cmd_restart ;;
  logs)       shift; cmd_logs "${1:-50}" ;;
  queue)      cmd_queue ;;
  approvals)  cmd_approvals ;;
  approve)    shift; cmd_approve "${1:-}" ;;
  deny)       shift; cmd_deny "${1:-}" ;;
  install)    cmd_install ;;
  uninstall)  cmd_uninstall ;;
  test)       cmd_test ;;
  help|--help|-h)
    echo "Usage: persistent-ctl.sh {status|start|stop|restart|logs|queue|approvals|approve|deny|install|uninstall|test}"
    echo ""
    echo "Commands:"
    echo "  status        Show daemon state and queue stats"
    echo "  start         Start the daemon (launchd or direct)"
    echo "  stop          Stop the daemon gracefully"
    echo "  restart       Restart the daemon"
    echo "  logs [N]      Show last N log lines (default: 50)"
    echo "  queue         Show task queue"
    echo "  approvals     List pending Level 3 approvals"
    echo "  approve <id>  Approve a Level 3 task"
    echo "  deny <id>     Deny a Level 3 task"
    echo "  install       Install launchd service"
    echo "  uninstall     Remove launchd service"
    echo "  test          Run self-test"
    ;;
  *)
    echo "Unknown command: $1. Use --help for usage." >&2
    exit 1
    ;;
esac
