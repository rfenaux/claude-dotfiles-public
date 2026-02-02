"""Chunk classification for enhanced retrieval.

Classifies chunks by:
1. Relevance: critical | high | medium | low | reference
2. Category: decision | requirement | business_strategy | business_process |
             technical | constraint | risk | action_item | context
3. Custom tags: Optional LLM-extracted tags specific to content

Two modes:
- Rule-based (default): Fast keyword/pattern matching
- LLM-enhanced: Uses Ollama for better accuracy + custom tags
"""
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Relevance(str, Enum):
    """Relevance levels for chunks."""
    CRITICAL = "critical"    # Must-know, blocking decisions
    HIGH = "high"            # Important information
    MEDIUM = "medium"        # Standard content (default)
    LOW = "low"              # Nice-to-know, optional
    REFERENCE = "reference"  # Background, historical


class Category(str, Enum):
    """Thematic categories for chunks."""
    DECISION = "decision"              # Choices made, rationale
    REQUIREMENT = "requirement"        # What must be done
    BUSINESS_STRATEGY = "business_strategy"  # Goals, vision
    BUSINESS_PROCESS = "business_process"    # Workflows, operations
    TECHNICAL = "technical"            # Implementation details
    CONSTRAINT = "constraint"          # Limitations, boundaries
    RISK = "risk"                      # Issues, concerns
    ACTION_ITEM = "action_item"        # Tasks, next steps
    CONTEXT = "context"                # Background information


# Relevance patterns: (regex_pattern, relevance_level, weight)
RELEVANCE_PATTERNS: List[Tuple[str, Relevance, float]] = [
    # Critical signals
    (r'\b(must|mandatory|required|critical|blocker|blocking|essential|non-negotiable)\b', Relevance.CRITICAL, 1.0),
    (r'\b(p0|priority\s*0|severity\s*1|sev-?1)\b', Relevance.CRITICAL, 1.0),
    (r'\bcritical\s+(requirement|decision|issue|bug)\b', Relevance.CRITICAL, 1.0),

    # High signals
    (r'\b(important|key|significant|priority|should|primary|major)\b', Relevance.HIGH, 0.8),
    (r'\b(p1|priority\s*1|high\s*priority)\b', Relevance.HIGH, 0.9),
    (r'\b(core|fundamental|strategic)\b', Relevance.HIGH, 0.7),

    # Low signals
    (r'\b(optional|nice\s*to\s*have|could|might|possibly|future|later|someday)\b', Relevance.LOW, 0.7),
    (r'\b(p3|p4|low\s*priority|minor)\b', Relevance.LOW, 0.8),
    (r'\b(enhancement|improvement|wish\s*list)\b', Relevance.LOW, 0.6),

    # Reference signals
    (r'\b(previously|formerly|legacy|deprecated|old|historical|was|used\s*to)\b', Relevance.REFERENCE, 0.6),
    (r'\b(background|context|fyi|for\s*reference|note\s*that)\b', Relevance.REFERENCE, 0.5),
    (r'\b(archive|obsolete|outdated)\b', Relevance.REFERENCE, 0.8),

    # Supersession signals - content that has been replaced
    (r'~~[^~]+~~', Relevance.REFERENCE, 1.0),  # Strikethrough markdown = superseded
    (r'\b(superseded|replaced)\s+(?:by|with)', Relevance.REFERENCE, 1.0),
    (r'\[(?:deprecated|obsolete|superseded)\]', Relevance.REFERENCE, 0.9),
    (r'→\s*\w+\s*\(\d{4}', Relevance.REFERENCE, 0.8),  # "→ PostgreSQL (2026" pattern
]

