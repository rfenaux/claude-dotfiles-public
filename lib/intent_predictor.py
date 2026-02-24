#!/usr/bin/env python3
"""
Intent Prediction System

Learns from tool usage patterns to predict user actions.
Tracks tool sequences and context keywords to surface predictions in session briefings.

Usage:
    # Track an interaction
    python intent_predictor.py track --tool "rag_search" --context "hubspot api"

    # Get predictions
    python intent_predictor.py predict --context "working on hubspot integration"

    # List patterns
    python intent_predictor.py list
"""

import argparse
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Use shared utilities (DRY consolidation)
from text_utils import extract_keywords_for_context
from temporal_utils import calculate_confidence as calc_confidence_shared

# Configure logging
LOG_FILE = Path.home() / ".claude" / "logs" / "intent-predictor.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
    ]
)
logger = logging.getLogger(__name__)

# Pattern storage
PATTERNS_FILE = Path.home() / ".claude" / "intent-patterns.json"
AGENT_PATTERNS_FILE = Path.home() / ".claude" / "intent-agent-patterns.json"

# Configuration
MIN_OCCURRENCES_FOR_PATTERN = 3  # Times before creating a pattern
MAX_PATTERNS = 50  # Maximum patterns to store
RECENCY_DECAY_DAYS = 30  # Days for recency factor decay
MAX_SEQUENCE_LENGTH = 3  # Tool sequence window size


@dataclass
class InteractionPattern:
    """A learned pattern from tool usage."""
    id: str                             # "pat_001"
    trigger: str                        # e.g., "ctm spawn" or "hubspot workflow"
    predicted_action: str               # e.g., "rag_search for similar projects"
    frequency: int                      # Times observed
    confidence: float                   # 0.0 - 1.0
    project: str                        # Project path or "global"
    last_seen: str                      # ISO timestamp
    context_keywords: List[str] = field(default_factory=list)
    tool_sequence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InteractionPattern":
        return cls(
            id=data.get("id", ""),
            trigger=data.get("trigger", ""),
            predicted_action=data.get("predicted_action", ""),
            frequency=data.get("frequency", 0),
            confidence=data.get("confidence", 0.0),
            project=data.get("project", "global"),
            last_seen=data.get("last_seen", ""),
            context_keywords=data.get("context_keywords", []),
            tool_sequence=data.get("tool_sequence", []),
        )


@dataclass
class PatternStore:
    """Storage for interaction patterns."""
    version: str = "1.0"
    patterns: List[InteractionPattern] = field(default_factory=list)
    pending_sequences: List[Dict[str, Any]] = field(default_factory=list)  # Tool sequences not yet patterns
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "patterns": [p.to_dict() for p in self.patterns],
            "pending_sequences": self.pending_sequences,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternStore":
        patterns = [InteractionPattern.from_dict(p) for p in data.get("patterns", [])]
        return cls(
            version=data.get("version", "1.0"),
            patterns=patterns,
            pending_sequences=data.get("pending_sequences", []),
            last_updated=data.get("last_updated", ""),
        )


def load_patterns() -> PatternStore:
    """Load patterns from storage file."""
    if not PATTERNS_FILE.exists():
        return PatternStore()

    try:
        data = json.loads(PATTERNS_FILE.read_text())
        return PatternStore.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load patterns: {e}")
        return PatternStore()


def save_patterns(store: PatternStore):
    """Save patterns to storage file."""
    store.last_updated = datetime.utcnow().isoformat()
    PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PATTERNS_FILE.write_text(json.dumps(store.to_dict(), indent=2))


def calculate_confidence(frequency: int, last_seen: str) -> float:
    """
    Calculate confidence score based on frequency and recency.

    Delegates to shared temporal_utils.calculate_confidence().
    """
    return calc_confidence_shared(
        frequency=frequency,
        last_seen=last_seen,
        halflife_days=RECENCY_DECAY_DAYS,
        frequency_factor=5,
        max_confidence=0.95
    )


def extract_context_keywords(context: str) -> List[str]:
    """Extract relevant keywords from context string.

    Delegates to shared text_utils.extract_keywords_for_context().
    """
    return extract_keywords_for_context(context, max_keywords=5)


