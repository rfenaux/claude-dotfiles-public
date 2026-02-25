#!/usr/bin/env python3
"""
Standardize hook scripts — adds set +e after shebang, exit 0 as final line.

Usage:
  python3 scripts/standardize-hooks.py --check    # Report only
  python3 scripts/standardize-hooks.py --fix      # Apply fixes
"""

import argparse
import glob
import sys

HOOKS_DIR = "hooks"
# Lib files are sourced, not executed directly — exempt from hook rules
EXEMPT_FILES = {"hooks/lib/circuit-breaker.sh", "hooks/lib/idempotency.sh"}


def check_hook(filepath: str) -> list[str]:
    """Check a hook file for quality issues. Returns list of issue descriptions."""
    issues = []
    with open(filepath) as f:
        content = f.read()
        lines = content.split('\n')

    # Strip trailing empty lines for last-line check
    non_empty = [l for l in lines if l.strip()]
    if not non_empty:
        return ["empty file"]

    # Check 1: set +e after shebang
    if 'set +e' not in content:
        issues.append("missing 'set +e'")

    # Check 2: exit 0 as last meaningful line
    last_line = non_empty[-1].strip()
    if last_line != 'exit 0':
        issues.append(f"missing 'exit 0' (last: {last_line[:40]})")

    return issues


def fix_hook(filepath: str) -> list[str]:
    """Fix hook quality issues. Returns list of changes made."""
    changes = []
    with open(filepath) as f:
        content = f.read()
        lines = content.split('\n')

    # Fix 1: Add set +e after shebang if missing
    if 'set +e' not in content:
        new_lines = []
        shebang_found = False
        for i, line in enumerate(lines):
            new_lines.append(line)
            if not shebang_found and line.startswith('#!/'):
                new_lines.append('set +e  # Never use set -e in hooks — non-zero exits kill the hook')
                shebang_found = True
        if not shebang_found:
            # No shebang — add set +e at top
            new_lines = ['set +e  # Never use set -e in hooks — non-zero exits kill the hook'] + lines
        lines = new_lines
        changes.append("added 'set +e' after shebang")

    # Fix 2: Add exit 0 as last line if missing
    # Strip trailing empty lines first
    while lines and lines[-1].strip() == '':
        lines.pop()

    if lines and lines[-1].strip() != 'exit 0':
        lines.append('')
        lines.append('exit 0')
        changes.append("added 'exit 0' as final line")

    if changes:
        # Ensure file ends with newline
        content = '\n'.join(lines)
        if not content.endswith('\n'):
            content += '\n'
        with open(filepath, 'w') as f:
            f.write(content)

    return changes


def main():
    parser = argparse.ArgumentParser(description="Standardize hook scripts")
    parser.add_argument("--check", action="store_true", help="Report only, don't modify")
    parser.add_argument("--fix", action="store_true", help="Apply fixes")
    args = parser.parse_args()

    if not args.check and not args.fix:
        print("Usage: --check (report) or --fix (apply)")
        sys.exit(1)

    hook_files = sorted(glob.glob(f"{HOOKS_DIR}/**/*.sh", recursive=True))
    total = len(hook_files)
    issues_count = 0
    fixed_count = 0

    for filepath in hook_files:
        if filepath in EXEMPT_FILES:
            continue

        if args.check:
            issues = check_hook(filepath)
            if issues:
                issues_count += 1
                print(f"  ISSUE {filepath}: {'; '.join(issues)}")
        elif args.fix:
            changes = fix_hook(filepath)
            if changes:
                fixed_count += 1
                print(f"  FIXED {filepath}: {'; '.join(changes)}")

    print(f"\n{'='*60}")
    print(f"Hook Quality {'Report' if args.check else 'Fix Summary'}")
    print(f"{'='*60}")
    print(f"Total hooks: {total} (excluding {len(EXEMPT_FILES)} lib files)")
    if args.check:
        print(f"Hooks with issues: {issues_count}")
    if args.fix:
        print(f"Fixed: {fixed_count} files")


if __name__ == "__main__":
    main()
