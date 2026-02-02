"""
CTM Reflection Loop

Self-evaluation pattern for task completion:
- Verify acceptance criteria achievement
- Extract decisions and learnings
- Identify improvement opportunities
- Generate reusable patterns

Enables agents to evaluate and refine their outputs before marking complete.
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

from config import load_config, get_ctm_dir
from agents import Agent, get_agent, update_agent
from extraction import DecisionExtractor, ExtractedDecision, ExtractedLearning


@dataclass
class ReflectionResult:
    """Result of reflecting on task completion."""
    criteria_met: List[str]
    criteria_unmet: List[str]
    decisions_made: List[ExtractedDecision]
    learnings_extracted: List[ExtractedLearning]
    improvement_suggestions: List[str]
    patterns_identified: List[str]
    completion_score: float  # 0-1
    ready_to_complete: bool
    blockers: List[str]


@dataclass
class LearningCandidate:
    """A candidate learning for the lessons system."""
    text: str
    category: str
    confidence: float
    source_agent: str
    tags: List[str]


class ReflectionLoop:
    """
    Self-evaluation loop for task completion.

    Runs reflection before marking tasks complete to ensure
    quality and extract maximum learning value.
    """

    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        self.config = load_config()
        self.extractor = DecisionExtractor()

    def reflect_on_completion(self, agent: Agent) -> ReflectionResult:
        """
        Comprehensive reflection before marking task complete.

        Evaluates:
        - Acceptance criteria achievement
        - Decisions made during task
        - Learnings to extract
        - Patterns for reuse
        """
        criteria_met = []
        criteria_unmet = []
        improvement_suggestions = []
        patterns = []
        blockers = []

        # Check acceptance criteria
        acceptance_criteria = agent.task.get("acceptance_criteria", [])
        progress = agent.state.get("progress_pct", 0)

        for criterion in acceptance_criteria:
            if isinstance(criterion, dict):
                text = criterion.get("text", "")
                met = criterion.get("met", False)
            else:
                text = str(criterion)
                met = progress >= 100  # Assume met if 100% progress

            if met:
                criteria_met.append(text)
            else:
                criteria_unmet.append(text)
                blockers.append(f"Unmet criterion: {text[:50]}")

        # Extract decisions and learnings
        decisions, learnings = self.extractor.extract_from_agent(agent)

        # Identify patterns
        patterns = self._identify_patterns(agent, decisions, learnings)

        # Generate improvement suggestions
        if len(criteria_unmet) > 0:
            improvement_suggestions.append(f"Complete {len(criteria_unmet)} remaining acceptance criteria")

        if len(decisions) < 2 and progress > 50:
            improvement_suggestions.append("Document key decisions made during implementation")

        if not agent.context.get("key_files"):
            improvement_suggestions.append("Record key files modified for future reference")

        # Calculate completion score
        if acceptance_criteria:
            criteria_score = len(criteria_met) / len(acceptance_criteria)
        else:
            criteria_score = progress / 100

        documentation_score = min(1.0, (len(decisions) + len(learnings)) / 5)
        completion_score = (criteria_score * 0.7) + (documentation_score * 0.3)

        # Determine if ready
        ready = (
            len(criteria_unmet) == 0 and
            progress >= 90 and
            agent.state.get("status") != "blocked"
        )

        return ReflectionResult(
            criteria_met=criteria_met,
            criteria_unmet=criteria_unmet,
            decisions_made=decisions,
            learnings_extracted=learnings,
            improvement_suggestions=improvement_suggestions,
            patterns_identified=patterns,
            completion_score=completion_score,
            ready_to_complete=ready,
            blockers=blockers
        )

    def _identify_patterns(self, agent: Agent, decisions: List[ExtractedDecision],
                           learnings: List[ExtractedLearning]) -> List[str]:
        """Identify reusable patterns from the task."""
        patterns = []

        # Check for integration patterns
        goal = agent.task.get("goal", "").lower()
        if "api" in goal or "integration" in goal:
            patterns.append("api-integration-pattern")
        if "hubspot" in goal:
            patterns.append("hubspot-implementation")
        if "migration" in goal:
            patterns.append("data-migration")

        # Check decision categories
        categories = set(d.category for d in decisions)
        if "architecture" in categories:
            patterns.append("architectural-decision")
        if "security" in categories:
            patterns.append("security-consideration")

        return patterns

    def extract_learnings(self, agent: Agent) -> List[LearningCandidate]:
        """
        Extract high-quality learnings for the lessons system.

        Filters for actionable, generalizable insights.
        """
        candidates = []
        _, learnings = self.extractor.extract_from_agent(agent)

        for learning in learnings:
            # Filter for quality
            if learning.confidence < 0.7:
                continue
            if len(learning.text) < 20:
                continue

            # Determine tags
            tags = [learning.category]
            goal = agent.task.get("goal", "").lower()
            if "hubspot" in goal:
                tags.append("hubspot")
            if "api" in goal:
                tags.append("api")
            if "integration" in goal:
                tags.append("integration")

            candidates.append(LearningCandidate(
                text=learning.text,
                category=learning.category,
                confidence=learning.confidence,
                source_agent=agent.id,
                tags=tags
            ))

        return candidates

    def generate_completion_summary(self, agent: Agent, reflection: ReflectionResult) -> str:
        """Generate a completion summary for the agent."""
        lines = []
        lines.append(f"## Task Completion: {agent.task.get('title', 'Unknown')}")
        lines.append(f"**Completion Score:** {reflection.completion_score:.0%}")
        lines.append("")

        if reflection.criteria_met:
            lines.append("### Criteria Met")
            for c in reflection.criteria_met:
                lines.append(f"- ✅ {c}")
            lines.append("")

        if reflection.criteria_unmet:
            lines.append("### Criteria Pending")
            for c in reflection.criteria_unmet:
                lines.append(f"- ⏳ {c}")
            lines.append("")

        if reflection.decisions_made:
            lines.append("### Key Decisions")
            for d in reflection.decisions_made[:5]:
                lines.append(f"- {d.title}")
            lines.append("")

        if reflection.learnings_extracted:
            lines.append("### Learnings")
            for l in reflection.learnings_extracted[:5]:
                lines.append(f"- {l.text[:80]}")
            lines.append("")

        if reflection.patterns_identified:
            lines.append(f"**Patterns:** {', '.join(reflection.patterns_identified)}")

        return "\n".join(lines)


def reflect_before_complete(agent_id: str) -> Tuple[ReflectionResult, str]:
    """
    Convenience function to reflect on an agent before completion.

    Returns (reflection_result, summary_text).
    """
    agent = get_agent(agent_id)
    if not agent:
        return None, "Agent not found"

    loop = ReflectionLoop()
    reflection = loop.reflect_on_completion(agent)
    summary = loop.generate_completion_summary(agent, reflection)

    return reflection, summary


def extract_agent_learnings(agent_id: str) -> List[LearningCandidate]:
    """Extract learnings from an agent for the lessons system."""
    agent = get_agent(agent_id)
    if not agent:
        return []

    loop = ReflectionLoop()
    return loop.extract_learnings(agent)
