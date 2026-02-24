---
name: tmux-teams
description: Help with tmux setup for Agent Teams visual mode. Detects environment, explains current mode, and guides user to split-pane agent viewing.
async:
  mode: never
  require_sync:
    - environment detection
    - user guidance
---

# /tmux-teams - Agent Teams Visual Mode Helper

Help the user set up and use tmux for watching agent teams work in real-time.

## Trigger

Invoke when:
- User says `/tmux-teams`, "tmux help", "see agents working", "watch agents"
- User is confused about in-process vs tmux mode
- User wants to switch from invisible to visible agent teams
- Agent teams spawned but user can't see them

## Step 1: Detect Environment

Run these checks:

```bash
# Check if we're inside tmux already
echo "TMUX_ENV=${TMUX:-not_in_tmux}"

# Check if tmux is installed
which tmux 2>/dev/null && tmux -V || echo "TMUX_NOT_INSTALLED"

# Check if tmux config exists
ls -la ~/.tmux.conf 2>/dev/null || echo "NO_TMUX_CONFIG"

# Check for running tmux sessions
tmux list-sessions 2>/dev/null || echo "NO_SESSIONS"
```

## Step 2: Report Status

Based on detection, tell user one of:

### A) Already in tmux
```
You're IN tmux right now. Agent teams will auto-use split-pane mode.
When you spawn teammates, each gets its own visible pane.

Navigate: Shift+Up/Down or Alt+Arrow
Watch: Just look at the other panes - agents work autonomously
Interact: Stay in YOUR pane (team lead). Use SendMessage to talk to teammates.
```

### B) Not in tmux, but it's installed
```
You're NOT in tmux. Agent teams will run in-process (invisible).

To switch to visual mode:
1. Exit Claude Code (Ctrl+C or /exit)
2. Start tmux:  tmux new -s claude
3. Re-launch:   claude
4. Now agent teams will use split-pane mode automatically!

To reattach to existing session: tmux attach -t claude
```

### C) tmux not installed
```
tmux is not installed. Install it:
  brew install tmux

Then create config:
  (offer to create ~/.tmux.conf)
```

## Step 3: Quick Reference Card

Always show this:

```
TMUX CHEAT SHEET (prefix = Ctrl+A)
------------------------------------
Ctrl+A then d     Detach (session keeps running)
tmux attach -t X  Reattach to session X
Alt+Arrow          Switch between panes (no prefix)
Shift+Up/Down     Switch panes (Agent Teams default)
Ctrl+A then |     Split pane horizontally
Ctrl+A then -     Split pane vertically
Ctrl+A then z     Zoom current pane (toggle fullscreen)
Ctrl+A then r     Reload tmux config
Mouse scroll      Scroll pane history
Ctrl+A then [     Enter scroll mode (q to exit)

AGENT TEAMS IN TMUX
------------------------------------
- Each teammate = 1 visible pane
- YOU stay in the team lead pane
- Agents are autonomous (read-only viewing)
- Communicate via SendMessage tool only
- Shift+Up/Down to observe different agents
```

## Common Issues

| Problem | Fix |
|---------|-----|
| Agents spawn but no new panes | You're not in tmux. Start tmux first. |
| Can't type in agent's pane | Correct! Agents are autonomous. Talk via SendMessage. |
| Panes too small | `Ctrl+A` then `z` to zoom one pane. Or resize iTerm2 window. |
| Want to go back to invisible mode | Exit tmux, run Claude Code directly. |
| tmux config not loading | Run `tmux source-file ~/.tmux.conf` inside tmux. |
| Session detached accidentally | `tmux attach -t claude` to reconnect. |
