#!/usr/bin/env python3
"""
Fathom Transcripts Sync Script

Downloads Fathom meeting transcripts from the last 24 hours,
organized by client name into folders.

Usage: python sync_fathom_transcripts.py [--days N] [--dry-run]
"""

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

# Configuration
FATHOM_API_BASE = "https://api.fathom.ai/external/v1"
API_KEY = os.environ.get("FATHOM_API_KEY", "")

# Rate limiting settings
REQUEST_DELAY = 0.5  # seconds between requests
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

OUTPUT_DIR = Path(
    os.environ.get("FATHOM_OUTPUT_DIR", os.path.expanduser("~/fathom-transcripts"))
)
MANIFEST_FILE = OUTPUT_DIR / ".fathom_manifest.json"
LOG_FILE = OUTPUT_DIR / ".fathom_sync.log"

# Domains to ignore when extracting client name
# Set FATHOM_INTERNAL_DOMAINS env var to override (comma-separated)
_default_internal = {"gmail.com", "outlook.com", "hotmail.com"}
_env_domains = os.environ.get("FATHOM_INTERNAL_DOMAINS", "")
INTERNAL_DOMAINS = set(_env_domains.split(",")) | _default_internal if _env_domains else _default_internal


def log(message: str) -> None:
    """Log message to file and stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def get_headers() -> dict[str, str]:
    """Get authorization headers for Fathom API."""
    return {
        "X-Api-Key": API_KEY,
        "Content-Type": "application/json",
    }


def fathom_request(endpoint: str, params: dict | None = None, retries: int = MAX_RETRIES) -> dict:
    """Make a GET request to the Fathom API with retry logic."""
    url = f"{FATHOM_API_BASE}{endpoint}"

    for attempt in range(retries):
        try:
            time.sleep(REQUEST_DELAY)  # Rate limiting
            with httpx.Client(timeout=60.0) as client:
                response = client.get(url, headers=get_headers(), params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                wait_time = REQUEST_DELAY * (RETRY_BACKOFF ** (attempt + 1))
                log(f"  Rate limited, waiting {wait_time:.1f}s (attempt {attempt + 1}/{retries})")
                time.sleep(wait_time)
                if attempt == retries - 1:
                    raise
            else:
                raise

    return {}


def load_manifest() -> dict:
    """Load the manifest of already-downloaded recordings."""
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {"downloaded_recordings": [], "last_sync": None}


def save_manifest(manifest: dict) -> None:
    """Save the manifest."""
    manifest["last_sync"] = datetime.now(timezone.utc).isoformat()
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


def extract_client_from_title(title: str) -> str | None:
    """
    Extract client name from meeting title.

    Patterns:
    - "ClientName | Meeting Description"
    - "ClientName - Meeting Description"
    - "ClientName / Meeting Description"
    - "ClientName: Meeting Description"
    """
    # Common separators in meeting titles
    separators = [" | ", " - ", " / ", ": "]

    for sep in separators:
        if sep in title:
            client = title.split(sep)[0].strip()
            # Skip if it looks like a generic prefix
            if client.lower() not in ["external", "internal", "meeting", "call", "sync"]:
                return sanitize_folder_name(client)

    return None


def extract_client_from_attendees(invitees: list[dict]) -> str | None:
    """
    Extract client name from external attendees' email domains.

    Returns the most common external domain, prettified.
    """
    external_domains = []

    for invitee in invitees:
        if invitee.get("is_external", False):
            domain = invitee.get("email_domain", "")
            if domain and domain.lower() not in INTERNAL_DOMAINS:
                external_domains.append(domain.lower())

    if not external_domains:
        return None

    # Get most common domain
    domain_counts = Counter(external_domains)
    most_common_domain = domain_counts.most_common(1)[0][0]

    # Prettify domain name (e.g., "dotdigital.com" -> "DotDigital")
    name = most_common_domain.split(".")[0]
    # Convert to title case, handling common patterns
    name = name.replace("-", " ").replace("_", " ").title().replace(" ", "")

    return name


def get_client_name(meeting: dict) -> str:
    """
    Determine client name using title prefix first, then external domain fallback.
    """
    title = meeting.get("title", "") or meeting.get("meeting_title", "")

    # Try title prefix first
    client = extract_client_from_title(title)
    if client:
        return client

    # Fall back to external domain
    invitees = meeting.get("calendar_invitees", [])
    client = extract_client_from_attendees(invitees)
    if client:
        return client

    # Last resort: use "Internal" for internal-only meetings
    return "Internal"


def sanitize_folder_name(name: str) -> str:
    """Sanitize a string for use as a folder name."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", " ", name).strip()
    # Limit length
    return name[:50] if len(name) > 50 else name


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove or replace invalid characters
    name = re.sub(r'[<>:"/\\|?*]', "", name)
    name = re.sub(r"\s+", "_", name).strip("_")
    # Limit length
    return name[:100] if len(name) > 100 else name


