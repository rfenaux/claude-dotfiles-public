#!/usr/bin/env python3
"""
Monthly Config Health Report - Comprehensive audit of the Claude Code configuration.

Sections:
  1. Agent Utilization — cross-reference agents with spawn logs
  2. Hook Performance — count hooks, estimate budget
  3. Lesson Health — confidence distribution, stale lessons
  4. Storage Audit — total size of logs, observations, metrics
  5. Config Coherence — check for conflicting settings

Output: ~/.claude/metrics/monthly-{YYYY-MM}.md

Usage:
    python3 ~/.claude/scripts/monthly-health-report.py
"""

import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
METRICS_DIR = CLAUDE_DIR / "metrics"
AGENTS_DIR = CLAUDE_DIR / "agents"
SUBAGENT_LOG = CLAUDE_DIR / "logs" / "subagent-activity.log"
LESSONS_FILE = CLAUDE_DIR / "lessons" / "lessons.jsonl"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"


def dir_size_mb(path):
    """Calculate total size of a directory in MB."""
    total = 0
    p = Path(path)
    if not p.exists():
        return 0
    for f in p.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return round(total / (1024 * 1024), 1)


def count_files(path, pattern="*"):
    p = Path(path)
    if not p.exists():
        return 0
    return sum(1 for f in p.rglob(pattern) if f.is_file())


def analyze_agent_utilization():
    """Cross-reference agent definitions with actual usage."""
    # Get all defined agents
    defined = set()
    if AGENTS_DIR.exists():
        for f in AGENTS_DIR.glob("*.md"):
            defined.add(f.stem)

    # Get spawned agent types from last 30 days
    spawned = Counter()
    if SUBAGENT_LOG.exists():
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        with open(SUBAGENT_LOG) as f:
            for line in f:
                match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
                if not match:
                    continue
                try:
                    ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    if ts < cutoff:
                        continue
                except ValueError:
                    continue
                type_m = re.search(r"type=(\S+)", line)
                if type_m:
                    spawned[type_m.group(1)] += 1

    # Find never-spawned agents
    never_spawned = defined - set(spawned.keys())
    # Find top-used agents
    top_used = spawned.most_common(10)

    return {
        "defined": len(defined),
        "spawned_unique": len(set(spawned.keys())),
        "never_spawned": sorted(never_spawned),
        "top_used": top_used,
        "utilization_pct": round(len(set(spawned.keys())) / max(len(defined), 1) * 100, 1),
    }


def analyze_hook_performance():
    """Count hooks and estimate time budget."""
    if not SETTINGS_FILE.exists():
        return None

    try:
        settings = json.loads(SETTINGS_FILE.read_text())
    except Exception:
        return None

    hooks = settings.get("hooks", {})
    event_counts = {}
    total_hooks = 0
    session_start_count = 0

    for event, entries in hooks.items():
        if not isinstance(entries, list):
            continue
        count = 0
        for entry in entries:
            hook_list = entry.get("hooks", [])
            count += len(hook_list)
            if event == "SessionStart":
                session_start_count += len(hook_list)
        event_counts[event] = count
        total_hooks += count

    return {
        "total_hooks": total_hooks,
        "events": event_counts,
        "session_start_hooks": session_start_count,
        "estimated_session_start_ms": session_start_count * 100,  # ~100ms avg per hook
    }