# Category patterns: (regex_pattern, category, weight)
CATEGORY_PATTERNS: List[Tuple[str, Category, float]] = [
    # Decision
    (r'\b(decided|decision|agreed|chosen|selected|will\s+use|opted\s+for)\b', Category.DECISION, 0.9),
    (r'\b(rationale|reasoning|why\s+we|because)\b', Category.DECISION, 0.6),
    (r'\b(approved|confirmed|finalized)\b', Category.DECISION, 0.8),

    # Requirement
    (r'\b(requirement|shall|must\s+be|needs?\s+to|has\s+to)\b', Category.REQUIREMENT, 0.9),
    (r'\b(user\s+story|acceptance\s+criteria|as\s+a\s+user)\b', Category.REQUIREMENT, 1.0),
    (r'\b(spec|specification|functional|non-functional)\b', Category.REQUIREMENT, 0.7),

    # Business Strategy
    (r'\b(strategy|strategic|vision|mission|goal|objective)\b', Category.BUSINESS_STRATEGY, 0.9),
    (r'\b(roadmap|milestone|okr|kpi|target)\b', Category.BUSINESS_STRATEGY, 0.8),
    (r'\b(market|competitive|positioning|growth)\b', Category.BUSINESS_STRATEGY, 0.7),
    (r'\b(business\s+model|revenue|pricing)\b', Category.BUSINESS_STRATEGY, 0.8),

    # Business Process
    (r'\b(process|workflow|procedure|step\s*\d|flow)\b', Category.BUSINESS_PROCESS, 0.8),
    (r'\b(sop|standard\s+operating|handoff|escalation)\b', Category.BUSINESS_PROCESS, 0.9),
    (r'\b(approval|review\s+process|sign-?off)\b', Category.BUSINESS_PROCESS, 0.7),
    (r'\b(lifecycle|stage|phase|pipeline)\b', Category.BUSINESS_PROCESS, 0.6),

    # Technical
    (r'\b(api|endpoint|database|schema|architecture)\b', Category.TECHNICAL, 0.9),
    (r'\b(implementation|code|function|class|method)\b', Category.TECHNICAL, 0.8),
    (r'\b(server|client|frontend|backend|infrastructure)\b', Category.TECHNICAL, 0.7),
    (r'\b(integration|webhook|oauth|authentication)\b', Category.TECHNICAL, 0.8),
    (r'\b(deploy|ci/cd|docker|kubernetes)\b', Category.TECHNICAL, 0.9),

    # Constraint
    (r'\b(constraint|limitation|cannot|restricted|boundary)\b', Category.CONSTRAINT, 0.9),
    (r'\b(budget|timeline|deadline|scope)\b', Category.CONSTRAINT, 0.7),
    (r'\b(compliance|regulation|legal|gdpr|security)\b', Category.CONSTRAINT, 0.8),
    (r'\b(out\s+of\s+scope|excluded|not\s+included)\b', Category.CONSTRAINT, 0.9),

    # Risk
    (r'\b(risk|concern|issue|problem|blocker)\b', Category.RISK, 0.8),
    (r'\b(mitigation|contingency|fallback)\b', Category.RISK, 0.7),
    (r'\b(warning|caution|careful|attention)\b', Category.RISK, 0.6),
    (r'\b(dependency|bottleneck|single\s+point)\b', Category.RISK, 0.7),

    # Action Item
    (r'\b(todo|to-do|action\s*item|task|assign)\b', Category.ACTION_ITEM, 0.9),
    (r'\b(next\s+step|follow\s*up|owner|responsible)\b', Category.ACTION_ITEM, 0.8),
    (r'\b(deadline|due\s+date|by\s+\w+\s+\d+)\b', Category.ACTION_ITEM, 0.7),
    (r'\[@\w+\]|\(\s*@\w+\s*\)', Category.ACTION_ITEM, 0.9),  # @mentions

    # Context
    (r'\b(background|context|overview|introduction)\b', Category.CONTEXT, 0.8),
    (r'\b(history|previously|originally|initially)\b', Category.CONTEXT, 0.7),
    (r'\b(summary|recap|tldr|in\s+summary)\b', Category.CONTEXT, 0.6),
]

