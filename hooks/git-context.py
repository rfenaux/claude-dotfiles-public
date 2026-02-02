#!/usr/bin/env python3
"""
Git Context Query Tool

Provides Claude with ability to query git history for context understanding.
Supports:
- Recent changes summary
- File history
- Search commits by content/message
- Changes since a date
- Blame/annotation for specific lines

Usage:
    git-context recent [--count N] [--since DATE]
    git-context file <filepath> [--count N]
    git-context search <query>
    git-context diff [--from REF] [--to REF]
    git-context blame <filepath> [--line N]
    git-context summary
"""

import subprocess
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


def run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except Exception:
        return ""


def format_commit(hash: str, date: str, author: str, subject: str, files: int = 0) -> str:
    """Format a commit for display."""
    return f"[{hash}] {date[:10]} - {subject} ({author})" + (f" [{files} files]" if files else "")


def cmd_recent(args, cwd: Path) -> str:
    """Show recent commits with summaries."""
    count = args.count or 10
    since = args.since

    git_args = ["log", f"-{count}", "--format=%h|%ai|%an|%s"]
    if since:
        git_args.append(f"--since={since}")

    output = run_git(git_args, cwd)

    if not output:
        return "No commits found."

    lines = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 4:
                hash, date, author, subject = parts[0], parts[1], parts[2], "|".join(parts[3:])
                # Get file count
                files = run_git(["show", "--name-only", "--format=", hash], cwd)
                file_count = len([f for f in files.split("\n") if f])
                lines.append(format_commit(hash, date, author, subject, file_count))

    result = f"## Recent Changes ({len(lines)} commits)\n\n"
    for line in lines:
        result += f"- {line}\n"

    return result


def cmd_file(args, cwd: Path) -> str:
    """Show history for a specific file."""
    filepath = args.filepath
    count = args.count or 10

    # Check if file exists or existed
    output = run_git(["log", f"-{count}", "--format=%h|%ai|%an|%s", "--follow", "--", filepath], cwd)

    if not output:
        return f"No history found for: {filepath}"

    lines = []
    for line in output.split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 4:
                hash, date, author, subject = parts[0], parts[1], parts[2], "|".join(parts[3:])
                lines.append(format_commit(hash, date, author, subject))

    result = f"## History for `{filepath}` ({len(lines)} commits)\n\n"
    for line in lines:
        result += f"- {line}\n"

    # Show recent diff
    if lines:
        result += f"\n### Most Recent Change\n"
        recent_hash = lines[0].split("]")[0][1:]
        diff = run_git(["show", "--format=", "--", filepath, recent_hash], cwd)
        if diff:
            # Truncate if too long
            diff_lines = diff.split("\n")
            if len(diff_lines) > 50:
                diff = "\n".join(diff_lines[:50]) + f"\n... ({len(diff_lines) - 50} more lines)"
            result += f"```diff\n{diff}\n```\n"

    return result


def cmd_search(args, cwd: Path) -> str:
    """Search commits by message or content."""
    query = args.query

    # Search in commit messages
    msg_output = run_git(["log", "--all", "-20", f"--grep={query}", "--format=%h|%ai|%an|%s"], cwd)

    # Search in commit content (pickaxe)
    content_output = run_git(["log", "--all", "-10", f"-S{query}", "--format=%h|%ai|%an|%s"], cwd)

    results = []
    seen = set()

    for output, source in [(msg_output, "message"), (content_output, "content")]:
        for line in output.split("\n"):
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 4 and parts[0] not in seen:
                    seen.add(parts[0])
                    hash, date, author, subject = parts[0], parts[1], parts[2], "|".join(parts[3:])
                    results.append((format_commit(hash, date, author, subject), source))

    if not results:
        return f"No commits found matching: {query}"

    result = f"## Search Results for \"{query}\" ({len(results)} commits)\n\n"
    for line, source in results:
        result += f"- {line} *({source})*\n"

    return result


def cmd_diff(args, cwd: Path) -> str:
    """Show diff between two refs."""
    from_ref = args.from_ref or "HEAD~1"
    to_ref = args.to_ref or "HEAD"

    # Get stats
    stats = run_git(["diff", "--stat", from_ref, to_ref], cwd)

    # Get summary of changed files
    files = run_git(["diff", "--name-status", from_ref, to_ref], cwd)

    result = f"## Diff: {from_ref}..{to_ref}\n\n"

    if files:
        result += "### Files Changed\n"
        for line in files.split("\n")[:30]:
            if "\t" in line:
                status, filepath = line.split("\t", 1)
                status_map = {"A": "+", "M": "~", "D": "-", "R": "→"}
                icon = status_map.get(status[0], "?")
                result += f"- {icon} `{filepath}`\n"

        if len(files.split("\n")) > 30:
            result += f"- ... and more files\n"

    if stats:
        result += f"\n### Stats\n```\n{stats}\n```\n"

    return result