def track_tool_usage(
    tool_name: str,
    context: str = "",
    project: str = "global"
) -> Optional[InteractionPattern]:
    """
    Track a tool usage and potentially create/update patterns.

    Returns created/updated pattern if any.
    """
    store = load_patterns()
    timestamp = datetime.utcnow().isoformat()
    keywords = extract_context_keywords(context)

    # Create sequence entry
    sequence_entry = {
        "tool": tool_name,
        "keywords": keywords,
        "project": project,
        "timestamp": timestamp,
    }

    # Add to pending sequences
    store.pending_sequences.append(sequence_entry)

    # Keep only recent sequences (last 20)
    store.pending_sequences = store.pending_sequences[-20:]

    # Analyze recent sequences for patterns
    recent_tools = [s["tool"] for s in store.pending_sequences[-MAX_SEQUENCE_LENGTH:]]
    recent_keywords = []
    for s in store.pending_sequences[-MAX_SEQUENCE_LENGTH:]:
        recent_keywords.extend(s.get("keywords", []))
    recent_keywords = list(dict.fromkeys(recent_keywords))[:5]

    # Check if this sequence matches an existing pattern
    pattern_found = None
    for pattern in store.patterns:
        if pattern.tool_sequence == recent_tools:
            # Update existing pattern
            pattern.frequency += 1
            pattern.last_seen = timestamp
            pattern.confidence = calculate_confidence(pattern.frequency, pattern.last_seen)
            # Merge keywords
            combined_keywords = list(dict.fromkeys(pattern.context_keywords + recent_keywords))[:5]
            pattern.context_keywords = combined_keywords
            pattern_found = pattern
            break

    # If no pattern found, check if we should create one
    if not pattern_found and len(recent_tools) >= 2:
        # Count occurrences of this sequence in pending
        sequence_count = 0
        for i in range(len(store.pending_sequences) - MAX_SEQUENCE_LENGTH + 1):
            window = [s["tool"] for s in store.pending_sequences[i:i + len(recent_tools)]]
            if window == recent_tools:
                sequence_count += 1

        if sequence_count >= MIN_OCCURRENCES_FOR_PATTERN:
            # Create new pattern
            pattern_id = f"pat_{len(store.patterns) + 1:03d}"
            trigger = " + ".join(recent_tools[:-1])
            predicted_action = recent_tools[-1]

            new_pattern = InteractionPattern(
                id=pattern_id,
                trigger=trigger,
                predicted_action=predicted_action,
                frequency=sequence_count,
                confidence=calculate_confidence(sequence_count, timestamp),
                project=project,
                last_seen=timestamp,
                context_keywords=recent_keywords,
                tool_sequence=recent_tools,
            )
            store.patterns.append(new_pattern)
            pattern_found = new_pattern

            # Prune old patterns if exceeding max
            if len(store.patterns) > MAX_PATTERNS:
                # Remove lowest confidence patterns
                store.patterns.sort(key=lambda p: p.confidence, reverse=True)
                store.patterns = store.patterns[:MAX_PATTERNS]

            logger.info(f"Created new pattern: {new_pattern.id} - {trigger} -> {predicted_action}")

    save_patterns(store)
    return pattern_found


def get_predictions(
    context: str = "",
    project: str = "global",
    min_confidence: float = 0.5,
    max_results: int = 3
) -> List[InteractionPattern]:
    """
    Get predictions based on current context.

    Returns patterns matching the context keywords or project, sorted by confidence.
    """
    store = load_patterns()
    keywords = set(extract_context_keywords(context))

    # Score each pattern
    scored_patterns: List[Tuple[float, InteractionPattern]] = []

    for pattern in store.patterns:
        # Recalculate confidence with current time
        pattern.confidence = calculate_confidence(pattern.frequency, pattern.last_seen)

        if pattern.confidence < min_confidence:
            continue

        # Calculate match score
        score = pattern.confidence

        # Boost for matching keywords
        pattern_keywords = set(pattern.context_keywords)
        keyword_overlap = len(keywords & pattern_keywords)
        if keyword_overlap > 0:
            score *= (1 + 0.1 * keyword_overlap)

        # Boost for matching project
        if pattern.project != "global" and pattern.project == project:
            score *= 1.2

        scored_patterns.append((score, pattern))

    # Sort by score and return top results
    scored_patterns.sort(key=lambda x: -x[0])
    return [p for _, p in scored_patterns[:max_results]]


def format_predictions_for_briefing(predictions: List[InteractionPattern]) -> str:
    """Format predictions as markdown for session briefing."""
    if not predictions:
        return ""

    lines = ["", "### Predicted Actions", ""]

    for p in predictions:
        confidence_pct = int(p.confidence * 100)
        lines.append(f"- **{p.predicted_action}** ({confidence_pct}% confidence)")
        lines.append(f"  _Triggered by: {p.trigger}_")

    return "\n".join(lines)


def list_all_patterns() -> List[InteractionPattern]:
    """List all stored patterns."""
    store = load_patterns()
    # Update confidence scores
    for p in store.patterns:
        p.confidence = calculate_confidence(p.frequency, p.last_seen)
    return sorted(store.patterns, key=lambda p: -p.confidence)


def clear_patterns():
    """Clear all patterns."""
    store = PatternStore()
    save_patterns(store)
    logger.info("Cleared all patterns")


