#!/usr/bin/env python3
"""gemini-routing-hook.py - PreToolUse hook for auto-routing bulk ops to Gemini.

Part of: TOOL-003 PRD
Created: 2026-02-14
Event: PreToolUse (Grep|Glob|Read)

Detects bulk/exploratory tool use patterns and suggests delegating to
gemini-delegate agent. Returns additionalContext when triggered.

Trigger detection:
- Broad glob patterns (e.g., **/*.py on large dirs)
- Read operations on many files (tracked via state file)
- User intent keywords in tool context

Safety: Blocks routing for sensitive paths/content per gemini-routing.json.
"""

import json
import os
import sys
import time
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude" / "config" / "gemini-routing.json"
STATE_FILE = Path("/tmp/gemini-routing-state.json")
STATE_TTL = 10  # seconds


def load_config():
    """Load routing config."""
    try:
        return json.loads(CONFIG_PATH.read_text())
    except Exception:
        return {}


def load_state():
    """Load recent tool call state for counting."""
    try:
        if STATE_FILE.exists():
            data = json.loads(STATE_FILE.read_text())
            # Prune old entries
            now = time.time()
            data["calls"] = [
                c for c in data.get("calls", [])
                if now - c.get("ts", 0) < STATE_TTL
            ]
            return data
    except Exception:
        pass
    return {"calls": [], "suggested_this_session": False}


def save_state(state):
    """Save state atomically."""
    try:
        tmp = str(STATE_FILE) + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.rename(tmp, str(STATE_FILE))
    except Exception:
        pass


def check_safety(config, tool_input, tool_name):
    """Check safety blacklists. Returns True if safe to route."""
    safety = config.get("safety", {})

    # Check blacklisted tools
    if tool_name in safety.get("blacklist_tools", []):
        return False

    # Check paths for sensitive content
    input_str = json.dumps(tool_input).lower()
    for keyword in safety.get("blacklist_keywords", []):
        if keyword.lower() in input_str:
            return False

    # Check path blacklists
    file_path = tool_input.get("file_path", "") or tool_input.get("path", "") or ""
    for blocked_path in safety.get("blacklist_paths", []):
        if blocked_path in file_path:
            return False

    for blocked_dir in safety.get("blacklist_directories", []):
        expanded = os.path.expanduser(blocked_dir)
        if file_path.startswith(expanded):
            return False

    return True


def check_triggers(config, tool_name, tool_input, state):
    """Check if current tool call triggers Gemini routing."""
    triggers = config.get("triggers", [])
    matched = []

    for trigger in triggers:
        trigger_tool = trigger.get("tool", "*")
        if trigger_tool != "*" and trigger_tool != tool_name:
            continue

        name = trigger.get("name", "")

        # Broad glob pattern detection
        if name == "exploratory_glob" and tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            if "**/" in pattern and pattern.count("*") >= 2:
                path = tool_input.get("path", "")
                # Only trigger for broad project-wide searches
                if not path or path in ("/", os.path.expanduser("~")):
                    matched.append(trigger)

        # Bulk file read tracking
        elif name == "bulk_file_read" and tool_name == "Read":
            threshold = trigger.get("threshold", {})
            min_count = threshold.get("file_count", 5)
            recent_reads = [
                c for c in state.get("calls", [])
                if c.get("tool") == "Read"
            ]
            if len(recent_reads) + 1 >= min_count:
                matched.append(trigger)

        # User intent keywords (check in tool input text)
        elif name == "user_intent_bulk":
            keywords = trigger.get("keywords", [])
            input_text = json.dumps(tool_input).lower()
            for kw in keywords:
                if kw.lower() in input_text:
                    matched.append(trigger)
                    break

    return matched


def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only process relevant tools
    if tool_name not in ("Read", "Grep", "Glob"):
        sys.exit(0)

    config = load_config()
    if not config.get("enabled", False):
        sys.exit(0)

    # Check override
    override = config.get("override", {})
    env_var = override.get("env_var", "")
    if env_var and os.environ.get(env_var) == "0":
        sys.exit(0)

    # Safety check first
    if not check_safety(config, tool_input, tool_name):
        sys.exit(0)

    # Load and update state
    state = load_state()
    state["calls"].append({
        "tool": tool_name,
        "ts": time.time()
    })

    # Check triggers
    matched = check_triggers(config, tool_name, tool_input, state)

    # Don't suggest twice in same burst
    if matched and not state.get("suggested_this_session", False):
        state["suggested_this_session"] = True
        save_state(state)

        reasons = [t.get("reason", "bulk operation detected") for t in matched]
        reason_text = "; ".join(reasons)

        print(json.dumps({
            "additionalContext": (
                f"[GEMINI-ROUTE] {reason_text}. "
                "Consider delegating this bulk operation to gemini-delegate agent "
                "(2M context window, web grounding). "
                "Use: Task tool with subagent_type='gemini-delegate'. "
                "Skip if: task needs MCP tools, involves sensitive files, "
                "or is a quick targeted lookup."
            )
        }))
    else:
        save_state(state)

    sys.exit(0)


if __name__ == "__main__":
    main()
