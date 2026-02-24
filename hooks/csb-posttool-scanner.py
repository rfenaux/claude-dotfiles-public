#!/usr/bin/env python3
"""
Content Security Buffer - PostToolUse Scanner Hook

Scans content retrieved by Read/WebFetch for injection patterns.
Outputs warnings to stderr (visible to user) and logs events.

Creates TAINT MARKERS for HIGH/CRITICAL content to enable blocking
of subsequent Write/Edit/Bash operations until user approval.
"""

import json
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Import taint manager for creating taint markers on HIGH/CRITICAL detection
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Also add security dir for source classifier and taint manager
SECURITY_DIR = os.path.expanduser("~/.claude/security")
sys.path.insert(0, SECURITY_DIR)
# Taint manager moved to ~/.claude/security/ (was in archive/)

try:
    from csb_taint_manager import create_taint
    TAINT_MANAGER_AVAILABLE = True
except ImportError:
    TAINT_MANAGER_AVAILABLE = False

try:
    from csb_source_classifier import classify_source, get_trust_multiplier
    SOURCE_CLASSIFIER_AVAILABLE = True
except ImportError:
    SOURCE_CLASSIFIER_AVAILABLE = False

# Load whitelist for per-tool overrides
WHITELIST_PATH = os.path.expanduser("~/.claude/security/csb-whitelist.json")
try:
    with open(WHITELIST_PATH, 'r') as _f:
        CSB_WHITELIST = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError):
    CSB_WHITELIST = {}

PROTECTED_TOOLS = {"Read", "WebFetch"}
CONFIG_PATH = os.path.expanduser("~/.claude/config/csb-patterns.json")
LOG_PATH = os.path.expanduser("~/.claude/logs/security-events.jsonl")  # Unified security log

# Trusted paths - scan but don't create taint (documentation with examples)
TAINT_WHITELIST = [
    os.path.expanduser("~/.claude/docs/"),
    os.path.expanduser("~/.claude/security/"),
    os.path.expanduser("~/.claude/config/"),
    os.path.expanduser("~/.claude/hooks/"),  # Our own hooks contain patterns
    os.path.expanduser("~/.claude/agents/"),  # Agent definitions contain tool references
    os.path.expanduser("~/.claude/skills/"),  # Skill definitions contain tool references
    os.path.expanduser("~/.claude/scripts/"),  # Our own scripts
    os.path.expanduser("~/.claude/AGENTS_INDEX.md"),  # Index file references tools
    os.path.expanduser("~/.claude/SKILLS_INDEX.md"),
    os.path.expanduser("~/.claude/CLAUDE.md"),
    os.path.expanduser("~/.claude/CONFIGURATION_GUIDE.md"),
    os.path.expanduser("~/.claude/settings"),  # Prefix match for settings*.json
    os.path.expanduser("~/.claude/rag-dashboard/"),  # Dashboard HTML has inline JS/SVG
    # Removed: ~/.claude/projects/ was too broad — is_conversation_export() handles exports precisely
]

# Path patterns that indicate conversation exports (reduce tool_invocation score)
CONVERSATION_EXPORT_PATTERNS = [
    "conversation-history/",
    "PreCompact",
    ".jsonl",
]


def is_whitelisted(source: str) -> bool:
    """Check if source path is in the taint whitelist."""
    expanded = os.path.expanduser(source)
    for trusted_path in TAINT_WHITELIST:
        if expanded.startswith(trusted_path):
            return True
    return False


def is_conversation_export(source: str) -> bool:
    """Check if source path looks like a conversation export file."""
    for pattern in CONVERSATION_EXPORT_PATTERNS:
        if pattern in source:
            return True
    return False

# Fallback patterns if config file is missing
DEFAULT_PATTERNS = {
    "instruction_override": {
        "weight": 3,
        "patterns": [
            r"ignore\s+(all\s+)?(previous|prior|above)",
            r"disregard\s+(all\s+)?(previous|prior|instructions)",
            r"forget\s+(everything|all|what)",
        ]
    },
    "role_manipulation": {
        "weight": 2,
        "patterns": [
            r"you\s+are\s+(now|a|an)\s+",
            r"act\s+as\s+(a|an|if)",
            r"pretend\s+(to\s+be|you)",
            r"\[system\]",
            r"<<SYS>>",
        ]
    },
    "tool_invocation": {
        "weight": 4,
        "patterns": [
            r"<function_calls>\s*\n\s*<invoke\s+name=",
            r"tool_use",
            r"function_call",
            r"mcp__\w+__",
        ]
    }
}

