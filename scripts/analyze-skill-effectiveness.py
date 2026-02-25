#!/usr/bin/env python3
"""
Skill Effectiveness Tracker (Phase 3.3)

Cross-references skill invocations (from usage-tracker.sh stats) with
session outcome scores (from stop-session-scorer.sh via sessions.jsonl).

Low-effectiveness skills (<0.5 avg session score) are surfaced in weekly report.

Usage:
    python3 ~/.claude/scripts/analyze-skill-effectiveness.py [--days 7]
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
STATS_DIR = CLAUDE_DIR / "stats" / "usage"
SESSIONS_FILE = CLAUDE_DIR / "metrics" / "sessions.jsonl"
OBS_ARCHIVE = CLAUDE_DIR / "observations" / "archive"

DAYS = 7


def parse_args():
    global DAYS
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--days" and i + 2 <= len(sys.argv[1:]):
            DAYS = int(sys.argv[i + 2])


def load_session_scores():
    """Load session scores from metrics JSONL."""
    scores = {}
    if not SESSIONS_FILE.exists():
        return scores

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    with open(SESSIONS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("ts", "")
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= cutoff:
                    sid = entry.get("session_id", "")
                    score = entry.get("session_score")
                    if sid and score is not None:
                        scores[sid] = {
                            "score": score,
                            "ts": ts_str,
                            "tool_calls": entry.get("total_tool_calls", 0),
                        }
            except (json.JSONDecodeError, ValueError):
                continue
    return scores


def detect_skill_invocations_from_observations():
    """Scan observation archives for Skill tool invocations and group by session."""
    skill_sessions = defaultdict(list)  # skill_name -> [session_id, ...]

    if not OBS_ARCHIVE.exists():
        return skill_sessions

    cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS)
    for archive_file in sorted(OBS_ARCHIVE.glob("*.jsonl")):
        try:
            date_str = archive_file.stem.split("_")[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff - timedelta(days=1):
                continue
        except (ValueError, IndexError):
            continue

        # Extract session_id from filename (format: YYYY-MM-DD_HHMMSS-NNNNN.jsonl)
        session_proxy = archive_file.stem

        with open(archive_file) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("tool") == "Skill":
                        skill_name = entry.get("skill", "")
                        if not skill_name:
                            # Try to extract from input
                            inp = str(entry.get("input", ""))
                            m = re.search(r"skill['\"]?\s*[:=]\s*['\"]?(\w+)", inp)
                            if m:
                                skill_name = m.group(1)
                        if skill_name:
                            skill_sessions[skill_name].append(session_proxy)
                except (json.JSONDecodeError, KeyError):
                    continue

    return skill_sessions


def load_skill_counts():
    """Load skill invocation counts from usage-tracker stats."""
    skill_dir = STATS_DIR / "skill"
    counts = {}
    if not skill_dir.exists():
        return counts

    for count_file in skill_dir.glob("*.count"):
        skill_name = count_file.stem
        try:
            count = int(count_file.read_text().strip())
            counts[skill_name] = count
        except (ValueError, IOError):
            continue
    return counts


def analyze():
    """Cross-reference skill usage with session scores."""
    parse_args()

    session_scores = load_session_scores()
    skill_counts = load_skill_counts()
    skill_sessions = detect_skill_invocations_from_observations()

    results = []

    for skill, sessions in skill_sessions.items():
        # Match sessions to scores (best-effort — session_id vs archive filename)
        matched_scores = []
        for sess_proxy in sessions:
            # Try exact match or date-based matching
            for sid, sdata in session_scores.items():
                if sess_proxy[:10] in sdata.get("ts", ""):
                    matched_scores.append(sdata["score"])
                    break

        total_invocations = skill_counts.get(skill, len(sessions))
        avg_score = sum(matched_scores) / len(matched_scores) if matched_scores else None

        results.append({
            "skill": skill,
            "invocations": total_invocations,
            "sessions_matched": len(matched_scores),
            "avg_session_score": round(avg_score, 3) if avg_score is not None else None,
            "effectiveness": "low" if avg_score is not None and avg_score < 0.5 else
                            "medium" if avg_score is not None and avg_score < 0.7 else
                            "good" if avg_score is not None else "insufficient_data",
        })

    # Sort by effectiveness (low first) then by invocations
    results.sort(key=lambda x: (
        0 if x["effectiveness"] == "low" else
        1 if x["effectiveness"] == "medium" else
        2 if x["effectiveness"] == "good" else 3,
        -x["invocations"]
    ))

    return results


def main():
    results = analyze()

    if not results:
        print("No skill invocations found in observation archives.")
        print("Skills need to be used in sessions with outcome scoring enabled.")
        return

    print(f"Skill Effectiveness Analysis (last {DAYS} days)")
    print("=" * 60)
    print(f"{'Skill':<25} {'Invoc':>6} {'Matched':>8} {'Avg Score':>10} {'Status':<15}")
    print("-" * 60)

    low_count = 0
    for r in results:
        score_str = f"{r['avg_session_score']:.3f}" if r["avg_session_score"] is not None else "—"
        status = r["effectiveness"]
        if status == "low":
            low_count += 1
        print(f"{r['skill']:<25} {r['invocations']:>6} {r['sessions_matched']:>8} {score_str:>10} {status:<15}")

    if low_count:
        print(f"\n{low_count} skill(s) with low effectiveness — review in weekly report")

    return results


if __name__ == "__main__":
    main()
