"""Extract dates mentioned within text content for chronology awareness."""
import re
from datetime import datetime
from typing import List, Optional, Tuple
from collections import Counter


# Month name mappings (English + French)
MONTH_NAMES = {
    # English
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    # French
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
    "juillet": 7, "août": 8, "aout": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}


def extract_dates(text: str) -> Tuple[Optional[str], List[str]]:
    """Extract dates mentioned in text content.

    Returns:
        Tuple of (most_recent_date, all_unique_dates) where dates are YYYY-MM-DD strings.
        Returns (None, []) if no valid dates found.
    """
    if not text:
        return None, []

    dates_found = []

    # Pattern 1: ISO format YYYY-MM-DD
    iso_pattern = r'\b(20[0-2][0-9])-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])\b'
    for match in re.finditer(iso_pattern, text):
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if _is_valid_date(year, month, day):
                dates_found.append(f"{year:04d}-{month:02d}-{day:02d}")
        except ValueError:
            pass

    # Pattern 2: European format DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY
    eu_pattern = r'\b(0?[1-9]|[12][0-9]|3[01])[/\-\.](0?[1-9]|1[0-2])[/\-\.](20[0-2][0-9])\b'
    for match in re.finditer(eu_pattern, text):
        try:
            day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
            if _is_valid_date(year, month, day):
                dates_found.append(f"{year:04d}-{month:02d}-{day:02d}")
        except ValueError:
            pass

    # Pattern 3: Written format - "January 15, 2024" or "15 January 2024"
    month_names_pattern = '|'.join(MONTH_NAMES.keys())

    # "January 15, 2024" or "January 15 2024"
    written_pattern1 = rf'\b({month_names_pattern})\s+(0?[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?[,\s]?\s*(20[0-2][0-9])\b'
    for match in re.finditer(written_pattern1, text, re.IGNORECASE):
        try:
            month = MONTH_NAMES[match.group(1).lower()]
            day = int(match.group(2))
            year = int(match.group(3))
            if _is_valid_date(year, month, day):
                dates_found.append(f"{year:04d}-{month:02d}-{day:02d}")
        except (KeyError, ValueError):
            pass

    # "15 January 2024" or "15th January 2024"
    written_pattern2 = rf'\b(0?[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?\s+({month_names_pattern})[,\s]?\s*(20[0-2][0-9])\b'
    for match in re.finditer(written_pattern2, text, re.IGNORECASE):
        try:
            day = int(match.group(1))
            month = MONTH_NAMES[match.group(2).lower()]
            year = int(match.group(3))
            if _is_valid_date(year, month, day):
                dates_found.append(f"{year:04d}-{month:02d}-{day:02d}")
        except (KeyError, ValueError):
            pass

    # Pattern 4: Month/Year only - "January 2024" (use day 1)
    month_year_pattern = rf'\b({month_names_pattern})\s+(20[0-2][0-9])\b'
    for match in re.finditer(month_year_pattern, text, re.IGNORECASE):
        try:
            month = MONTH_NAMES[match.group(1).lower()]
            year = int(match.group(2))
            # Only add if we don't already have a more specific date for this month
            month_key = f"{year:04d}-{month:02d}"
            if not any(d.startswith(month_key) for d in dates_found):
                dates_found.append(f"{year:04d}-{month:02d}-01")
        except (KeyError, ValueError):
            pass

    # Pattern 5: Quarter references - "Q1 2024", "Q4 2023"
    quarter_pattern = r'\bQ([1-4])\s*(20[0-2][0-9])\b'
    for match in re.finditer(quarter_pattern, text, re.IGNORECASE):
        try:
            quarter = int(match.group(1))
            year = int(match.group(2))
            # Use first month of quarter
            month = (quarter - 1) * 3 + 1
            dates_found.append(f"{year:04d}-{month:02d}-01")
        except ValueError:
            pass

    # Deduplicate and sort
    unique_dates = sorted(set(dates_found))

    # Get most recent date
    most_recent = unique_dates[-1] if unique_dates else None

    return most_recent, unique_dates


def _is_valid_date(year: int, month: int, day: int) -> bool:
    """Check if a date is valid and reasonable (2000-2029)."""
    if not (2000 <= year <= 2029):
        return False
    if not (1 <= month <= 12):
        return False
    if not (1 <= day <= 31):
        return False

    # Check actual day validity for month
    try:
        datetime(year, month, day)
        return True
    except ValueError:
        return False


def get_date_context(text: str, max_dates: int = 5) -> dict:
    """Get date context for a text chunk.

    Returns a dict with:
    - most_recent: The most recent date mentioned (YYYY-MM-DD)
    - dates: List of all unique dates found (up to max_dates)
    - date_range: Tuple of (earliest, latest) if multiple dates found
    """
    most_recent, all_dates = extract_dates(text)

    if not all_dates:
        return {
            "most_recent": None,
            "dates": [],
            "date_range": None,
        }

    # Limit number of dates stored
    dates_to_store = all_dates[-max_dates:] if len(all_dates) > max_dates else all_dates

    return {
        "most_recent": most_recent,
        "dates": dates_to_store,
        "date_range": (all_dates[0], all_dates[-1]) if len(all_dates) > 1 else None,
    }
