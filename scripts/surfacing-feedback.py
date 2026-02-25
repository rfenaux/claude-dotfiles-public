#!/usr/bin/env python3
"""
surfacing-feedback.py - Analyze session to determine if surfaced context was used.

Called at SessionEnd (before session-compressor archives active-session.jsonl).

Algorithm:
1. Read /tmp/claude-surfacing-results.json (what was surfaced this session)
2. Read ~/.claude/observations/active-session.jsonl (what happened this session)
3. For each surfaced file: check if file path appears in session reads or commands
4. Compute use_rate per source_type
5. Update surfacing-weights.json: boost weight if use_rate > 0.6, reduce if < 0.1
6. Append outcome to surfacing.jsonl
"""

import json
import re
import sys
from datetime import datetime, timezone
from math import ceil, floor
from pathlib import Path

SIDECAR = Path("/tmp/claude-surfacing-results.json")
OBS_FILE = Path.home() / ".claude" / "observations" / "active-session.jsonl"
WEIGHTS_FILE = Path.home() / ".claude" / "config" / "surfacing-weights.json"
SURFACING_LOG = Path.home() / ".claude" / "lessons" / "surfacing.jsonl"


def load_sidecar():
    """Load the surfacing sidecar written by proactive_rag.py."""
    if not SIDECAR.exists():
        return None
    try:
        data = json.loads(SIDECAR.read_text())
        return data.get("surfaced", [])
    except Exception:
        return None


def load_observations():
    """Load active-session.jsonl."""
    if not OBS_FILE.exists():
        return []
    obs = []
    try:
        for line in OBS_FILE.read_text().strip().split("\n"):
            if line.strip():
                try:
                    obs.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return obs


def detect_usage(surfaced, observations):
    """Heuristic: was each surfaced file referenced in session activity?"""
    # Build set of all references from session
    session_refs = set()
    for obs in observations:
        for f in obs.get("files", []):
            session_refs.add(f)
            session_refs.add(Path(f).stem.lower())
        inp = str(obs.get("input", "")).lower()
        for token in re.findall(r"[\w\-]+", inp):
            if len(token) > 5:
                session_refs.add(token)

    results = {}
    for item in surfaced:
        src = item.get("source_file", "")
        stem = Path(src).stem.lower()
        title_tokens = set(re.findall(r"\w+", item.get("title", "").lower()))

        used = (
            src in session_refs
            or stem in session_refs
            or len(title_tokens & session_refs) >= 2
        )
        results[src] = {
            "used": used,
            "source_type": item.get("source_type", "unknown"),
        }
    return results


def aggregate_by_source_type(usage_results):
    """Aggregate usage stats by source_type."""
    by_type = {}
    for src, info in usage_results.items():
        st = info["source_type"]
        if st not in by_type:
            by_type[st] = {"surfaced": 0, "used": 0}
        by_type[st]["surfaced"] += 1
        if info["used"]:
            by_type[st]["used"] += 1
    return by_type


def update_weights(usage_by_source_type):
    """Adjust weights based on aggregated usage per source_type."""
    if WEIGHTS_FILE.exists():
        try:
            weights = json.loads(WEIGHTS_FILE.read_text())
        except Exception:
            weights = {}
    else:
        weights = {}

    weights.setdefault("_meta", {"total_sessions": 0, "by_source": {}})
    weights.setdefault(
        "source_weights",
        {
            "lessons": 1.0,
            "config": 1.0,
            "org-wiki": 1.0,
            "project": 1.0,
            "observations": 1.0,
        },
    )

    meta = weights["_meta"]
    meta["total_sessions"] = meta.get("total_sessions", 0) + 1

    for source_type, stats in usage_by_source_type.items():
        src_meta = meta["by_source"].setdefault(
            source_type, {"sessions": 0, "used_count": 0, "surfaced_count": 0}
        )
        src_meta["sessions"] += 1
        src_meta["surfaced_count"] += stats.get("surfaced", 0)
        src_meta["used_count"] += stats.get("used", 0)

        # Only adjust after 3+ sessions with this source type
        if src_meta["sessions"] < 3:
            continue

        use_rate = src_meta["used_count"] / max(src_meta["surfaced_count"], 1)
        current = weights["source_weights"].get(source_type, 1.0)

        if use_rate > 0.6:
            weights["source_weights"][source_type] = min(
                5.0, round(current * 1.05, 3)
            )
        elif use_rate < 0.1 and src_meta["sessions"] >= 5:
            weights["source_weights"][source_type] = max(
                0.5, round(current * 0.95, 3)
            )

    # Atomic write
    tmp = WEIGHTS_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(weights, indent=2))
    tmp.rename(WEIGHTS_FILE)


def log_feedback(usage_by_source_type):
    """Append feedback record to surfacing.jsonl."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "surfacing_feedback",
        "by_source_type": usage_by_source_type,
    }
    try:
        SURFACING_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(SURFACING_LOG, "a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass


def main():
    surfaced = load_sidecar()
    if not surfaced:
        return

    observations = load_observations()
    if not observations:
        return

    usage = detect_usage(surfaced, observations)
    by_source = aggregate_by_source_type(usage)

    update_weights(by_source)
    log_feedback(by_source)

    # Clean up sidecar
    try:
        SIDECAR.unlink(missing_ok=True)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # Fail-silent always
