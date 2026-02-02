"""
CTM Cognitive Load Tracking

Tracks attention residue and cognitive load from task switching:
- Interruption tracking (based on 23-minute refocus research)
- Attention residue scoring
- Focus recommendations
- Cognitive block extraction (reusable patterns like PFC)

Research basis:
- 23 minutes average refocus time after interruption
- 9.5 minutes to return to productive workflow
- 40% of productive time lost to chronic multitasking
"""

import json
import math
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field

from config import load_config, get_ctm_dir
from agents import Agent, get_agent


# Research-based constants
REFOCUS_TIME_MINUTES = 23  # Average time to refocus after interruption
PRODUCTIVE_RETURN_MINUTES = 9.5  # Time to return to productive workflow
ATTENTION_DECAY_HALFLIFE_HOURS = 4  # How quickly attention residue fades


@dataclass
class InterruptionEvent:
    """Record of a task interruption."""
    from_agent: str
    to_agent: str
    timestamp: str
    reason: str
    from_progress: float
    was_blocked: bool = False


@dataclass
class CognitiveBlock:
    """A reusable cognitive pattern/concept."""
    name: str
    category: str  # technical, domain, process
    agents_using: List[str]
    first_seen: str
    last_used: str
    usage_count: int


@dataclass
class FocusRecommendation:
    """Recommendation for focus management."""
    action: str  # continue, switch, break, clear_residue
    reason: str
    suggested_agent: Optional[str] = None
    estimated_refocus_minutes: float = 0


