"""
CTM Tiered Memory Management

Implements MemGPT-style tiered memory architecture with:
- L1 Active: Current task context (in-prompt, fastest access)
- L2 Working: Hot agent pool (quick retrieval)
- L3 Episodic: Timestamped session history (temporal queries)
- L4 Semantic: Knowledge graph + RAG (semantic search)

Memory pressure at 70% triggers automatic compression and demotion.
Inspired by:
- MemGPT virtual context management
- Human prefrontal cortex working memory
- Cognitive workspace paradigm
"""

import json
import math
import subprocess
from enum import Enum, IntEnum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict

from config import load_config, get_ctm_dir
from agents import Agent, get_agent, update_agent


class MemoryTier(IntEnum):
    """Memory tiers ordered by accessibility (lower = faster)."""
    L1_ACTIVE = 1      # Current task context, in-prompt
    L2_WORKING = 2     # Hot agent pool, quick retrieval
    L3_EPISODIC = 3    # Timestamped sessions, temporal queries
    L4_SEMANTIC = 4    # Knowledge graph + RAG, semantic search


@dataclass
class TierConfig:
    """Configuration for a memory tier."""
    max_agents: int
    token_budget: int
    retention_days: Optional[int] = None  # Only for L3+


@dataclass
class TierSlot:
    """A slot in a memory tier."""
    agent_id: str
    tier: MemoryTier
    loaded_at: str
    last_accessed: str
    access_count: int
    token_estimate: int
    compressed_summary: Optional[str] = None
    compression_timestamp: Optional[str] = None


@dataclass
class EpisodicEntry:
    """An entry in episodic memory (L3)."""
    agent_id: str
    session_id: str
    timestamp: str
    summary: str
    decisions: List[Dict[str, Any]]
    learnings: List[Dict[str, Any]]
    key_context: Dict[str, Any]
    token_estimate: int


@dataclass
class CompressionResult:
    """Result of compressing an agent's context."""
    summary: str
    key_facts: List[str]
    decisions_preserved: int
    learnings_preserved: int
    original_tokens: int
    compressed_tokens: int
    compression_ratio: float


