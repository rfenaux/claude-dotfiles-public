#!/usr/bin/env python3
"""CSB False-Positive Preventer - PreToolUse hook for Bash commands.
Detects patterns likely to trigger Content Security Buffer false positives
and provides advisory warnings with safer alternatives. Exit 0 always."""

import json
import sys
import re

# Patterns that commonly trigger CSB false positives
# Each: (compiled_regex, description, alternative)
FP_PATTERNS = [
    # ANSI escape codes
    (re.compile(r'ls\s+--color'), "ls --color (ANSI escapes)", "Use ls without --color, or pipe through cat"),
    (re.compile(r'\btput\b'), "tput (terminal control)", "Avoid tput in non-interactive context"),
    (re.compile(r'printf.*\\e\['), "printf with ANSI escapes", "Write to file first, then cat"),
    (re.compile(r'echo.*\\033'), "echo with octal escapes", "Use plain echo or write to file"),
    # Conversation exports
    (re.compile(r'cat\s+.*conversation'), "cat conversation file", "Use Read tool instead of cat for conversation files"),
    (re.compile(r'cat\s+.*\.jsonl\b'), "cat JSONL file", "Use Read tool or python3 for JSONL files"),
    (re.compile(r'cat\s+.*transcript'), "cat transcript file", "Use Read tool for transcript files"),
    # Heredocs with control chars
    (re.compile(r'<<.*\\u001b'), "heredoc with unicode escapes", "Write to temp file first"),
    (re.compile(r'<<.*\\x1b'), "heredoc with hex escapes", "Write to temp file first"),
    # Injection-like strings
    (re.compile(r'echo\s+.*<script', re.IGNORECASE), "echo with script tag", "Write HTML to file instead"),
    (re.compile(r'echo\s+.*javascript:', re.IGNORECASE), "echo with javascript:", "Write to file instead"),
    (re.compile(r'echo\s+.*\bon(error|load|click)\b', re.IGNORECASE), "echo with event handler", "Write to file instead"),
    # Raw JSON with escape sequences
    (re.compile(r'echo\s+.*\\u001b'), "echo with unicode escape", "Write to file, avoid inline escapes"),
    (re.compile(r'printf\s+.*\\x1b'), "printf with hex escape", "Write to file first"),
]


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = input_data.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    # Check all patterns
    matches = []
    for pattern, desc, alt in FP_PATTERNS:
        if pattern.search(command):
            matches.append(f"{desc} -> {alt}")

    if matches:
        advice = "; ".join(matches[:3])  # Cap at 3 matches
        response = {
            "hookSpecificOutput": {
                "additionalContext": f"CSB Advisory: Command may trigger false positive. {advice}"
            }
        }
        print(json.dumps(response))

    sys.exit(0)


if __name__ == "__main__":
    main()
