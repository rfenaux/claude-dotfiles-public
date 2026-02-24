#!/usr/bin/env python3
"""
CSB WebFetch Cache - PostToolUse Hook for WebFetch Tool

Since PostToolUse hooks don't receive the tool result, this hook:
1. Re-fetches the URL to a local cache
2. Scans the cached content for injection patterns
3. Creates taint markers if HIGH/CRITICAL detected

This enables taint-based blocking for content fetched via WebFetch.
"""

import json
import sys
import os
import re
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Import taint manager
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from csb_taint_manager import create_taint
    TAINT_MANAGER_AVAILABLE = True
except ImportError:
    TAINT_MANAGER_AVAILABLE = False

CACHE_DIR = "/tmp/claude-csb-cache"
LOG_PATH = os.path.expanduser("~/.claude/logs/csb-events.jsonl")
CONFIG_PATH = os.path.expanduser("~/.claude/config/csb-patterns.json")
MAX_FETCH_SIZE = 500000  # 500KB max

# Default patterns (subset for web content)
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
            r"<invoke",
            r"tool_use",
            r"function_call",
            r"mcp__\w+__",
        ]
    }
}

DEFAULT_THRESHOLDS = {"LOW": 0, "MEDIUM": 3, "HIGH": 6, "CRITICAL": 9}


def load_config() -> Dict[str, Any]:
    """Load pattern configuration."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "categories": DEFAULT_PATTERNS,
            "risk_thresholds": DEFAULT_THRESHOLDS
        }


def url_to_hash(url: str) -> str:
    """Convert URL to safe filename hash."""
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def fetch_url_content(url: str, timeout: int = 10) -> str:
    """Fetch URL content using curl."""
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        url_hash = url_to_hash(url)
        cache_file = f"{CACHE_DIR}/{url_hash}.txt"

        # Use curl to fetch content
        result = subprocess.run(
            ["curl", "-sL", "--max-time", str(timeout), "-o", cache_file, url],
            capture_output=True,
            text=True,
            timeout=timeout + 5
        )

        if result.returncode != 0:
            return ""

        # Read cached content
        if os.path.exists(cache_file):
            with open(cache_file, 'r', errors='ignore') as f:
                return f.read(MAX_FETCH_SIZE)

    except (subprocess.TimeoutExpired, OSError, IOError):
        pass

    return ""


def scan_content(content: str, config: Dict[str, Any]) -> Tuple[List[Dict], int]:
    """Scan content for injection patterns."""
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
                        "pattern": pattern[:50],
                        "count": match_count,
                        "examples": [str(f)[:30] for f in found[:3]]
                    })
                    total_score += weight * match_count
            except re.error:
                pass

    return matches, total_score


def score_to_level(score: int, thresholds: Dict[str, int]) -> str:
    """Convert score to risk level."""
    if score >= thresholds.get("CRITICAL", 9):
        return "CRITICAL"
    elif score >= thresholds.get("HIGH", 6):
        return "HIGH"
    elif score >= thresholds.get("MEDIUM", 3):
        return "MEDIUM"
    return "LOW"


def log_event(event_data: Dict[str, Any]) -> None:
    """Log event to JSONL file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        event_data["ts"] = datetime.utcnow().isoformat() + "Z"
        event_data["component"] = "csb-webfetch-cache"
        event_data["pid"] = os.getpid()

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(event_data) + "\n")
    except (IOError, OSError):
        pass


def main():
    """Main entry point."""
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")

    # Only process WebFetch
    if tool_name != "WebFetch":
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    session_id = input_data.get("session_id", "unknown")
    url = tool_input.get("url", "")

    if not url:
        sys.exit(0)

    # Fetch and cache content
    content = fetch_url_content(url)

    if not content:
        log_event({
            "event": "webfetch_cache_failed",
            "level": "warning",
            "session_id": session_id,
            "url": url[:100]
        })
        sys.exit(0)

    # Load config and scan
    config = load_config()
    thresholds = config.get("risk_thresholds", DEFAULT_THRESHOLDS)
    matches, score = scan_content(content, config)
    level = score_to_level(score, thresholds)

    # Log scan event
    log_event({
        "event": "webfetch_scanned",
        "level": "warning" if level in ("HIGH", "CRITICAL") else "info",
        "session_id": session_id,
        "url": url[:100],
        "risk_level": level,
        "risk_score": score,
        "patterns_matched": len(matches),
        "content_length": len(content),
        "categories": list(set(m["category"] for m in matches)) if matches else []
    })

    # Create taint for HIGH/CRITICAL
    if level in ("HIGH", "CRITICAL") and TAINT_MANAGER_AVAILABLE:
        categories = list(set(m["category"] for m in matches))
        examples = []
        for m in matches[:3]:
            examples.extend(m.get("examples", []))

        create_taint(
            session_id=session_id,
            level=level,
            score=score,
            source=url[:100],
            source_type="WebFetch",
            categories=categories,
            examples=examples[:5]
        )

        # Output warning
        indicator = "\U0001F6A8" if level == "CRITICAL" else "\u26a1"
        print(f"[CSB] {indicator} WebFetch Risk: {level} | Score: {score} | URL: {url[:60]}...", file=sys.stderr)
        print(f"[CSB] Detected: {', '.join(categories)}", file=sys.stderr)

        if level == "CRITICAL":
            print(f"[CSB] TAINT CREATED: Write/Edit/Bash BLOCKED until 'csb approve'", file=sys.stderr)
        else:
            print(f"[CSB] TAINT CREATED: Write/Edit/Bash will require approval", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
