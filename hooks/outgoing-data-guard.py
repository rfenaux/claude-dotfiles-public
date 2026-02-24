#!/usr/bin/env python3
"""
Outgoing Data Guard - PreToolUse Hook for Bash

Scans Bash commands (especially curl/wget) for potentially sensitive data
before they execute. Outputs warnings but does NOT block.

Global hook - protects across all projects.
"""

import json
import sys
import os
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any

LOG_PATH = os.path.expanduser("~/.claude/logs/security-events.jsonl")  # Unified log
PATTERNS_PATH = os.path.expanduser("~/.claude/security/patterns.json")  # External patterns
CONFIG_PATH = os.path.expanduser("~/.claude/security/PROTECTED_INFORMATION.md")

# Import taint manager for recording outgoing violations
sys.path.insert(0, os.path.expanduser("~/.claude/security"))
try:
    from csb_taint_manager import record_outgoing_violation
    TAINT_MANAGER_AVAILABLE = True
except ImportError:
    TAINT_MANAGER_AVAILABLE = False


def load_external_patterns() -> Dict[str, Any]:
    """Load patterns from unified external config if available."""
    try:
        with open(PATTERNS_PATH, 'r') as f:
            config = json.load(f)
            outbound = config.get("categories", {}).get("outbound_sensitive", {})
            subcats = outbound.get("subcategories", {})

            # Convert to internal format
            patterns = {}
            for name, data in subcats.items():
                patterns[name] = {
                    "patterns": data.get("patterns", []),
                    "severity": data.get("severity", "MEDIUM"),
                    "message": f"{name.replace('_', ' ').title()} detected"
                }
            return patterns if patterns else None
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


# Patterns that indicate outgoing network requests
NETWORK_COMMANDS = [
    r'\bcurl\b',
    r'\bwget\b',
    r'\bhttpie\b',
    r'\bhttp\b',  # httpie alias
    r'\bfetch\b',
    r'\bnc\b',    # netcat
    r'\btelnet\b',
]

# Sensitive data patterns to detect in outgoing commands
SENSITIVE_PATTERNS = {
    "api_key": {
        "patterns": [
            r'sk-[a-zA-Z0-9]{20,}',           # OpenAI-style
            r'api[_-]?key[=:]\s*["\']?[\w-]+', # Generic API key
            r'token[=:]\s*["\']?[\w-]+',       # Generic token
            r'secret[=:]\s*["\']?[\w-]+',      # Generic secret
            r'moltbook_[a-zA-Z0-9]+',          # Moltbook API key
            r'bearer\s+[\w.-]+',               # Bearer tokens
        ],
        "severity": "CRITICAL",
        "message": "Potential API key or token detected"
    },
    "password": {
        "patterns": [
            r'password[=:]\s*["\']?[^\s"\'&]+',
            r'passwd[=:]\s*["\']?[^\s"\'&]+',
            r'pwd[=:]\s*["\']?[^\s"\'&]+',
        ],
        "severity": "CRITICAL",
        "message": "Password detected in command"
    },
    "email": {
        "patterns": [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ],
        "severity": "HIGH",
        "message": "Email address detected"
    },
    "file_path": {
        "patterns": [
            r'/Users/[a-zA-Z0-9_-]+/',         # macOS user paths
            r'/home/[a-zA-Z0-9_-]+/',          # Linux user paths
            r'C:\\Users\\[a-zA-Z0-9_-]+\\',    # Windows paths
        ],
        "severity": "MEDIUM",
        "message": "User file path detected (may reveal username)"
    },
    "private_dirs": {
        "patterns": [
            r'/private/',
            r'/inner/',
            r'\.env\b',
            r'credentials\.json',
            r'secrets\.yaml',
        ],
        "severity": "HIGH",
        "message": "Reference to private/sensitive directory or file"
    },
    "phone_number": {
        "patterns": [
            r'\+?[0-9]{1,3}[-.\s]?\(?[0-9]{2,4}\)?[-.\s]?[0-9]{2,4}[-.\s]?[0-9]{2,4}',
        ],
        "severity": "HIGH",
        "message": "Potential phone number detected"
    },
    "ip_address": {
        "patterns": [
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
        ],
        "severity": "MEDIUM",
        "message": "IP address detected"
    },
}

# Whitelist patterns (only truly local destinations)
# NOTE: Even test services are NOT whitelisted - we check everything external
WHITELIST = [
    r'^https?://localhost[:/]',
    r'^https?://127\.0\.0\.1[:/]',
]