class TieredMemoryManager:
    """
    Manages 4-tier memory hierarchy with automatic promotion/demotion.

    Like the brain's memory consolidation, context flows from active
    working memory to long-term semantic storage through compression
    and summarization.
    """

    def __init__(self):
        self.config = load_config()
        self.ctm_dir = get_ctm_dir()
        self.state_path = self.ctm_dir / "tiered-memory.json"
        self.episodic_dir = self.ctm_dir / "episodic"
        self._state = self._load_state()
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """Ensure required directories exist."""
        self.episodic_dir.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, Any]:
        """Load tiered memory state."""
        if not self.state_path.exists():
            return {
                "version": "2.0.0",
                "tiers": {
                    "L1_ACTIVE": {"slots": {}, "token_usage": 0},
                    "L2_WORKING": {"slots": {}, "token_usage": 0},
                    "L3_EPISODIC": {"entries": [], "token_usage": 0},
                    "L4_SEMANTIC": {"indexed": [], "last_sync": None}
                },
                "pressure_events": [],
                "compression_stats": {
                    "total_compressions": 0,
                    "tokens_saved": 0,
                    "avg_compression_ratio": 0.0
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        """Save tiered memory state."""
        self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    @property
    def tier_configs(self) -> Dict[MemoryTier, TierConfig]:
        """Get tier configurations from config."""
        mem_config = self.config.raw.get("memory_tiers", {})
        return {
            MemoryTier.L1_ACTIVE: TierConfig(
                max_agents=mem_config.get("l1_max_agents", 2),
                token_budget=mem_config.get("l1_token_budget", 4000)
            ),
            MemoryTier.L2_WORKING: TierConfig(
                max_agents=mem_config.get("l2_max_agents", 5),
                token_budget=mem_config.get("l2_token_budget", 8000)
            ),
            MemoryTier.L3_EPISODIC: TierConfig(
                max_agents=999,  # Unlimited
                token_budget=50000,
                retention_days=mem_config.get("l3_retention_days", 30)
            ),
            MemoryTier.L4_SEMANTIC: TierConfig(
                max_agents=999,  # Unlimited (stored in RAG)
                token_budget=999999,
                retention_days=None  # Permanent
            )
        }

    @property
    def pressure_threshold(self) -> float:
        """Get memory pressure threshold (default 70%)."""
        return self.config.raw.get("memory_tiers", {}).get("pressure_threshold", 0.7)

    def get_tier_state(self, tier: MemoryTier) -> Dict[str, Any]:
        """Get current state of a tier."""
        tier_key = tier.name
        return self._state["tiers"].get(tier_key, {"slots": {}, "token_usage": 0})

    def check_pressure(self, tier: MemoryTier) -> Tuple[bool, float]:
        """
        Check if a tier is under memory pressure.

        Returns (is_under_pressure, current_usage_ratio).
        """
        config = self.tier_configs[tier]
        tier_state = self.get_tier_state(tier)

        # Check slot count
        if tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
            slot_count = len(tier_state.get("slots", {}))
            slot_ratio = slot_count / config.max_agents
        else:
            slot_ratio = 0  # Episodic and semantic don't have slot limits

        # Check token budget
        token_usage = tier_state.get("token_usage", 0)
        token_ratio = token_usage / config.token_budget

        # Use max of both ratios
        usage_ratio = max(slot_ratio, token_ratio)
        is_under_pressure = usage_ratio >= self.pressure_threshold

        return is_under_pressure, usage_ratio

    def select_for_demotion(self, tier: MemoryTier) -> Optional[str]:
        """
        Select the best agent to demote from a tier.

        Uses weighted scoring based on:
        - Time since last access (higher = demote)
        - Access frequency (lower = demote)
        - Token cost (higher = demote)
        """
        tier_state = self.get_tier_state(tier)
        slots = tier_state.get("slots", {})

        if not slots:
            return None

        now = datetime.now(timezone.utc)
        scores = []

        for agent_id, slot_data in slots.items():
            last_accessed = datetime.fromisoformat(
                slot_data["last_accessed"].rstrip("Z")
            ).replace(tzinfo=timezone.utc)

            # Time decay (hours since access)
            hours_since = (now - last_accessed).total_seconds() / 3600
            time_score = math.log(1 + hours_since)  # Log to dampen extreme values

            # Frequency score (inverse of access count)
            frequency_score = 1 / (1 + math.log(1 + slot_data["access_count"]))

            # Token cost score (normalized)
            token_score = slot_data["token_estimate"] / self.tier_configs[tier].token_budget

            # Combined demotion score (higher = demote first)
            demotion_score = (time_score * 0.5) + (frequency_score * 0.3) + (token_score * 0.2)
            scores.append((agent_id, demotion_score))

        # Return agent with highest demotion score
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[0][0] if scores else None

    def promote(self, agent_id: str, to_tier: MemoryTier) -> bool:
        """
        Promote an agent to a higher (more accessible) tier.

        Returns True if successful.
        """
        agent = get_agent(agent_id)
        if not agent:
            return False

        # Find current tier
        current_tier = self._find_agent_tier(agent_id)
        if current_tier is None:
            # Agent not in tiered memory, add to target tier
            return self._add_to_tier(agent_id, to_tier, agent)

        if to_tier >= current_tier:
            # Can't promote to same or lower tier
            return False

        # Check if target tier has capacity
        is_under_pressure, _ = self.check_pressure(to_tier)
        if is_under_pressure:
            # Need to demote something first
            demote_id = self.select_for_demotion(to_tier)
            if demote_id:
                self.demote(demote_id)

        # Remove from current tier
        self._remove_from_tier(agent_id, current_tier)

        # Add to new tier
        return self._add_to_tier(agent_id, to_tier, agent)

    def demote(self, agent_id: str) -> bool:
        """
        Demote an agent to the next lower tier.

        Applies compression when moving from L2 to L3.
        Returns True if successful.
        """
        current_tier = self._find_agent_tier(agent_id)
        if current_tier is None:
            return False

        if current_tier == MemoryTier.L4_SEMANTIC:
            # Already at lowest tier
            return False

        # Get agent data before removing
        tier_state = self.get_tier_state(current_tier)
        slot_data = tier_state.get("slots", {}).get(agent_id)

        agent = get_agent(agent_id)
        if not agent:
            return False

        # Determine target tier
        target_tier = MemoryTier(current_tier + 1)

        # Apply compression if moving to L3 or L4
        compressed_summary = None
        if target_tier in [MemoryTier.L3_EPISODIC, MemoryTier.L4_SEMANTIC]:
            compression = self.compress(agent)
            compressed_summary = compression.summary if compression else None

            # Update compression stats
            if compression:
                stats = self._state["compression_stats"]
                stats["total_compressions"] += 1
                stats["tokens_saved"] += compression.original_tokens - compression.compressed_tokens
                # Running average
                n = stats["total_compressions"]
                stats["avg_compression_ratio"] = (
                    (stats["avg_compression_ratio"] * (n - 1) + compression.compression_ratio) / n
                )

        # Remove from current tier
        self._remove_from_tier(agent_id, current_tier)

        # Add to target tier
        if target_tier == MemoryTier.L3_EPISODIC:
            # Add as episodic entry
            return self._add_episodic_entry(agent, compressed_summary)
        elif target_tier == MemoryTier.L4_SEMANTIC:
            # Index to RAG
            return self._index_to_semantic(agent, compressed_summary)
        else:
            return self._add_to_tier(agent_id, target_tier, agent)

    def compress(self, agent: Agent) -> Optional[CompressionResult]:
        """
        Compress an agent's context for lower-tier storage.

        Uses Haiku for efficiency.
        """
        # Build context string
        context_parts = []

        context_parts.append(f"Task: {agent.task.get('title', 'Unknown')}")
        context_parts.append(f"Goal: {agent.task.get('goal', '')}")
        context_parts.append(f"Status: {agent.state.get('status', 'unknown')}")
        context_parts.append(f"Progress: {agent.state.get('progress_pct', 0)}%")

        if agent.context.get("decisions"):
            context_parts.append("Decisions:")
            for d in agent.context["decisions"][:10]:  # Limit to 10
                text = d.get("text", "") if isinstance(d, dict) else str(d)
                context_parts.append(f"  - {text}")

        if agent.context.get("learnings"):
            context_parts.append("Learnings:")
            for l in agent.context["learnings"][:10]:
                text = l.get("text", "") if isinstance(l, dict) else str(l)
                context_parts.append(f"  - {text}")

        original_text = "\n".join(context_parts)
        original_tokens = len(original_text) // 4  # Rough estimate

        # Generate compressed summary
        # For now, use a simple extraction approach
        # TODO: Use Haiku API for intelligent summarization

        key_facts = []
        key_facts.append(f"Task: {agent.task.get('title', 'Unknown')}")
        key_facts.append(f"Goal: {agent.task.get('goal', '')[:100]}")
        key_facts.append(f"Status: {agent.state.get('status', 'unknown')} ({agent.state.get('progress_pct', 0)}%)")

        # Extract top decisions (by confidence if available)
        decisions = agent.context.get("decisions", [])
        for d in decisions[:3]:
            text = d.get("text", "") if isinstance(d, dict) else str(d)
            if len(text) > 10:
                key_facts.append(f"Decision: {text[:80]}")

        # Extract top learnings
        learnings = agent.context.get("learnings", [])
        for l in learnings[:3]:
            text = l.get("text", "") if isinstance(l, dict) else str(l)
            if len(text) > 10:
                key_facts.append(f"Learning: {text[:80]}")

        summary = " | ".join(key_facts[:8])
        compressed_tokens = len(summary) // 4

        return CompressionResult(
            summary=summary,
            key_facts=key_facts,
            decisions_preserved=min(3, len(decisions)),
            learnings_preserved=min(3, len(learnings)),
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            compression_ratio=compressed_tokens / max(1, original_tokens)
        )

    def _find_agent_tier(self, agent_id: str) -> Optional[MemoryTier]:
        """Find which tier an agent is currently in."""
        for tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
            tier_state = self.get_tier_state(tier)
            if agent_id in tier_state.get("slots", {}):
                return tier

        # Check episodic
        for entry in self._state["tiers"]["L3_EPISODIC"].get("entries", []):
            if entry.get("agent_id") == agent_id:
                return MemoryTier.L3_EPISODIC

        # Check semantic
        if agent_id in self._state["tiers"]["L4_SEMANTIC"].get("indexed", []):
            return MemoryTier.L4_SEMANTIC

        return None

    def _add_to_tier(self, agent_id: str, tier: MemoryTier, agent: Agent) -> bool:
        """Add agent to a specific tier."""
        tier_key = tier.name
        now = datetime.now(timezone.utc).isoformat()

        # Estimate tokens
        token_estimate = self._estimate_tokens(agent)

        if tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
            self._state["tiers"][tier_key]["slots"][agent_id] = {
                "loaded_at": now,
                "last_accessed": now,
                "access_count": 1,
                "token_estimate": token_estimate
            }
            self._state["tiers"][tier_key]["token_usage"] += token_estimate

        self._save_state()
        return True

    def _remove_from_tier(self, agent_id: str, tier: MemoryTier) -> None:
        """Remove agent from a tier."""
        tier_key = tier.name

        if tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
            slots = self._state["tiers"][tier_key].get("slots", {})
            if agent_id in slots:
                token_estimate = slots[agent_id].get("token_estimate", 0)
                del slots[agent_id]
                self._state["tiers"][tier_key]["token_usage"] -= token_estimate
        elif tier == MemoryTier.L3_EPISODIC:
            entries = self._state["tiers"][tier_key].get("entries", [])
            self._state["tiers"][tier_key]["entries"] = [
                e for e in entries if e.get("agent_id") != agent_id
            ]
        elif tier == MemoryTier.L4_SEMANTIC:
            indexed = self._state["tiers"][tier_key].get("indexed", [])
            if agent_id in indexed:
                indexed.remove(agent_id)

        self._save_state()

    def _add_episodic_entry(self, agent: Agent, summary: Optional[str] = None) -> bool:
        """Add an agent to episodic memory as a session entry."""
        now = datetime.now(timezone.utc).isoformat()

        entry = {
            "agent_id": agent.id,
            "session_id": f"{agent.id}-{now[:10]}",
            "timestamp": now,
            "summary": summary or f"Task: {agent.task.get('title', 'Unknown')}",
            "decisions": agent.context.get("decisions", [])[:5],
            "learnings": agent.context.get("learnings", [])[:5],
            "key_context": {
                "title": agent.task.get("title"),
                "goal": agent.task.get("goal", "")[:200],
                "status": agent.state.get("status"),
                "progress": agent.state.get("progress_pct", 0)
            },
            "token_estimate": len(summary or "") // 4 + 100
        }

        self._state["tiers"]["L3_EPISODIC"]["entries"].append(entry)
        self._state["tiers"]["L3_EPISODIC"]["token_usage"] += entry["token_estimate"]

        # Save to episodic file for persistence
        episodic_file = self.episodic_dir / f"{agent.id}.json"
        if episodic_file.exists():
            with open(episodic_file, 'r') as f:
                entries = json.load(f)
        else:
            entries = []
        entries.append(entry)
        with open(episodic_file, 'w') as f:
            json.dump(entries, f, indent=2)

        self._save_state()
        return True

    def _index_to_semantic(self, agent: Agent, summary: Optional[str] = None) -> bool:
        """Index agent to semantic memory (RAG)."""
        # Check if RAG is available
        project_path = agent.context.get("project")
        if not project_path:
            project_path = str(self.ctm_dir)

        # Build content for indexing
        content = []
        content.append(f"# Agent: {agent.id}")
        content.append(f"## Task: {agent.task.get('title', 'Unknown')}")
        content.append(f"Goal: {agent.task.get('goal', '')}")
        content.append(f"Status: {agent.state.get('status', 'unknown')}")

        if summary:
            content.append(f"## Summary\n{summary}")

        if agent.context.get("decisions"):
            content.append("## Decisions")
            for d in agent.context["decisions"]:
                text = d.get("text", "") if isinstance(d, dict) else str(d)
                content.append(f"- {text}")

        if agent.context.get("learnings"):
            content.append("## Learnings")
            for l in agent.context["learnings"]:
                text = l.get("text", "") if isinstance(l, dict) else str(l)
                content.append(f"- {text}")

        # Write to temp file for indexing
        semantic_file = self.ctm_dir / "semantic" / f"{agent.id}.md"
        semantic_file.parent.mkdir(parents=True, exist_ok=True)
        semantic_file.write_text("\n".join(content))

        # Mark as indexed
        if agent.id not in self._state["tiers"]["L4_SEMANTIC"]["indexed"]:
            self._state["tiers"]["L4_SEMANTIC"]["indexed"].append(agent.id)
        self._state["tiers"]["L4_SEMANTIC"]["last_sync"] = datetime.now(timezone.utc).isoformat()

        self._save_state()
        return True

    def _estimate_tokens(self, agent: Agent) -> int:
        """Estimate token count for an agent."""
        tokens = 200  # Base overhead

        tokens += len(agent.task.get("title", "")) // 4
        tokens += len(agent.task.get("goal", "")) // 4

        for d in agent.context.get("decisions", []):
            text = d.get("text", "") if isinstance(d, dict) else str(d)
            tokens += len(text) // 4

        for l in agent.context.get("learnings", []):
            text = l.get("text", "") if isinstance(l, dict) else str(l)
            tokens += len(text) // 4

        tokens += len(agent.context.get("key_files", [])) * 20

        return max(100, tokens)

    def touch(self, agent_id: str) -> None:
        """Update access time for an agent."""
        tier = self._find_agent_tier(agent_id)
        if tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
            tier_key = tier.name
            if agent_id in self._state["tiers"][tier_key]["slots"]:
                self._state["tiers"][tier_key]["slots"][agent_id]["last_accessed"] = \
                    datetime.now(timezone.utc).isoformat()
                self._state["tiers"][tier_key]["slots"][agent_id]["access_count"] += 1
                self._save_state()

    def check_and_manage_pressure(self) -> List[str]:
        """
        Check all tiers for pressure and auto-manage.

        Returns list of actions taken.
        """
        actions = []

        # Check L1 first (highest priority)
        is_pressure, ratio = self.check_pressure(MemoryTier.L1_ACTIVE)
        while is_pressure:
            demote_id = self.select_for_demotion(MemoryTier.L1_ACTIVE)
            if demote_id:
                self.demote(demote_id)
                actions.append(f"Demoted {demote_id} from L1 to L2 (pressure: {ratio:.0%})")
                is_pressure, ratio = self.check_pressure(MemoryTier.L1_ACTIVE)
            else:
                break

        # Check L2
        is_pressure, ratio = self.check_pressure(MemoryTier.L2_WORKING)
        while is_pressure:
            demote_id = self.select_for_demotion(MemoryTier.L2_WORKING)
            if demote_id:
                self.demote(demote_id)
                actions.append(f"Demoted {demote_id} from L2 to L3 (pressure: {ratio:.0%})")
                is_pressure, ratio = self.check_pressure(MemoryTier.L2_WORKING)
            else:
                break

        # Clean old episodic entries
        retention_days = self.tier_configs[MemoryTier.L3_EPISODIC].retention_days or 30
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        old_entries = [
            e for e in self._state["tiers"]["L3_EPISODIC"].get("entries", [])
            if datetime.fromisoformat(e["timestamp"].rstrip("Z")).replace(tzinfo=timezone.utc) < cutoff
        ]

        for entry in old_entries:
            agent = get_agent(entry["agent_id"])
            if agent:
                self._index_to_semantic(agent, entry.get("summary"))
                actions.append(f"Consolidated {entry['agent_id']} from L3 to L4 (age: {retention_days}+ days)")

        # Remove old entries
        self._state["tiers"]["L3_EPISODIC"]["entries"] = [
            e for e in self._state["tiers"]["L3_EPISODIC"].get("entries", [])
            if datetime.fromisoformat(e["timestamp"].rstrip("Z")).replace(tzinfo=timezone.utc) >= cutoff
        ]

        if actions:
            self._state["pressure_events"].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actions": actions
            })
            # Keep only last 100 events
            self._state["pressure_events"] = self._state["pressure_events"][-100:]
            self._save_state()

        return actions

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive memory tier statistics."""
        stats = {
            "tiers": {},
            "compression": self._state["compression_stats"],
            "recent_pressure_events": self._state["pressure_events"][-5:]
        }

        for tier in MemoryTier:
            config = self.tier_configs[tier]
            tier_state = self.get_tier_state(tier)
            is_pressure, ratio = self.check_pressure(tier)

            if tier in [MemoryTier.L1_ACTIVE, MemoryTier.L2_WORKING]:
                slot_count = len(tier_state.get("slots", {}))
                stats["tiers"][tier.name] = {
                    "agents": slot_count,
                    "max_agents": config.max_agents,
                    "token_usage": tier_state.get("token_usage", 0),
                    "token_budget": config.token_budget,
                    "usage_ratio": ratio,
                    "under_pressure": is_pressure
                }
            elif tier == MemoryTier.L3_EPISODIC:
                entry_count = len(tier_state.get("entries", []))
                stats["tiers"][tier.name] = {
                    "entries": entry_count,
                    "retention_days": config.retention_days,
                    "token_usage": tier_state.get("token_usage", 0)
                }
            else:  # L4_SEMANTIC
                indexed_count = len(tier_state.get("indexed", []))
                stats["tiers"][tier.name] = {
                    "indexed_agents": indexed_count,
                    "last_sync": tier_state.get("last_sync")
                }

        return stats


def get_tiered_memory() -> TieredMemoryManager:
    """Get a tiered memory manager instance."""
    return TieredMemoryManager()


def check_memory_pressure() -> List[str]:
    """Check and manage memory pressure across all tiers."""
    mm = TieredMemoryManager()
    return mm.check_and_manage_pressure()
