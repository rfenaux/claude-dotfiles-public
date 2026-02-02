"""
CTM Decision Extraction

Intelligently extracts decisions, learnings, and key insights from:
- Agent context (explicit decisions)
- Conversation patterns (implicit decisions)
- Code changes (architectural choices)

Like the brain's memory consolidation during sleep, this transforms
episodic memories into structured semantic knowledge.

Now includes conflict detection via Knowledge Graph integration.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass

from agents import Agent, get_agent

# Lazy import for knowledge graph
_knowledge_graph = None

def get_kg():
    global _knowledge_graph
    if _knowledge_graph is None:
        try:
            from knowledge_graph import get_knowledge_graph
            _knowledge_graph = get_knowledge_graph()
        except ImportError:
            _knowledge_graph = None
    return _knowledge_graph


@dataclass
class ExtractedDecision:
    """A decision extracted from context."""
    title: str
    choice: str
    context: str
    category: str  # architecture, process, scope, data-model, etc.
    confidence: float  # 0-1, how confident we are this is a decision
    source: str
    timestamp: str


@dataclass
class ExtractedLearning:
    """A learning/insight extracted from context."""
    text: str
    category: str  # technical, process, domain, gotcha
    confidence: float
    source: str


class DecisionExtractor:
    """
    Extracts decisions from agent context using pattern matching.
    """

    # Patterns that indicate a decision was made
    DECISION_PATTERNS = [
        # Explicit decision language
        (r"(?:decided|chose|selected|picked|went with|using|opted for)\s+(.+?)(?:\.|$)", 0.9),
        (r"(?:will|going to|plan to)\s+(?:use|implement|go with)\s+(.+?)(?:\.|$)", 0.8),
        (r"(?:the decision is|we decided|decision:)\s*(.+?)(?:\.|$)", 0.95),

        # Rejection patterns (implies choice of alternative)
        (r"(?:rejected|ruled out|not using|won't use|avoiding)\s+(.+?)(?:\s+(?:because|due to|since))?", 0.7),

        # Comparative patterns
        (r"(?:prefer|better than|instead of|rather than)\s+(.+?)(?:\.|$)", 0.75),

        # Architecture patterns
        (r"(?:architecture|design|pattern|approach):\s*(.+?)(?:\.|$)", 0.85),
        (r"(?:using|implementing)\s+(?:a\s+)?(\w+(?:\s+\w+)?)\s+(?:pattern|architecture|approach)", 0.85),
    ]

    # Patterns that indicate a learning
    LEARNING_PATTERNS = [
        (r"(?:learned|discovered|found out|realized|noticed)\s+(?:that\s+)?(.+?)(?:\.|$)", 0.9),
        (r"(?:gotcha|caveat|watch out|note|important):\s*(.+?)(?:\.|$)", 0.85),
        (r"(?:turns out|apparently|interestingly)\s+(.+?)(?:\.|$)", 0.75),
        (r"(?:tip|trick|workaround):\s*(.+?)(?:\.|$)", 0.8),
    ]

    # Category detection patterns
    CATEGORY_PATTERNS = {
        "architecture": r"(?:architecture|design|pattern|structure|component|module|layer)",
        "data-model": r"(?:schema|model|entity|table|field|property|relationship|database)",
        "integration": r"(?:api|endpoint|integration|webhook|sync|connection)",
        "security": r"(?:auth|permission|role|security|credential|token|access)",
        "process": r"(?:workflow|process|pipeline|automation|trigger)",
        "scope": r"(?:scope|requirement|feature|mvp|phase|milestone)",
        "technical": r"(?:library|package|dependency|version|framework|tool)",
    }

    def __init__(self):
        pass

    def _detect_category(self, text: str) -> str:
        """Detect the category of a decision/learning."""
        text_lower = text.lower()

        for category, pattern in self.CATEGORY_PATTERNS.items():
            if re.search(pattern, text_lower):
                return category

        return "general"

    def _create_title(self, text: str, max_length: int = 60) -> str:
        """Create a short title from decision text."""
        # Clean up the text
        title = text.strip()

        # Remove common prefixes
        for prefix in ["to ", "that ", "we ", "I "]:
            if title.lower().startswith(prefix):
                title = title[len(prefix):]

        # Capitalize first letter
        if title:
            title = title[0].upper() + title[1:]

        # Truncate if needed
        if len(title) > max_length:
            title = title[:max_length-3] + "..."

        return title

    def extract_from_text(self, text: str, source: str = "unknown") -> Tuple[List[ExtractedDecision], List[ExtractedLearning]]:
        """
        Extract decisions and learnings from free text.
        """
        decisions = []
        learnings = []
        now = datetime.now(timezone.utc).isoformat()

        # Extract decisions
        for pattern, confidence in self.DECISION_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                choice = match.group(1).strip()
                if len(choice) > 10:  # Skip very short matches
                    category = self._detect_category(choice)
                    decisions.append(ExtractedDecision(
                        title=self._create_title(choice),
                        choice=choice,
                        context=text[:200] + "..." if len(text) > 200 else text,
                        category=category,
                        confidence=confidence,
                        source=source,
                        timestamp=now
                    ))

        # Extract learnings
        for pattern, confidence in self.LEARNING_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE):
                learning_text = match.group(1).strip()
                if len(learning_text) > 10:
                    category = self._detect_category(learning_text)
                    learnings.append(ExtractedLearning(
                        text=learning_text,
                        category=category,
                        confidence=confidence,
                        source=source
                    ))

        # Deduplicate by similarity
        decisions = self._dedupe_decisions(decisions)
        learnings = self._dedupe_learnings(learnings)

        return decisions, learnings

    def extract_from_agent(self, agent: Agent) -> Tuple[List[ExtractedDecision], List[ExtractedLearning]]:
        """
        Extract decisions and learnings from an agent's full context.
        """
        all_decisions = []
        all_learnings = []

        # Extract from explicit decisions in context
        for d in agent.context.get("decisions", []):
            text = d.get("text", "")
            timestamp = d.get("timestamp", datetime.now(timezone.utc).isoformat())

            # These are explicit decisions, high confidence
            category = self._detect_category(text)
            all_decisions.append(ExtractedDecision(
                title=self._create_title(text),
                choice=text,
                context=f"Agent [{agent.id}]: {agent.task['title']}",
                category=category,
                confidence=0.95,  # Explicit decisions are high confidence
                source=f"agent:{agent.id}",
                timestamp=timestamp
            ))

        # Extract from explicit learnings
        for l in agent.context.get("learnings", []):
            text = l.get("text", "")
            category = self._detect_category(text)
            all_learnings.append(ExtractedLearning(
                text=text,
                category=category,
                confidence=0.95,
                source=f"agent:{agent.id}"
            ))

        # Extract from task goal (may contain implicit decisions)
        goal_decisions, goal_learnings = self.extract_from_text(
            agent.task.get("goal", ""),
            source=f"agent:{agent.id}:goal"
        )
        all_decisions.extend(goal_decisions)
        all_learnings.extend(goal_learnings)

        # Deduplicate
        all_decisions = self._dedupe_decisions(all_decisions)
        all_learnings = self._dedupe_learnings(all_learnings)

        return all_decisions, all_learnings

    def _dedupe_decisions(self, decisions: List[ExtractedDecision]) -> List[ExtractedDecision]:
        """Remove duplicate decisions based on similarity."""
        if not decisions:
            return []

        unique = []
        seen_titles = set()

        # Sort by confidence descending
        sorted_decisions = sorted(decisions, key=lambda d: d.confidence, reverse=True)

        for d in sorted_decisions:
            title_lower = d.title.lower()

            # Check if we've seen a similar title
            is_dupe = False
            for seen in seen_titles:
                if self._similar(title_lower, seen):
                    is_dupe = True
                    break

            if not is_dupe:
                unique.append(d)
                seen_titles.add(title_lower)

        return unique

    def _dedupe_learnings(self, learnings: List[ExtractedLearning]) -> List[ExtractedLearning]:
        """Remove duplicate learnings."""
        if not learnings:
            return []

        unique = []
        seen = set()

        sorted_learnings = sorted(learnings, key=lambda l: l.confidence, reverse=True)

        for l in sorted_learnings:
            text_lower = l.text.lower()[:50]  # First 50 chars for comparison

            if text_lower not in seen:
                unique.append(l)
                seen.add(text_lower)

        return unique

    def _similar(self, a: str, b: str, threshold: float = 0.6) -> bool:
        """Check if two strings are similar using word overlap."""
        words_a = set(a.split())
        words_b = set(b.split())

        if not words_a or not words_b:
            return False

        overlap = len(words_a & words_b)
        total = max(len(words_a), len(words_b))

        return overlap / total > threshold


def extract_decisions(agent_id: str) -> List[ExtractedDecision]:
    """
    Extract decisions from an agent.

    Convenience function for external use.
    """
    agent = get_agent(agent_id)
    if not agent:
        return []

    extractor = DecisionExtractor()
    decisions, _ = extractor.extract_from_agent(agent)
    return decisions


def extract_learnings(agent_id: str) -> List[ExtractedLearning]:
    """
    Extract learnings from an agent.

    Convenience function for external use.
    """
    agent = get_agent(agent_id)
    if not agent:
        return []

    extractor = DecisionExtractor()
    _, learnings = extractor.extract_from_agent(agent)
    return learnings


def format_decision_for_md(decision: ExtractedDecision) -> str:
    """Format a decision for DECISIONS.md."""
    return f"""