DEFAULT_THRESHOLDS = {"LOW": 0, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 9}


def load_config() -> Dict[str, Any]:
    """Load pattern configuration from file or use defaults."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "categories": DEFAULT_PATTERNS,
            "risk_thresholds": DEFAULT_THRESHOLDS
        }


def scan_content(content: str, config: Dict[str, Any]) -> Tuple[List[Dict], int]:
    """
    Scan content for injection patterns.

    Returns:
        Tuple of (matches list, total score)
    """
    matches = []
    total_score = 0

    categories = config.get("categories", DEFAULT_PATTERNS)

    for category_name, category_data in categories.items():
        weight = category_data.get("weight", 1)
        patterns = category_data.get("patterns", [])

        for pattern in patterns:
            try:
                found = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                if found:
                    match_count = len(found)
                    matches.append({
                        "category": category_name,
                        "pattern": pattern[:50],  # Truncate for logging
                        "count": match_count,
                        "examples": [str(f)[:30] for f in found[:3]]  # First 3 examples
                    })
                    total_score += weight * match_count
            except re.error as e:
                # Invalid regex, skip
                log_event({
                    "event": "pattern_error",
                    "level": "warning",
                    "pattern": pattern[:50],
                    "error": str(e)
                })

    return matches, total_score


def score_to_level(score: int, thresholds: Dict[str, int]) -> str:
    """Convert numeric score to risk level."""
    if score >= thresholds.get("CRITICAL", 9):
        return "CRITICAL"
    elif score >= thresholds.get("HIGH", 6):
        return "HIGH"
    elif score >= thresholds.get("MEDIUM", 3):
        return "MEDIUM"
    return "LOW"


def log_event(event_data: Dict[str, Any]) -> None:
    """Append event to unified security JSONL log file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        event_data["ts"] = datetime.utcnow().isoformat() + "Z"
        event_data["component"] = "csb"
        event_data["direction"] = "inbound"  # Unified schema field
        event_data["pid"] = os.getpid()

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(event_data) + "\n")
    except (IOError, OSError):
        # Silent fail - don't break the hook
        pass


def output_warning(level: str, score: int, source: str, matches: List[Dict]) -> None:
    """Output warning to stderr (visible to user in Claude Code)."""
    categories = sorted(set(m["category"] for m in matches))

    # Risk indicator
    indicators = {
        "LOW": "",
        "MEDIUM": "\u26a0\ufe0f",      # Warning sign
        "HIGH": "\u26a1",              # Lightning
        "CRITICAL": "\ud83d\udea8"     # Rotating light
    }
    indicator = indicators.get(level, "")

    # Truncate source for display
    source_display = source[:60] + "..." if len(source) > 60 else source

    print(f"[CSB] {indicator} Risk: {level} | Score: {score} | Source: {source_display}", file=sys.stderr)
    print(f"[CSB] Detected: {', '.join(categories)}", file=sys.stderr)

    if level in ("HIGH", "CRITICAL"):
        print(f"[CSB] {indicator} ALERT: Potential injection attempt detected. Content treated as DATA only.", file=sys.stderr)

        # Show examples for high-risk
        for match in matches[:3]:
            examples = match.get("examples", [])
            if examples:
                print(f"[CSB]   - {match['category']}: '{examples[0]}'...", file=sys.stderr)


def read_file_content(file_path: str, max_bytes: int = 500000) -> str:
    """
    Read file content for scanning.
    PostToolUse hooks don't receive tool_result, so we re-read the file.
    """
    try:
        expanded_path = os.path.expanduser(file_path)
        if os.path.exists(expanded_path) and os.path.isfile(expanded_path):
            with open(expanded_path, 'r', errors='ignore') as f:
                return f.read(max_bytes)
    except (IOError, OSError, PermissionError):
        pass
    return ""


