#!/usr/bin/env python3
"""
corrections-to-lessons.py - Extract recurring correction patterns into lessons

Reads ~/.claude/correction-history.jsonl and extracts patterns that repeat
frequently, converting them into lesson candidates for review.

Usage:
    python3 corrections-to-lessons.py [--min-count 3] [--days 30]

Options:
    --min-count: Minimum times a pattern must appear (default: 3)
    --days: Look back period in days (default: 30)
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, List, Any
import hashlib

CORRECTIONS_FILE = Path.home() / ".claude" / "correction-history.jsonl"
LESSONS_DIR = Path.home() / ".claude" / "lessons"
REVIEW_DIR = LESSONS_DIR / "review"


def load_corrections(days: int) -> List[Dict[str, Any]]:
    """Load corrections from the specified time period."""
    if not CORRECTIONS_FILE.exists():
        print(f"No corrections file found at {CORRECTIONS_FILE}")
        return []

    cutoff = datetime.now() - timedelta(days=days)
    corrections = []

    with open(CORRECTIONS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                timestamp_str = entry.get("timestamp", "")
                if timestamp_str:
                    # Parse ISO timestamp
                    timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    if timestamp.replace(tzinfo=None) >= cutoff:
                        corrections.append(entry)
            except (json.JSONDecodeError, ValueError):
                continue

    return corrections


def extract_patterns(corrections: List[Dict[str, Any]], min_count: int) -> List[Dict[str, Any]]:
    """Extract recurring patterns from corrections."""
    # Group by correction type
    type_counts = Counter(c.get("type", "unknown") for c in corrections)

    # Find patterns that meet threshold
    patterns = []
    for ctype, count in type_counts.items():
        if count >= min_count:
            # Get all corrections of this type
            type_corrections = [c for c in corrections if c.get("type") == ctype]

            # Extract common trigger phrases
            triggers = [c.get("trigger_phrase", "") for c in type_corrections if c.get("trigger_phrase")]
            common_trigger = max(set(triggers), key=triggers.count) if triggers else ctype

            # Build pattern
            patterns.append({
                "type": ctype,
                "count": count,
                "trigger": common_trigger,
                "examples": [c.get("message_excerpt", "")[:100] for c in type_corrections[:3]],
            })

    return sorted(patterns, key=lambda p: -p["count"])


def create_lesson_from_pattern(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a correction pattern into a lesson candidate."""
    ctype = pattern["type"]
    count = pattern["count"]
    trigger = pattern["trigger"]

    # Map correction type to lesson content
    lesson_mapping = {
        "explicit_rejection": {
            "title": f"Avoid assumptions when user says '{trigger}'",
            "lesson": "When user explicitly rejects something, stop and ask for clarification rather than continuing with a modified approach.",
            "category": "communication",
        },
        "redirect": {
            "title": "Clarify before acting when request is ambiguous",
            "lesson": "When user redirects with 'actually I meant...', the original interpretation was wrong. Ask clarifying questions upfront.",
            "category": "communication",
        },
        "stop_action": {
            "title": f"Stop immediately when user says '{trigger}'",
            "lesson": "User interruption means current approach is wrong. Stop, acknowledge, and ask what they actually want.",
            "category": "workflow",
        },
        "preference": {
            "title": "Remember user preferences for future sessions",
            "lesson": f"User has a preference pattern: '{trigger}'. Follow this in future interactions.",
            "category": "preference",
        },
        "preference_redirect": {
            "title": "Apply 'don't X, do Y' patterns consistently",
            "lesson": "When user specifies 'instead of X, do Y', remember this preference for similar situations.",
            "category": "preference",
        },
        "error_report": {
            "title": "Verify changes actually work before reporting success",
            "lesson": "When user reports something is 'still broken', the fix didn't work. Verify with tests or validation.",
            "category": "technical",
        },
        "clarification": {
            "title": "Match user's actual intent, not literal words",
            "lesson": "User clarifications reveal gap between words and intent. Pay attention to what they actually want.",
            "category": "communication",
        },
    }

    mapping = lesson_mapping.get(ctype, {
        "title": f"Pattern: {ctype}",
        "lesson": f"Correction pattern detected {count} times: {trigger}",
        "category": "unknown",
    })

    # Generate ID
    timestamp = datetime.now().isoformat()
    hash_input = f"{timestamp}{mapping['title']}{ctype}"
    lesson_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]

    return {
        "id": f"lesson-{datetime.now().strftime('%Y%m%d')}-{lesson_hash}",
        "type": "antipattern",
        "category": mapping["category"],
        "confidence": min(0.5 + (count * 0.1), 0.85),  # More occurrences = higher confidence
        "title": mapping["title"],
        "context": f"Extracted from {count} corrections",
        "lesson": mapping["lesson"],
        "rationale": f"This pattern occurred {count} times, suggesting systematic issue.",
        "example": pattern["examples"][0] if pattern["examples"] else "N/A",
        "tags": ["correction-extracted", ctype],
        "source": {
            "extraction_type": "correction-pattern",
            "timestamp": timestamp,
            "correction_count": count,
        },
        "metadata": {
            "seen_count": count,
            "last_seen": timestamp,
            "status": "pending_review",
            "extracted_by": "corrections-to-lessons.py",
        },
    }


def save_lessons(lessons: List[Dict[str, Any]]) -> int:
    """Save lesson candidates to review directory."""
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)

    saved = 0
    for lesson in lessons:
        filepath = REVIEW_DIR / f"{lesson['id']}.json"

        # Skip if already exists
        if filepath.exists():
            continue

        with open(filepath, "w") as f:
            json.dump(lesson, f, indent=2)
        saved += 1
        print(f"Created: {filepath.name} - {lesson['title']}")

    return saved


def main():
    parser = argparse.ArgumentParser(description="Extract lessons from corrections")
    parser.add_argument("--min-count", type=int, default=3, help="Minimum pattern occurrences")
    parser.add_argument("--days", type=int, default=30, help="Days to look back")
    args = parser.parse_args()

    print(f"Analyzing corrections from last {args.days} days...")
    corrections = load_corrections(args.days)
    print(f"Found {len(corrections)} corrections")

    if not corrections:
        print("No corrections to analyze")
        return

    patterns = extract_patterns(corrections, args.min_count)
    print(f"Extracted {len(patterns)} recurring patterns (min count: {args.min_count})")

    if not patterns:
        print("No patterns met the threshold")
        return

    lessons = [create_lesson_from_pattern(p) for p in patterns]
    saved = save_lessons(lessons)

    print(f"\nCreated {saved} new lesson candidate(s)")
    if saved > 0:
        print(f"Review with: cc lessons review")


if __name__ == "__main__":
    main()