def format_transcript(transcript_data: list[dict], meeting: dict) -> str:
    """Format transcript data into readable markdown."""
    title = meeting.get("title", "") or meeting.get("meeting_title", "Unknown Meeting")
    created_at = meeting.get("created_at", "")
    share_url = meeting.get("share_url", "")

    # Header
    lines = [
        f"# {title}",
        "",
        f"**Date:** {created_at[:10] if created_at else 'Unknown'}",
        f"**Fathom Link:** {share_url}" if share_url else "",
        "",
        "---",
        "",
        "## Transcript",
        "",
    ]

    # Transcript content
    current_speaker = None
    for entry in transcript_data:
        speaker = entry.get("speaker_display_name", "Unknown")
        text = entry.get("text", "")

        if speaker != current_speaker:
            lines.append(f"\n**{speaker}:**")
            current_speaker = speaker

        lines.append(text)

    return "\n".join(lines)


def fetch_meetings_since(since: datetime) -> list[dict]:
    """Fetch all meetings created after the given datetime."""
    meetings = []
    cursor = None
    since_iso = since.isoformat()

    while True:
        params = {"created_after": since_iso}
        if cursor:
            params["cursor"] = cursor

        result = fathom_request("/meetings", params=params)
        meetings.extend(result.get("items", []))

        cursor = result.get("next_cursor")
        if not cursor:
            break

    return meetings


def fetch_transcript(recording_id: int) -> list[dict]:
    """Fetch transcript for a recording."""
    result = fathom_request(f"/recordings/{recording_id}/transcript")
    return result.get("transcript", [])


def meeting_matches_project(meeting: dict, project_filter: str) -> bool:
    """
    Check if a meeting matches the project filter.

    Matches against:
    - Meeting title (case-insensitive, partial match)
    - Client name that would be extracted
    - External attendee domains
    """
    filter_lower = project_filter.lower()

    # Check meeting title
    title = (meeting.get("title", "") or meeting.get("meeting_title", "")).lower()
    if filter_lower in title:
        return True

    # Check client name that would be extracted
    client_name = get_client_name(meeting).lower()
    if filter_lower in client_name or client_name in filter_lower:
        return True

    # Check external domains
    invitees = meeting.get("calendar_invitees", [])
    for invitee in invitees:
        if invitee.get("is_external", False):
            domain = invitee.get("email_domain", "").lower()
            if domain and filter_lower in domain:
                return True

    return False


def file_exists_for_meeting(meeting: dict) -> bool:
    """Check if a transcript file already exists for this meeting (checks all folders)."""
    title = meeting.get("title", "") or meeting.get("meeting_title", "")
    created_at = meeting.get("created_at", "")
    date_str = created_at[:10] if created_at else ""

    if not date_str:
        return False

    safe_title = sanitize_filename(title)

    # Check in client-organized folders
    for md_file in OUTPUT_DIR.rglob("*.md"):
        # Match by date and title similarity
        if date_str in md_file.name:
            # Check if title matches (allowing for variations)
            if safe_title[:30].lower() in md_file.name.lower():
                return True
            # Also check if file stem is in the title
            if md_file.stem[:30].lower() in safe_title.lower():
                return True

    return False


