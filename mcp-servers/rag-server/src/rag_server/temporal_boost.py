"""Temporal boosting for RAG search results.

Applies recency weighting to search results based on:
1. Content dates mentioned within the text
2. File modification dates
3. Supersession detection (content marked as replaced)

This helps Claude prioritize newer decisions over older ones when conflicts exist.
"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Supersession patterns - content that indicates this is outdated/replaced
SUPERSESSION_PATTERNS = [
    # Explicit supersession markers
    (r'(?:superseded|replaced|updated)\s+(?:by|with|to)', 0.3),  # Strong signal
    (r'~~[^~]+~~', 0.4),  # Strikethrough markdown
    (r'\[(?:deprecated|obsolete|outdated|superseded)\]', 0.3),

    # Historical reference markers
    (r'(?:was|were)\s+(?:originally|previously|initially)', 0.6),
    (r'(?:old|former|previous)\s+(?:decision|approach|design)', 0.5),
    (r'(?:no\s+longer|not\s+anymore)', 0.5),

    # Phase/version markers indicating old content
    (r'(?:phase\s*1|v1|version\s*1)[^0-9].*?(?:replaced|upgraded)', 0.5),
    (r'(?:before|prior\s+to)\s+(?:the\s+)?(?:change|update|migration)', 0.6),
]

# Recency tiers for temporal boosting
# Boost factor is multiplied against the distance (lower = better ranking)
RECENCY_BOOST = {
    'very_recent': 0.7,    # Last 7 days - 30% boost
    'recent': 0.85,        # Last 30 days - 15% boost
    'moderate': 1.0,       # Last 90 days - no change
    'older': 1.1,          # Last year - 10% penalty
    'historical': 1.2,     # Older than 1 year - 20% penalty
}


def detect_supersession(text: str) -> Tuple[bool, float]:
    """Detect if content appears to be superseded/outdated.

    Returns:
        (is_superseded, confidence) where confidence is 0-1
    """
    if not text:
        return False, 0.0

    text_lower = text.lower()
    max_confidence = 0.0

    for pattern, confidence in SUPERSESSION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            max_confidence = max(max_confidence, 1 - confidence)  # Invert: pattern conf -> supersession conf

    return max_confidence > 0.3, max_confidence


def get_recency_tier(date_str: Optional[str]) -> str:
    """Determine recency tier from a date string.

    Args:
        date_str: Date in YYYY-MM-DD format

    Returns:
        Tier name (very_recent, recent, moderate, older, historical)
    """
    if not date_str:
        return 'moderate'  # Default to neutral

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        now = datetime.now()
        age = now - date

        if age < timedelta(days=7):
            return 'very_recent'
        elif age < timedelta(days=30):
            return 'recent'
        elif age < timedelta(days=90):
            return 'moderate'
        elif age < timedelta(days=365):
            return 'older'
        else:
            return 'historical'
    except (ValueError, TypeError):
        return 'moderate'


def apply_temporal_boost(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply temporal boosting to search results.

    Adjusts scores based on:
    1. Date recency (newer content ranks higher)
    2. Supersession detection (superseded content ranks lower)

    Args:
        results: Search results with 'score', 'relevant_date', 'text' fields

    Returns:
        Results with adjusted scores and temporal metadata, re-sorted
    """
    for result in results:
        original_score = result.get('score', 0)

        # Get relevant date (prefer content_date over file_date)
        relevant_date = result.get('relevant_date') or result.get('content_date') or result.get('file_date')

        # Calculate recency boost
        tier = get_recency_tier(relevant_date)
        recency_boost = RECENCY_BOOST.get(tier, 1.0)

        # Check for supersession
        text = result.get('text', '')
        is_superseded, supersession_confidence = detect_supersession(text)

        # Apply supersession penalty (boost the distance = lower ranking)
        supersession_penalty = 1.0 + (supersession_confidence * 0.3) if is_superseded else 1.0

        # Combined temporal adjustment
        temporal_factor = recency_boost * supersession_penalty

        # Apply to score
        result['temporal_original_score'] = original_score
        result['score'] = original_score * temporal_factor
        result['temporal_boost'] = {
            'factor': temporal_factor,
            'recency_tier': tier,
            'recency_boost': recency_boost,
            'is_superseded': is_superseded,
            'supersession_confidence': round(supersession_confidence, 2) if is_superseded else None,
        }

    # Re-sort by adjusted score
    return sorted(results, key=lambda x: x['score'])


def extract_decision_date(text: str) -> Optional[str]:
    """Extract decision date from DECISIONS.md format.

    Looks for patterns like:
    - **Decided**: 2026-01-07
    - Decided: 2026-01-07
    - [2026-01-07] Decided...

    Returns:
        Date string in YYYY-MM-DD format or None
    """
    patterns = [
        r'\*\*Decided\*\*:\s*(\d{4}-\d{2}-\d{2})',
        r'Decided:\s*(\d{4}-\d{2}-\d{2})',
        r'\[(\d{4}-\d{2}-\d{2})\]',
        r'- \*\*(\d{4}-\d{2}-\d{2})\*\*',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None


def compare_decision_dates(result1: Dict, result2: Dict) -> int:
    """Compare two results by decision date for conflict resolution.

    Returns:
        -1 if result1 is newer, 1 if result2 is newer, 0 if equal/unknown
    """
    date1 = result1.get('relevant_date') or extract_decision_date(result1.get('text', ''))
    date2 = result2.get('relevant_date') or extract_decision_date(result2.get('text', ''))

    if not date1 and not date2:
        return 0
    if not date1:
        return 1
    if not date2:
        return -1

    if date1 > date2:
        return -1
    elif date1 < date2:
        return 1
    return 0
