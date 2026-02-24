"""
CTM Trigger Detection

Detects when user input should trigger a context switch:
- Keyword patterns ("back to X", "continue X", "what about X")
- Agent name/ID mentions
- Priority escalation signals ("urgent", "critical", "ASAP")
- Completion signals ("done with", "finished")
- Semantic similarity matching (via embeddings)

Like the brain's interruption detection, this surfaces relevant
context when the user's attention shifts.
"""

import re
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass

from config import load_config
from agents import Agent, get_agent, AgentIndex, list_agents

# Lazy import for embeddings
_embeddings = None
_embedding_cache = {}

def get_embeddings():
    global _embeddings
    if _embeddings is None:
        try:
            from knowledge_graph import OllamaEmbeddings
            _embeddings = OllamaEmbeddings()
        except ImportError:
            _embeddings = None
    return _embeddings

def cosine_sim(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    import math
    dot = sum(x * y for x, y in zip(a, b))
    na, nb = math.sqrt(sum(x*x for x in a)), math.sqrt(sum(x*x for x in b))
    return dot / (na * nb) if na and nb else 0.0


@dataclass
class TriggerMatch:
    """Represents a detected trigger."""
    type: str  # switch, resume, complete, escalate, mention
    agent_id: Optional[str]
    agent_title: Optional[str]
    confidence: float  # 0-1
    matched_text: str
    action_suggested: str


class TriggerDetector:
    """
    Detects triggers in user input that should cause context switches.
    """

    # Patterns that suggest switching to a task
    SWITCH_PATTERNS = [
        r"(?:back to|return to|continue|resume|pick up)\s+['\"]?(.+?)['\"]?(?:\s|$|\.|\?)",
        r"(?:what about|how about|let's work on|switch to)\s+['\"]?(.+?)['\"]?(?:\s|$|\.|\?)",
        r"(?:can we|let's)\s+(?:get back to|continue)\s+['\"]?(.+?)['\"]?(?:\s|$|\.|\?)",
    ]

    # Patterns that suggest completing current task
    COMPLETE_PATTERNS = [
        r"(?:done|finished|completed?|that's it|all done)\s*(?:with)?\s*(?:this|that|the task)?",
        r"(?:mark|set)\s+(?:as|it)?\s*(?:complete|done|finished)",
        r"task\s+(?:is\s+)?(?:complete|done|finished)",
    ]

    # Patterns that suggest priority escalation
    ESCALATE_PATTERNS = [
        r"\b(?:urgent|urgently|asap|critical|emergency|immediately|right now)\b",
        r"\b(?:drop everything|highest priority|most important)\b",
        r"\b(?:this is urgent|need this now|priority one|p0|p1)\b",
    ]

    # Patterns for pausing
    PAUSE_PATTERNS = [
        r"(?:pause|stop|hold|park)\s+(?:this|that|the task|current)",
        r"(?:put|set)\s+(?:this|that)?\s*(?:aside|on hold)",
        r"(?:let's take a break|pause here)",
    ]

    def __init__(self):
        self.config = load_config()
        self.index = AgentIndex()
        self._agent_cache = None

    def _get_agents(self) -> List[Dict[str, Any]]:
        """Get cached list of active agents."""
        if self._agent_cache is None:
            self._agent_cache = list_agents()
        return self._agent_cache

    def _fuzzy_match_agent(self, text: str) -> Optional[Tuple[str, str, float]]:
        """
        Try to match text to an agent by ID or title.

        Returns (agent_id, title, confidence) or None.
        """
        text_lower = text.lower().strip()

        # Direct ID match
        for agent in self._get_agents():
            if agent["id"].lower().startswith(text_lower):
                return (agent["id"], agent["title"], 1.0)

        # Title match (fuzzy)
        best_match = None
        best_score = 0.0

        for agent in self._get_agents():
            title_lower = agent["title"].lower()

            # Exact title match
            if text_lower == title_lower:
                return (agent["id"], agent["title"], 1.0)

            # Partial title match
            if text_lower in title_lower or title_lower in text_lower:
                score = len(text_lower) / len(title_lower)
                if score > best_score:
                    best_score = score
                    best_match = (agent["id"], agent["title"], min(0.9, score))

            # Word overlap
            text_words = set(text_lower.split())
            title_words = set(title_lower.split())
            overlap = len(text_words & title_words)
            if overlap > 0:
                score = overlap / max(len(text_words), len(title_words))
                if score > best_score:
                    best_score = score
                    best_match = (agent["id"], agent["title"], score)

        # Check custom triggers on agents
        for agent in self._get_agents():
            full_agent = get_agent(agent["id"])
            if full_agent and full_agent.triggers:
                for trigger in full_agent.triggers:
                    if text_lower in trigger.lower() or trigger.lower() in text_lower:
                        return (agent["id"], agent["title"], 0.95)

        return best_match if best_score > 0.3 else None

    def detect(self, user_input: str) -> List[TriggerMatch]:
        """
        Detect triggers in user input.

        Returns list of trigger matches, sorted by confidence.
        """
        matches = []
        input_lower = user_input.lower()

        # Check switch patterns
        for pattern in self.SWITCH_PATTERNS:
            for match in re.finditer(pattern, input_lower, re.IGNORECASE):
                task_ref = match.group(1).strip()
                agent_match = self._fuzzy_match_agent(task_ref)

                if agent_match:
                    agent_id, title, conf = agent_match
                    matches.append(TriggerMatch(
                        type="switch",
                        agent_id=agent_id,
                        agent_title=title,
                        confidence=conf * 0.9,  # Reduce slightly for pattern match
                        matched_text=match.group(0),
                        action_suggested=f"Switch to [{agent_id}]: {title}"
                    ))

        # Check complete patterns
        for pattern in self.COMPLETE_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                matches.append(TriggerMatch(
                    type="complete",
                    agent_id=None,  # Current agent
                    agent_title=None,
                    confidence=0.8,
                    matched_text=re.search(pattern, input_lower, re.IGNORECASE).group(0),
                    action_suggested="Mark current agent as complete"
                ))

        # Check escalation patterns
        for pattern in self.ESCALATE_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                matches.append(TriggerMatch(
                    type="escalate",
                    agent_id=None,
                    agent_title=None,
                    confidence=0.7,
                    matched_text=re.search(pattern, input_lower, re.IGNORECASE).group(0),
                    action_suggested="Escalate priority of current or mentioned task"
                ))

        # Check pause patterns
        for pattern in self.PAUSE_PATTERNS:
            if re.search(pattern, input_lower, re.IGNORECASE):
                matches.append(TriggerMatch(
                    type="pause",
                    agent_id=None,
                    agent_title=None,
                    confidence=0.8,
                    matched_text=re.search(pattern, input_lower, re.IGNORECASE).group(0),
                    action_suggested="Pause current agent"
                ))

        # Check for direct agent mentions (ID or title)
        for agent in self._get_agents():
            # Check ID mention
            if agent["id"].lower() in input_lower:
                matches.append(TriggerMatch(
                    type="mention",
                    agent_id=agent["id"],
                    agent_title=agent["title"],
                    confidence=0.95,
                    matched_text=agent["id"],
                    action_suggested=f"Agent [{agent['id']}] mentioned"
                ))

            # Check title mention (at least 3 words to avoid false positives)
            title_lower = agent["title"].lower()
            if len(title_lower.split()) >= 2 and title_lower in input_lower:
                matches.append(TriggerMatch(
                    type="mention",
                    agent_id=agent["id"],
                    agent_title=agent["title"],
                    confidence=0.85,
                    matched_text=agent["title"],
                    action_suggested=f"Agent [{agent['id']}] mentioned by title"
                ))

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)

        # Remove duplicates (same agent, keep highest confidence)
        seen_agents = set()
        unique_matches = []
        for m in matches:
            key = (m.type, m.agent_id)
            if key not in seen_agents:
                seen_agents.add(key)
                unique_matches.append(m)

        return unique_matches

    def get_suggested_action(self, matches: List[TriggerMatch]) -> Optional[str]:
        """
        Get the suggested action based on trigger matches.

        Returns action string or None if no clear action.
        """
        if not matches:
            return None

        top_match = matches[0]

        if top_match.confidence < 0.5:
            return None

        return top_match.action_suggested