def sync_transcripts(days: int = 1, dry_run: bool = False, project_filter: str | None = None) -> None:
    """Main sync function."""
    if project_filter:
        log(f"Starting Fathom transcript sync (last {days} day(s), project={project_filter}, dry_run={dry_run})")
    else:
        log(f"Starting Fathom transcript sync (last {days} day(s), dry_run={dry_run})")

    if not API_KEY:
        log("ERROR: FATHOM_API_KEY not set")
        sys.exit(1)

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load manifest
    manifest = load_manifest()
    downloaded_ids = set(manifest.get("downloaded_recordings", []))

    # Calculate time range
    since = datetime.now(timezone.utc) - timedelta(days=days)

    log(f"Fetching meetings since {since.isoformat()}")
    meetings = fetch_meetings_since(since)
    log(f"Found {len(meetings)} meeting(s)")

    new_downloads = 0
    skipped = 0
    errors = 0

    filtered_count = 0
    for meeting in meetings:
        recording_id = meeting.get("recording_id")
        if not recording_id:
            continue

        # Filter by project if specified
        if project_filter and not meeting_matches_project(meeting, project_filter):
            filtered_count += 1
            continue

        title = meeting.get("title", "") or meeting.get("meeting_title", "Unknown")
        created_at = meeting.get("created_at", "")
        date_str = created_at[:10] if created_at else datetime.now().strftime("%Y-%m-%d")

        # Skip if already in manifest OR if file already exists
        if recording_id in downloaded_ids:
            skipped += 1
            continue

        if file_exists_for_meeting(meeting):
            log(f"Skipping (file exists): {title}")
            # Add to manifest so we don't check again
            downloaded_ids.add(recording_id)
            skipped += 1
            continue

        # Determine client and create folder
        client_name = get_client_name(meeting)
        client_folder = OUTPUT_DIR / client_name

        # Create filename
        safe_title = sanitize_filename(title)
        filename = f"{safe_title}_{date_str}.md"
        filepath = client_folder / filename

        log(f"Processing: {title} -> {client_name}/{filename}")

        if dry_run:
            log(f"  [DRY RUN] Would download to: {filepath}")
            new_downloads += 1
            continue

        try:
            # Create client folder if needed
            client_folder.mkdir(parents=True, exist_ok=True)

            # Fetch and save transcript
            transcript = fetch_transcript(recording_id)
            content = format_transcript(transcript, meeting)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)

            # Update manifest
            downloaded_ids.add(recording_id)
            new_downloads += 1
            log(f"  Downloaded successfully")

        except Exception as e:
            log(f"  ERROR: {e}")
            errors += 1

    # Save updated manifest
    if not dry_run:
        manifest["downloaded_recordings"] = list(downloaded_ids)
        save_manifest(manifest)

    if project_filter:
        log(f"Sync complete: {new_downloads} new, {skipped} skipped, {filtered_count} filtered out, {errors} errors")
    else:
        log(f"Sync complete: {new_downloads} new, {skipped} skipped, {errors} errors")


def build_initial_manifest() -> None:
    """
    Initialize an empty manifest.

    The sync will automatically detect existing files and skip them,
    so we just need an empty manifest to start tracking new downloads.
    """
    log("Initializing manifest...")

    # Get count of existing files for reference
    existing_files = list(OUTPUT_DIR.rglob("*.md"))
    log(f"Found {len(existing_files)} existing transcript files")
    log("These will be auto-detected and skipped during sync.")

    manifest = {
        "downloaded_recordings": [],
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "note": f"Initialized with {len(existing_files)} pre-existing files",
    }
    save_manifest(manifest)
    log("Manifest initialized. Run --dry-run to see what would be downloaded.")


def get_most_recent_transcript_date() -> datetime | None:
    """
    Scan existing transcripts and find the most recent date.

    Returns the date of the most recent transcript, or None if no files found.
    """
    dates = []

    for md_file in OUTPUT_DIR.rglob("*.md"):
        # Extract date from filename (format: ..._YYYY-MM-DD.md)
        match = re.search(r"(\d{4}-\d{2}-\d{2})\.md$", md_file.name)
        if match:
            try:
                date = datetime.strptime(match.group(1), "%Y-%m-%d")
                dates.append(date)
            except ValueError:
                pass

    if dates:
        return max(dates)
    return None


def calculate_days_since(date: datetime) -> int:
    """Calculate number of days between a date and today."""
    today = datetime.now()
    delta = today - date
    return max(1, delta.days)  # At least 1 day


def main():
    parser = argparse.ArgumentParser(description="Sync Fathom transcripts")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Number of days to look back (default: 1, or auto-detect with --auto)",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Auto-detect days since most recent transcript and sync all missing",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Filter meetings by project/client name (partial match on title, client, or domain)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without downloading",
    )
    parser.add_argument(
        "--build-manifest",
        action="store_true",
        help="Build initial manifest from existing files",
    )

    args = parser.parse_args()

    if args.build_manifest:
        build_initial_manifest()
    elif args.auto:
        # Auto-detect mode: find most recent transcript and sync since then
        most_recent = get_most_recent_transcript_date()
        if most_recent:
            days = calculate_days_since(most_recent)
            log(f"Auto-detect: Most recent transcript is from {most_recent.date()}")
            log(f"Auto-detect: Syncing last {days} day(s) to fill any gaps")
        else:
            days = 30  # Default if no files found
            log("Auto-detect: No existing transcripts found, syncing last 30 days")
        sync_transcripts(days=days, dry_run=args.dry_run, project_filter=args.project)
    else:
        days = args.days if args.days is not None else 1
        sync_transcripts(days=days, dry_run=args.dry_run, project_filter=args.project)


if __name__ == "__main__":
    main()