def log_event(event_data: Dict[str, Any]) -> None:
    """Append event to unified security JSONL log file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        event_data["ts"] = datetime.utcnow().isoformat() + "Z"
        event_data["component"] = "outgoing-data-guard"
        event_data["direction"] = "outbound"  # Unified schema field
        event_data["pid"] = os.getpid()

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(event_data) + "\n")
    except (IOError, OSError):
        pass


def is_network_command(command: str) -> bool:
    """Check if command involves network requests."""
    for pattern in NETWORK_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def is_whitelisted(command: str) -> bool:
    """Check if command targets whitelisted destinations."""
    for pattern in WHITELIST:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def scan_command(command: str) -> List[Dict[str, Any]]:
    """Scan command for sensitive data patterns.

    Uses external patterns from ~/.claude/security/patterns.json if available,
    falls back to inline SENSITIVE_PATTERNS for backward compatibility.
    """
    findings = []

    # Try external patterns first, fall back to inline
    patterns = load_external_patterns() or SENSITIVE_PATTERNS

    for category, config in patterns.items():
        for pattern in config["patterns"]:
            try:
                matches = re.findall(pattern, command, re.IGNORECASE)
                if matches:
                    # Redact the actual values for logging
                    redacted = [m[:4] + "..." + m[-2:] if len(m) > 8 else "***" for m in matches]
                    findings.append({
                        "category": category,
                        "severity": config["severity"],
                        "message": config.get("message", f"{category} detected"),
                        "count": len(matches),
                        "redacted_examples": redacted[:3]
                    })
            except re.error:
                pass  # Skip invalid patterns

    return findings


def output_warning(command: str, findings: List[Dict[str, Any]]) -> None:
    """Output warning to stderr."""
    severities = [f["severity"] for f in findings]
    max_severity = "CRITICAL" if "CRITICAL" in severities else "HIGH" if "HIGH" in severities else "MEDIUM"

    indicators = {
        "MEDIUM": "⚠️",
        "HIGH": "⚡",
        "CRITICAL": "🚨"
    }
    indicator = indicators.get(max_severity, "⚠️")

    print(f"\n{indicator} [OUTGOING DATA GUARD] Sensitive data detected in command!", file=sys.stderr)
    print(f"Severity: {max_severity}", file=sys.stderr)
    print(f"", file=sys.stderr)

    for finding in findings:
        print(f"  • {finding['message']} ({finding['category']})", file=sys.stderr)
        if finding.get("redacted_examples"):
            print(f"    Examples: {', '.join(finding['redacted_examples'])}", file=sys.stderr)

    print(f"", file=sys.stderr)
    print(f"⚠️  VERIFY this data should be sent externally before proceeding.", file=sys.stderr)
    print(f"    If unintentional, cancel and redact sensitive information.", file=sys.stderr)
    print(f"", file=sys.stderr)


def main():
    """Main entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")

    # Only check Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    session_id = input_data.get("session_id", "unknown")

    # Only scan network commands
    if not is_network_command(command):
        sys.exit(0)

    # Skip if targeting whitelisted destinations
    if is_whitelisted(command):
        log_event({
            "event": "whitelisted_request",
            "level": "debug",
            "session_id": session_id,
            "command_preview": command[:100]
        })
        sys.exit(0)

    # Scan for sensitive data
    findings = scan_command(command)

    if findings:
        # Log the event
        log_event({
            "event": "sensitive_data_detected",
            "level": "warning",
            "session_id": session_id,
            "findings": [{"category": f["category"], "severity": f["severity"]} for f in findings],
            "command_preview": command[:50] + "..." if len(command) > 50 else command
        })

        # Output warning
        output_warning(command, findings)

        # Record outgoing violations to taint manager (F7: CSB Hardening)
        if TAINT_MANAGER_AVAILABLE:
            for finding in findings:
                if finding["severity"] in ("HIGH", "CRITICAL"):
                    snippet = finding.get("redacted_examples", [""])[0] if finding.get("redacted_examples") else ""
                    record_outgoing_violation(
                        session_id=session_id,
                        severity=finding["severity"],
                        category=finding["category"],
                        snippet=snippet
                    )
    else:
        # Log clean network request
        log_event({
            "event": "clean_network_request",
            "level": "info",
            "session_id": session_id,
            "command_preview": command[:50] + "..." if len(command) > 50 else command
        })

    # Always exit 0 - warn but don't block
    sys.exit(0)


if __name__ == "__main__":
    main()