def detect_triggers(user_input: str) -> List[TriggerMatch]:
    """Convenience function to detect triggers."""
    detector = TriggerDetector()
    return detector.detect(user_input)


def check_for_switch(user_input: str) -> Optional[str]:
    """
    Check if user input suggests switching to an agent.

    Returns agent ID if switch detected, None otherwise.
    """
    matches = detect_triggers(user_input)

    for m in matches:
        if m.type in ("switch", "mention") and m.agent_id and m.confidence > 0.6:
            return m.agent_id

    return None


class SemanticTriggerDetector:
    """
    Semantic trigger detection using embeddings.

    Better than keyword matching for natural language references like:
    - "let's work on the QuickBooks thing" -> accounting-ph1
    - "back to the ERP integration" -> erp-integration
    """

    def __init__(self, similarity_threshold: float = 0.7):
        self.threshold = similarity_threshold
        self.embeddings = get_embeddings()
        self._agent_embeddings = {}

    def _get_agent_embedding(self, agent: Dict[str, Any]) -> Optional[List[float]]:
        """Get or compute embedding for an agent."""
        agent_id = agent["id"]
        if agent_id in self._agent_embeddings:
            return self._agent_embeddings[agent_id]

        if not self.embeddings:
            return None

        # Create text representation
        text = f"{agent['title']} {agent.get('goal', '')}"
        embedding = self.embeddings.embed(text)

        if embedding:
            self._agent_embeddings[agent_id] = embedding

        return embedding

    def detect_semantic_match(self, user_input: str) -> Optional[Tuple[str, str, float]]:
        """
        Use embeddings to detect which task user is referring to.

        Returns (agent_id, title, confidence) or None.
        """
        if not self.embeddings:
            return None

        # Embed user input
        input_embedding = self.embeddings.embed(user_input)
        if not input_embedding:
            return None

        # Compare to all active agents
        best_match = None
        best_score = 0.0

        for agent in list_agents():
            if agent.get("status") in ("completed", "cancelled"):
                continue

            agent_embedding = self._get_agent_embedding(agent)
            if not agent_embedding:
                continue

            similarity = cosine_sim(input_embedding, agent_embedding)

            if similarity > best_score and similarity > self.threshold:
                best_score = similarity
                best_match = (agent["id"], agent["title"], similarity)

        return best_match

    def enhance_triggers(self, user_input: str, keyword_matches: List[TriggerMatch]) -> List[TriggerMatch]:
        """
        Enhance keyword matches with semantic matches.

        Adds semantic matches that keyword detection missed.
        """
        enhanced = list(keyword_matches)

        # Try semantic matching
        semantic_match = self.detect_semantic_match(user_input)

        if semantic_match:
            agent_id, title, confidence = semantic_match

            # Check if already matched by keywords
            already_matched = any(m.agent_id == agent_id for m in enhanced)

            if not already_matched and confidence > 0.7:
                enhanced.append(TriggerMatch(
                    type="semantic",
                    agent_id=agent_id,
                    agent_title=title,
                    confidence=confidence,
                    matched_text=f"semantic:{user_input[:30]}",
                    action_suggested=f"Semantic match: [{agent_id}] {title}"
                ))

        # Re-sort by confidence
        enhanced.sort(key=lambda m: m.confidence, reverse=True)

        return enhanced


def detect_triggers_semantic(user_input: str) -> List[TriggerMatch]:
    """
    Detect triggers with semantic enhancement.

    Combines keyword and embedding-based matching.
    """
    # Get keyword matches
    detector = TriggerDetector()
    keyword_matches = detector.detect(user_input)

    # Enhance with semantic
    semantic_detector = SemanticTriggerDetector()
    return semantic_detector.enhance_triggers(user_input, keyword_matches)


def check_for_switch_semantic(user_input: str) -> Optional[str]:
    """
    Check for switch with semantic matching.

    More flexible than keyword-only matching.
    """
    matches = detect_triggers_semantic(user_input)

    for m in matches:
        if m.type in ("switch", "mention", "semantic") and m.agent_id and m.confidence > 0.6:
            return m.agent_id

    return None
