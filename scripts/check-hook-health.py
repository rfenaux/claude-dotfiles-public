#!/usr/bin/env python3
"""Check hook timing data and permanently disable consistently slow hooks.

Reads from /tmp/claude-hook-timing/slow-hooks.jsonl (populated by circuit-breaker.sh).
If a hook averages >200ms over 20+ invocations in the last 7 days, adds it to
~/.claude/config/disabled-hooks.json for permanent skip via check_disabled().
"""
import json
import os
import sys
from datetime import datetime, timedelta
from collections import defaultdict

TIMING_DIR = "/tmp/claude-hook-timing"
DISABLED_FILE = os.path.expanduser("~/.claude/config/disabled-hooks.json")
THRESHOLD_AVG_MS = 200
THRESHOLD_COUNT = 20
LOOKBACK_DAYS = 7

# Stop hooks run once per session — exclude from hot-path performance checks
STOP_HOOK_PREFIXES = ("stop-", "session-end-", "save-conversation", "session-compressor",
                       "session-metrics", "claude-config-backup", "ctm-session-end",
                       "ctm-auto-decompose", "auto-sync-decisions", "session-context-cleanup")


def main():
    slow_file = os.path.join(TIMING_DIR, "slow-hooks.jsonl")
    if not os.path.exists(slow_file):
        return

    cutoff = datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)
    hook_times = defaultdict(list)

    with open(slow_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                ts = datetime.fromisoformat(entry["ts"].replace("Z", "+00:00")).replace(tzinfo=None)
                if ts >= cutoff:
                    hook_times[entry["hook"]].append(entry.get("ms", entry.get("duration_ms", 0)))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    # Load existing disabled list + protected hooks
    disabled = {"disabled": [], "disabled_at": {}, "reason": {}, "protected": []}
    if os.path.exists(DISABLED_FILE):
        try:
            with open(DISABLED_FILE) as f:
                disabled = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    protected = set(disabled.get("protected", []))

    changed = False
    for hook, times in hook_times.items():
        # Skip already disabled
        if hook in disabled.get("disabled", []):
            continue
        # Skip protected hooks (core infrastructure)
        if hook in protected:
            if len(times) >= THRESHOLD_COUNT:
                avg = sum(times) / len(times)
                if avg > THRESHOLD_AVG_MS:
                    print(f"[Hook Health WARNING] Protected hook {hook}: avg {avg:.0f}ms (not disabled)")
            continue
        # Skip Stop/SessionEnd hooks (run once per session, allowed to be slow)
        if any(hook.startswith(p) for p in STOP_HOOK_PREFIXES):
            continue
        if len(times) >= THRESHOLD_COUNT:
            avg = sum(times) / len(times)
            if avg > THRESHOLD_AVG_MS:
                disabled.setdefault("disabled", []).append(hook)
                disabled.setdefault("disabled_at", {})[hook] = datetime.utcnow().isoformat() + "Z"
                disabled.setdefault("reason", {})[hook] = f"avg {avg:.0f}ms over {len(times)} invocations"
                changed = True
                print(f"[Hook Auto-Disabled] {hook}: {disabled['reason'][hook]}")

    if changed:
        os.makedirs(os.path.dirname(DISABLED_FILE), exist_ok=True)
        with open(DISABLED_FILE, "w") as f:
            json.dump(disabled, f, indent=2)

    if not changed:
        print("[Hook Health] All hooks within performance thresholds")


if __name__ == "__main__":
    main()
