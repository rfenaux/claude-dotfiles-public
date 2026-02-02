"""
CTM Scheduler

Manages the priority queue and working memory pool.
Implements bio-inspired priority calculation based on:
- Urgency (deadline proximity)
- Recency (time since last active)
- Value (importance/impact)
- Novelty (how new/fresh the task is)
- User signal (explicit priority hints)
- Error boost (failed tasks get priority)
"""

import json
import math
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from config import load_config, get_ctm_dir
from agents import Agent, AgentIndex, get_agent, AgentStatus


# Project context boost when task matches current working directory
PROJECT_CONTEXT_BOOST = 0.20  # +20% priority for matching project


@dataclass
class SchedulerState:
    """Current scheduler state."""
    active_agent: Optional[str]
    priority_queue: List[Tuple[str, float]]  # (agent_id, score)
    last_switch: Optional[str]
    session: Dict[str, Any]


class Scheduler:
    """
    Priority-based task scheduler inspired by human executive function.

    The DLPFC (dorsolateral prefrontal cortex) maintains active goals
    and switches between them based on priority signals. This scheduler
    mimics that behavior with weighted priority scoring.
    """

    def __init__(self):
        self.config = load_config()
        self.state_path = get_ctm_dir() / "scheduler.json"
        self._state = self._load_state()
        self._index = AgentIndex()

    def _load_state(self) -> Dict[str, Any]:
        """Load scheduler state from file."""
        if not self.state_path.exists():
            return {
                "version": "1.1.0",
                "active_agent": None,
                "priority_queue": [],
                "last_switch": None,
                "project_context": None,  # v2.1: Current project context
                "session": {
                    "started_at": None,
                    "switches": 0,
                    "checkpoints": 0,
                    "consolidations": 0
                }
            }

        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        """Save scheduler state to file."""
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    # ─────────────────────────────────────────────────────────────────────────
    # Project Context Management (v2.1)
    # ─────────────────────────────────────────────────────────────────────────

    def get_project_context(self) -> Optional[str]:
        """Get the current project context path."""
        return self._state.get("project_context")

    def set_project_context(self, project_path: Optional[str]) -> None:
        """
        Set the project context for priority calculations.

        Args:
            project_path: Absolute path to project directory, or None to clear
        """
        if project_path:
            # Normalize path
            project_path = str(Path(project_path).resolve())
        self._state["project_context"] = project_path
        self._save_state()

    def detect_project_context(self) -> Optional[str]:
        """
        Auto-detect project context from current working directory.

        Returns the project root if detected, None otherwise.
        """
        cwd = Path.cwd()

        # Look for project markers (git, .claude, package.json, etc.)
        markers = [".git", ".claude", "package.json", "pyproject.toml", "Cargo.toml"]

        current = cwd
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return str(current)
            current = current.parent

        # No marker found - use cwd as-is
        return str(cwd)

    def is_project_match(self, agent: Agent) -> bool:
        """
        Check if an agent belongs to the current project context.

        Matches if:
        - Agent's project path starts with project context (subdirectory)
        - Agent's project path equals project context exactly
        """
        project_context = self.get_project_context()
        if not project_context:
            return False

        agent_project = agent.context.get("project", "")
        if not agent_project:
            return False

        # Normalize both paths
        context_path = Path(project_context).resolve()
        agent_path = Path(agent_project).resolve()

        # Check if agent path is same or subdirectory of context
        try:
            agent_path.relative_to(context_path)
            return True
        except ValueError:
            return False

    def get_agents_by_project(self) -> Dict[str, List[str]]:
        """
        Group all active agents by their project path.

        Returns:
            Dict mapping project paths to lists of agent IDs
        """
        active_ids = self._index.get_all_active()
        by_project: Dict[str, List[str]] = {}

        for agent_id in active_ids:
            agent = get_agent(agent_id)
            if agent:
                project = agent.context.get("project", "unknown")
                if project not in by_project:
                    by_project[project] = []
                by_project[project].append(agent_id)

        return by_project

    def calculate_priority(self, agent: Agent) -> float:
        """
        Calculate priority score for an agent using weighted factors.

        Formula: Σ(weight_i × factor_i) with recency decay

        Factors:
        - urgency: How time-sensitive (0-1)
        - recency: Decays over time based on halflife
        - value: Importance/impact (0-1)
        - novelty: Freshness, decays from 1.0 at creation
        - user_signal: Explicit priority hints (-1 to 1)
        - error_boost: Bump for failed tasks (0 or boost value)
        """
        weights = self.config.priority_weights
        halflife = self.config.recency_halflife_hours

        # Calculate recency decay
        last_active = datetime.fromisoformat(
            agent.timing["last_active"].rstrip("Z")
        ).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_since = (now - last_active).total_seconds() / 3600

        # Exponential decay: recency = 2^(-hours/halflife)
        recency = math.pow(2, -hours_since / halflife)

        # Calculate novelty decay (from creation)
        created = datetime.fromisoformat(
            agent.timing["created_at"].rstrip("Z")
        ).replace(tzinfo=timezone.utc)
        days_since_created = (now - created).total_seconds() / 86400
        novelty = max(0.1, math.pow(2, -days_since_created / 7))  # 7-day halflife

        # Error boost: if last_error exists and recent
        error_boost = 0.0
        if agent.state.get("last_error"):
            error_boost = 0.3  # Significant bump

        # Get base values from agent
        value = agent.priority.get("value", 0.5)
        user_signal = agent.priority.get("user_signal", 0.0)

        # IMPROVEMENT 1: Deadline-aware urgency calculation
        # If deadline is set, calculate urgency dynamically based on proximity
        deadline_str = agent.timing.get("deadline")
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                days_until = (deadline - now).days
                hours_until = (deadline - now).total_seconds() / 3600

                if hours_until <= 0:
                    urgency = 1.0  # Overdue - maximum urgency
                elif days_until <= 1:
                    urgency = 0.95  # Due today/tomorrow
                elif days_until <= 3:
                    urgency = 0.85  # Critical - within 3 days
                elif days_until <= 7:
                    urgency = 0.70  # Soon - within a week
                elif days_until <= 14:
                    urgency = 0.55  # Coming up - within 2 weeks
                else:
                    # Gradual decay for longer deadlines
                    urgency = max(0.3, 0.5 * (30 / max(30, days_until)))
            except (ValueError, TypeError):
                # Invalid deadline format, fall back to default
                urgency = agent.priority.get("urgency", 0.5)
        else:
            urgency = agent.priority.get("urgency", 0.5)

        # Normalize user_signal from [-1, 1] to [0, 1]
        user_signal_normalized = (user_signal + 1) / 2

        # Calculate weighted sum
        score = (
            weights["urgency"] * urgency +
            weights["recency"] * recency +
            weights["value"] * value +
            weights["novelty"] * novelty +
            weights["user_signal"] * user_signal_normalized +
            weights["error_boost"] * error_boost
        )

        # v2.1: Project context boost
        if self.is_project_match(agent):
            score += PROJECT_CONTEXT_BOOST

        # Clamp to [0, 1]
        return max(0.0, min(1.0, score))

    def rebuild_queue(self, project_path: Optional[str] = None) -> List[Tuple[str, float]]:
        """
        Rebuild the priority queue from all active agents.

        Args:
            project_path: Optional project path to set context before building.
                          If provided, agents matching this project get priority boost.
        """
        # v2.1: Set project context if provided
        if project_path:
            self.set_project_context(project_path)

        active_ids = self._index.get_all_active()
        queue = []

        for agent_id in active_ids:
            agent = get_agent(agent_id)
            if agent and agent.state["status"] != AgentStatus.COMPLETED.value:
                # IMPROVEMENT 2: Task dependency enforcement
                # Check if agent is blocked by unresolved dependencies
                blockers = agent.task.get("blockers", [])
                is_blocked = False

                if blockers:
                    for blocker_id in blockers:
                        blocker = get_agent(blocker_id)
                        if blocker and blocker.state["status"] not in (
                            AgentStatus.COMPLETED.value,
                            AgentStatus.CANCELLED.value
                        ):
                            is_blocked = True
                            break

                    if is_blocked:
                        # Mark as blocked and skip from active queue
                        if agent.state["status"] != AgentStatus.BLOCKED.value:
                            agent.set_status(AgentStatus.BLOCKED)
                            agent.save()
                            self._index.update(agent)
                        continue
                    else:
                        # Blockers resolved - unblock if was blocked
                        if agent.state["status"] == AgentStatus.BLOCKED.value:
                            agent.set_status(AgentStatus.PAUSED)
                            agent.save()
                            self._index.update(agent)

                score = self.calculate_priority(agent)
                queue.append((agent_id, score))

                # Update agent's computed score
                agent.priority["computed_score"] = score
                agent.save()

        # Sort by score descending
        queue.sort(key=lambda x: x[1], reverse=True)

        self._state["priority_queue"] = queue
        self._save_state()

        return queue

    def get_next(self) -> Optional[Tuple[str, float]]:
        """Get the highest priority agent."""
        if not self._state["priority_queue"]:
            self.rebuild_queue()

        if self._state["priority_queue"]:
            return tuple(self._state["priority_queue"][0])
        return None

    def get_active(self) -> Optional[str]:
        """Get currently active agent ID."""
        return self._state["active_agent"]

    def set_active(self, agent_id: Optional[str]) -> None:
        """Set the active agent."""
        old_active = self._state["active_agent"]
        now = datetime.now(timezone.utc)

        if old_active and old_active != agent_id:
            # Pause the old active agent
            old_agent = get_agent(old_active)
            if old_agent:
                # IMPROVEMENT 3: Track active time on the old agent
                session_start_str = old_agent.timing.get("session_start")
                if session_start_str:
                    try:
                        session_start = datetime.fromisoformat(
                            session_start_str.rstrip("Z")
                        ).replace(tzinfo=timezone.utc)
                        duration = (now - session_start).total_seconds()
                        old_agent.timing["total_active_seconds"] = (
                            old_agent.timing.get("total_active_seconds", 0) + duration
                        )
                        old_agent.timing["session_start"] = None
                    except (ValueError, TypeError):
                        pass  # Invalid timestamp, skip tracking

                old_agent.set_status(AgentStatus.PAUSED)
                old_agent.save()

        self._state["active_agent"] = agent_id
        self._state["last_switch"] = now.isoformat()
        self._state["session"]["switches"] += 1

        if agent_id:
            # Activate the new agent
            agent = get_agent(agent_id)
            if agent:
                agent.set_status(AgentStatus.ACTIVE)
                # IMPROVEMENT 3: Start session timer for the new agent
                agent.timing["session_start"] = now.isoformat()
                agent.timing["session_count"] = agent.timing.get("session_count", 0) + 1
                agent.save()
                self._index.update(agent)

        self._save_state()

    def switch_to(self, agent_id: str) -> bool:
        """Switch to a specific agent."""
        agent = get_agent(agent_id)
        if not agent:
            return False

        self.set_active(agent_id)
        self.rebuild_queue()
        return True

    def preempt_check(self, current_agent_id: str) -> Optional[str]:
        """
        Check if a higher-priority agent should preempt the current one.

        Returns the preempting agent ID if preemption should occur, None otherwise.
        """
        self.rebuild_queue()

        if not self._state["priority_queue"]:
            return None

        top_id, top_score = self._state["priority_queue"][0]

        if top_id == current_agent_id:
            return None

        # Get current agent's score
        current_agent = get_agent(current_agent_id)
        if not current_agent:
            return top_id

        current_score = current_agent.priority.get("computed_score", 0)

        # Preempt if top score is significantly higher (>0.2 difference)
        if top_score - current_score > 0.2:
            return top_id

        return None

    def start_session(self, project_path: Optional[str] = None) -> None:
        """
        Start a new session.

        Args:
            project_path: Optional project path for context-aware prioritization.
                          If not provided, auto-detects from current directory.
        """
        self._state["session"] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "switches": 0,
            "checkpoints": 0,
            "consolidations": 0
        }

        # v2.1: Set project context
        if project_path:
            self.set_project_context(project_path)
        else:
            # Auto-detect from cwd
            detected = self.detect_project_context()
            if detected:
                self.set_project_context(detected)

        self.rebuild_queue()
        self._save_state()

    def end_session(self) -> Dict[str, Any]:
        """End the current session and return stats."""
        stats = self._state["session"].copy()
        self._state["active_agent"] = None
        self._save_state()
        return stats

    def get_queue(self) -> List[Dict[str, Any]]:
        """Get the priority queue with agent info."""
        result = []
        for agent_id, score in self._state["priority_queue"]:
            info = self._index.get_info(agent_id)
            if info:
                result.append({
                    "id": agent_id,
                    "title": info["title"],
                    "score": round(score, 3),
                    "status": info["status"]
                })
        return result

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status summary."""
        project_context = self.get_project_context()

        # Count agents matching current project
        matching_count = 0
        if project_context:
            for agent_id, _ in self._state["priority_queue"]:
                agent = get_agent(agent_id)
                if agent and self.is_project_match(agent):
                    matching_count += 1

        return {
            "active_agent": self._state["active_agent"],
            "queue_length": len(self._state["priority_queue"]),
            "top_priority": self._state["priority_queue"][0] if self._state["priority_queue"] else None,
            "session": self._state["session"],
            "last_switch": self._state["last_switch"],
            "project_context": project_context,
            "project_tasks": matching_count
        }


# Singleton cache for scheduler
_scheduler_instance: Optional[Scheduler] = None
_scheduler_mtime: Optional[float] = None


def get_scheduler(force_reload: bool = False) -> Scheduler:
    """
    Get a cached scheduler instance (singleton pattern).

    The scheduler is reloaded only if:
    - It hasn't been loaded yet
    - force_reload=True is passed
    - The underlying state file has been modified externally
    """
    global _scheduler_instance, _scheduler_mtime

    state_path = get_ctm_dir() / "scheduler.json"

    # Check if we need to reload
    current_mtime = state_path.stat().st_mtime if state_path.exists() else None

    if (force_reload or
        _scheduler_instance is None or
        _scheduler_mtime != current_mtime):

        _scheduler_instance = Scheduler()
        _scheduler_mtime = current_mtime

    return _scheduler_instance


def invalidate_scheduler_cache() -> None:
    """Invalidate the scheduler cache, forcing a reload on next access."""
    global _scheduler_instance, _scheduler_mtime
    _scheduler_instance = None
    _scheduler_mtime = None