# Header level to relevance mapping
HEADER_RELEVANCE: Dict[int, Relevance] = {
    1: Relevance.HIGH,      # H1 headers
    2: Relevance.HIGH,      # H2 headers
    3: Relevance.MEDIUM,    # H3 headers
    4: Relevance.MEDIUM,    # H4 headers
    5: Relevance.LOW,       # H5 headers
    6: Relevance.LOW,       # H6 headers
}


@dataclass
class Classification:
    """Classification result for a chunk."""
    relevance: Relevance
    relevance_confidence: float
    category: Category
    category_confidence: float
    custom_tags: List[str]
    signals: List[str]  # Which patterns matched

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "relevance": self.relevance.value,
            "relevance_confidence": round(self.relevance_confidence, 2),
            "category": self.category.value,
            "category_confidence": round(self.category_confidence, 2),
            "custom_tags": self.custom_tags,
            "signals": self.signals[:5],  # Keep top 5 signals for debugging
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Classification":
        """Create from dictionary."""
        return cls(
            relevance=Relevance(data.get("relevance", "medium")),
            relevance_confidence=data.get("relevance_confidence", 0.5),
            category=Category(data.get("category", "context")),
            category_confidence=data.get("category_confidence", 0.5),
            custom_tags=data.get("custom_tags", []),
            signals=data.get("signals", []),
        )


class ChunkClassifier:
    """Classify chunks by relevance and category."""

    def __init__(self, use_llm: bool = False, ollama_model: str = "llama3.2:3b"):
        """Initialize classifier.

        Args:
            use_llm: Whether to use LLM for enhanced classification
            ollama_model: Ollama model for LLM classification
        """
        self.use_llm = use_llm
        self.ollama_model = ollama_model

        # Compile patterns for performance
        self._relevance_patterns = [
            (re.compile(pattern, re.IGNORECASE), level, weight)
            for pattern, level, weight in RELEVANCE_PATTERNS
        ]
        self._category_patterns = [
            (re.compile(pattern, re.IGNORECASE), cat, weight)
            for pattern, cat, weight in CATEGORY_PATTERNS
        ]

    def classify(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Classification:
        """Classify a chunk of text.

        Args:
            text: Chunk text to classify
            metadata: Optional metadata (section_level, section_header, etc.)

        Returns:
            Classification result
        """
        metadata = metadata or {}
        signals = []

        # Rule-based classification
        relevance, rel_conf, rel_signals = self._classify_relevance(text, metadata)
        category, cat_conf, cat_signals = self._classify_category(text)

        signals.extend(rel_signals)
        signals.extend(cat_signals)

        # Custom tags (empty for rule-based, filled by LLM if enabled)
        custom_tags = []

        # LLM enhancement if enabled
        if self.use_llm:
            llm_result = self._llm_classify(text)
            if llm_result:
                # LLM can override low-confidence classifications
                if llm_result.get("relevance") and rel_conf < 0.7:
                    relevance = Relevance(llm_result["relevance"])
                    rel_conf = max(rel_conf, 0.8)
                if llm_result.get("category") and cat_conf < 0.7:
                    category = Category(llm_result["category"])
                    cat_conf = max(cat_conf, 0.8)
                custom_tags = llm_result.get("tags", [])

        return Classification(
            relevance=relevance,
            relevance_confidence=rel_conf,
            category=category,
            category_confidence=cat_conf,
            custom_tags=custom_tags,
            signals=signals,
        )

    def _classify_relevance(
        self,
        text: str,
        metadata: Dict[str, Any]
    ) -> Tuple[Relevance, float, List[str]]:
        """Classify relevance level using patterns."""
        scores: Dict[Relevance, float] = {r: 0.0 for r in Relevance}
        signals = []

        # Check text patterns
        for pattern, level, weight in self._relevance_patterns:
            matches = pattern.findall(text)
            if matches:
                scores[level] += weight * len(matches)
                signals.append(f"rel:{level.value}:{matches[0]}")

        # Boost based on header level
        section_level = metadata.get("section_level")
        if section_level and section_level in HEADER_RELEVANCE:
            header_rel = HEADER_RELEVANCE[section_level]
            scores[header_rel] += 0.3
            signals.append(f"header:h{section_level}")

        # Find best match
        if max(scores.values()) > 0:
            best = max(scores.items(), key=lambda x: x[1])
            confidence = min(0.95, 0.5 + best[1] * 0.2)
            return best[0], confidence, signals

        # Default to medium
        return Relevance.MEDIUM, 0.5, signals

    def _classify_category(self, text: str) -> Tuple[Category, float, List[str]]:
        """Classify category using patterns."""
        scores: Dict[Category, float] = {c: 0.0 for c in Category}
        signals = []

        for pattern, cat, weight in self._category_patterns:
            matches = pattern.findall(text)
            if matches:
                scores[cat] += weight * min(len(matches), 3)  # Cap at 3 matches
                signals.append(f"cat:{cat.value}:{matches[0]}")

        # Find best match
        if max(scores.values()) > 0:
            best = max(scores.items(), key=lambda x: x[1])
            confidence = min(0.95, 0.5 + best[1] * 0.15)
            return best[0], confidence, signals

        # Default to context
        return Category.CONTEXT, 0.4, signals

    def _llm_classify(self, text: str) -> Optional[Dict[str, Any]]:
        """Use LLM for enhanced classification (optional).

        Returns dict with:
        - relevance: Override relevance if confident
        - category: Override category if confident
        - tags: List of custom tags
        """
        try:
            import httpx

            prompt = f"""Classify this text chunk. Respond with JSON only.

Text:
{text[:1500]}

Respond with:
{{
  "relevance": "critical|high|medium|low|reference",
  "category": "decision|requirement|business_strategy|business_process|technical|constraint|risk|action_item|context",
  "tags": ["tag1", "tag2"]  // 2-4 specific tags describing the content
}}

JSON:"""

            response = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                },
                timeout=10.0
            )

            if response.status_code == 200:
                import json
                result_text = response.json().get("response", "")
                # Extract JSON from response
                start = result_text.find("{")
                end = result_text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(result_text[start:end])
        except Exception:
            pass  # Fall back to rule-based

        return None