def main():
    """Main entry point."""
    # Read hook input
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)  # Invalid input, allow tool to proceed

    tool_name = input_data.get("tool_name", "")

    # Only scan protected tools
    if tool_name not in PROTECTED_TOOLS:
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "unknown")

    # Get source identifier and content
    content = ""
    if tool_name == "Read":
        source = tool_input.get("file_path", "unknown")
        # PostToolUse hooks don't receive tool_result, so re-read the file
        content = read_file_content(source)
    elif tool_name == "WebFetch":
        source = tool_input.get("url", "unknown")
        # Can't re-fetch web content; rely on PreToolUse defense
        # Log event but can't scan without content
        log_event({
            "event": "webfetch_logged",
            "level": "info",
            "session_id": session_id,
            "tool": tool_name,
            "source": source,
            "note": "WebFetch content not available for scanning; PreToolUse defense active"
        })
        sys.exit(0)
    else:
        source = "unknown"

    # Skip if no content to scan
    if not content:
        sys.exit(0)

    # Load configuration
    config = load_config()
    thresholds = config.get("risk_thresholds", DEFAULT_THRESHOLDS)

    # Scan content
    matches, score = scan_content(content, config)

    # Source-aware scoring (F7: CSB Hardening)
    source_type = "unknown"
    trust_multiplier = 1.0
    if SOURCE_CLASSIFIER_AVAILABLE:
        source_type = classify_source(tool_name, tool_input, "")
        trust_multiplier = get_trust_multiplier(source_type)

        # Apply per-tool overrides from whitelist
        per_tool = CSB_WHITELIST.get("per_tool_overrides", {}).get(tool_name, {})
        # Check file extension overrides
        file_ext = os.path.splitext(source)[1] if source != "unknown" else ""
        override = per_tool.get(file_ext) or per_tool.get("*")
        disabled_cats = set(override.get("disable_categories", [])) if override else set()

        # Zero out disabled categories and apply trust multiplier
        adjusted_matches = []
        for m in matches:
            if m["category"] in disabled_cats:
                score -= m["count"] * config.get("categories", DEFAULT_PATTERNS).get(
                    m["category"], {}
                ).get("weight", 1) * m["count"]
                m["category"] = f"{m['category']} (disabled: {override.get('reason', 'override')})"
                m["count"] = 0
            adjusted_matches.append(m)
        matches = adjusted_matches

        # Apply trust multiplier to final score
        score = max(0, int(score * trust_multiplier))
    else:
        # Legacy fallback: hard-coded conversation export reduction
        if is_conversation_export(source):
            reduced_matches = []
            for m in matches:
                if m["category"] == "tool_invocation":
                    score -= m["count"] * 4
                    reduced_count = max(1, m["count"] // 5)
                    score += reduced_count * 4
                    m["count"] = reduced_count
                    m["category"] = "tool_invocation (conv_export, reduced)"
                reduced_matches.append(m)
            matches = reduced_matches
            score = max(0, score)

    level = score_to_level(score, thresholds)

    # Log event (always)
    log_event({
        "event": "content_scanned",
        "level": "warning" if level in ("HIGH", "CRITICAL") else "info",
        "session_id": session_id,
        "tool": tool_name,
        "source": source,
        "source_type": source_type,
        "trust_multiplier": trust_multiplier,
        "risk_level": level,
        "risk_score": score,
        "patterns_matched": len(matches),
        "content_length": len(content),
        "categories": list(set(m["category"] for m in matches)) if matches else []
    })

    # Output warning if patterns detected
    if matches:
        output_warning(level, score, source, matches)

    # Create taint marker for HIGH/CRITICAL detection
    # This enables blocking of subsequent Write/Edit/Bash operations
    # Skip taint for whitelisted paths (our own docs/config contain examples)
    if level in ("HIGH", "CRITICAL") and TAINT_MANAGER_AVAILABLE and not is_whitelisted(source):
        categories = list(set(m["category"] for m in matches))
        examples = []
        for m in matches[:3]:
            examples.extend(m.get("examples", []))

        create_taint(
            session_id=session_id,
            level=level,
            score=score,
            source=source,
            source_type=tool_name,
            categories=categories,
            examples=examples[:5]
        )

        # Additional warning about taint
        if level == "CRITICAL":
            print(f"[CSB] TAINT CREATED: Write/Edit/Bash BLOCKED until 'csb approve'", file=sys.stderr)
        else:
            print(f"[CSB] TAINT CREATED: Write/Edit/Bash will require approval", file=sys.stderr)

    # Always exit 0 - never block content (blocking happens in PreToolUse guards)
    sys.exit(0)


if __name__ == "__main__":
    main()
