#!/usr/bin/env python3
"""
Agent Routing Auto-Suggest (Phase 3.4)

Analyzes agent spawn patterns from subagent-start-tracker.sh analytics
and compares against CLAUDE.md routing table. Suggests new routing entries
when a keyword-agent pair appears frequently (>=10 times) and isn't already
in the routing table.

Output: Suggestions for weekly report (never auto-modifies CLAUDE.md).

Usage:
    python3 ~/.claude/scripts/sync-routing-from-patterns.py [--days 30]
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
ANALYTICS_FILE = CLAUDE_DIR / "logs" / "agent-analytics.jsonl"
CLAUDE_MD = CLAUDE_DIR / "CLAUDE.md"
SUBAGENT_LOG = CLAUDE_DIR / "logs" / "subagent-activity.log"

DAYS = 30
MIN_FREQUENCY = 10
MIN_CONFIDENCE = 0.70  # 70% of times keyword appears, this agent is used


def parse_args():
    global DAYS
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--days" and i + 2 <= len(sys.argv[1:]):
            DAYS = int(sys.argv[i + 2])


def load_analytics():
    """Load agent spawn analytics from JSONL."""
    entries = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)

    if ANALYTICS_FILE.exists():
        with open(ANALYTICS_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts_str = entry.get("ts", "")
                    ts = datetime.fromisoformat(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts >= cutoff:
                        entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue

    return entries


def extract_existing_routing():
    """Parse CLAUDE.md to find all existing routing entries (trigger -> agent)."""
    existing = set()
    if not CLAUDE_MD.exists():
        return existing

    content = CLAUDE_MD.read_text()

    # Find routing tables: "| trigger text | `agent-name` |" patterns
    for match in re.finditer(
        r"\|\s*(.+?)\s*\|\s*`?([a-z0-9_-]+)`?\s*\|",
        content
    ):
        trigger = match.group(1).strip().lower()
        agent = match.group(2).strip()
        # Skip table headers
        if trigger.startswith("---") or trigger.startswith("trigger") or trigger.startswith("context"):
            continue
        existing.add((trigger, agent))

    return existing


def extract_keywords_from_description(description):
    """Extract meaningful keywords from agent spawn descriptions."""
    if not description:
        return []
    # Remove common filler words
    stopwords = {"the", "a", "an", "for", "to", "and", "or", "in", "on", "of",
                 "is", "it", "this", "that", "with", "from", "by", "as", "at",
                 "be", "do", "use", "let", "me", "i", "we", "my", "check", "get"}
    words = re.findall(r'[a-z]+', description.lower())
    return [w for w in words if w not in stopwords and len(w) > 2]


def analyze_patterns(entries):
    """Analyze keyword-agent co-occurrence patterns."""
    # keyword -> agent_type -> count
    keyword_agent = defaultdict(Counter)
    # keyword -> total appearances
    keyword_total = Counter()

    for entry in entries:
        agent_type = entry.get("agent_type", "unknown")
        if agent_type in ("unknown", "general-purpose", "Explore", "Plan", "worker"):
            continue

        description = entry.get("description", "")
        keywords = extract_keywords_from_description(description)

        for kw in keywords:
            keyword_agent[kw][agent_type] += 1
            keyword_total[kw] += 1

    # Find strong keyword-agent associations
    suggestions = []
    for kw, agents in keyword_agent.items():
        total = keyword_total[kw]
        if total < MIN_FREQUENCY:
            continue

        top_agent, top_count = agents.most_common(1)[0]
        confidence = top_count / total

        if confidence >= MIN_CONFIDENCE:
            suggestions.append({
                "keyword": kw,
                "agent": top_agent,
                "frequency": top_count,
                "total_keyword_appearances": total,
                "confidence": round(confidence, 2),
            })

    # Sort by frequency descending
    suggestions.sort(key=lambda x: -x["frequency"])
    return suggestions


def filter_against_existing(suggestions, existing_routing):
    """Remove suggestions that are already in CLAUDE.md routing table."""
    new_suggestions = []
    existing_agents = {agent for _, agent in existing_routing}
    existing_triggers = {trigger for trigger, _ in existing_routing}

    for s in suggestions:
        # Check if this agent is already routed for a similar trigger
        agent_already_routed = False
        for trigger, agent in existing_routing:
            if s["agent"] == agent and s["keyword"] in trigger:
                agent_already_routed = True
                break

        if not agent_already_routed:
            new_suggestions.append(s)

    return new_suggestions


def format_routing_suggestion(suggestion):
    """Format a suggestion as a CLAUDE.md table row."""
    return (
        f"| {suggestion['keyword']} (auto-detected, {suggestion['frequency']}x, "
        f"{suggestion['confidence']:.0%} conf) | `{suggestion['agent']}` |"
    )


def main():
    parse_args()

    entries = load_analytics()
    if not entries:
        print(f"No agent analytics data found in last {DAYS} days.")
        print(f"Analytics file: {ANALYTICS_FILE}")
        return []

    print(f"Routing Pattern Analysis (last {DAYS} days, {len(entries)} spawns)")
    print("=" * 60)

    existing = extract_existing_routing()
    print(f"Existing routing entries in CLAUDE.md: {len(existing)}")

    suggestions = analyze_patterns(entries)
    print(f"Raw keyword-agent patterns found: {len(suggestions)}")

    new_suggestions = filter_against_existing(suggestions, existing)
    print(f"New suggestions (not in CLAUDE.md): {len(new_suggestions)}")
    print()

    if not new_suggestions:
        print("No new routing suggestions. All frequent patterns are already documented.")
        return []

    print("Suggested additions to CLAUDE.md routing table:")
    print("-" * 60)
    for s in new_suggestions[:10]:
        print(f"  Keyword: '{s['keyword']}' -> {s['agent']}")
        print(f"    Frequency: {s['frequency']}x | Confidence: {s['confidence']:.0%}")
        print(f"    Table row: {format_routing_suggestion(s)}")
        print()

    return new_suggestions


if __name__ == "__main__":
    main()