# ─── Agent Routing Learning (Batch 2B.3) ────────────────────────────────────────

@dataclass
class AgentUsageEntry:
    """A single agent spawn record."""
    agent_type: str
    context: str
    model: str
    timestamp: str
    prompt_preview: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentUsageEntry":
        return cls(
            agent_type=data.get("agent_type", ""),
            context=data.get("context", ""),
            model=data.get("model", ""),
            timestamp=data.get("timestamp", ""),
            prompt_preview=data.get("prompt_preview", ""),
        )


@dataclass
class AgentPatternStore:
    """Storage for agent usage patterns."""
    version: str = "1.0"
    entries: List[Dict[str, Any]] = field(default_factory=list)
    co_occurrence: Dict[str, int] = field(default_factory=dict)
    type_context_map: Dict[str, List[str]] = field(default_factory=dict)
    last_updated: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "entries": self.entries[-500:],  # Keep last 500
            "co_occurrence": self.co_occurrence,
            "type_context_map": self.type_context_map,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentPatternStore":
        return cls(
            version=data.get("version", "1.0"),
            entries=data.get("entries", []),
            co_occurrence=data.get("co_occurrence", {}),
            type_context_map=data.get("type_context_map", {}),
            last_updated=data.get("last_updated", ""),
        )


def load_agent_patterns() -> AgentPatternStore:
    """Load agent pattern store."""
    if not AGENT_PATTERNS_FILE.exists():
        return AgentPatternStore()
    try:
        data = json.loads(AGENT_PATTERNS_FILE.read_text())
        return AgentPatternStore.from_dict(data)
    except Exception as e:
        logger.warning(f"Failed to load agent patterns: {e}")
        return AgentPatternStore()


def save_agent_patterns(store: AgentPatternStore):
    """Save agent pattern store."""
    store.last_updated = datetime.utcnow().isoformat()
    AGENT_PATTERNS_FILE.parent.mkdir(parents=True, exist_ok=True)
    AGENT_PATTERNS_FILE.write_text(json.dumps(store.to_dict(), indent=2))


def track_agent_usage(
    agent_type: str,
    context: str = "",
    model: str = "",
    prompt_preview: str = "",
) -> None:
    """Record an agent spawn for routing learning."""
    store = load_agent_patterns()
    timestamp = datetime.utcnow().isoformat()
    keywords = extract_context_keywords(context)

    entry = {
        "agent_type": agent_type,
        "context_keywords": keywords,
        "model": model,
        "timestamp": timestamp,
        "prompt_preview": prompt_preview[:100],
    }
    store.entries.append(entry)

    # Update type-context map (which keywords associate with which agent)
    if agent_type not in store.type_context_map:
        store.type_context_map[agent_type] = []
    existing_kw = set(store.type_context_map[agent_type])
    for kw in keywords:
        if kw not in existing_kw:
            store.type_context_map[agent_type].append(kw)
    # Trim to last 20 keywords per type
    store.type_context_map[agent_type] = store.type_context_map[agent_type][-20:]

    # Update co-occurrence (track pairs of agents used in same 10-min window)
    recent_types = set()
    for e in store.entries[-20:]:
        ts = e.get("timestamp", "")
        if ts[:15] == timestamp[:15]:  # Same ~minute window
            recent_types.add(e.get("agent_type", ""))
    recent_types.discard(agent_type)
    for other in recent_types:
        pair_key = "|".join(sorted([agent_type, other]))
        store.co_occurrence[pair_key] = store.co_occurrence.get(pair_key, 0) + 1

    save_agent_patterns(store)
    logger.info(f"Tracked agent: {agent_type} model={model} keywords={keywords}")


def get_agent_recommendations(
    context: str = "",
    min_confidence: float = 0.7,
    max_results: int = 3,
) -> List[Dict[str, Any]]:
    """Predict best agent types for a given context."""
    store = load_agent_patterns()
    keywords = set(extract_context_keywords(context))

    if not keywords or not store.type_context_map:
        return []

    # Score each agent type by keyword overlap
    scored = []
    for agent_type, agent_keywords in store.type_context_map.items():
        overlap = len(keywords & set(agent_keywords))
        if overlap == 0:
            continue
        # Count frequency
        freq = sum(1 for e in store.entries if e.get("agent_type") == agent_type)
        confidence = min(0.95, overlap / max(len(keywords), 1) * 0.5 + min(freq / 50, 0.45))
        if confidence >= min_confidence:
            scored.append({
                "agent_type": agent_type,
                "confidence": round(confidence, 2),
                "frequency": freq,
                "matching_keywords": list(keywords & set(agent_keywords)),
            })

    scored.sort(key=lambda x: -x["confidence"])
    return scored[:max_results]


