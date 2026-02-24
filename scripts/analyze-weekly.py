#!/usr/bin/env python3
"""
Weekly Analysis Digest - Turns captured data into actionable insights.

Reads ALL data sources:
  - observations/archive/*.jsonl — raw tool usage
  - observations/summaries/*.md — compressed summaries
  - logs/subagent-activity.log — agent spawns
  - logs/failure-catalog.jsonl — failures
  - logs/self-healing/services.jsonl — healing events
  - metrics/sessions.jsonl — session metrics

Output: ~/.claude/metrics/weekly-{YYYY-MM-DD}.md

Usage:
    python3 ~/.claude/scripts/analyze-weekly.py [--days 7]
"""

import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
METRICS_DIR = CLAUDE_DIR / "metrics"
OBS_ARCHIVE = CLAUDE_DIR / "observations" / "archive"
OBS_SUMMARIES = CLAUDE_DIR / "observations" / "summaries"
SUBAGENT_LOG = CLAUDE_DIR / "logs" / "subagent-activity.log"
FAILURE_CATALOG = CLAUDE_DIR / "logs" / "failure-catalog.jsonl"
PATTERN_LOG = CLAUDE_DIR / "logs" / "pattern-tracker.log"
HEALING_LOG = CLAUDE_DIR / "logs" / "self-healing" / "services.jsonl"
REINDEX_LOG = CLAUDE_DIR / "logs" / "self-healing" / "reindex.jsonl"
DECISION_LOG = CLAUDE_DIR / "logs" / "self-healing" / "decision-sync.jsonl"
SESSIONS_FILE = METRICS_DIR / "sessions.jsonl"

DAYS = 7


def parse_args():
    global DAYS
    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--days" and i + 2 <= len(sys.argv[1:]):
            DAYS = int(sys.argv[i + 2])


def cutoff_ts():
    return datetime.now(timezone.utc) - timedelta(days=DAYS)


