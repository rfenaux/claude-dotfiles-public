"""
Unified Temporal Utilities for Claude Code

Provides shared time-based calculations used across:
- scheduler.py (task priority decay)
- intent_predictor.py (pattern confidence decay)
- temporal_boost.py (RAG recency boost)
- briefing.py (time-ago formatting)

Consolidates duplicate implementations for:
- Exponential decay calculations
- Time delta formatting
- Timestamp parsing
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Tuple


# =============================================================================
# CONSTANTS
# =============================================================================

# Default halflife values (can be overridden)
DEFAULT_RECENCY_HALFLIFE_HOURS = 24  # For task recency
DEFAULT_NOVELTY_HALFLIFE_DAYS = 7    # For task freshness
DEFAULT_PATTERN_DECAY_DAYS = 30      # For pattern confidence


# =============================================================================
# TIMESTAMP PARSING
# =============================================================================

def parse_timestamp(
    timestamp: Union[str, datetime, None],
    default: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Parse a timestamp string to datetime with timezone.

    Handles various ISO 8601 formats and normalizes to UTC.

    Args:
        timestamp: ISO timestamp string, datetime, or None
        default: Default value if parsing fails

    Returns:
        datetime with timezone (UTC) or default
    """
    if timestamp is None:
        return default

    if isinstance(timestamp, datetime):
        if timestamp.tzinfo is None:
            return timestamp.replace(tzinfo=timezone.utc)
        return timestamp

    if not isinstance(timestamp, str):
        return default

    try:
        # Handle "Z" suffix
        ts = timestamp.rstrip("Z")
        if "+" not in ts and "-" not in ts[-6:]:
            # No timezone info, assume UTC
            ts += "+00:00"
        elif timestamp.endswith("Z"):
            ts = timestamp[:-1] + "+00:00"

        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    except (ValueError, TypeError):
        return default


def now_utc() -> datetime:
    """Get current time in UTC."""
    return datetime.now(timezone.utc)


# =============================================================================
# TIME DELTAS
# =============================================================================

def time_since(
    timestamp: Union[str, datetime, None],
    unit: str = 'auto'
) -> Tuple[float, str]:
    """
    Calculate time elapsed since a timestamp.

    Args:
        timestamp: The timestamp to measure from
        unit: 'seconds', 'minutes', 'hours', 'days', or 'auto'

    Returns:
        Tuple of (value, unit_string)
        e.g., (2.5, 'hours') or (3, 'days')
    """
    dt = parse_timestamp(timestamp)
    if dt is None:
        return (0, 'unknown')

    now = now_utc()
    delta = now - dt

    total_seconds = delta.total_seconds()
    total_minutes = total_seconds / 60
    total_hours = total_minutes / 60
    total_days = total_hours / 24

    if unit == 'seconds':
        return (total_seconds, 'seconds')
    elif unit == 'minutes':
        return (total_minutes, 'minutes')
    elif unit == 'hours':
        return (total_hours, 'hours')
    elif unit == 'days':
        return (total_days, 'days')
    else:  # auto
        if total_days >= 1:
            return (total_days, 'days')
        elif total_hours >= 1:
            return (total_hours, 'hours')
        elif total_minutes >= 1:
            return (total_minutes, 'minutes')
        else:
            return (total_seconds, 'seconds')


def format_time_ago(
    timestamp: Union[str, datetime, None],
    short: bool = True
) -> str:
    """
    Format timestamp as human-readable "time ago" string.

    Args:
        timestamp: The timestamp
        short: If True, use abbreviated format (e.g., "2h ago")

    Returns:
        Formatted string like "2 hours ago" or "2h ago"
    """
    value, unit = time_since(timestamp)

    if unit == 'unknown':
        return 'unknown'

    value = int(value)

    if short:
        unit_short = {
            'seconds': 's',
            'minutes': 'm',
            'hours': 'h',
            'days': 'd'
        }
        return f"{value}{unit_short.get(unit, unit[0])} ago"
    else:
        if value == 1:
            unit = unit.rstrip('s')  # Remove plural
        return f"{value} {unit} ago"


# =============================================================================
# EXPONENTIAL DECAY FUNCTIONS
# =============================================================================

def decay_exp2(
    timestamp: Union[str, datetime, None],
    halflife_hours: float = DEFAULT_RECENCY_HALFLIFE_HOURS,
    min_value: float = 0.0
) -> float:
    """
    Calculate exponential decay using base 2.

    Formula: 2^(-hours_since / halflife)

    Used by scheduler.py for task recency.

    Args:
        timestamp: When the thing was last active
        halflife_hours: Time in hours for value to halve
        min_value: Minimum return value (floor)

    Returns:
        Decay value between min_value and 1.0
    """
    hours, _ = time_since(timestamp, unit='hours')
    if hours <= 0:
        return 1.0

    decay = math.pow(2, -hours / halflife_hours)
    return max(min_value, decay)


