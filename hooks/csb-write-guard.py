#!/usr/bin/env python3
"""
CSB Write Guard - PreToolUse Hook for Write Tool

Checks taint status before allowing Write operations.
- CRITICAL taint: HARD BLOCK (exit 2)
- HIGH taint: Request permission (permissionDecision: ask)
- Cleared taint: Allow operation
"""

import json
import sys
import os

# Import taint manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from csb_taint_manager import check_taint, format_block_message, format_ask_message
    TAINT_MANAGER_AVAILABLE = True
except ImportError:
    TAINT_MANAGER_AVAILABLE = False


def main():
    """Main entry point."""
    # Read hook input
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, allow tool

    tool_name = input_data.get("tool_name", "")

    # Only guard Write tool
    if tool_name != "Write":
        sys.exit(0)

    # Skip if taint manager not available
    if not TAINT_MANAGER_AVAILABLE:
        sys.exit(0)

    session_id = input_data.get("session_id", "unknown")
    tool_input = input_data.get("tool_input", {})
    target = tool_input.get("file_path", "unknown")

    # Check taint status
    taint = check_taint(session_id)

    # If not tainted or cleared, allow operation
    if not taint["tainted"] or taint["cleared"]:
        sys.exit(0)

    # CRITICAL: Hard block
    if taint["level"] == "CRITICAL":
        message = format_block_message(taint)
        print(message, file=sys.stderr)
        sys.exit(2)  # BLOCK operation

    # HIGH: Ask for permission
    if taint["level"] == "HIGH":
        message = format_ask_message(taint, "Write", target)
        print(message, file=sys.stderr)

        # Output JSON for permission dialog
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": f"CSB: Session contains HIGH risk content from {taint['source']}"
            }
        }
        print(json.dumps(response))
        sys.exit(0)

    # Default: allow
    sys.exit(0)


if __name__ == "__main__":
    main()
