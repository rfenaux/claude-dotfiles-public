"""
CTM Working Memory Management

Implements bio-inspired working memory with:
- Hot agent pool (limited capacity like human 4±1 items)
- Token budget management
- Weighted LRU eviction
- Decay-based priority adjustment
- Integration with tiered memory (L1/L2) for pressure management

The working memory represents what's "in focus" - agents whose
context can be quickly retrieved without full file reads.
"""

import json
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

from config import load_config, get_ctm_dir
from agents import Agent, get_agent, AgentIndex, update_agent

# Lazy import to avoid circular dependency
_tiered_memory = None

def get_tiered_memory_manager():
    """Lazy load tiered memory manager."""
    global _tiered_memory
    if _tiered_memory is None:
        try:
            from memory_tiers import TieredMemoryManager
            _tiered_memory = TieredMemoryManager()
        except ImportError:
            _tiered_memory = None
    return _tiered_memory


@dataclass
class MemorySlot:
    """A slot in working memory for one agent."""
    agent_id: str
    loaded_at: str
    last_accessed: str
    access_count: int
    token_estimate: int
    decay_score: float


class WorkingMemory:
    """
    Working memory pool manager.

    Like the brain's phonological loop and visuospatial sketchpad,
    this maintains a limited set of active contexts that can be
    quickly accessed without full retrieval.
    """

    def __init__(self):
        self.config = load_config()
        self.state_path = get_ctm_dir() / "working-memory.json"
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load working memory state."""
        if not self.state_path.exists():
            return {
                "version": "1.0.0",
                "hot_agents": {},
                "token_usage": 0,
                "eviction_count": 0,
                "last_eviction": None
            }

        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        """Save working memory state."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    def estimate_tokens(self, agent: Agent) -> int:
        """
        Estimate token count for an agent's context.

        Rough estimate: ~4 chars per token for English text.
        """
        # Base structure
        tokens = 200  # JSON overhead

        # Task description
        tokens += len(agent.task.get("title", "")) // 4
        tokens += len(agent.task.get("goal", "")) // 4

        # Context (decisions, learnings, files)
        for decision in agent.context.get("decisions", []):
            if isinstance(decision, dict):
                tokens += len(decision.get("text", "")) // 4
            else:
                tokens += len(str(decision)) // 4

        for learning in agent.context.get("learnings", []):
            if isinstance(learning, dict):
                tokens += len(learning.get("text", "")) // 4
            else:
                tokens += len(str(learning)) // 4

        # Key files (just paths, not content)
        tokens += len(agent.context.get("key_files", [])) * 20

        # State
        tokens += len(str(agent.state.get("pending_actions", []))) // 4

        return max(100, tokens)  # Minimum 100 tokens

    def calculate_decay(self, slot: MemorySlot) -> float:
        """
        Calculate decay score for a memory slot.

        Higher score = more likely to be evicted.
        Factors: time since access, access frequency, original priority.
        """
        now = datetime.now(timezone.utc)
        last_access = datetime.fromisoformat(
            slot.last_accessed.rstrip("Z")
        ).replace(tzinfo=timezone.utc)

        # Time decay (exponential with 1-hour halflife for working memory)
        hours_since = (now - last_access).total_seconds() / 3600
        time_decay = math.pow(2, hours_since / 1)  # Fast decay

        # Frequency boost (more accesses = more important)
        frequency_factor = 1 / (1 + math.log(1 + slot.access_count))

        # Token cost factor (larger contexts cost more to keep)
        token_factor = slot.token_estimate / self.config.token_budget

        # Combined decay score (higher = evict first)
        return time_decay * frequency_factor * (1 + token_factor)

    def is_loaded(self, agent_id: str) -> bool:
        """Check if agent is in working memory."""
        return agent_id in self._state["hot_agents"]

    def load(self, agent_id: str) -> bool:
        """
        Load an agent into working memory.

        Returns True if loaded, False if eviction needed but failed.
        """
        if self.is_loaded(agent_id):
            # Update access time
            self._state["hot_agents"][agent_id]["last_accessed"] = \
                datetime.now(timezone.utc).isoformat()
            self._state["hot_agents"][agent_id]["access_count"] += 1
            self._save_state()
            return True

        agent = get_agent(agent_id)
        if not agent:
            return False

        token_estimate = self.estimate_tokens(agent)

        # Check if we need to evict
        while (len(self._state["hot_agents"]) >= self.config.max_hot_agents or
               self._state["token_usage"] + token_estimate > self.config.token_budget):

            evicted = self._evict_one()
            if not evicted:
                # Can't evict anything, fail
                return False

        # Add to working memory
        now = datetime.now(timezone.utc).isoformat()
        self._state["hot_agents"][agent_id] = {
            "loaded_at": now,
            "last_accessed": now,
            "access_count": 1,
            "token_estimate": token_estimate,
            "decay_score": 0.0
        }
        self._state["token_usage"] += token_estimate
        self._save_state()

        return True

    def _evict_one(self) -> Optional[str]:
        """
        Evict the lowest-priority agent from working memory.

        Returns the evicted agent ID or None if nothing to evict.
        """
        if not self._state["hot_agents"]:
            return None

        # Calculate decay scores and find max
        max_decay = -1
        evict_id = None

        for agent_id, slot_data in self._state["hot_agents"].items():
            slot = MemorySlot(
                agent_id=agent_id,
                loaded_at=slot_data["loaded_at"],
                last_accessed=slot_data["last_accessed"],
                access_count=slot_data["access_count"],
                token_estimate=slot_data["token_estimate"],
                decay_score=0
            )
            decay = self.calculate_decay(slot)

            if decay > max_decay:
                max_decay = decay
                evict_id = agent_id

        if evict_id:
            self._evict(evict_id)

        return evict_id

    def _evict(self, agent_id: str) -> None:
        """Evict a specific agent from working memory."""
        if agent_id not in self._state["hot_agents"]:
            return

        slot = self._state["hot_agents"][agent_id]
        self._state["token_usage"] -= slot["token_estimate"]
        del self._state["hot_agents"][agent_id]

        self._state["eviction_count"] += 1
        self._state["last_eviction"] = datetime.now(timezone.utc).isoformat()

        self._save_state()

    def unload(self, agent_id: str) -> None:
        """Explicitly unload an agent from working memory."""
        self._evict(agent_id)

    def get_loaded_agents(self) -> List[str]:
        """Get list of agent IDs in working memory."""
        return list(self._state["hot_agents"].keys())

    def get_slot(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get slot info for an agent."""
        return self._state["hot_agents"].get(agent_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get working memory statistics."""
        return {
            "loaded_count": len(self._state["hot_agents"]),
            "max_capacity": self.config.max_hot_agents,
            "token_usage": self._state["token_usage"],
            "token_budget": self.config.token_budget,
            "usage_pct": round(self._state["token_usage"] / self.config.token_budget * 100, 1),
            "eviction_count": self._state["eviction_count"],
            "last_eviction": self._state["last_eviction"]
        }

    def touch(self, agent_id: str) -> None:
        """Update access time for an agent (keep it hot)."""
        if agent_id in self._state["hot_agents"]:
            self._state["hot_agents"][agent_id]["last_accessed"] = \
                datetime.now(timezone.utc).isoformat()
            self._state["hot_agents"][agent_id]["access_count"] += 1
            self._save_state()

    def check_and_manage_pressure(self) -> List[str]:
        """
        Check memory pressure and auto-manage if enabled.

        Integrates with tiered memory for L1/L2 pressure management.
        Returns list of actions taken.
        """
        actions = []

        # Check if auto-management is enabled
        if not self.config.get('self_management.enabled', True):
            return actions

        # Get pressure threshold
        threshold = self.config.get('self_management.pressure_threshold', 0.7)

        # Check slot pressure
        slot_usage = len(self._state["hot_agents"]) / self.config.max_hot_agents

        # Check token pressure
        token_usage = self._state["token_usage"] / self.config.token_budget

        # Take max of both
        pressure = max(slot_usage, token_usage)

        if pressure >= threshold:
            # Evict agents until below pressure
            while pressure >= threshold and self._state["hot_agents"]:
                evicted_id = self._evict_one()
                if evicted_id:
                    actions.append(f"Auto-evicted {evicted_id} (pressure: {pressure:.0%})")

                    # Try to demote to tiered memory if available
                    tmm = get_tiered_memory_manager()
                    if tmm:
                        try:
                            tmm.demote(evicted_id)
                            actions.append(f"Demoted {evicted_id} to L3 episodic")
                        except Exception:
                            pass

                    # Recalculate pressure
                    slot_usage = len(self._state["hot_agents"]) / self.config.max_hot_agents
                    token_usage = self._state["token_usage"] / self.config.token_budget
                    pressure = max(slot_usage, token_usage)
                else:
                    break

        # Also check tiered memory pressure
        tmm = get_tiered_memory_manager()
        if tmm:
            try:
                tier_actions = tmm.check_and_manage_pressure()
                actions.extend(tier_actions)
            except Exception:
                pass

        return actions

    def get_pressure_status(self) -> Dict[str, Any]:
        """Get current memory pressure status."""
        slot_usage = len(self._state["hot_agents"]) / self.config.max_hot_agents
        token_usage = self._state["token_usage"] / self.config.token_budget
        threshold = self.config.get('self_management.pressure_threshold', 0.7)

        pressure = max(slot_usage, token_usage)

        return {
            "slot_usage": slot_usage,
            "token_usage": token_usage,
            "pressure": pressure,
            "threshold": threshold,
            "under_pressure": pressure >= threshold,
            "status": "OK" if pressure < 0.5 else "CAUTION" if pressure < threshold else "HIGH_LOAD"
        }


def get_working_memory() -> WorkingMemory:
    """Get a working memory instance."""
    return WorkingMemory()


def check_memory_pressure() -> Dict[str, Any]:
    """Check memory pressure and return status."""
    wm = WorkingMemory()
    return wm.get_pressure_status()


def manage_memory_pressure() -> List[str]:
    """Check and manage memory pressure, returning actions taken."""
    wm = WorkingMemory()
    return wm.check_and_manage_pressure()