def analyze_lesson_health():
    """Analyze lesson confidence distribution."""
    if not LESSONS_FILE.exists():
        return None

    lessons = []
    with open(LESSONS_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                lessons.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not lessons:
        return None

    confidences = [l.get("confidence", 0.5) for l in lessons]
    high = sum(1 for c in confidences if c >= 0.8)
    medium = sum(1 for c in confidences if 0.5 <= c < 0.8)
    low = sum(1 for c in confidences if c < 0.5)

    # Find stale lessons (low confidence, old)
    stale = []
    for l in lessons:
        conf = l.get("confidence", 0.5)
        if conf < 0.5:
            stale.append({
                "title": l.get("title", "?")[:60],
                "confidence": conf,
            })

    return {
        "total": len(lessons),
        "high_confidence": high,
        "medium_confidence": medium,
        "low_confidence": low,
        "avg_confidence": round(sum(confidences) / len(confidences), 3),
        "stale_lessons": stale[:5],
    }


def analyze_storage():
    """Audit storage usage across all data directories."""
    dirs = {
        "logs": CLAUDE_DIR / "logs",
        "observations": CLAUDE_DIR / "observations",
        "metrics": METRICS_DIR,
        "lessons": CLAUDE_DIR / "lessons",
        "agents": AGENTS_DIR,
        "skills": CLAUDE_DIR / "skills",
        "ctm": CLAUDE_DIR / "ctm",
        "config": CLAUDE_DIR / "config",
    }

    results = {}
    total = 0
    for name, path in dirs.items():
        size = dir_size_mb(path)
        files = count_files(path)
        results[name] = {"size_mb": size, "files": files}
        total += size

    results["_total_mb"] = round(total, 1)

    # Cleanup suggestions
    suggestions = []
    obs_size = results.get("observations", {}).get("size_mb", 0)
    if obs_size > 50:
        suggestions.append(f"Observations: {obs_size}MB — consider reducing retention_days")
    log_size = results.get("logs", {}).get("size_mb", 0)
    if log_size > 20:
        suggestions.append(f"Logs: {log_size}MB — consider archiving old log files")

    return results, suggestions


def check_config_coherence():
    """Check for conflicting or inconsistent settings."""
    issues = []

    configs = {
        "self-healing": CLAUDE_DIR / "config" / "self-healing.json",
        "self-improvement": CLAUDE_DIR / "config" / "self-improvement.json",
        "pruning": CLAUDE_DIR / "config" / "pruning.json",
        "observation-config": CLAUDE_DIR / "config" / "observation-config.json",
    }

    loaded = {}
    for name, path in configs.items():
        if path.exists():
            try:
                loaded[name] = json.loads(path.read_text())
            except Exception:
                issues.append(f"{name}: JSON parse error")

    # Check: observation captures skip_tools shouldn't include tools in capture_tools
    obs = loaded.get("observation-config", {})
    capture = set(obs.get("capture_tools", []))
    skip = set(obs.get("skip_tools", []))
    overlap = capture & skip
    if overlap:
        issues.append(f"observation-config: tools in both capture and skip: {overlap}")

    # Check: pruning never_prune_tools should be in observation capture_tools
    prun = loaded.get("pruning", {})
    never_prune = set(prun.get("never_prune_tools", []))
    if capture and never_prune:
        not_captured = never_prune - capture
        if not_captured:
            issues.append(f"pruning.never_prune_tools lists {not_captured} but not in observation capture_tools")

    # Check: self-improvement enabled but self-healing disabled
    si = loaded.get("self-improvement", {})
    sh = loaded.get("self-healing", {})
    if si.get("enabled") and not sh.get("enabled", True):
        issues.append("self-improvement enabled but self-healing disabled — improvement depends on healing data")

    if not issues:
        issues.append("No coherence issues found")

    return issues


def main():
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    month = datetime.now().strftime("%Y-%m")
    output_path = METRICS_DIR / f"monthly-{month}.md"

    print(f"Generating monthly health report for {month}...")

    agents = analyze_agent_utilization()
    hooks = analyze_hook_performance()
    lessons = analyze_lesson_health()
    storage, storage_suggestions = analyze_storage()
    coherence = check_config_coherence()

    lines = [
        f"# Monthly Config Health Report — {month}",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]

    # Agent Utilization
    lines.append("## Agent Utilization")
    lines.append("")
    lines.append(f"- Defined agents: {agents['defined']}")
    lines.append(f"- Used (30d): {agents['spawned_unique']}")
    lines.append(f"- Utilization: **{agents['utilization_pct']}%**")
    lines.append("")
    if agents["top_used"]:
        lines.append("**Top used:**")
        lines.append("")
        for atype, count in agents["top_used"][:5]:
            lines.append(f"- {atype}: {count}x")
        lines.append("")
    if agents["never_spawned"]:
        never_list = agents["never_spawned"]
        lines.append(f"**Never spawned** ({len(never_list)} agents):")
        lines.append("")
        # Show first 10
        for a in never_list[:10]:
            lines.append(f"- {a}")
        if len(never_list) > 10:
            lines.append(f"- ...and {len(never_list) - 10} more")
        lines.append("")

    # Hook Performance
    if hooks:
        lines.append("## Hook Performance")
        lines.append("")
        lines.append(f"- Total hooks: {hooks['total_hooks']}")
        lines.append(f"- SessionStart hooks: {hooks['session_start_hooks']}")
        lines.append(f"- Est. SessionStart budget: ~{hooks['estimated_session_start_ms']}ms")
        lines.append("")
        if hooks["events"]:
            lines.append("| Event | Hook Count |")
            lines.append("|-------|------------|")
            for event, count in sorted(hooks["events"].items(), key=lambda x: -x[1]):
                lines.append(f"| {event} | {count} |")
            lines.append("")

    # Lesson Health
    if lessons:
        lines.append("## Lesson Health")
        lines.append("")
        lines.append(f"- Total lessons: {lessons['total']}")
        lines.append(f"- Average confidence: {lessons['avg_confidence']}")
        lines.append(f"- High (>=0.8): {lessons['high_confidence']}")
        lines.append(f"- Medium (0.5-0.8): {lessons['medium_confidence']}")
        lines.append(f"- Low (<0.5): {lessons['low_confidence']}")
        lines.append("")
        if lessons["stale_lessons"]:
            lines.append("**Stale lessons** (confidence <0.5):")
            lines.append("")
            for sl in lessons["stale_lessons"]:
                lines.append(f"- {sl['title']} ({sl['confidence']:.2f})")
            lines.append("")

    # Storage Audit
    lines.append("## Storage Audit")
    lines.append("")
    lines.append(f"**Total: {storage['_total_mb']}MB**")
    lines.append("")
    lines.append("| Directory | Size (MB) | Files |")
    lines.append("|-----------|-----------|-------|")
    for name, info in sorted(storage.items()):
        if name.startswith("_"):
            continue
        lines.append(f"| {name} | {info['size_mb']} | {info['files']} |")
    lines.append("")
    if storage_suggestions:
        lines.append("**Suggestions:**")
        lines.append("")
        for s in storage_suggestions:
            lines.append(f"- {s}")
        lines.append("")

    # Config Coherence
    lines.append("## Config Coherence")
    lines.append("")
    for issue in coherence:
        lines.append(f"- {issue}")
    lines.append("")

    # Write report
    report = "\n".join(lines)
    output_path.write_text(report)
    print(f"Report written to: {output_path}")


if __name__ == "__main__":
    main()
