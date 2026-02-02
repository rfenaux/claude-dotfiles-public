#!/usr/bin/env python3
"""
Git Changelog Generator for RAG Indexing

Generates structured changelog entries from git commits that can be:
1. Indexed to RAG for semantic search
2. Used in session briefings
3. Queried for context understanding

Output format optimized for RAG chunking and retrieval.
"""

import subprocess
import json
import sys
import re
from pathlib import Path
from datetime import datetime, timezone
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
        return result.stdout.strip()
    except Exception as e:
        return ""


def get_commit_info(commit_hash: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
    """Get detailed information about a commit."""
    # Get commit metadata
    format_str = "%H|%h|%an|%ae|%ai|%s"
    info = run_git(["show", "-s", f"--format={format_str}", commit_hash], cwd)

    if not info:
        return {}

    parts = info.split("|")
    if len(parts) < 6:
        return {}

    full_hash, short_hash, author, email, date, subject = parts[:6]

    # Get changed files
    files_output = run_git(["show", "--name-status", "--format=", commit_hash], cwd)
    changed_files = []
    for line in files_output.strip().split("\n"):
        if line and "\t" in line:
            status, filepath = line.split("\t", 1)
            status_map = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed"}
            changed_files.append({
                "path": filepath,
                "status": status_map.get(status[0], "changed")
            })

    # Get diff stats
    stats = run_git(["show", "--stat", "--format=", commit_hash], cwd)

    return {
        "hash": full_hash,
        "short_hash": short_hash,
        "author": author,
        "email": email,
        "date": date,
        "subject": subject,
        "files": changed_files,
        "stats": stats
    }


def classify_commit(subject: str, files: List[Dict]) -> str:
    """Classify commit type based on subject and files."""
    subject_lower = subject.lower()

    # Check conventional commit prefixes
    if subject_lower.startswith("feat"):
        return "feature"
    elif subject_lower.startswith("fix"):
        return "bugfix"
    elif subject_lower.startswith("docs"):
        return "documentation"
    elif subject_lower.startswith("refactor"):
        return "refactor"
    elif subject_lower.startswith("test"):
        return "test"
    elif subject_lower.startswith("chore"):
        return "chore"
    elif "auto-checkpoint" in subject_lower:
        return "checkpoint"

    # Check file patterns
    doc_extensions = {".md", ".txt", ".rst", ".doc", ".docx"}
    test_patterns = {"test", "spec", "__tests__"}

    doc_count = sum(1 for f in files if Path(f["path"]).suffix in doc_extensions)
    test_count = sum(1 for f in files if any(p in f["path"].lower() for p in test_patterns))

    if doc_count > len(files) / 2:
        return "documentation"
    elif test_count > len(files) / 2:
        return "test"

    return "change"


def get_key_diffs(commit_hash: str, cwd: Optional[Path] = None, max_lines: int = 50) -> List[Dict[str, str]]:
    """Get key diffs for significant files (not all files)."""
    # Prioritize certain file types for diffs
    priority_extensions = {".md", ".py", ".ts", ".tsx", ".js", ".json"}
    skip_patterns = {"package-lock.json", "yarn.lock", ".min.js", ".min.css"}

    files_output = run_git(["show", "--name-only", "--format=", commit_hash], cwd)
    files = [f for f in files_output.strip().split("\n") if f]

    key_diffs = []
    lines_used = 0

    for filepath in files:
        # Skip noisy files
        if any(p in filepath for p in skip_patterns):
            continue

        # Prioritize important files
        ext = Path(filepath).suffix
        if ext not in priority_extensions and lines_used > max_lines / 2:
            continue

        # Get diff for this file
        diff = run_git(["show", "--format=", "--", filepath, commit_hash], cwd)

        if not diff:
            continue

        # Truncate if too long
        diff_lines = diff.split("\n")
        if len(diff_lines) > 30:
            diff = "\n".join(diff_lines[:30]) + f"\n... ({len(diff_lines) - 30} more lines)"

        key_diffs.append({
            "file": filepath,
            "diff": diff
        })

        lines_used += len(diff_lines)
        if lines_used >= max_lines:
            break

    return key_diffs


def generate_changelog_entry(commit_hash: str, cwd: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Generate a structured changelog entry for a commit."""
    info = get_commit_info(commit_hash, cwd)

    if not info:
        return None

    commit_type = classify_commit(info["subject"], info["files"])
    key_diffs = get_key_diffs(commit_hash, cwd)

    # Build the entry
    entry = {
        "type": "git_changelog",
        "commit_hash": info["hash"],
        "short_hash": info["short_hash"],
        "date": info["date"],
        "author": info["author"],
        "subject": info["subject"],
        "commit_type": commit_type,
        "files_changed": [f["path"] for f in info["files"]],
        "file_count": len(info["files"]),
        "stats": info["stats"],
        "key_diffs": key_diffs,
        "indexed_at": datetime.now(timezone.utc).isoformat()
    }

    return entry


def generate_markdown(entry: Dict[str, Any]) -> str:
    """Generate markdown representation for RAG indexing."""
    md = f"""# Git Change: {entry['subject']}

> Commit: {entry['short_hash']} | Date: {entry['date'][:10]} | Type: {entry['commit_type']}

## Summary
- **Author**: {entry['author']}
- **Files changed**: {entry['file_count']}
- **Type**: {entry['commit_type']}

## Files Modified
"""

    for filepath in entry["files_changed"][:20]:
        md += f"- `{filepath}`\n"

    if len(entry["files_changed"]) > 20:
        md += f"- ... and {len(entry['files_changed']) - 20} more files\n"

    if entry.get("key_diffs"):
        md += "\n## Key Changes\n"
        for diff_item in entry["key_diffs"]:
            md += f"\n### {diff_item['file']}\n```diff\n{diff_item['diff']}\n```\n"

    md += f"\n---\n*Indexed: {entry['indexed_at'][:10]}*\n"

    return md


def get_recent_commits(count: int = 10, since: Optional[str] = None, cwd: Optional[Path] = None) -> List[str]:
    """Get recent commit hashes."""
    args = ["log", f"-{count}", "--format=%H"]
    if since:
        args.append(f"--since={since}")

    output = run_git(args, cwd)
    return [h for h in output.split("\n") if h]


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate git changelog entries for RAG")
    parser.add_argument("--commit", "-c", help="Specific commit hash")
    parser.add_argument("--recent", "-r", type=int, default=1, help="Number of recent commits")
    parser.add_argument("--since", "-s", help="Since date (e.g., '1 week ago')")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--output", "-o", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--save-dir", help="Directory to save changelog files")

    args = parser.parse_args()

    cwd = Path(args.project) if args.project else None

    if args.commit:
        commits = [args.commit]
    else:
        commits = get_recent_commits(args.recent, args.since, cwd)

    entries = []
    for commit_hash in commits:
        entry = generate_changelog_entry(commit_hash, cwd)
        if entry:
            entries.append(entry)

    if args.save_dir:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        for entry in entries:
            filename = f"changelog-{entry['short_hash']}-{entry['date'][:10]}.md"
            filepath = save_dir / filename
            filepath.write_text(generate_markdown(entry))
            print(f"Saved: {filepath}")
    else:
        for entry in entries:
            if args.output == "json":
                print(json.dumps(entry, indent=2))
            else:
                print(generate_markdown(entry))
                print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
