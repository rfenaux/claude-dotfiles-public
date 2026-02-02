"""
Progress Auto-Tracking Module (CTM v3.0)

Infers task progress from multiple signals:
- File activity (key files touched)
- Git commits mentioning task
- Manual progress (highest weight)
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import get_ctm_dir


# Weight configuration for progress signals
SIGNAL_WEIGHTS = {
    "manual": 3.0,      # Manual progress gets highest weight
    "files": 2.0,       # File activity
    "commits": 1.0,     # Git commits
}

# Maximum contribution from each signal type
SIGNAL_CAPS = {
    "manual": 100,
    "files": 100,
    "commits": 50,      # Commits capped at 50% contribution
}

# Time window for "recent" file modifications (days)
RECENT_WINDOW_DAYS = 7


def get_file_mtime(filepath: str) -> Optional[datetime]:
    """Get file modification time, or None if file doesn't exist."""
    try:
        stat = os.stat(filepath)
        return datetime.fromtimestamp(stat.st_mtime)
    except (OSError, FileNotFoundError):
        return None


def count_recently_modified(
    filepaths: List[str],
    base_path: Optional[str] = None,
    window_days: int = RECENT_WINDOW_DAYS
) -> int:
    """Count how many files were modified within the time window."""
    cutoff = datetime.now() - timedelta(days=window_days)
    touched = 0

    for fp in filepaths:
        # Resolve relative paths if base_path provided
        if base_path and not os.path.isabs(fp):
            fp = os.path.join(base_path, fp)

        mtime = get_file_mtime(fp)
        if mtime and mtime > cutoff:
            touched += 1

    return touched


def count_commits_mentioning(
    search_term: str,
    repo_path: Optional[str] = None,
    since_days: int = 30
) -> int:
    """Count git commits mentioning a search term (agent ID or task title)."""
    try:
        since = (datetime.now() - timedelta(days=since_days)).strftime("%Y-%m-%d")
        cmd = [
            "git", "log",
            f"--since={since}",
            f"--grep={search_term}",
            "--oneline"
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=repo_path,
            timeout=5
        )

        if result.returncode == 0:
            lines = [l for l in result.stdout.strip().split('\n') if l]
            return len(lines)
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        pass

    return 0


def weighted_average(signals: List[Tuple[str, float]]) -> int:
    """Calculate weighted average of progress signals."""
    if not signals:
        return 0

    total_weight = 0.0
    weighted_sum = 0.0

    for signal_type, value in signals:
        weight = SIGNAL_WEIGHTS.get(signal_type, 1.0)
        cap = SIGNAL_CAPS.get(signal_type, 100)
        capped_value = min(value, cap)

        weighted_sum += capped_value * weight
        total_weight += weight

    if total_weight == 0:
        return 0

    return int(round(weighted_sum / total_weight))


class ProgressTracker:
    """Tracks and infers progress for CTM agents."""

    def __init__(self):
        self._cache: Dict[str, Tuple[datetime, int]] = {}
        self._cache_ttl = timedelta(minutes=5)

    def infer_progress(self, agent: "Agent") -> Optional[int]:
        """
        Infer progress from various signals.

        Returns weighted average of:
        - Manual progress (weight: 3.0)
        - Key files touched ratio (weight: 2.0)
        - Git commits mentioning task (weight: 1.0, capped at 50%)
        """
        # Check cache
        cache_key = agent.id
        if cache_key in self._cache:
            cached_time, cached_value = self._cache[cache_key]
            if datetime.now() - cached_time < self._cache_ttl:
                return cached_value

        signals: List[Tuple[str, float]] = []

        # 1. Manual progress (highest priority)
        manual = agent.state.get("progress_pct", 0)
        if manual > 0:
            signals.append(("manual", float(manual)))

        # 2. Key files touched ratio
        context = agent.context or {}
        key_files = context.get("key_files", [])
        project_path = context.get("project_path")

        if key_files:
            touched = count_recently_modified(key_files, project_path)
            file_progress = (touched / len(key_files)) * 100
            signals.append(("files", file_progress))

        # 3. Git commits mentioning task
        # Search for agent ID (short) or task title
        search_terms = [agent.id[:8]]  # Short ID
        if agent.task and agent.task.get("title"):
            # Add first 3 words of title for search
            title_words = agent.task["title"].split()[:3]
            if len(title_words) >= 2:
                search_terms.append(" ".join(title_words))

        total_commits = 0
        for term in search_terms:
            total_commits += count_commits_mentioning(term, project_path)

        # Each commit adds ~10% progress, capped at 50%
        commit_progress = min(total_commits * 10, 50) if total_commits > 0 else 0
        signals.append(("commits", float(commit_progress)))

        # Calculate weighted average
        result = weighted_average(signals) if signals else None

        # Cache result
        if result is not None:
            self._cache[cache_key] = (datetime.now(), result)

        return result

    def get_progress_breakdown(self, agent: "Agent") -> Dict[str, any]:
        """Get detailed breakdown of progress signals for debugging."""
        breakdown = {
            "agent_id": agent.id,
            "signals": {},
            "inferred": None
        }

        # Manual progress
        manual = agent.state.get("progress_pct", 0)
        breakdown["signals"]["manual"] = {
            "value": manual,
            "weight": SIGNAL_WEIGHTS["manual"],
            "cap": SIGNAL_CAPS["manual"]
        }

        # File progress
        context = agent.context or {}
        key_files = context.get("key_files", [])
        project_path = context.get("project_path")

        if key_files:
            touched = count_recently_modified(key_files, project_path)
            breakdown["signals"]["files"] = {
                "key_files_total": len(key_files),
                "files_touched": touched,
                "value": (touched / len(key_files)) * 100,
                "weight": SIGNAL_WEIGHTS["files"],
                "cap": SIGNAL_CAPS["files"]
            }

        # Commit progress
        search_term = agent.id[:8]
        commits = count_commits_mentioning(search_term, project_path)
        breakdown["signals"]["commits"] = {
            "count": commits,
            "value": min(commits * 10, 50),
            "weight": SIGNAL_WEIGHTS["commits"],
            "cap": SIGNAL_CAPS["commits"]
        }

        # Final inference
        breakdown["inferred"] = self.infer_progress(agent)

        return breakdown

    def clear_cache(self, agent_id: Optional[str] = None):
        """Clear progress cache for an agent or all agents."""
        if agent_id:
            self._cache.pop(agent_id, None)
        else:
            self._cache.clear()


# Singleton instance
_tracker: Optional[ProgressTracker] = None


def get_tracker() -> ProgressTracker:
    """Get the singleton ProgressTracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker


def infer_progress(agent: "Agent") -> Optional[int]:
    """Convenience function to infer progress for an agent."""
    return get_tracker().infer_progress(agent)


def get_progress_breakdown(agent: "Agent") -> Dict[str, any]:
    """Convenience function to get progress breakdown."""
    return get_tracker().get_progress_breakdown(agent)
