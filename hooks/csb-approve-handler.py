#!/usr/bin/env python3
"""
CSB Approve Handler - UserPromptSubmit Hook

Detects "csb approve" commands in user messages and clears session taint.
This enables the blocking guards to allow Write/Edit/Bash operations.
"""

import json
import sys
import os
import re

# Import taint manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from csb_taint_manager import clear_taint, check_taint
    TAINT_MANAGER_AVAILABLE = True
except ImportError:
    TAINT_MANAGER_AVAILABLE = False

# Approval patterns (case insensitive)
APPROVE_PATTERNS = [
    r"^\s*csb\s+approve\s*$",
    r"^\s*approve\s+all\s*$",
    r"^\s*clear\s+taint\s*$",
    r"^\s*csb\s+clear\s*$",
]


def main():
    """Main entry point."""
    if not TAINT_MANAGER_AVAILABLE:
        sys.exit(0)

    # Read hook input
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    # Get user message
    user_message = input_data.get("user_message", "")
    if not user_message:
        # Try alternate field names
        user_message = input_data.get("message", "")
        if not user_message:
            user_message = input_data.get("prompt", "")

    session_id = input_data.get("session_id", "unknown")

    # Check if this is an approval command
    for pattern in APPROVE_PATTERNS:
        if re.match(pattern, user_message.strip(), re.IGNORECASE):
            # Check if session is actually tainted
            taint_status = check_taint(session_id)

            if taint_status["tainted"]:
                # Clear the taint
                success = clear_taint(session_id, cleared_by="user_command")

                if success:
                    print(f"[CSB] ✅ Session taint CLEARED. Write/Edit/Bash operations now allowed.", file=sys.stderr)
                else:
                    print(f"[CSB] ⚠️ Failed to clear taint. Try: rm /tmp/claude-csb-taint-{session_id}.json", file=sys.stderr)
            else:
                print(f"[CSB] ℹ️ Session not tainted. No action needed.", file=sys.stderr)

            break

    sys.exit(0)


if __name__ == "__main__":
    main()
