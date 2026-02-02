"""
CTM Resumption Cues

Generates context restoration cues when switching back to an agent:
- What was being worked on
- Where we left off (current step)
- Key decisions made
- Pending actions
- Files that were being modified

Like the brain's "task resumption lag", this helps reduce the
cognitive cost of context switching by providing structured cues.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from config import get_ctm_dir
from agents import Agent, get_agent


class ResumptionCue:
    """
    Generates structured resumption cues for an agent.

    Based on research showing that task resumption benefits from:
    1. Goal state reminder (what we're trying to achieve)
    2. Progress checkpoint (where we stopped)
    3. Recent context (decisions, learnings)
    4. Pending items (what was next)
    """

    def __init__(self, agent: Agent):
        self.agent = agent
        self.checkpoint = self._load_latest_checkpoint()

    def _load_latest_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load the most recent checkpoint for this agent."""
        checkpoint_dir = get_ctm_dir() / "checkpoints"
        if not checkpoint_dir.exists():
            return None

        # Find checkpoints for this agent
        checkpoints = list(checkpoint_dir.glob(f"{self.agent.id}-*.json"))
        if not checkpoints:
            return None

        # Sort by filename (which includes timestamp)
        latest = sorted(checkpoints)[-1]

        with open(latest, 'r') as f:
            return json.load(f)

    def generate_brief(self) -> str:
        """
        Generate a brief resumption cue (1-3 lines).

        For quick context when switching frequently.
        """
        lines = []

        # Goal reminder
        lines.append(f"**{self.agent.task['title']}**: {self.agent.task['goal']}")

        # Progress
        progress = self.agent.state['progress_pct']
        step = self.agent.state.get('current_step')
        if step:
            lines.append(f"Progress: {progress}% — Last: {step}")
        else:
            lines.append(f"Progress: {progress}%")

        return "\n".join(lines)

    def generate_full(self) -> str:
        """
        Generate a full resumption cue with all context.

        For resuming after longer breaks.
        """
        sections = []

        # Header
        sections.append(f"═══ Resuming: {self.agent.task['title']} ═══")
        sections.append("")

        # Goal
        sections.append(f"**Goal**: {self.agent.task['goal']}")
        sections.append("")

        # Progress
        progress = self.agent.state['progress_pct']
        step = self.agent.state.get('current_step')
        sections.append(f"**Progress**: {progress}%")
        if step:
            sections.append(f"**Where we left off**: {step}")
        sections.append("")

        # Recent decisions (last 3)
        decisions = self.agent.context.get("decisions", [])
        if decisions:
            sections.append("**Recent Decisions**:")
            for d in decisions[-3:]:
                text = d.get("text", "")[:100]
                sections.append(f"  • {text}")
            sections.append("")

        # Key files
        files = self.agent.context.get("key_files", [])
        if files:
            sections.append("**Key Files**:")
            for f in files[:5]:
                sections.append(f"  • `{f}`")
            sections.append("")

        # Pending actions
        pending = self.agent.state.get("pending_actions", [])
        if pending:
            sections.append("**Pending Actions**:")
            for p in pending[:5]:
                sections.append(f"  • {p}")
            sections.append("")

        # Last error if any
        error = self.agent.state.get("last_error")
        if error:
            sections.append(f"**⚠ Last Error**: {error}")
            sections.append("")

        # Time context
        last_active = self.agent.timing.get("last_active", "")
        if last_active:
            try:
                last_dt = datetime.fromisoformat(last_active.rstrip("Z")).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = now - last_dt

                if delta.days > 0:
                    time_str = f"{delta.days} day(s) ago"
                elif delta.seconds > 3600:
                    time_str = f"{delta.seconds // 3600} hour(s) ago"
                elif delta.seconds > 60:
                    time_str = f"{delta.seconds // 60} minute(s) ago"
                else:
                    time_str = "just now"

                sections.append(f"**Last Active**: {time_str}")
            except:
                pass

        return "\n".join(sections)

    def generate_checkpoint_summary(self) -> Optional[str]:
        """
        Generate summary from the latest checkpoint.
        """
        if not self.checkpoint:
            return None

        lines = []
        lines.append("**From checkpoint**:")
        lines.append(f"  Type: {self.checkpoint.get('type', 'unknown')}")
        lines.append(f"  Time: {self.checkpoint.get('timestamp', 'unknown')[:19]}")

        summary = self.checkpoint.get("context_summary", {})
        if summary:
            lines.append(f"  Decisions: {summary.get('decisions_count', 0)}")
            lines.append(f"  Learnings: {summary.get('learnings_count', 0)}")
            lines.append(f"  Files: {summary.get('files_count', 0)}")

        return "\n".join(lines)


def generate_resumption_cue(agent_id: str, brief: bool = False) -> str:
    """
    Generate a resumption cue for an agent.

    Args:
        agent_id: The agent to resume
        brief: If True, generate short cue; if False, generate full cue

    Returns:
        Formatted resumption cue string
    """
    agent = get_agent(agent_id)
    if not agent:
        return f"Agent [{agent_id}] not found"

    cue = ResumptionCue(agent)

    if brief:
        return cue.generate_brief()
    else:
        return cue.generate_full()


def get_switch_context(from_agent_id: Optional[str], to_agent_id: str) -> Dict[str, str]:
    """
    Get context for a switch between agents.

    Returns dict with:
    - pause_summary: What to save from the paused agent
    - resume_cue: How to resume the target agent
    """
    result = {
        "pause_summary": None,
        "resume_cue": None
    }

    # Generate pause summary for outgoing agent
    if from_agent_id:
        from_agent = get_agent(from_agent_id)
        if from_agent:
            result["pause_summary"] = (
                f"Pausing [{from_agent_id}]: {from_agent.task['title']} "
                f"at {from_agent.state['progress_pct']}%"
            )
            if from_agent.state.get("current_step"):
                result["pause_summary"] += f" — {from_agent.state['current_step']}"

    # Generate resume cue for incoming agent
    result["resume_cue"] = generate_resumption_cue(to_agent_id, brief=False)

    return result