def cmd_blame(args, cwd: Path) -> str:
    """Show blame/annotation for a file."""
    filepath = args.filepath
    line = args.line

    if line:
        # Show blame for specific line range
        start = max(1, line - 5)
        end = line + 5
        output = run_git(["blame", "-L", f"{start},{end}", "--date=short", filepath], cwd)
    else:
        # Show blame summary (who wrote what percentage)
        output = run_git(["blame", "--line-porcelain", filepath], cwd)

        if not output:
            return f"Cannot get blame for: {filepath}"

        # Parse and summarize by author
        authors = {}
        for line in output.split("\n"):
            if line.startswith("author "):
                author = line[7:]
                authors[author] = authors.get(author, 0) + 1

        total = sum(authors.values())
        result = f"## Blame Summary for `{filepath}`\n\n"
        for author, count in sorted(authors.items(), key=lambda x: -x[1]):
            pct = (count / total) * 100
            result += f"- {author}: {count} lines ({pct:.1f}%)\n"

        return result

    if not output:
        return f"Cannot get blame for: {filepath}"

    result = f"## Blame for `{filepath}`"
    if line:
        result += f" (lines {start}-{end})"
    result += f"\n\n```\n{output}\n```\n"

    return result


def cmd_summary(args, cwd: Path) -> str:
    """Generate a summary of the repository state."""
    # Get basic info
    branch = run_git(["branch", "--show-current"], cwd)
    last_commit = run_git(["log", "-1", "--format=%h %s (%ar)"], cwd)
    total_commits = run_git(["rev-list", "--count", "HEAD"], cwd)

    # Get recent activity
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recent_count = run_git(["rev-list", "--count", f"--since={week_ago}", "HEAD"], cwd)

    # Get contributors this week
    contributors = run_git(["shortlog", "-sn", f"--since={week_ago}", "HEAD"], cwd)

    # Get uncommitted changes
    status = run_git(["status", "--porcelain"], cwd)
    uncommitted = len([l for l in status.split("\n") if l])

    result = f"""## Repository Summary

**Branch**: {branch}
**Last commit**: {last_commit}
**Total commits**: {total_commits}
**Commits this week**: {recent_count}
**Uncommitted changes**: {uncommitted} files

### Recent Contributors
"""

    for line in contributors.split("\n")[:5]:
        if line.strip():
            result += f"- {line.strip()}\n"

    # Top changed files this week
    changed_files = run_git(["log", f"--since={week_ago}", "--name-only", "--format="], cwd)
    if changed_files:
        file_counts = {}
        for f in changed_files.split("\n"):
            if f.strip():
                file_counts[f] = file_counts.get(f, 0) + 1

        result += "\n### Most Active Files This Week\n"
        for filepath, count in sorted(file_counts.items(), key=lambda x: -x[1])[:10]:
            result += f"- `{filepath}` ({count} changes)\n"

    return result


def main():
    parser = argparse.ArgumentParser(description="Git Context Query Tool")
    parser.add_argument("--project", "-p", help="Project path")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Recent command
    recent_parser = subparsers.add_parser("recent", help="Show recent commits")
    recent_parser.add_argument("--count", "-n", type=int, help="Number of commits")
    recent_parser.add_argument("--since", "-s", help="Since date")

    # File command
    file_parser = subparsers.add_parser("file", help="Show file history")
    file_parser.add_argument("filepath", help="File path")
    file_parser.add_argument("--count", "-n", type=int, help="Number of commits")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search commits")
    search_parser.add_argument("query", help="Search query")

    # Diff command
    diff_parser = subparsers.add_parser("diff", help="Show diff between refs")
    diff_parser.add_argument("--from", dest="from_ref", help="From ref")
    diff_parser.add_argument("--to", dest="to_ref", help="To ref")

    # Blame command
    blame_parser = subparsers.add_parser("blame", help="Show file blame")
    blame_parser.add_argument("filepath", help="File path")
    blame_parser.add_argument("--line", "-l", type=int, help="Line number")

    # Summary command
    subparsers.add_parser("summary", help="Repository summary")

    args = parser.parse_args()

    if args.project:
        cwd = Path(args.project)
    else:
        cwd = Path.cwd()

    if not args.command:
        # Default to summary
        args.command = "summary"

    commands = {
        "recent": cmd_recent,
        "file": cmd_file,
        "search": cmd_search,
        "diff": cmd_diff,
        "blame": cmd_blame,
        "summary": cmd_summary
    }

    if args.command in commands:
        result = commands[args.command](args, cwd)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
