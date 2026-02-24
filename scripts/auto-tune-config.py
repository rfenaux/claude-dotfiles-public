#!/usr/bin/env python3
"""
Config Auto-Tuner - Reads weekly report suggestions and applies them.

Reads the Config Suggestions section from the latest weekly report
and offers to apply changes with before/after comparison.

Safety:
  - --dry-run (default): shows proposed changes, writes nothing
  - --apply: backs up config, applies bounded changes, logs to JSONL

Bounds:
  - max_change_percent from self-improvement.json (default 50%)
  - Only modifies params listed in self-improvement.json tunable_params
  - Backs up config before any modification

Usage:
    python3 ~/.claude/scripts/auto-tune-config.py [--dry-run|--apply]
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
METRICS_DIR = CLAUDE_DIR / "metrics"
TUNING_LOG = CLAUDE_DIR / "logs" / "self-healing" / "config-tuning.jsonl"

# Load self-improvement config for bounds
SI_PATH = CLAUDE_DIR / "config" / "self-improvement.json"


def load_self_improvement_config():
    if SI_PATH.exists():
        try:
            return json.loads(SI_PATH.read_text())
        except Exception:
            pass
    return {}


def get_tunable_params(si_config):
    """Get list of allowed tunable parameter paths."""
    return si_config.get("auto_tune", {}).get("tunable_params", [])


def get_max_change_pct(si_config):
    return si_config.get("auto_tune", {}).get("max_change_percent", 50)


def requires_approval(si_config):
    return si_config.get("auto_tune", {}).get("require_approval", True)


def parse_suggestions_from_report():
    """Extract config suggestions from the latest weekly report."""
    reports = sorted(METRICS_DIR.glob("weekly-*.md"), reverse=True)
    if not reports:
        return []

    content = reports[0].read_text()

    # Find Config Suggestions table
    match = re.search(
        r"## Config Suggestions\n\n"
        r"\| Parameter \| Current \| Suggested \| Reason \|\n"
        r"\|[-|]+\|\n"
        r"((?:\|[^\n]+\n)*)",
        content
    )
    if not match:
        return []

    suggestions = []
    for line in match.group(1).strip().split("\n"):
        # Parse: | `param` | current | suggested | reason |
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4:
            param = cells[0].strip("`").strip()
            current = cells[1].strip()
            suggested = cells[2].strip()
            reason = cells[3].strip()
            suggestions.append({
                "param": param,
                "current": current,
                "suggested": suggested,
                "reason": reason,
            })

    return suggestions


def resolve_config_path(param):
    """Resolve a dotted param path to config file + JSON path."""
    # param format: "pruning.tool_rules.Read.ttl_minutes"
    # or "observation-config.max_entries_per_session"
    # or "self-healing.services.ollama.rate_limit_min"
    parts = param.split(".", 1)
    if len(parts) < 2:
        return None, None

    config_name = parts[0]
    json_path = parts[1]

    config_file_map = {
        "pruning": CLAUDE_DIR / "config" / "pruning.json",
        "observation-config": CLAUDE_DIR / "config" / "observation-config.json",
        "self-healing": CLAUDE_DIR / "config" / "self-healing.json",
    }

    config_file = config_file_map.get(config_name)
    if not config_file or not config_file.exists():
        return None, None

    return config_file, json_path


def get_nested_value(data, path):
    """Get value from nested dict using dotted path."""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def set_nested_value(data, path, value):
    """Set value in nested dict using dotted path."""
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if key not in current:
            return False
        current = current[key]
    if keys[-1] in current:
        current[keys[-1]] = value
        return True
    return False


def is_param_tunable(param, tunable_params):
    """Check if a parameter matches any tunable_params pattern."""
    for pattern in tunable_params:
        # Convert glob pattern to regex: * matches any single key
        regex = pattern.replace(".", r"\.").replace("*", r"[^.]+")
        if re.fullmatch(regex, param):
            return True
    return False


def validate_change(current_val, suggested_val, max_change_pct):
    """Validate that change is within bounds."""
    try:
        current = float(current_val)
        suggested = float(suggested_val)
    except (ValueError, TypeError):
        return False, "Cannot parse numeric values"

    if current == 0:
        return True, ""

    change_pct = abs(suggested - current) / current * 100
    if change_pct > max_change_pct:
        return False, f"Change {change_pct:.0f}% exceeds max {max_change_pct}%"

    return True, ""


def backup_config(config_file):
    """Create timestamped backup of config file."""
    backup_dir = CLAUDE_DIR / "config" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{config_file.stem}_{ts}.json"
    shutil.copy2(config_file, backup_path)
    return backup_path


def log_change(param, before, after, config_file):
    """Log the change to tuning log."""
    TUNING_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "param": param,
        "before": before,
        "after": after,
        "config_file": str(config_file),
    }
    with open(TUNING_LOG, "a") as f:
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")


def main():
    apply_mode = "--apply" in sys.argv
    dry_run = not apply_mode

    si_config = load_self_improvement_config()
    tunable_params = get_tunable_params(si_config)
    max_change_pct = get_max_change_pct(si_config)

    print(f"Config Auto-Tuner {'(DRY RUN)' if dry_run else '(APPLY MODE)'}")
    print("=" * 50)
    print(f"Max change: {max_change_pct}%")
    print(f"Tunable params: {len(tunable_params)}")
    print()

    suggestions = parse_suggestions_from_report()
    if not suggestions:
        print("No config suggestions found in latest weekly report.")
        print("Run: python3 ~/.claude/scripts/analyze-weekly.py")
        return

    print(f"Found {len(suggestions)} suggestion(s):\n")

    applied = 0
    skipped = 0

    for s in suggestions:
        param = s["param"]
        suggested = s["suggested"]
        reason = s["reason"]

        print(f"  Parameter: {param}")
        print(f"  Current:   {s['current']}")
        print(f"  Suggested: {suggested}")
        print(f"  Reason:    {reason}")

        # Check if tunable
        if not is_param_tunable(param, tunable_params):
            print(f"  Status:    SKIP (not in tunable_params)")
            skipped += 1
            print()
            continue

        # Resolve config file
        config_file, json_path = resolve_config_path(param)
        if not config_file:
            print(f"  Status:    SKIP (config file not found)")
            skipped += 1
            print()
            continue

        # Read current value from config
        try:
            config_data = json.loads(config_file.read_text())
        except Exception as e:
            print(f"  Status:    SKIP (error reading config: {e})")
            skipped += 1
            print()
            continue

        current_val = get_nested_value(config_data, json_path)
        if current_val is None:
            print(f"  Status:    SKIP (path not found in config)")
            skipped += 1
            print()
            continue

        # Validate bounds
        valid, msg = validate_change(current_val, suggested, max_change_pct)
        if not valid:
            print(f"  Status:    SKIP ({msg})")
            skipped += 1
            print()
            continue

        if dry_run:
            print(f"  Status:    WOULD APPLY ({current_val} -> {suggested})")
        else:
            # Backup
            backup = backup_config(config_file)
            print(f"  Backup:    {backup}")

            # Apply
            try:
                new_val = type(current_val)(suggested)
            except (ValueError, TypeError):
                new_val = int(suggested)

            set_nested_value(config_data, json_path, new_val)
            config_file.write_text(json.dumps(config_data, indent=2) + "\n")
            log_change(param, current_val, new_val, config_file)
            print(f"  Status:    APPLIED ({current_val} -> {new_val})")
            applied += 1

        print()

    print(f"\nSummary: {applied} applied, {skipped} skipped" +
          (" (dry run)" if dry_run else ""))
    if dry_run and applied == 0 and skipped < len(suggestions):
        print("Re-run with --apply to make changes.")


if __name__ == "__main__":
    main()
