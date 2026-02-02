#!/usr/bin/env python3
"""
lesson-maintenance.py - Maintenance functions for the learned lessons system.

Commands:
    consolidate [--dry-run]  - Find and link similar lessons
    stats                    - Show lesson health statistics
    rebuild-embeddings       - Regenerate embeddings cache

Uses hybrid similarity: title matching (fast) + embedding similarity (thorough).
"""

import os
import sys
import json
import re
import math
import subprocess
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

# Configuration
LESSONS_DIR = Path.home() / ".claude" / "lessons"
LESSONS_FILE = LESSONS_DIR / "lessons.jsonl"
EMBEDDINGS_FILE = LESSONS_DIR / "embeddings.json"
SIMILARITY_THRESHOLD = 0.85
TITLE_SIMILARITY_THRESHOLD = 0.85
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "mxbai-embed-large"


def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
    # Lowercase, remove punctuation, collapse whitespace
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def title_similarity(t1: str, t2: str) -> float:
    """Calculate Jaccard similarity between two titles."""
    words1 = set(normalize_title(t1).split())
    words2 = set(normalize_title(t2).split())

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


def get_embedding(text: str) -> Optional[list]:
    """Get embedding vector from Ollama."""
    import urllib.request
    import urllib.error

    try:
        data = json.dumps({
            "model": EMBEDDING_MODEL,
            "prompt": text[:2000]  # Truncate long text
        }).encode('utf-8')

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("embedding")
    except Exception as e:
        print(f"[maintenance] Embedding failed: {e}", file=sys.stderr)
        return None