def load_jsonl(path, date_field="ts"):
    """Load JSONL file, filtering to entries within DAYS window."""
    entries = []
    if not path.exists():
        return entries
    cutoff = cutoff_ts()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
                ts_str = d.get(date_field, "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts >= cutoff:
                            entries.append(d)
                    except (ValueError, TypeError):
                        entries.append(d)  # Include if can't parse date
                else:
                    entries.append(d)
            except json.JSONDecodeError:
                continue
    return entries


def analyze_observations():
    """Analyze raw observation archives for tool usage."""
    tool_counts = Counter()
    file_counts = Counter()
    session_count = 0
    total_entries = 0
    search_total = 0
    search_hits = 0

    if not OBS_ARCHIVE.exists():
        return tool_counts, file_counts, session_count, total_entries, search_total, search_hits

    cutoff = cutoff_ts()
    for archive_file in sorted(OBS_ARCHIVE.glob("*.jsonl")):
        # Check file date from name (format: YYYY-MM-DD_HHMMSS-NNNNN.jsonl)
        try:
            date_str = archive_file.stem.split("_")[0]
            file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff - timedelta(days=1):
                continue
        except (ValueError, IndexError):
            continue

        session_count += 1
        with open(archive_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    total_entries += 1
                    tool = entry.get("tool", "unknown")
                    tool_counts[tool] += 1

                    # Track file access
                    files = entry.get("files", [])
                    if isinstance(files, list):
                        for fp in files:
                            if fp:
                                file_counts[fp] += 1

                    # Search effectiveness
                    if tool in ("Grep", "Glob"):
                        search_total += 1
                        output = str(entry.get("output", ""))
                        if output and len(output) > 20:
                            search_hits += 1
                except json.JSONDecodeError:
                    continue

    return tool_counts, file_counts, session_count, total_entries, search_total, search_hits


def analyze_subagents():
    """Analyze subagent spawn patterns."""
    type_counts = Counter()
    if not SUBAGENT_LOG.exists():
        return type_counts

    cutoff = cutoff_ts()
    with open(SUBAGENT_LOG) as f:
        for line in f:
            # Format: [2026-02-13 22:16:04] Subagent spawned: type=Explore id=abc123
            # Or new format: [2026-02-13 22:16:04] event=SubagentStart type=Explore ...
            match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
            if not match:
                continue
            try:
                ts = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                if ts < cutoff:
                    continue
            except ValueError:
                continue

            type_match = re.search(r"type=(\S+)", line)
            if type_match:
                type_counts[type_match.group(1)] += 1

    return type_counts


def analyze_failures():
    """Analyze failure catalog for repeat patterns."""
    entries = load_jsonl(FAILURE_CATALOG, "timestamp")
    sig_groups = defaultdict(list)
    for e in entries:
        sig = e.get("error_signature", "unknown")
        sig_groups[sig].append(e)

    # Sort by count descending
    sorted_sigs = sorted(sig_groups.items(), key=lambda x: len(x[1]), reverse=True)
    return sorted_sigs


def analyze_healing():
    """Analyze self-healing activity."""
    service_events = load_jsonl(HEALING_LOG)
    reindex_events = load_jsonl(REINDEX_LOG)
    decision_events = load_jsonl(DECISION_LOG)

    service_restarts = Counter()
    for e in service_events:
        if e.get("result") == "success":
            service_restarts[e.get("service", "unknown")] += 1

    reindex_count = sum(1 for e in reindex_events if e.get("result") == "completed")
    decision_count = sum(1 for e in decision_events if "total_updated" in e)

    return service_restarts, reindex_count, decision_count


def analyze_sessions():
    """Analyze session metrics if available."""
    entries = load_jsonl(SESSIONS_FILE)
    if not entries:
        return None

    avg_tools = sum(e.get("total_tool_calls", 0) for e in entries) / len(entries)
    avg_duration = [e.get("duration_min") for e in entries if e.get("duration_min")]
    avg_dur = sum(avg_duration) / len(avg_duration) if avg_duration else None
    avg_spawns = sum(e.get("agent_spawns", 0) for e in entries) / len(entries)

    hit_rates = [e.get("search_hit_rate") for e in entries if e.get("search_hit_rate") is not None]
    avg_hit = sum(hit_rates) / len(hit_rates) if hit_rates else None

    return {
        "count": len(entries),
        "avg_tool_calls": round(avg_tools, 1),
        "avg_duration_min": round(avg_dur, 1) if avg_dur else None,
        "avg_agent_spawns": round(avg_spawns, 1),
        "avg_search_hit_rate": round(avg_hit, 2) if avg_hit else None,
    }


def load_previous_report():
    """Load key metrics from the most recent previous weekly report for delta calculation."""
    prev = {}
    reports = sorted(METRICS_DIR.glob("weekly-*.md"), reverse=True)
    # Skip the current day's report if it exists (we're regenerating)
    today = datetime.now().strftime("%Y-%m-%d")
    for rpath in reports:
        if today in rpath.name:
            continue
        try:
            content = rpath.read_text()
            m = re.search(r"Total tool calls: (\d+)", content)
            if m:
                prev["total_tool_calls"] = int(m.group(1))
            m = re.search(r"Sessions analyzed: (\d+)", content)
            if m:
                prev["sessions"] = int(m.group(1))
            # Extract total agent spawns
            m = re.search(r"Total spawns: (\d+)", content)
            if m:
                prev["total_spawns"] = int(m.group(1))
            # Extract unknown agent count
            m = re.search(r"unknown.*?\|\s*(\d+)\s*\|", content)
            if m:
                prev["unknown_agents"] = int(m.group(1))
            # Extract total failures
            failure_total = 0
            for fm in re.finditer(r"\|\s*`\w+\.{3}`\s*\|\s*(\d+)\s*\|", content):
                failure_total += int(fm.group(1))
            if failure_total:
                prev["total_failures"] = failure_total
            prev["date"] = rpath.stem.replace("weekly-", "")
            break  # Only use most recent
        except Exception:
            continue
    return prev


def delta_str(current, previous, label=""):
    """Format a delta string like '+12%' or '-5%'."""
    if previous is None or previous == 0:
        return ""
    pct = (current - previous) / previous * 100
    if abs(pct) < 1:
        return " (unchanged)"
    arrow = "+" if pct > 0 else ""
    return f" ({arrow}{pct:.0f}% vs prev)"


# ─── Batch 2B: Tool Effectiveness (2B.1) ───────────────────────────────────────

def analyze_tool_effectiveness(tool_counts, failures):
    """Cross-reference tool usage with failures for effectiveness scoring."""
    failure_by_tool = Counter()
    for sig, entries in failures:
        for e in entries:
            tool = e.get("tool", "unknown")
            failure_by_tool[tool] += 1

    total_calls = sum(tool_counts.values()) or 1
    results = []
    for tool, count in tool_counts.most_common(20):
        fails = failure_by_tool.get(tool, 0)
        success_rate = 1.0 - (fails / count) if count > 0 else None
        score = round(success_rate * math.log2(max(count, 2)), 1) if success_rate is not None else None
        status = "OK"
        if success_rate is not None and success_rate < 0.8:
            status = "needs attention"
        elif count / total_calls < 0.01:
            status = "low usage"
        results.append({
            "tool": tool, "calls": count, "failures": fails,
            "success_rate": success_rate, "score": score, "status": status,
        })

    # Flag tools that appear only in failures (never in normal observations)
    for tool, fails in failure_by_tool.items():
        if tool not in tool_counts:
            results.append({
                "tool": tool, "calls": 0, "failures": fails,
                "success_rate": None, "score": None, "status": "failures only",
            })

    return results


# ─── Batch 2B: Config Suggestions (2B.2) ───────────────────────────────────────

def generate_config_suggestions(tool_counts, session_metrics, total_entries):
    """Generate config tuning suggestions based on usage patterns."""
    suggestions = []

    # Load self-improvement config for thresholds
    si_path = CLAUDE_DIR / "config" / "self-improvement.json"
    si_config = {}
    if si_path.exists():
        try:
            si_config = json.loads(si_path.read_text())
        except Exception:
            pass

    min_sessions = si_config.get("tool_effectiveness", {}).get("min_sessions", 10)
    session_count = session_metrics["count"] if session_metrics else 0

    if session_count < min_sessions:
        suggestions.append({
            "param": "general",
            "current": f"{session_count} sessions",
            "suggested": f">={min_sessions} needed",
            "reason": f"Collecting data ({session_count}/{min_sessions} sessions)",
        })
        return suggestions

    avg_duration = session_metrics.get("avg_duration_min") if session_metrics else None

    # Check pruning TTLs vs actual session duration
    pruning_path = CLAUDE_DIR / "config" / "pruning.json"
    if pruning_path.exists() and avg_duration:
        try:
            pruning = json.loads(pruning_path.read_text())
            for tool, rule in pruning.get("tool_rules", {}).items():
                ttl = rule.get("ttl_minutes", 60)
                if ttl > avg_duration * 2:
                    suggestions.append({
                        "param": f"pruning.tool_rules.{tool}.ttl_minutes",
                        "current": ttl,
                        "suggested": int(avg_duration * 1.5),
                        "reason": f"TTL ({ttl}m) >> avg session ({avg_duration:.0f}m)",
                    })
        except Exception:
            pass

    # Check observation config vs actual usage
    obs_path = CLAUDE_DIR / "config" / "observation-config.json"
    if obs_path.exists() and session_metrics:
        try:
            obs_config = json.loads(obs_path.read_text())
            max_entries = obs_config.get("max_entries_per_session", 200)
            avg_calls = session_metrics.get("avg_tool_calls", 0)
            if avg_calls > max_entries * 0.8:
                suggestions.append({
                    "param": "observation-config.max_entries_per_session",
                    "current": max_entries,
                    "suggested": int(avg_calls * 1.5),
                    "reason": f"Avg calls ({avg_calls:.0f}) near limit ({max_entries})",
                })
        except Exception:
            pass

    # Check self-healing rate limits vs actual restart frequency
    sh_path = CLAUDE_DIR / "config" / "self-healing.json"
    if sh_path.exists():
        try:
            sh_config = json.loads(sh_path.read_text())
            service_events = load_jsonl(HEALING_LOG)
            restart_count = sum(1 for e in service_events if e.get("result") == "success")
            if restart_count > 3:
                for svc, svc_cfg in sh_config.get("services", {}).items():
                    rate = svc_cfg.get("rate_limit_min", 60)
                    if rate > 30:
                        suggestions.append({
                            "param": f"self-healing.services.{svc}.rate_limit_min",
                            "current": rate,
                            "suggested": max(30, rate - 15),
                            "reason": f"High restart frequency ({restart_count}x/week)",
                        })
        except Exception:
            pass

    return suggestions


# ─── Batch 2B: Agent Routing Analysis (2B.3) ───────────────────────────────────

def analyze_agent_routing_detailed():
    """Detailed agent routing: co-occurrence and model distribution."""
    if not SUBAGENT_LOG.exists():
        return None

    cutoff = cutoff_ts()
    entries = []

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
            model_m = re.search(r"model=(\S+)", line)

            entries.append({
                "ts": ts,
                "type": type_m.group(1) if type_m else "unknown",
                "model": model_m.group(1) if model_m else "",
            })

    if not entries:
        return None

    # Co-occurrence: group spawns within 10-min windows (proxy for same session)
    windows = defaultdict(set)
    for e in entries:
        # Round to 10-min window
        window_key = e["ts"].strftime("%Y-%m-%d %H:") + str(e["ts"].minute // 10)
        windows[window_key].add(e["type"])

    co_occurrence = Counter()
    for types in windows.values():
        types_list = sorted(t for t in types if t != "unknown")
        for i, t1 in enumerate(types_list):
            for t2 in types_list[i + 1:]:
                co_occurrence[(t1, t2)] += 1

    # Model distribution per agent type
    type_models = defaultdict(Counter)
    for e in entries:
        if e["model"]:
            type_models[e["type"]][e["model"]] += 1

    return {
        "co_occurrence": co_occurrence.most_common(5),
        "type_models": dict(type_models),
        "total_entries": len(entries),
    }


# ─── Phase 3: Failure Trend Detection (3.1) ────────────────────────────────────

def detect_failure_trends(failures):
    """Detect accelerating or resolved failure patterns by comparing this week vs previous week."""
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    trends = []
    for sig, entries in failures:
        this_week = 0
        prev_week = 0
        for e in entries:
            ts_str = e.get("timestamp", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= week_ago:
                    this_week += 1
                elif ts >= two_weeks_ago:
                    prev_week += 1
            except (ValueError, TypeError):
                this_week += 1  # Count as current if can't parse

        trend = "stable"
        if prev_week > 0 and this_week > prev_week * 1.5:
            trend = "trending_up"
        elif prev_week >= 5 and this_week == 0:
            trend = "resolved"
        elif this_week == 0 and prev_week == 0:
            trend = "inactive"

        tool = entries[0].get("tool", "?") if entries else "?"
        trends.append({
            "signature": sig,
            "tool": tool,
            "this_week": this_week,
            "prev_week": prev_week,
            "trend": trend,
            "total": len(entries),
        })

    # Only return active trends (not inactive old signatures)
    return [t for t in trends if t["trend"] != "inactive"]


# ─── Phase 3: Session Anomaly Detection (3.2) ──────────────────────────────────

def detect_session_anomalies():
    """Detect statistical outliers in session metrics."""
    entries = load_jsonl(SESSIONS_FILE)
    if not entries or len(entries) < 3:
        return None, len(entries) if entries else 0

    anomalies = []

    for metric_key, label in [
        ("total_tool_calls", "tool storm"),
        ("duration_min", "marathon session"),
        ("agent_spawns", "agent heavy"),
    ]:
        values = [e.get(metric_key) for e in entries if e.get(metric_key) is not None]
        if len(values) < 3:
            continue

        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        stddev = math.sqrt(variance) if variance > 0 else 0

        if stddev == 0:
            continue

        threshold = mean + 2 * stddev
        for e in entries:
            val = e.get(metric_key)
            if val is not None and val > threshold:
                anomalies.append({
                    "session": e.get("session_id", "?")[:12],
                    "metric": metric_key,
                    "value": val,
                    "mean": round(mean, 1),
                    "threshold": round(threshold, 1),
                    "classification": label,
                    "date": e.get("date", "?"),
                })

    return anomalies, len(entries)


# ─── Recommendations ────────────────────────────────────────────────────────────

def generate_recommendations(tool_counts, search_total, search_hits, agent_types, failures):
    """Generate top 3 actionable recommendations."""
    recs = []

    # Search effectiveness
    if search_total > 10:
        hit_rate = search_hits / search_total
        if hit_rate < 0.5:
            recs.append(
                f"Search hit rate is {hit_rate:.0%} ({search_hits}/{search_total}). "
                "Consider adding domain-specific patterns to SEARCH_PATTERNS_INDEX.md"
            )

    # Unknown agent types
    unknown_count = agent_types.get("unknown", 0)
    total_agents = sum(agent_types.values())
    if total_agents > 0 and unknown_count / total_agents > 0.2:
        recs.append(
            f"{unknown_count}/{total_agents} agent spawns logged as 'unknown' ({unknown_count/total_agents:.0%}). "
            "Subagent logger needs field name fix."
        )

    # Repeat failures
    for sig, entries in failures[:3]:
        if len(entries) >= 10:
            tool = entries[0].get("tool", "unknown")
            error_preview = str(entries[0].get("error", ""))[:80]
            recs.append(
                f"Failure signature repeats {len(entries)}x for {tool}: \"{error_preview}...\" "
                "Consider adding a specific lesson or workaround."
            )

    return recs[:3]


# ─── Main Report Generator ─────────────────────────────────────────────────────

def main():
    parse_args()
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = METRICS_DIR / f"weekly-{today}.md"

    print(f"Analyzing last {DAYS} days...")

    # Gather all data
    tool_counts, file_counts, session_count, total_entries, search_total, search_hits = analyze_observations()
    agent_types = analyze_subagents()
    failures = analyze_failures()
    service_restarts, reindex_count, decision_count = analyze_healing()
    session_metrics = analyze_sessions()

    # New analyses (Batch 2B + Phase 3)
    tool_eff = analyze_tool_effectiveness(tool_counts, failures)
    config_suggestions = generate_config_suggestions(tool_counts, session_metrics, total_entries)
    agent_detail = analyze_agent_routing_detailed()
    failure_trends = detect_failure_trends(failures)
    anomalies, anomaly_session_count = detect_session_anomalies()

    # Load previous report for deltas
    prev = load_previous_report()

    # Build report
    header_delta = ""
    if prev:
        parts = []
        if "total_tool_calls" in prev:
            parts.append(f"tool calls {delta_str(total_entries, prev['total_tool_calls'])}")
        if "sessions" in prev:
            parts.append(f"sessions {delta_str(session_count, prev['sessions'])}")
        if parts:
            header_delta = f" | vs {prev.get('date', '?')}: {', '.join(parts)}"

    lines = [
        f"# Weekly Analysis Digest — {today}",
        f"",
        f"Period: last {DAYS} days | Sessions analyzed: {session_count} | "
        f"Total tool calls: {total_entries}{header_delta}",
        "",
    ]

    # Tool trends
    lines.append("## Tool Usage")
    lines.append("")
    lines.append("| Tool | Count | % |")
    lines.append("|------|-------|---|")
    for tool, count in tool_counts.most_common(15):
        pct = count / total_entries * 100 if total_entries > 0 else 0
        lines.append(f"| {tool} | {count} | {pct:.1f}% |")
    lines.append("")

    # Search effectiveness
    if search_total > 0:
        hit_rate = search_hits / search_total
        lines.append("## Search Effectiveness")
        lines.append("")
        lines.append(f"- Grep/Glob total: {search_total}")
        lines.append(f"- Hits (non-empty results): {search_hits}")
        lines.append(f"- Hit rate: **{hit_rate:.0%}**")
        lines.append("")

    # Agent routing
    if agent_types:
        total_spawns = sum(agent_types.values())
        spawns_delta = delta_str(total_spawns, prev.get("total_spawns"))
        lines.append("## Agent Routing")
        lines.append("")
        lines.append(f"Total spawns: {total_spawns}{spawns_delta}")
        lines.append("")
        lines.append("| Agent Type | Count | % |")
        lines.append("|------------|-------|---|")
        for atype, count in agent_types.most_common(10):
            pct = count / total_spawns * 100
            marker = " **FIX**" if atype == "unknown" else ""
            # Show delta for unknown specifically
            unknown_delta = ""
            if atype == "unknown" and "unknown_agents" in prev:
                unknown_delta = delta_str(count, prev["unknown_agents"])
            lines.append(f"| {atype}{marker} | {count} | {pct:.1f}%{unknown_delta} |")
        lines.append("")

    # Repeat failures
    if failures:
        lines.append("## Repeat Failures")
        lines.append("")
        lines.append("| Signature | Count | Tool | Error Preview |")
        lines.append("|-----------|-------|------|---------------|")
        for sig, entries in failures[:5]:
            tool = entries[0].get("tool", "?")
            error = str(entries[0].get("error", ""))[:60].replace("|", "\\|")
            lines.append(f"| `{sig[:8]}...` | {len(entries)} | {tool} | {error} |")
        lines.append("")

    # Hot files
    if file_counts:
        lines.append("## Hot Files (most accessed)")
        lines.append("")
        for fp, count in file_counts.most_common(10):
            # Shorten path
            short = fp.replace(str(Path.home()), "~")
            lines.append(f"- `{short}` ({count}x)")
        lines.append("")

    # Self-healing activity
    lines.append("## Self-Healing Activity")
    lines.append("")
    if any([service_restarts, reindex_count, decision_count]):
        if service_restarts:
            for svc, count in service_restarts.items():
                lines.append(f"- {svc} restarted: {count}x")
        if reindex_count:
            lines.append(f"- RAG auto-reindexed: {reindex_count}x")
        if decision_count:
            lines.append(f"- Decisions auto-synced: {decision_count}x")
    else:
        lines.append("No healing events in this period.")
    lines.append("")

    # Session metrics (if available)
    if session_metrics:
        lines.append("## Session Metrics")
        lines.append("")
        lines.append(f"- Sessions with metrics: {session_metrics['count']}")
        lines.append(f"- Avg tool calls/session: {session_metrics['avg_tool_calls']}")
        if session_metrics["avg_duration_min"]:
            lines.append(f"- Avg duration: {session_metrics['avg_duration_min']} min")
        lines.append(f"- Avg agent spawns/session: {session_metrics['avg_agent_spawns']}")
        if session_metrics["avg_search_hit_rate"] is not None:
            lines.append(f"- Avg search hit rate: {session_metrics['avg_search_hit_rate']:.0%}")
        lines.append("")

    # ─── NEW: Tool Effectiveness (2B.1) ─────────────────────────────────────
    if tool_eff:
        lines.append("## Tool Effectiveness")
        lines.append("")

        # Check if we have enough data
        si_path = CLAUDE_DIR / "config" / "self-improvement.json"
        min_sessions = 10
        if si_path.exists():
            try:
                min_sessions = json.loads(si_path.read_text()).get("tool_effectiveness", {}).get("min_sessions", 10)
            except Exception:
                pass

        sess_count = session_metrics["count"] if session_metrics else 0
        if sess_count < min_sessions:
            lines.append(f"_Collecting data ({sess_count}/{min_sessions} sessions)_")
            lines.append("")
        else:
            lines.append("| Tool | Calls | Failures | Success% | Score | Status |")
            lines.append("|------|-------|----------|----------|-------|--------|")

        # Always show the table (useful even with limited data)
        attention_tools = []
        for t in tool_eff:
            sr = f"{t['success_rate']:.1%}" if t["success_rate"] is not None else "—"
            sc = str(t["score"]) if t["score"] is not None else "—"
            flag = ""
            if t["status"] == "needs attention":
                flag = " ⚠"
                attention_tools.append(t["tool"])
            elif t["status"] == "failures only":
                flag = " ⚠"
                attention_tools.append(t["tool"])
            lines.append(f"| {t['tool']}{flag} | {t['calls']} | {t['failures']} | {sr} | {sc} | {t['status']} |")
        lines.append("")

        if attention_tools:
            lines.append(f"**Attention needed:** {', '.join(attention_tools)}")
            lines.append("")

    # ─── NEW: Agent Routing Analysis (2B.3) ─────────────────────────────────
    if agent_detail:
        lines.append("## Agent Routing Analysis")
        lines.append("")

        # Co-occurrence
        if agent_detail["co_occurrence"]:
            lines.append("**Co-occurrence** (agents commonly paired):")
            lines.append("")
            for (t1, t2), count in agent_detail["co_occurrence"]:
                lines.append(f"- {t1} + {t2}: {count} sessions")
            lines.append("")

        # Model distribution
        if agent_detail["type_models"]:
            lines.append("**Model distribution:**")
            lines.append("")
            lines.append("| Agent Type | Models |")
            lines.append("|------------|--------|")
            for atype, models in sorted(agent_detail["type_models"].items()):
                if atype == "unknown":
                    continue
                model_str = ", ".join(f"{m}({c})" for m, c in models.most_common(3))
                lines.append(f"| {atype} | {model_str} |")
            lines.append("")

    # ─── NEW: Config Suggestions (2B.2) ─────────────────────────────────────
    if config_suggestions:
        lines.append("## Config Suggestions")
        lines.append("")
        if len(config_suggestions) == 1 and config_suggestions[0]["param"] == "general":
            lines.append(f"_{config_suggestions[0]['reason']}_")
        else:
            lines.append("| Parameter | Current | Suggested | Reason |")
            lines.append("|-----------|---------|-----------|--------|")
            for s in config_suggestions:
                lines.append(f"| `{s['param']}` | {s['current']} | {s['suggested']} | {s['reason']} |")
            lines.append("")
            lines.append("_Apply: `python3 ~/.claude/scripts/auto-tune-config.py --dry-run`_")
        lines.append("")

    # ─── NEW: Failure Trends (3.1) ──────────────────────────────────────────
    active_trends = [t for t in failure_trends if t["trend"] in ("trending_up", "resolved")]
    if active_trends:
        lines.append("## Failure Trends")
        lines.append("")
        lines.append("| Signature | Tool | This Week | Prev Week | Trend |")
        lines.append("|-----------|------|-----------|-----------|-------|")
        for t in active_trends:
            icon = "↑ TRENDING" if t["trend"] == "trending_up" else "✓ RESOLVED"
            lines.append(f"| `{t['signature'][:8]}...` | {t['tool']} | {t['this_week']} | {t['prev_week']} | {icon} |")
        lines.append("")

    # ─── NEW: Anomalies (3.2) ───────────────────────────────────────────────
    if anomalies is None:
        if anomaly_session_count < 3:
            lines.append("## Anomalies")
            lines.append("")
            lines.append(f"_Building baseline ({anomaly_session_count}/3 sessions)_")
            lines.append("")
    elif anomalies:
        lines.append("## Anomalies")
        lines.append("")
        lines.append("| Session | Type | Value | Mean | Threshold |")
        lines.append("|---------|------|-------|------|-----------|")
        for a in anomalies:
            lines.append(
                f"| {a['session']} | {a['classification']} | "
                f"{a['value']:.0f} | {a['mean']:.0f} | >{a['threshold']:.0f} |"
            )
        lines.append("")

    # Recommendations
    recs = generate_recommendations(tool_counts, search_total, search_hits, agent_types, failures)
    if recs:
        lines.append("## Recommendations")
        lines.append("")
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

    # Write report
    report = "\n".join(lines)
    output_path.write_text(report)
    print(f"Report written to: {output_path}")
    print(f"\nSummary: {session_count} sessions, {total_entries} tool calls, "
          f"{sum(agent_types.values())} agent spawns, "
          f"{sum(len(e) for _, e in failures)} failures")

    if recs:
        print(f"\nTop recommendations:")
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec}")


if __name__ == "__main__":
    main()
