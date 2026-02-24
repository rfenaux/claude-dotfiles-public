#!/usr/bin/env python3
"""
Backfill empty errors in failure-catalog.jsonl from observation archives.

One-time script. Matches catalog entries (by timestamp + tool) to observation
archive entries and extracts the actual error/output text.

Usage:
    python3 ~/.claude/scripts/backfill-failure-errors.py [--dry-run]
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
CATALOG = CLAUDE_DIR / "logs" / "failure-catalog.jsonl"
OBS_ARCHIVE = CLAUDE_DIR / "observations" / "archive"

DRY_RUN = "--dry-run" in sys.argv


def load_catalog():
    """Load catalog entries, tracking which have empty errors."""
    entries = []
    if not CATALOG.exists():
        return entries
    with open(CATALOG) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                entries.append(None)  # Preserve line position
    return entries


def build_observation_index():
    """Build a lookup index from observation archives: (tool, timestamp_prefix) -> output."""
    index = {}
    if not OBS_ARCHIVE.exists():
        return index
    for archive_file in sorted(OBS_ARCHIVE.glob("*.jsonl")):
        with open(archive_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    tool = entry.get("tool", "")
                    ts = entry.get("ts", "")
                    output = str(entry.get("output", ""))
                    if tool and ts and output and len(output) > 5:
                        # Key by tool + timestamp (first 16 chars = minute precision)
                        key = f"{tool}:{ts[:16]}"
                        if key not in index or len(output) > len(index[key]):
                            index[key] = output[:500]
                except json.JSONDecodeError:
                    continue
    return index


def main():
    print(f"Backfill Failure Catalog Errors {'(DRY RUN)' if DRY_RUN else ''}")
    print("=" * 50)

    entries = load_catalog()
    if not entries:
        print("No catalog entries found.")
        return

    # Count empty errors
    empty_count = sum(
        1 for e in entries
        if e and (not e.get("error") or len(str(e.get("error", ""))) < 5)
    )
    print(f"Catalog: {len(entries)} entries, {empty_count} with empty/short errors")

    if empty_count == 0:
        print("Nothing to backfill.")
        return

    print("Building observation index...")
    obs_index = build_observation_index()
    print(f"Observation index: {len(obs_index)} entries")

    filled = 0
    for i, entry in enumerate(entries):
        if entry is None:
            continue
        error = str(entry.get("error", ""))
        if error and len(error) >= 5:
            continue  # Already has error

        tool = entry.get("tool", "")
        ts = entry.get("timestamp", "")
        if not tool or not ts:
            continue

        # Try to find matching observation first
        key = f"{tool}:{ts[:16]}"
        new_error = obs_index.get(key, "")

        # Fallback: use input_summary as context if no observation match
        if not new_error:
            input_summary = entry.get("input_summary", "")
            if input_summary and len(input_summary) > 5:
                new_error = f"[from input] {input_summary[:300]}"

        if new_error:
            if not DRY_RUN:
                entries[i]["error"] = new_error
                entries[i]["title"] = f"Failure: {tool} - {new_error[:80]}"
            filled += 1
            if filled <= 5:
                print(f"  FILL [{i}] {tool} @ {ts[:19]}: {new_error[:60]}...")

    print(f"\nFilled: {filled}/{empty_count} empty errors")

    if not DRY_RUN and filled > 0:
        # Write back
        with open(CATALOG, "w") as f:
            for entry in entries:
                if entry is not None:
                    f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        print(f"Catalog updated: {CATALOG}")
    elif DRY_RUN:
        print("(dry run — no changes written)")


if __name__ == "__main__":
    main()
