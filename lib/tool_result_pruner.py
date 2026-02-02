#!/usr/bin/env python3
"""
Tool Result Pruner

Prunes old tool results from conversation context to save tokens.
Supports soft-trim (truncate) and hard-clear (replace) strategies.

Part of: OpenClaw-inspired improvements (Phase 1, F03)
Created: 2026-01-30
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class TrimStrategy(Enum):
    """Pruning strategies for tool results."""
    NONE = "none"       # Keep as-is
    SOFT = "soft"       # Truncate to first/last N chars
    HARD = "hard"       # Replace with placeholder
    REMOVE = "remove"   # Remove entirely

@dataclass
class ToolRule:
    """Pruning rule for a specific tool."""
    tool_name: str
    strategy: TrimStrategy = TrimStrategy.SOFT
    ttl_minutes: int = 60
    size_threshold: int = 500

@dataclass
class PruneConfig:
    """Global pruning configuration."""

    # Defaults
    default_ttl_minutes: int = 60
    default_strategy: TrimStrategy = TrimStrategy.SOFT

    # Protection
    keep_last_assistants: int = 3
    never_prune_tools: List[str] = field(default_factory=lambda: [
        "Write", "Edit", "NotebookEdit"  # Mutations preserved
    ])
    skip_image_results: bool = True

    # Soft trim settings
    soft_trim_keep_start: int = 200
    soft_trim_keep_end: int = 100

    # Hard clear settings
    hard_clear_placeholder: str = "[Tool result cleared - aged {age}min, was {size} chars]"

    # Tool-specific rules
    tool_rules: Dict[str, ToolRule] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str = "~/.claude/config/pruning.json") -> "PruneConfig":
        """Load config from file or return defaults."""
        config_path = Path(path).expanduser()

        if not config_path.exists():
            return cls()

        try:
            with open(config_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return cls()

        # Parse tool rules
        tool_rules = {}
        for name, rule_data in data.get("tool_rules", {}).items():
            tool_rules[name] = ToolRule(
                tool_name=name,
                strategy=TrimStrategy(rule_data.get("strategy", "soft")),
                ttl_minutes=rule_data.get("ttl_minutes", 60),
                size_threshold=rule_data.get("size_threshold", 500)
            )

        return cls(
            default_ttl_minutes=data.get("default_ttl_minutes", 60),
            default_strategy=TrimStrategy(data.get("default_strategy", "soft")),
            keep_last_assistants=data.get("keep_last_assistants", 3),
            never_prune_tools=data.get("never_prune_tools", cls().never_prune_tools),
            skip_image_results=data.get("skip_image_results", True),
            soft_trim_keep_start=data.get("soft_trim_keep_start", 200),
            soft_trim_keep_end=data.get("soft_trim_keep_end", 100),
            hard_clear_placeholder=data.get(
                "hard_clear_placeholder",
                "[Tool result cleared - aged {age}min, was {size} chars]"
            ),
            tool_rules=tool_rules
        )

    def save(self, path: str = "~/.claude/config/pruning.json"):
        """Save config to file."""
        config_path = Path(path).expanduser()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "default_ttl_minutes": self.default_ttl_minutes,
            "default_strategy": self.default_strategy.value,
            "keep_last_assistants": self.keep_last_assistants,
            "never_prune_tools": self.never_prune_tools,
            "skip_image_results": self.skip_image_results,
            "soft_trim_keep_start": self.soft_trim_keep_start,
            "soft_trim_keep_end": self.soft_trim_keep_end,
            "hard_clear_placeholder": self.hard_clear_placeholder,
            "tool_rules": {
                name: {
                    "strategy": rule.strategy.value,
                    "ttl_minutes": rule.ttl_minutes,
                    "size_threshold": rule.size_threshold
                }
                for name, rule in self.tool_rules.items()
            }
        }

        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)


class ToolResultPruner:
    """Prunes old tool results from message history."""

    def __init__(self, config: Optional[PruneConfig] = None):
        self.config = config or PruneConfig.load()

    def get_rule(self, tool_name: str) -> ToolRule:
        """Get pruning rule for a tool."""
        if tool_name in self.config.tool_rules:
            return self.config.tool_rules[tool_name]

        return ToolRule(
            tool_name=tool_name,
            strategy=self.config.default_strategy,
            ttl_minutes=self.config.default_ttl_minutes
        )

    def should_prune(self, msg: dict, now: float) -> bool:
        """Check if a tool result should be pruned."""
        if msg.get("role") != "tool_result":
            return False

        tool_name = msg.get("tool_name", msg.get("name", ""))

        # Never prune protected tools
        if tool_name in self.config.never_prune_tools:
            return False

        # Skip image results
        if self.config.skip_image_results and self._has_image(msg):
            return False

        # Check age
        rule = self.get_rule(tool_name)
        timestamp = msg.get("timestamp", msg.get("created_at", now))
        if isinstance(timestamp, str):
            # Try to parse ISO format
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except:
                timestamp = now

        age_minutes = (now - timestamp) / 60
        return age_minutes > rule.ttl_minutes

    def _has_image(self, msg: dict) -> bool:
        """Check if message contains image content."""
        content = msg.get("content", "")
        if isinstance(content, list):
            return any(
                isinstance(block, dict) and block.get("type") == "image"
                for block in content
            )
        return False

    def prune_message(self, msg: dict, now: float) -> dict:
        """Apply pruning to a single message."""
        tool_name = msg.get("tool_name", msg.get("name", ""))
        rule = self.get_rule(tool_name)
        content = msg.get("content", "")

        if not isinstance(content, str):
            return msg  # Skip non-string content

        original_size = len(content)
        timestamp = msg.get("timestamp", msg.get("created_at", now))
        if isinstance(timestamp, str):
            try:
                from datetime import datetime
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
            except:
                timestamp = now

        age_minutes = int((now - timestamp) / 60)

        if rule.strategy == TrimStrategy.HARD:
            # Replace entirely
            msg = msg.copy()
            msg["content"] = self.config.hard_clear_placeholder.format(
                age=age_minutes,
                size=original_size
            )
            msg["_pruned"] = "hard"
            msg["_original_size"] = original_size

        elif rule.strategy == TrimStrategy.SOFT:
            # Truncate if over threshold
            if original_size > rule.size_threshold:
                msg = msg.copy()
                start = content[:self.config.soft_trim_keep_start]
                end = content[-self.config.soft_trim_keep_end:]
                trimmed = original_size - self.config.soft_trim_keep_start - self.config.soft_trim_keep_end

                msg["content"] = (
                    f"{start}\n\n"
                    f"...[{trimmed:,} chars trimmed, aged {age_minutes}min]...\n\n"
                    f"{end}"
                )
                msg["_pruned"] = "soft"
                msg["_original_size"] = original_size

        elif rule.strategy == TrimStrategy.REMOVE:
            msg = msg.copy()
            msg["_pruned"] = "remove"

        return msg

    def get_protected_indices(self, messages: List[dict]) -> set:
        """Get indices of messages that should not be pruned."""
        protected = set()
        assistant_count = 0

        # Walk backwards to find last N assistants
        for i in range(len(messages) - 1, -1, -1):
            role = messages[i].get("role", "")
            if role == "assistant":
                assistant_count += 1
                if assistant_count <= self.config.keep_last_assistants:
                    protected.add(i)
                    # Protect following tool results
                    for j in range(i + 1, len(messages)):
                        j_role = messages[j].get("role", "")
                        if j_role == "tool_result":
                            protected.add(j)
                        elif j_role == "assistant":
                            break

        return protected

    def prune(self, messages: List[dict]) -> Tuple[List[dict], dict]:
        """
        Prune old tool results from message history.

        Returns:
            Tuple of (pruned messages, stats dict)
        """
        now = time.time()
        protected = self.get_protected_indices(messages)

        pruned = []
        stats = {
            "soft": 0,
            "hard": 0,
            "removed": 0,
            "protected": len(protected),
            "total_original": len(messages),
            "bytes_saved": 0
        }

        for i, msg in enumerate(messages):
            if i in protected:
                pruned.append(msg)
                continue

            if self.should_prune(msg, now):
                original_size = len(str(msg.get("content", "")))
                msg = self.prune_message(msg, now)

                prune_type = msg.get("_pruned")
                if prune_type == "remove":
                    stats["removed"] += 1
                    stats["bytes_saved"] += original_size
                    continue  # Skip adding to result
                elif prune_type:
                    stats[prune_type] += 1
                    new_size = len(str(msg.get("content", "")))
                    stats["bytes_saved"] += original_size - new_size

            pruned.append(msg)

        stats["total_pruned"] = len(pruned)
        return pruned, stats


def get_prune_recommendations(messages: List[dict]) -> dict:
    """
    Analyze messages and recommend pruning actions.

    Returns dict with:
    - prune_candidates: list of messages that could be pruned
    - protected_count: number of protected messages
    - potential_savings: estimated bytes that could be saved
    - total_tool_results: total tool results in history
    """
    pruner = ToolResultPruner()
    now = time.time()

    recommendations = {
        "prune_candidates": [],
        "protected_count": 0,
        "potential_savings": 0,
        "total_tool_results": 0,
        "by_tool": {}
    }

    protected = pruner.get_protected_indices(messages)
    recommendations["protected_count"] = len(protected)

    for i, msg in enumerate(messages):
        if msg.get("role") != "tool_result":
            continue

        recommendations["total_tool_results"] += 1
        tool_name = msg.get("tool_name", msg.get("name", "unknown"))

        # Track by tool
        if tool_name not in recommendations["by_tool"]:
            recommendations["by_tool"][tool_name] = {"count": 0, "size": 0}

        content = msg.get("content", "")
        size = len(content) if isinstance(content, str) else 0
        recommendations["by_tool"][tool_name]["count"] += 1
        recommendations["by_tool"][tool_name]["size"] += size

        if i in protected:
            continue

        if pruner.should_prune(msg, now):
            timestamp = msg.get("timestamp", msg.get("created_at", now))
            if isinstance(timestamp, str):
                try:
                    from datetime import datetime
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).timestamp()
                except:
                    timestamp = now

            age = int((now - timestamp) / 60)

            recommendations["prune_candidates"].append({
                "index": i,
                "tool": tool_name,
                "age_minutes": age,
                "size_chars": size
            })
            recommendations["potential_savings"] += size

    return recommendations


def format_recommendations(recommendations: dict) -> str:
    """Format recommendations as human-readable text."""
    lines = []
    lines.append("═══ Tool Result Pruning Analysis ═══\n")

    lines.append(f"Total tool results: {recommendations['total_tool_results']}")
    lines.append(f"Protected (recent): {recommendations['protected_count']}")
    lines.append(f"Prune candidates: {len(recommendations['prune_candidates'])}")
    lines.append(f"Potential savings: {recommendations['potential_savings']:,} chars")

    if recommendations["by_tool"]:
        lines.append("\nBy Tool:")
        for tool, data in sorted(recommendations["by_tool"].items(),
                                  key=lambda x: x[1]["size"], reverse=True):
            lines.append(f"  {tool}: {data['count']} results, {data['size']:,} chars")

    if recommendations["prune_candidates"]:
        lines.append("\nPrune Candidates (oldest first):")
        for candidate in sorted(recommendations["prune_candidates"],
                               key=lambda x: x["age_minutes"], reverse=True)[:10]:
            lines.append(
                f"  [{candidate['age_minutes']}min] {candidate['tool']}: "
                f"{candidate['size_chars']:,} chars"
            )
        if len(recommendations["prune_candidates"]) > 10:
            lines.append(f"  ... and {len(recommendations['prune_candidates']) - 10} more")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    # CLI for testing
    config = PruneConfig.load()
    print(f"Loaded config:")
    print(f"  Default TTL: {config.default_ttl_minutes}min")
    print(f"  Default strategy: {config.default_strategy.value}")
    print(f"  Protected tools: {config.never_prune_tools}")
    print(f"  Keep last assistants: {config.keep_last_assistants}")
    print(f"  Tool rules: {list(config.tool_rules.keys())}")

    if len(sys.argv) > 1 and sys.argv[1] == "--save-default":
        # Create default config
        default_config = PruneConfig(
            tool_rules={
                "Read": ToolRule("Read", TrimStrategy.SOFT, 30, 500),
                "Grep": ToolRule("Grep", TrimStrategy.SOFT, 45, 300),
                "Glob": ToolRule("Glob", TrimStrategy.HARD, 30, 200),
                "Bash": ToolRule("Bash", TrimStrategy.SOFT, 60, 500),
                "WebFetch": ToolRule("WebFetch", TrimStrategy.SOFT, 120, 1000),
                "WebSearch": ToolRule("WebSearch", TrimStrategy.SOFT, 120, 500),
            }
        )
        default_config.save()
        print("\nSaved default config to ~/.claude/config/pruning.json")
