#!/usr/bin/env python3
"""
counter-pattern-detector.py - Detect session behavior that contradicts stored preferences.

Called at SessionEnd (before session-compressor archives active-session.jsonl).

Algorithm:
1. Load rules from ~/.claude/config/preference-rules.json
2. Load active-session.jsonl (current session observations)
3. For each rule: check violation_signals against observations
4. Write violations to /tmp/claude-counter-patterns.json (surfaced next session)
5. Append to persistent counter-pattern-history.jsonl (dedup within 48h)
"""

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

RULES_FILE = Path.home() / ".claude" / "config" / "preference-rules.json"
OBS_FILE = Path.home() / ".claude" / "observations" / "active-session.jsonl"
OUTPUT_FILE = Path("/tmp/claude-counter-patterns.json")
HISTORY_FILE = Path.home() / ".claude" / "config" / "counter-pattern-history.jsonl"

DEDUP_HOURS = 48


def load_rules():
    """Load preference rules from config."""
    if not RULES_FILE.exists():
        return []
    try:
        with open(RULES_FILE) as f:
            data = json.load(f)
        return data.get("rules", [])
    except Exception:
        return []


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


def load_recent_history():
    """Load violation IDs surfaced within DEDUP_HOURS."""
    if not HISTORY_FILE.exists():
        return set()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=DEDUP_HOURS)
    recent_ids = set()
    try:
        for line in HISTORY_FILE.read_text().strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                ts_str = entry.get("matched_at", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts > cutoff:
                        recent_ids.add(entry.get("rule_id", ""))
            except Exception:
                pass
    except Exception:
        pass
    return recent_ids


def check_signal(signal, observations):
    """Check a single signal against observations. Returns list of matching obs."""
    signal_type = signal.get("type", "")
    pattern = signal.get("pattern", "")
    matched = []

    for obs in observations:
        inp = str(obs.get("input", ""))
        out = str(obs.get("output", ""))
        tool = obs.get("tool", "")
        files = obs.get("files", [])
        project = obs.get("project", "")

        if signal_type == "command_contains":
            if tool == "Bash" and re.search(pattern, inp, re.I):
                matched.append(obs)

        elif signal_type == "file_read_matches":
            if tool == "Read":
                for f in files:
                    if re.search(pattern, f, re.I):
                        matched.append(obs)
                        break

        elif signal_type == "tool_repeated_failure":
            tool_pattern = signal.get("tool_pattern", pattern)
            min_repeats = signal.get("min_repeats", 2)
            if re.search(tool_pattern, tool, re.I):
                if "error" in out.lower() or "fail" in out.lower():
                    matched.append(obs)
            # Check if we hit min_repeats threshold
            if len(matched) < min_repeats:
                matched = []

        elif signal_type == "project_is":
            if re.search(pattern, project, re.I):
                matched.append(obs)

    return matched


def check_rule(rule, observations):
    """Return a violation dict if the rule is violated, else None."""
    signals = rule.get("violation_signals", [])
    context_filter = rule.get("context_filter", {})
    logic = rule.get("logic", "OR")  # OR = any signal matches, AND = all must match

    all_matched = []
    signals_matched = 0

    for signal in signals:
        matched = check_signal(signal, observations)
        if matched:
            all_matched.extend(matched)
            signals_matched += 1

    # Logic check
    if logic == "AND" and signals_matched < len(signals):
        return None
    if logic == "OR" and signals_matched == 0:
        return None
    if not all_matched:
        return None

    # Context filter: additional pattern must also be present in session
    if context_filter:
        must_also = context_filter.get("must_also_contain", "")
        if must_also:
            all_text = " ".join(
                str(o.get("input", "")) + " " + str(o.get("output", ""))
                for o in observations
            )
            if not re.search(must_also, all_text, re.I):
                return None

    return {
        "rule_id": rule["id"],
        "description": rule["description"],
        "severity": rule.get("severity", "low"),
        "source": rule.get("source", ""),
        "matched_at": datetime.now(timezone.utc).isoformat(),
        "example_input": str(all_matched[0].get("input", ""))[:100],
    }


def run_detection(verbose=False):
    """Run all rules against current session. Return list of violations."""
    rules = load_rules()
    if not rules:
        return []

    observations = load_observations()
    if not observations:
        return []

    recent_ids = load_recent_history()
    violations = []

    for rule in rules:
        if not rule.get("enabled", True):
            continue

        # Dedup: skip if recently surfaced
        if rule["id"] in recent_ids:
            if verbose:
                print(f"[DEDUP] {rule['id']}: skipped (surfaced within {DEDUP_HOURS}h)")
            continue

        violation = check_rule(rule, observations)
        if violation:
            violations.append(violation)
            if verbose:
                print(f"[VIOLATION] {violation['rule_id']}: {violation['description']}")

    return violations


def main():
    verbose = "--verbose" in sys.argv
    violations = run_detection(verbose=verbose)

    if violations:
        # Write to temp file for next session to pick up
        OUTPUT_FILE.write_text(
            json.dumps(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "violations": violations,
                },
                indent=2,
            )
        )

        # Append to persistent history
        with open(HISTORY_FILE, "a") as f:
            for v in violations:
                f.write(json.dumps(v, separators=(",", ":")) + "\n")
    else:
        # Clean up stale violations file
        OUTPUT_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # Fail-silent always