class CognitiveLoadTracker:
    """
    Tracks cognitive load and attention residue across task switches.
    """

    def __init__(self):
        self.config = load_config()
        self.ctm_dir = get_ctm_dir()
        self.state_path = self.ctm_dir / "cognitive-load.json"
        self._state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_path.exists():
            return {
                "version": "1.0.0",
                "interruptions": [],
                "cognitive_blocks": {},
                "agent_load": {},
                "current_session": {
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "switches": 0,
                    "total_residue": 0.0
                },
                "stats": {
                    "total_switches": 0,
                    "avg_session_minutes": 0,
                    "most_interrupted_agents": {}
                }
            }
        with open(self.state_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        with open(self.state_path, 'w') as f:
            json.dump(self._state, f, indent=2)

    def on_task_switch(self, from_agent: str, to_agent: str, reason: str = "user_initiated") -> Dict[str, Any]:
        """
        Record a task switch and calculate attention residue.

        Returns impact analysis.
        """
        now = datetime.now(timezone.utc)

        # Get from_agent progress
        agent = get_agent(from_agent)
        from_progress = agent.state.get("progress_pct", 0) if agent else 0

        # Create interruption event
        event = InterruptionEvent(
            from_agent=from_agent,
            to_agent=to_agent,
            timestamp=now.isoformat(),
            reason=reason,
            from_progress=from_progress,
            was_blocked=reason == "blocked"
        )

        self._state["interruptions"].append({
            "from_agent": event.from_agent,
            "to_agent": event.to_agent,
            "timestamp": event.timestamp,
            "reason": event.reason,
            "from_progress": event.from_progress,
            "was_blocked": event.was_blocked
        })

        # Keep only last 100 interruptions
        self._state["interruptions"] = self._state["interruptions"][-100:]

        # Update agent-specific load
        if from_agent not in self._state["agent_load"]:
            self._state["agent_load"][from_agent] = {
                "interruption_count": 0,
                "total_time_minutes": 0,
                "attention_residue": 0.0,
                "last_switch": None
            }

        agent_load = self._state["agent_load"][from_agent]
        agent_load["interruption_count"] += 1
        agent_load["last_switch"] = now.isoformat()

        # Calculate residue for this switch
        residue = self._calculate_switch_residue(from_progress, reason)
        agent_load["attention_residue"] = min(1.0, agent_load["attention_residue"] + residue)

        # Update session stats
        self._state["current_session"]["switches"] += 1
        self._state["current_session"]["total_residue"] += residue
        self._state["stats"]["total_switches"] += 1

        # Update most interrupted
        mia = self._state["stats"]["most_interrupted_agents"]
        mia[from_agent] = mia.get(from_agent, 0) + 1

        self._save_state()

        return {
            "residue_added": residue,
            "total_residue": agent_load["attention_residue"],
            "interruption_count": agent_load["interruption_count"],
            "estimated_refocus_minutes": residue * REFOCUS_TIME_MINUTES
        }

    def _calculate_switch_residue(self, progress: float, reason: str) -> float:
        """
        Calculate attention residue from a task switch.

        Higher residue for:
        - Incomplete tasks (mid-progress)
        - Non-blocked switches (voluntary interruption)
        """
        # Base residue from progress (peaks at 50% - worst time to interrupt)
        progress_factor = 1 - abs(progress - 50) / 50  # 0 at 0% or 100%, 1 at 50%

        # Reason factor
        if reason == "blocked":
            reason_factor = 0.3  # Lower residue for blocked tasks
        elif reason == "completed":
            reason_factor = 0.1  # Minimal residue for completed tasks
        elif reason == "urgent":
            reason_factor = 0.7  # High residue for urgent interruptions
        else:
            reason_factor = 0.5  # Default for user-initiated

        return progress_factor * reason_factor

    def calculate_residue(self, agent_id: str) -> float:
        """
        Get current attention residue score for an agent.

        Score 0-1 indicating unfinished cognitive load.
        Decays over time based on ATTENTION_DECAY_HALFLIFE_HOURS.
        """
        if agent_id not in self._state["agent_load"]:
            return 0.0

        agent_load = self._state["agent_load"][agent_id]
        base_residue = agent_load.get("attention_residue", 0.0)

        # Apply time decay
        last_switch = agent_load.get("last_switch")
        if last_switch:
            try:
                last_dt = datetime.fromisoformat(last_switch.rstrip("Z")).replace(tzinfo=timezone.utc)
                hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                decay = math.pow(0.5, hours_since / ATTENTION_DECAY_HALFLIFE_HOURS)
                return base_residue * decay
            except ValueError:
                pass

        return base_residue

    def get_focus_recommendation(self, current_agent: Optional[str] = None) -> FocusRecommendation:
        """
        Get recommendation for focus management based on current state.
        """
        session = self._state["current_session"]
        total_residue = session.get("total_residue", 0)
        switches = session.get("switches", 0)

        # Calculate session duration
        try:
            started = datetime.fromisoformat(session["started_at"].rstrip("Z")).replace(tzinfo=timezone.utc)
            session_minutes = (datetime.now(timezone.utc) - started).total_seconds() / 60
        except (ValueError, KeyError):
            session_minutes = 0

        # High residue warning
        if total_residue > 0.7:
            return FocusRecommendation(
                action="clear_residue",
                reason=f"High attention residue ({total_residue:.0%}). Consider completing interrupted tasks.",
                estimated_refocus_minutes=total_residue * REFOCUS_TIME_MINUTES
            )

        # Too many switches
        if switches > 5 and session_minutes < 60:
            return FocusRecommendation(
                action="continue",
                reason=f"{switches} switches in {session_minutes:.0f}min. Stay focused to avoid 40% productivity loss.",
                suggested_agent=current_agent
            )

        # If current agent has high residue, suggest continuing
        if current_agent:
            residue = self.calculate_residue(current_agent)
            if residue > 0.3:
                return FocusRecommendation(
                    action="continue",
                    reason=f"Agent has {residue:.0%} residue. 23min needed to refocus if you switch.",
                    suggested_agent=current_agent,
                    estimated_refocus_minutes=REFOCUS_TIME_MINUTES
                )

        # Default: OK to work normally
        return FocusRecommendation(
            action="continue",
            reason="Focus state is healthy. Continue current work.",
            suggested_agent=current_agent
        )

    def extract_cognitive_blocks(self, agent_id: str) -> List[CognitiveBlock]:
        """
        Extract reusable cognitive blocks (concepts, patterns) from an agent.

        Like PFC assembling blocks across tasks.
        """
        agent = get_agent(agent_id)
        if not agent:
            return []

        blocks = []
        now = datetime.now(timezone.utc).isoformat()

        # Extract from decisions
        for decision in agent.context.get("decisions", []):
            text = decision.get("text", "") if isinstance(decision, dict) else str(decision)

            # Look for technical patterns
            if any(kw in text.lower() for kw in ["api", "oauth", "jwt", "rest", "graphql"]):
                block_name = "api-integration"
                category = "technical"
            elif any(kw in text.lower() for kw in ["hubspot", "crm", "salesforce"]):
                block_name = "crm-patterns"
                category = "domain"
            elif any(kw in text.lower() for kw in ["workflow", "automation", "pipeline"]):
                block_name = "automation"
                category = "process"
            else:
                continue

            # Check if block exists
            if block_name in self._state["cognitive_blocks"]:
                block = self._state["cognitive_blocks"][block_name]
                if agent_id not in block["agents_using"]:
                    block["agents_using"].append(agent_id)
                block["last_used"] = now
                block["usage_count"] += 1
            else:
                self._state["cognitive_blocks"][block_name] = {
                    "name": block_name,
                    "category": category,
                    "agents_using": [agent_id],
                    "first_seen": now,
                    "last_used": now,
                    "usage_count": 1
                }

            blocks.append(CognitiveBlock(
                name=block_name,
                category=category,
                agents_using=self._state["cognitive_blocks"][block_name]["agents_using"],
                first_seen=self._state["cognitive_blocks"][block_name]["first_seen"],
                last_used=now,
                usage_count=self._state["cognitive_blocks"][block_name]["usage_count"]
            ))

        self._save_state()
        return blocks

    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        session = self._state["current_session"]

        try:
            started = datetime.fromisoformat(session["started_at"].rstrip("Z")).replace(tzinfo=timezone.utc)
            duration_minutes = (datetime.now(timezone.utc) - started).total_seconds() / 60
        except (ValueError, KeyError):
            duration_minutes = 0

        return {
            "duration_minutes": round(duration_minutes, 1),
            "switches": session.get("switches", 0),
            "total_residue": round(session.get("total_residue", 0), 2),
            "switches_per_hour": round(session.get("switches", 0) / max(1, duration_minutes / 60), 1),
            "productivity_impact": f"{min(40, session.get('switches', 0) * 5)}%" if session.get("switches", 0) > 3 else "minimal"
        }

    def reset_session(self) -> None:
        """Reset session tracking (e.g., at start of new work session)."""
        self._state["current_session"] = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "switches": 0,
            "total_residue": 0.0
        }
        self._save_state()

    def get_agent_load(self, agent_id: str) -> Dict[str, Any]:
        """Get cognitive load info for a specific agent."""
        if agent_id not in self._state["agent_load"]:
            return {"interruption_count": 0, "attention_residue": 0.0, "status": "fresh"}

        load = self._state["agent_load"][agent_id]
        residue = self.calculate_residue(agent_id)

        status = "fresh" if residue < 0.2 else "moderate" if residue < 0.5 else "high"

        return {
            "interruption_count": load.get("interruption_count", 0),
            "attention_residue": round(residue, 2),
            "status": status,
            "refocus_estimate_minutes": round(residue * REFOCUS_TIME_MINUTES, 1)
        }


def get_cognitive_tracker() -> CognitiveLoadTracker:
    return CognitiveLoadTracker()