def cosine_similarity(v1: list, v2: list) -> float:
    """Calculate cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return dot_product / (norm1 * norm2)


def load_lessons() -> list:
    """Load all lessons from JSONL file."""
    lessons = []
    if not LESSONS_FILE.exists():
        return lessons

    with open(LESSONS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lessons.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return lessons


def save_lessons(lessons: list):
    """Save lessons back to JSONL file."""
    with open(LESSONS_FILE, 'w') as f:
        for lesson in lessons:
            f.write(json.dumps(lesson) + '\n')


def load_embeddings() -> dict:
    """Load cached embeddings."""
    if not EMBEDDINGS_FILE.exists():
        return {}
    try:
        return json.loads(EMBEDDINGS_FILE.read_text())
    except:
        return {}


def save_embeddings(embeddings: dict):
    """Save embeddings cache."""
    EMBEDDINGS_FILE.write_text(json.dumps(embeddings))


def rebuild_embeddings(lessons: list, force: bool = False) -> dict:
    """Rebuild embeddings cache for all lessons."""
    embeddings = {} if force else load_embeddings()

    missing = [l for l in lessons if l.get('id') not in embeddings]

    if not missing:
        print(f"[maintenance] Embeddings cache is current ({len(embeddings)} entries)")
        return embeddings

    print(f"[maintenance] Generating embeddings for {len(missing)} lessons...")

    for i, lesson in enumerate(missing, 1):
        lesson_id = lesson.get('id', '')
        title = lesson.get('title', '')
        content = lesson.get('lesson', '')
        text = f"{title}. {content}"

        embedding = get_embedding(text)
        if embedding:
            embeddings[lesson_id] = embedding

        if i % 10 == 0:
            print(f"[maintenance] Progress: {i}/{len(missing)}", file=sys.stderr)

    save_embeddings(embeddings)
    print(f"[maintenance] Embeddings cache updated ({len(embeddings)} total)")
    return embeddings


def find_similar_clusters(lessons: list, embeddings: dict) -> list:
    """Find clusters of similar lessons using hybrid approach."""
    clusters = []
    used = set()

    # Sort by confidence (highest first) to prefer as canonical
    sorted_lessons = sorted(lessons, key=lambda x: (-x.get('confidence', 0), x.get('approved_at', '')))

    for i, lesson in enumerate(sorted_lessons):
        lesson_id = lesson.get('id', '')
        if lesson_id in used or lesson.get('superseded_by'):
            continue

        cluster = [lesson]
        used.add(lesson_id)

        title1 = lesson.get('title', '')
        emb1 = embeddings.get(lesson_id)

        for other in sorted_lessons[i+1:]:
            other_id = other.get('id', '')
            if other_id in used or other.get('superseded_by'):
                continue

            title2 = other.get('title', '')

            # Fast check: title similarity
            t_sim = title_similarity(title1, title2)
            if t_sim >= TITLE_SIMILARITY_THRESHOLD:
                cluster.append(other)
                used.add(other_id)
                continue

            # Thorough check: embedding similarity
            if emb1:
                emb2 = embeddings.get(other_id)
                if emb2:
                    e_sim = cosine_similarity(emb1, emb2)
                    if e_sim >= SIMILARITY_THRESHOLD:
                        cluster.append(other)
                        used.add(other_id)

        if len(cluster) > 1:
            clusters.append(cluster)

    return clusters


def consolidate_lessons(dry_run: bool = False) -> dict:
    """Find and link similar lessons."""
    print(f"[maintenance] Loading lessons...")
    lessons = load_lessons()

    if not lessons:
        return {"success": True, "clusters": 0, "linked": 0, "message": "No lessons to consolidate"}

    print(f"[maintenance] Loaded {len(lessons)} lessons")

    # Build/load embeddings
    embeddings = rebuild_embeddings(lessons)

    # Find similar clusters
    print(f"[maintenance] Finding similar lessons...")
    clusters = find_similar_clusters(lessons, embeddings)

    if not clusters:
        return {"success": True, "clusters": 0, "linked": 0, "message": "No similar lessons found"}

    print(f"[maintenance] Found {len(clusters)} clusters of similar lessons")

    # Build lookup by ID
    lessons_by_id = {l.get('id'): l for l in lessons}

    linked_count = 0
    consolidation_log = []

    for cluster in clusters:
        # First lesson is canonical (highest confidence)
        canonical = cluster[0]
        canonical_id = canonical.get('id')

        # Collect all tags from cluster
        all_tags = set(canonical.get('tags', []))
        supersedes = []

        for other in cluster[1:]:
            other_id = other.get('id')
            all_tags.update(other.get('tags', []))
            supersedes.append(other_id)

            # Mark as superseded
            if other_id in lessons_by_id:
                lessons_by_id[other_id]['superseded_by'] = canonical_id
                linked_count += 1

        # Update canonical
        if canonical_id in lessons_by_id:
            lessons_by_id[canonical_id]['tags'] = list(all_tags)
            existing_supersedes = lessons_by_id[canonical_id].get('supersedes', []) or []
            lessons_by_id[canonical_id]['supersedes'] = list(set(existing_supersedes + supersedes))

        consolidation_log.append({
            "canonical": canonical.get('title'),
            "canonical_id": canonical_id,
            "linked": [l.get('title') for l in cluster[1:]],
            "linked_ids": supersedes
        })

    if dry_run:
        print(f"\n[DRY RUN] Would consolidate {len(clusters)} clusters, linking {linked_count} lessons")
        for entry in consolidation_log:
            print(f"\n  Canonical: {entry['canonical']}")
            for linked in entry['linked']:
                print(f"    ← {linked}")
        return {
            "success": True,
            "dry_run": True,
            "clusters": len(clusters),
            "linked": linked_count,
            "details": consolidation_log
        }

    # Save updated lessons
    updated_lessons = list(lessons_by_id.values())
    save_lessons(updated_lessons)

    # Log consolidation
    log_file = LESSONS_DIR / "consolidation.log"
    with open(log_file, 'a') as f:
        f.write(f"\n=== Consolidation {datetime.now().isoformat()} ===\n")
        for entry in consolidation_log:
            f.write(f"Canonical: {entry['canonical_id']} - {entry['canonical']}\n")
            for lid in entry['linked_ids']:
                f.write(f"  ← {lid}\n")

    print(f"\n[maintenance] Consolidated {len(clusters)} clusters, linked {linked_count} lessons")

    return {
        "success": True,
        "clusters": len(clusters),
        "linked": linked_count,
        "details": consolidation_log
    }


def get_stats() -> dict:
    """Get lesson health statistics."""
    lessons = load_lessons()
    embeddings = load_embeddings()

    if not lessons:
        return {
            "success": True,
            "total": 0,
            "clusters": 0,
            "superseded": 0,
            "by_category": {},
            "by_type": {},
            "embeddings_cached": 0,
            "embeddings_missing": 0
        }

    # Count categories and types
    by_category = defaultdict(int)
    by_type = defaultdict(int)
    superseded_count = 0

    for lesson in lessons:
        by_category[lesson.get('category', 'unknown')] += 1
        by_type[lesson.get('type', 'unknown')] += 1
        if lesson.get('superseded_by'):
            superseded_count += 1

    # Count unique clusters (lessons not superseded)
    active_lessons = [l for l in lessons if not l.get('superseded_by')]

    # Check embedding coverage
    lesson_ids = {l.get('id') for l in lessons}
    cached_ids = set(embeddings.keys())

    return {
        "success": True,
        "total": len(lessons),
        "active": len(active_lessons),
        "superseded": superseded_count,
        "by_category": dict(by_category),
        "by_type": dict(by_type),
        "embeddings_cached": len(cached_ids & lesson_ids),
        "embeddings_missing": len(lesson_ids - cached_ids)
    }


def print_stats():
    """Print formatted stats."""
    stats = get_stats()

    print("=== LESSON HEALTH ===")
    print(f"Total lessons: {stats['total']}")
    print(f"Active (not superseded): {stats['active']}")
    print(f"Superseded: {stats['superseded']}")
    print(f"\nBy category:")
    for cat, count in sorted(stats['by_category'].items(), key=lambda x: -x[1]):
        print(f"  {cat}: {count}")
    print(f"\nBy type:")
    for t, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
        print(f"  {t}: {count}")
    print(f"\nEmbedding cache: {stats['embeddings_cached']}/{stats['total']}")
    if stats['embeddings_missing'] > 0:
        print(f"  Missing: {stats['embeddings_missing']} (run 'rebuild-embeddings' to fix)")


def main():
    if len(sys.argv) < 2:
        print("Usage: lesson-maintenance.py <command> [options]")
        print("\nCommands:")
        print("  consolidate [--dry-run]  Find and link similar lessons")
        print("  stats                    Show lesson health statistics")
        print("  rebuild-embeddings       Regenerate embeddings cache")
        sys.exit(1)

    command = sys.argv[1]

    if command == "consolidate":
        dry_run = "--dry-run" in sys.argv
        result = consolidate_lessons(dry_run=dry_run)
        if not dry_run:
            print(json.dumps(result, indent=2))

    elif command == "stats":
        print_stats()

    elif command == "rebuild-embeddings":
        lessons = load_lessons()
        force = "--force" in sys.argv
        rebuild_embeddings(lessons, force=force)

    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
