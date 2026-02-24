#!/usr/bin/env python3
"""Claude Code usage API client with file-based caching.

Output format (pipe-delimited):
    {5h_pct}|{5h_remaining}|{7d_pct}|{7d_remaining}|{opus_pct}

Errors produce: ?|?|?|?|?
Cache: /tmp/claude-usage-cache-{hash}.json (30s TTL)
No external deps — stdlib only.
"""

import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

CACHE_TTL = 30  # seconds
API_URL = "https://api.anthropic.com/api/oauth/usage"
BETA_HEADER = "oauth-2025-04-20"
FALLBACK = "?|?|?|?|?"


def cache_path():
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "default")
    h = hashlib.md5(config_dir.encode()).hexdigest()[:8]
    return f"/tmp/claude-usage-cache-{h}.json"


def read_cache():
    p = cache_path()
    try:
        if not os.path.exists(p):
            return None
        age = time.time() - os.path.getmtime(p)
        if age > CACHE_TTL:
            return None
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None


def write_cache(data):
    try:
        with open(cache_path(), "w") as f:
            json.dump(data, f)
    except Exception:
        pass


def get_token():
    try:
        config_dir = os.environ.get("CLAUDE_CONFIG_DIR", "")
        if config_dir and config_dir != os.path.expanduser("~/.claude"):
            suffix = "-" + hashlib.sha256(config_dir.encode()).hexdigest()[:8]
        else:
            suffix = ""
        service = f"Claude Code-credentials{suffix}"
        out = subprocess.check_output(
            ["security", "find-generic-password", "-s", service, "-w"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        creds = json.loads(out.strip())
        return creds.get("claudeAiOauth", {}).get("accessToken")
    except Exception:
        return None


def fetch_usage(token):
    req = urllib.request.Request(
        API_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "anthropic-beta": BETA_HEADER,
        },
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def time_remaining(resets_at):
    """Parse ISO timestamp and return human-readable remaining time."""
    try:
        # Handle both Z suffix and +00:00
        ts = resets_at.replace("Z", "+00:00")
        reset = datetime.fromisoformat(ts)
        now = datetime.now(timezone.utc)
        delta = reset - now
        secs = max(0, int(delta.total_seconds()))
        hours, remainder = divmod(secs, 3600)
        minutes = remainder // 60
        return f"{hours}h{minutes:02d}m"
    except Exception:
        return "?"


def format_output(data):
    try:
        fh = data.get("five_hour", {})
        sd = data.get("seven_day", {})
        opus = data.get("seven_day_opus", {})

        fh_pct = int(round(fh.get("utilization", 0)))
        fh_rem = time_remaining(fh.get("resets_at", ""))
        sd_pct = int(round(sd.get("utilization", 0)))
        sd_rem = time_remaining(sd.get("resets_at", ""))
        opus_pct = int(round(opus.get("utilization", 0))) if opus else 0

        return f"{fh_pct}|{fh_rem}|{sd_pct}|{sd_rem}|{opus_pct}"
    except Exception:
        return FALLBACK


def main():
    # Try cache first
    cached = read_cache()
    if cached:
        print(format_output(cached))
        return

    # Fetch fresh
    token = get_token()
    if not token:
        print(FALLBACK)
        return

    try:
        data = fetch_usage(token)
        write_cache(data)
        print(format_output(data))
    except Exception:
        print(FALLBACK)


if __name__ == "__main__":
    main()
