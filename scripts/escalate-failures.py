#!/usr/bin/env python3
"""
Failure Pattern Escalation - Boost high-frequency failure signatures to lessons.

Reads failure-catalog.jsonl, groups by error_signature, and promotes
frequently-occurring failures to higher confidence in lessons.

Thresholds:
  - 10+ occurrences AND confidence < 0.85 → boost to 0.85
  - 20+ occurrences → boost to 0.90 + add [HIGH_FREQUENCY] tag

Usage:
    python3 ~/.claude/scripts/escalate-failures.py [--dry-run]
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
FAILURE_CATALOG = CLAUDE_DIR / "logs" / "failure-catalog.jsonl"
LESSONS_FILE = CLAUDE_DIR / "lessons" / "lessons.jsonl"
CONFIDENCE_PY = CLAUDE_DIR / "lessons" / "scripts" / "confidence.py"
LOG_FILE = CLAUDE_DIR / "logs" / "self-healing" / "failure-escalation.jsonl"
LOCK_FILE = Path("/tmp/claude-failure-escalation.lock")

DRY_RUN = "--dry-run" in sys.argv


def load_failure_catalog():
    """Load and group failures by signature."""
    if not FAILURE_CATALOG.exists():
        return {}

    groups = defaultdict(list)
    with open(FAILURE_CATALOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                sig = entry.get("error_signature", "")
                if sig:
                    groups[sig].append(entry)
            except json.JSONDecodeError:
                continue
    return groups


def load_lessons():
    """Load existing lessons and index by error_signature."""
    sig_to_lesson = {}
    if not LESSONS_FILE.exists():
        return sig_to_lesson

    with open(LESSONS_FILE) as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                lesson = json.loads(line)
                sig = lesson.get("error_signature", "")
                if sig:
                    sig_to_lesson[sig] = {"line": i, "data": lesson}
            except json.JSONDecodeError:
                continue
    return sig_to_lesson


def update_lesson_confidence(lessons_path, line_num, new_confidence, new_tags=None):
    """Update a specific lesson's confidence in the JSONL file."""
    lines = lessons_path.read_text().splitlines()
    if line_num >= len(lines):
        return False

    try:
        lesson = json.loads(lines[line_num])
        lesson["confidence"] = new_confidence
        if new_tags:
            existing_tags = lesson.get("tags", [])
            for tag in new_tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            lesson["tags"] = existing_tags
        lesson["metadata"] = lesson.get("metadata", {})
        lesson["metadata"]["escalated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines[line_num] = json.dumps(lesson, separators=(",", ":"))
        lessons_path.write_text("\n".join(lines) + "\n")
        return True
    except (json.JSONDecodeError, IndexError):
        return False


def log_escalation(sig, count, old_conf, new_conf, tool, error_preview):
    """Log escalation event."""
    if DRY_RUN:
        return
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "signature": sig,
        "occurrence_count": count,
        "old_confidence": old_conf,
        "new_confidence": new_conf,
        "tool": tool,
        "error_preview": error_preview[:100],
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main():
    print(f"Failure Pattern Escalation {'(DRY RUN)' if DRY_RUN else ''}")
    print("=" * 50)

    groups = load_failure_catalog()
    if not groups:
        print("No failure catalog found.")
        return

    lessons = load_lessons()
    escalated = 0

    # Sort by frequency
    sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]), reverse=True)

    for sig, entries in sorted_groups:
        count = len(entries)
        tool = entries[0].get("tool", "unknown")
        error = str(entries[0].get("error", ""))[:100]

        if count < 10:
            continue  # Only escalate frequent failures

        # Determine target confidence
        if count >= 20:
            target_conf = 0.90
            extra_tags = ["high_frequency"]
        else:
            target_conf = 0.85
            extra_tags = []

        # Check if lesson exists for this signature
        if sig in lessons:
            current = lessons[sig]["data"]
            current_conf = current.get("confidence", 0.70)

            if current_conf >= target_conf:
                continue  # Already at target or higher

            print(f"  ESCALATE: {sig[:8]}... ({count}x, {tool})")
            print(f"    {current_conf:.2f} → {target_conf:.2f}")
            print(f"    Error: {error[:60]}")

            if not DRY_RUN:
                success = update_lesson_confidence(
                    LESSONS_FILE, lessons[sig]["line"],
                    target_conf, extra_tags
                )
                if success:
                    log_escalation(sig, count, current_conf, target_conf, tool, error)
                    escalated += 1
            else:
                escalated += 1
        else:
            # No lesson exists — create one with boosted confidence
            print(f"  NEW LESSON: {sig[:8]}... ({count}x, {tool})")
            print(f"    Confidence: {target_conf:.2f}")
            print(f"    Error: {error[:60]}")

            if not DRY_RUN:
                new_lesson = {
                    "type": "tool_failure",
                    "tool": tool,
                    "title": f"Frequent failure: {tool} - {error[:60]}",
                    "error": error,
                    "error_signature": sig,
                    "tags": [tool.lower(), "failure", "high_frequency"] if count >= 20 else [tool.lower(), "failure"],
                    "confidence": target_conf,
                    "status": "approved",
                    "occurrences": count,
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "metadata": {
                        "escalated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "auto_escalated": True,
                    },
                }
                with open(LESSONS_FILE, "a") as f:
                    f.write(json.dumps(new_lesson, separators=(",", ":")) + "\n")
                log_escalation(sig, count, 0, target_conf, tool, error)
                escalated += 1

    print(f"\nTotal: {len(sorted_groups)} unique signatures, {escalated} escalated")


if __name__ == "__main__":
    main()