def get_agent_co_occurrence(min_count: int = 2) -> List[Dict[str, Any]]:
    """Get commonly co-occurring agent pairs."""
    store = load_agent_patterns()
    pairs = []
    for pair_key, count in store.co_occurrence.items():
        if count >= min_count:
            agents = pair_key.split("|")
            if len(agents) == 2:
                pairs.append({
                    "agent_1": agents[0],
                    "agent_2": agents[1],
                    "count": count,
                })
    pairs.sort(key=lambda x: -x["count"])
    return pairs


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Intent Prediction System")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Track command
    track_parser = subparsers.add_parser("track", help="Track a tool usage")
    track_parser.add_argument("--tool", required=True, help="Tool name")
    track_parser.add_argument("--context", default="", help="Context string")
    track_parser.add_argument("--project", default="global", help="Project path")

    # Predict command
    predict_parser = subparsers.add_parser("predict", help="Get predictions")
    predict_parser.add_argument("--context", default="", help="Context string")
    predict_parser.add_argument("--project", default="global", help="Project path")
    predict_parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence")
    predict_parser.add_argument("--max", type=int, default=3, help="Max results")
    predict_parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")

    # List command
    list_parser = subparsers.add_parser("list", help="List all patterns")
    list_parser.add_argument("--format", choices=["json", "table"], default="table", help="Output format")

    # Clear command
    subparsers.add_parser("clear", help="Clear all patterns")

    # Agent tracking commands (Batch 2B.3)
    track_agent_parser = subparsers.add_parser("track-agent", help="Track an agent spawn")
    track_agent_parser.add_argument("--type", required=True, help="Agent type")
    track_agent_parser.add_argument("--context", default="", help="Context string")
    track_agent_parser.add_argument("--model", default="", help="Model used")
    track_agent_parser.add_argument("--prompt", default="", help="Prompt preview")

    agent_stats_parser = subparsers.add_parser("agent-stats", help="Show agent routing stats")
    agent_stats_parser.add_argument("--format", choices=["json", "table"], default="table")

    agent_rec_parser = subparsers.add_parser("agent-recommend", help="Get agent recommendations")
    agent_rec_parser.add_argument("--context", required=True, help="Context for recommendation")
    agent_rec_parser.add_argument("--min-confidence", type=float, default=0.7)

    args = parser.parse_args()

    if args.command == "track":
        result = track_tool_usage(args.tool, args.context, args.project)
        if result:
            print(f"Pattern updated: {result.id} (confidence: {result.confidence:.2f})")
        else:
            print("Tool tracked, no pattern created yet")

    elif args.command == "predict":
        predictions = get_predictions(
            args.context,
            args.project,
            args.min_confidence,
            args.max
        )
        if args.format == "markdown":
            print(format_predictions_for_briefing(predictions))
        else:
            print(json.dumps([p.to_dict() for p in predictions], indent=2))

    elif args.command == "list":
        patterns = list_all_patterns()
        if args.format == "table":
            print(f"{'ID':<10} {'Trigger':<30} {'Action':<20} {'Freq':>5} {'Conf':>6}")
            print("-" * 75)
            for p in patterns:
                print(f"{p.id:<10} {p.trigger[:28]:<30} {p.predicted_action[:18]:<20} {p.frequency:>5} {p.confidence:>5.1%}")
        else:
            print(json.dumps([p.to_dict() for p in patterns], indent=2))

    elif args.command == "clear":
        clear_patterns()
        print("All patterns cleared")

    elif args.command == "track-agent":
        track_agent_usage(args.type, args.context, args.model, args.prompt)
        print(f"Agent tracked: {args.type}")

    elif args.command == "agent-stats":
        store = load_agent_patterns()
        from collections import Counter as C
        type_freq = C(e.get("agent_type", "?") for e in store.entries)
        if args.format == "table":
            print(f"Agent patterns: {len(store.entries)} entries, {len(store.type_context_map)} types")
            print(f"\n{'Type':<30} {'Count':>6}")
            print("-" * 38)
            for t, c in type_freq.most_common(15):
                print(f"{t:<30} {c:>6}")
            co = get_agent_co_occurrence()
            if co:
                print(f"\nCo-occurrence pairs:")
                for p in co[:5]:
                    print(f"  {p['agent_1']} + {p['agent_2']}: {p['count']}x")
        else:
            print(json.dumps({
                "entries": len(store.entries),
                "types": dict(type_freq),
                "co_occurrence": get_agent_co_occurrence(),
            }, indent=2))

    elif args.command == "agent-recommend":
        recs = get_agent_recommendations(args.context, args.min_confidence)
        if recs:
            for r in recs:
                print(f"  {r['agent_type']} ({r['confidence']:.0%}) — freq: {r['frequency']}, match: {r['matching_keywords']}")
        else:
            print("No recommendations (insufficient data or no keyword match)")

    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"Error: {e}")