def decay_exp(
    timestamp: Union[str, datetime, None],
    halflife_days: float = DEFAULT_PATTERN_DECAY_DAYS,
    min_value: float = 0.0
) -> float:
    """
    Calculate exponential decay using natural exponential.

    Formula: exp(-days_since / halflife)

    Used by intent_predictor.py for pattern confidence.

    Args:
        timestamp: When the thing was last seen
        halflife_days: Time in days for value to decay to ~37%
        min_value: Minimum return value (floor)

    Returns:
        Decay value between min_value and 1.0
    """
    days, _ = time_since(timestamp, unit='days')
    if days <= 0:
        return 1.0

    decay = math.exp(-days / halflife_days)
    return max(min_value, decay)


def decay_novelty(
    created_at: Union[str, datetime, None],
    halflife_days: float = DEFAULT_NOVELTY_HALFLIFE_DAYS,
    min_value: float = 0.1
) -> float:
    """
    Calculate novelty decay (how "fresh" something is).

    Formula: max(min_value, 2^(-days_since / halflife))

    Used by scheduler.py for task novelty scoring.

    Args:
        created_at: When the thing was created
        halflife_days: Days for novelty to halve
        min_value: Minimum novelty (never fully stale)

    Returns:
        Novelty value between min_value and 1.0
    """
    days, _ = time_since(created_at, unit='days')
    if days <= 0:
        return 1.0

    novelty = math.pow(2, -days / halflife_days)
    return max(min_value, novelty)


# =============================================================================
# CONFIDENCE CALCULATIONS
# =============================================================================

def calculate_confidence(
    frequency: int,
    last_seen: Union[str, datetime, None],
    halflife_days: float = DEFAULT_PATTERN_DECAY_DAYS,
    frequency_factor: int = 5,
    max_confidence: float = 0.95
) -> float:
    """
    Calculate confidence score based on frequency and recency.

    Formula: min(max_confidence, freq / (freq + factor) * recency_decay)

    Used by intent_predictor.py for pattern confidence.

    Args:
        frequency: Number of times observed
        last_seen: When last observed
        halflife_days: Decay period
        frequency_factor: Denominator factor (higher = slower growth)
        max_confidence: Maximum confidence cap

    Returns:
        Confidence value between 0.0 and max_confidence
    """
    if frequency <= 0:
        return 0.0

    # Frequency-based confidence
    freq_confidence = frequency / (frequency + frequency_factor)

    # Recency factor
    recency_factor = decay_exp(last_seen, halflife_days)

    # Combined with cap
    return min(max_confidence, freq_confidence * recency_factor)


# =============================================================================
# DEADLINE URGENCY
# =============================================================================

def calculate_urgency(
    deadline: Union[str, datetime, None],
    default_urgency: float = 0.5
) -> float:
    """
    Calculate urgency score based on deadline proximity.

    Used by scheduler.py for deadline-aware prioritization.

    Args:
        deadline: The deadline timestamp
        default_urgency: Value to return if no deadline

    Returns:
        Urgency score between 0.0 and 1.0
    """
    dt = parse_timestamp(deadline)
    if dt is None:
        return default_urgency

    now = now_utc()
    delta = dt - now
    hours_until = delta.total_seconds() / 3600
    days_until = delta.days

    if hours_until <= 0:
        return 1.0  # Overdue - maximum urgency
    elif days_until <= 1:
        return 0.95  # Due today/tomorrow
    elif days_until <= 3:
        return 0.85  # Critical - within 3 days
    elif days_until <= 7:
        return 0.70  # Soon - within a week
    elif days_until <= 14:
        return 0.55  # Coming up - within 2 weeks
    else:
        # Gradual decay for longer deadlines
        return max(0.3, 0.5 * (30 / max(30, days_until)))


# =============================================================================
# STALENESS CHECKS
# =============================================================================

def is_stale(
    timestamp: Union[str, datetime, None],
    threshold_days: int = 7
) -> bool:
    """
    Check if something is stale (not updated in threshold period).

    Args:
        timestamp: Last update timestamp
        threshold_days: Days after which it's considered stale

    Returns:
        True if stale, False otherwise
    """
    days, _ = time_since(timestamp, unit='days')
    return days > threshold_days


def staleness_level(
    timestamp: Union[str, datetime, None]
) -> str:
    """
    Get staleness level as a category.

    Args:
        timestamp: Last update timestamp

    Returns:
        One of: 'fresh', 'recent', 'aging', 'stale', 'very_stale'
    """
    days, _ = time_since(timestamp, unit='days')

    if days < 1:
        return 'fresh'
    elif days < 3:
        return 'recent'
    elif days < 7:
        return 'aging'
    elif days < 14:
        return 'stale'
    else:
        return 'very_stale'


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Constants
    'DEFAULT_RECENCY_HALFLIFE_HOURS',
    'DEFAULT_NOVELTY_HALFLIFE_DAYS',
    'DEFAULT_PATTERN_DECAY_DAYS',
    # Parsing
    'parse_timestamp',
    'now_utc',
    # Deltas
    'time_since',
    'format_time_ago',
    # Decay
    'decay_exp2',
    'decay_exp',
    'decay_novelty',
    # Confidence
    'calculate_confidence',
    # Urgency
    'calculate_urgency',
    # Staleness
    'is_stale',
    'staleness_level',
]