### {decision.title}
- **Decided**: {decision.timestamp[:10]}
- **Category**: {decision.category}
- **Context**: {decision.context}
- **Choice**: {decision.choice}
- **Source**: {decision.source}
"""


@dataclass
class ConflictAlert:
    """Alert for a potential decision conflict."""
    new_decision: str
    existing_decision: str
    existing_id: str
    similarity: float
    conflict_type: str
    recommendation: str


def check_decision_conflicts(decision_text: str, threshold: float = 0.75) -> List[ConflictAlert]:
    """
    Check if a new decision conflicts with existing ones in the knowledge graph.

    Returns list of conflict alerts sorted by severity.
    """
    kg = get_kg()
    if not kg:
        return []

    alerts = []
    conflicts = kg.find_conflicts(decision_text, threshold=threshold)

    for conflict in conflicts:
        if conflict.similarity > 0.9:
            recommendation = "REVIEW: Very similar decision exists - may be duplicate"
        elif conflict.similarity > 0.8:
            recommendation = "WARNING: Potential contradiction - verify consistency"
        else:
            recommendation = "INFO: Related decision exists - check alignment"

        alerts.append(ConflictAlert(
            new_decision=decision_text[:100],
            existing_decision=conflict.entity.content[:100],
            existing_id=conflict.entity.id,
            similarity=conflict.similarity,
            conflict_type=conflict.conflict_type,
            recommendation=recommendation
        ))

    return alerts


def add_decision_to_graph(decision: ExtractedDecision, check_conflicts: bool = True) -> Tuple[Optional[str], List[ConflictAlert]]:
    """
    Add an extracted decision to the knowledge graph.

    Returns (entity_id, conflicts) tuple.
    """
    kg = get_kg()
    if not kg:
        return None, []

    entity, conflicts = kg.add_decision(
        title=decision.title,
        choice=decision.choice,
        context=decision.context,
        category=decision.category,
        source=decision.source,
        check_conflicts=check_conflicts
    )

    # Convert conflicts to alerts
    alerts = []
    for c in conflicts:
        alerts.append(ConflictAlert(
            new_decision=decision.choice[:100],
            existing_decision=c.entity.content[:100],
            existing_id=c.entity.id,
            similarity=c.similarity,
            conflict_type=c.conflict_type,
            recommendation=c.explanation
        ))

    return entity.id, alerts


def extract_and_store_decisions(agent_id: str, store: bool = True) -> Tuple[List[ExtractedDecision], List[ConflictAlert]]:
    """
    Extract decisions from an agent and optionally store in knowledge graph.

    Returns (decisions, all_conflicts) tuple.
    """
    agent = get_agent(agent_id)
    if not agent:
        return [], []

    extractor = DecisionExtractor()
    decisions, _ = extractor.extract_from_agent(agent)

    all_alerts = []

    if store:
        for decision in decisions:
            _, alerts = add_decision_to_graph(decision, check_conflicts=True)
            all_alerts.extend(alerts)

    return decisions, all_alerts


def format_conflict_alert(alert: ConflictAlert) -> str:
    """Format a conflict alert for display."""
    icon = "🔴" if alert.similarity > 0.9 else "🟠" if alert.similarity > 0.8 else "🟡"
    return f"""{icon} {alert.conflict_type.upper()} ({alert.similarity:.0%} similar)
   New: {alert.new_decision}
   Existing: {alert.existing_decision}
   → {alert.recommendation}"""