def classify_chunk(
    text: str,
    metadata: Optional[Dict[str, Any]] = None,
    use_llm: bool = False
) -> Dict[str, Any]:
    """Convenience function to classify a chunk.

    Args:
        text: Chunk text
        metadata: Optional metadata
        use_llm: Whether to use LLM enhancement

    Returns:
        Classification as dictionary
    """
    classifier = ChunkClassifier(use_llm=use_llm)
    result = classifier.classify(text, metadata)
    return result.to_dict()


# Relevance boost factors for search ranking
RELEVANCE_BOOST: Dict[str, float] = {
    "critical": 0.7,   # Multiply distance by 0.7 (30% boost)
    "high": 0.85,      # 15% boost
    "medium": 1.0,     # No change
    "low": 1.1,        # 10% penalty
    "reference": 1.2,  # 20% penalty
}


def apply_relevance_boost(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply relevance boosting to search results.

    Modifies the score based on relevance level.
    Lower score = better match in vector search.

    Args:
        results: Search results with 'score' and 'metadata' fields

    Returns:
        Results with adjusted scores, re-sorted
    """
    for result in results:
        metadata = result.get("metadata", {})
        classification = metadata.get("classification", {})
        relevance = classification.get("relevance", "medium")

        boost = RELEVANCE_BOOST.get(relevance, 1.0)
        original_score = result.get("score", 0)
        result["original_score"] = original_score
        result["score"] = original_score * boost
        result["relevance_boost"] = boost

    # Re-sort by adjusted score
    return sorted(results, key=lambda x: x["score"])
