#!/usr/bin/env python3
"""
analyze-lessons.py - Extract lessons from conversation transcripts via Claude Code CLI

Called by: lesson-extractor.sh (background, detached)
Writes to: ~/.claude/lessons/review/

Usage:
    python3 analyze-lessons.py <conversation-jsonl-file> [session-id]

Uses Claude Code CLI in non-interactive mode (--print), so no separate API key needed.
"""

import os
import sys
import json
import hashlib
import subprocess
import re
import math
from datetime import datetime
from pathlib import Path

# Configuration
LESSONS_DIR = Path.home() / ".claude" / "lessons"
REVIEW_DIR = LESSONS_DIR / "review"
PENDING_DIR = LESSONS_DIR / "pending"
ARCHIVE_DIR = LESSONS_DIR / "archive"
LESSONS_FILE = LESSONS_DIR / "lessons.jsonl"
EMBEDDINGS_FILE = LESSONS_DIR / "embeddings.json"
MODEL = os.environ.get("LESSON_MODEL", "haiku")  # Use haiku for cost-efficiency

# Auto-approval threshold (conservative - user preference)
AUTO_APPROVE_THRESHOLD = 0.91
ARCHIVE_THRESHOLD = 0.70  # Below this = needs validation

# Duplicate detection thresholds
TITLE_SIMILARITY_THRESHOLD = 0.85
EMBEDDING_SIMILARITY_THRESHOLD = 0.85
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "mxbai-embed-large"

# Ensure directories exist
REVIEW_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Duplicate Detection Functions (Hybrid: Title + Embedding Similarity)
# ============================================================================

def normalize_title(title: str) -> str:
    """Normalize title for comparison."""
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


def get_embedding(text: str) -> list:
    """Get embedding vector from Ollama."""
    import urllib.request
    try:
        data = json.dumps({
            "model": EMBEDDING_MODEL,
            "prompt": text[:2000]
        }).encode('utf-8')
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result.get("embedding", [])
    except Exception as e:
        print(f"[analyze-lessons] Embedding failed: {e}", file=sys.stderr)
        return []


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


def load_existing_lessons() -> tuple[list, dict]:
    """Load existing lessons and embeddings cache."""
    lessons = []
    if LESSONS_FILE.exists():
        with open(LESSONS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        lessons.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue

    embeddings = {}
    if EMBEDDINGS_FILE.exists():
        try:
            embeddings = json.loads(EMBEDDINGS_FILE.read_text())
        except:
            pass

    return lessons, embeddings


def save_embedding(lesson_id: str, embedding: list):
    """Save a single embedding to cache."""
    embeddings = {}
    if EMBEDDINGS_FILE.exists():
        try:
            embeddings = json.loads(EMBEDDINGS_FILE.read_text())
        except:
            pass
    embeddings[lesson_id] = embedding
    EMBEDDINGS_FILE.write_text(json.dumps(embeddings))


def is_duplicate(new_lesson: dict, existing_lessons: list, embeddings: dict) -> tuple[bool, str]:
    """
    Check if lesson is duplicate using hybrid approach.
    Returns (is_duplicate, reason).
    """
    new_title = new_lesson.get('title', '')
    new_content = new_lesson.get('lesson', '')
    new_text = f"{new_title}. {new_content}"

    # Phase 1: Fast title similarity check
    for existing in existing_lessons:
        existing_title = existing.get('title', '')
        sim = title_similarity(new_title, existing_title)
        if sim >= TITLE_SIMILARITY_THRESHOLD:
            return True, f"Title match ({sim:.2f}): '{existing_title}'"

    # Phase 2: Embedding similarity check (only if Ollama available)
    new_embedding = get_embedding(new_text)
    if not new_embedding:
        return False, ""  # Skip embedding check if unavailable

    for existing in existing_lessons:
        existing_id = existing.get('id', '')
        existing_embedding = embeddings.get(existing_id)

        if not existing_embedding:
            # Generate embedding for existing lesson if missing
            existing_text = f"{existing.get('title', '')}. {existing.get('lesson', '')}"
            existing_embedding = get_embedding(existing_text)
            if existing_embedding:
                embeddings[existing_id] = existing_embedding

        if existing_embedding:
            sim = cosine_similarity(new_embedding, existing_embedding)
            if sim >= EMBEDDING_SIMILARITY_THRESHOLD:
                return True, f"Embedding match ({sim:.2f}): '{existing.get('title', '')}'"

    return False, ""


EXTRACTION_PROMPT = '''You are a lesson extraction agent. Analyze this conversation transcript and extract project-agnostic lessons learned.

## What to Extract

1. **Technical lessons** (HIGH VALUE)
   - API quirks, tool behaviors, workarounds discovered through trial
   - Error patterns and their solutions
   - Configuration gotchas

2. **User preferences** (MEDIUM VALUE)
   - Communication style preferences
   - Workflow preferences (phasing, formatting, etc.)
   - Implicit requirements revealed through clarification

3. **Problem-solving strategies** (HIGH VALUE)
   - Approaches that worked well
   - Non-obvious solutions discovered
   - Efficiency improvements

4. **Anti-patterns** (HIGH VALUE)
   - Mistakes that wasted time
   - Wrong assumptions to avoid
   - Things NOT to do

## Detection Signals

Look for:
- Multiple attempts before success (iteration)
- Clarifications like "I meant...", "actually...", "not quite..."
- Breakthroughs: "works!", "figured it out", "the trick is..."
- Errors followed by workarounds
- User corrections of Claude's approach

## Output Format

Return ONLY a JSON array of lessons. No markdown, no explanation. Each lesson:

[
  {
    "type": "technical|preference|strategy|antipattern",
    "category": "api|tool|communication|workflow|integration",
    "confidence": 0.5-1.0,
    "title": "Brief imperative summary",
    "context": "When/where this applies",
    "lesson": "The actual learning (1-3 sentences)",
    "rationale": "Why this matters for future conversations",
    "example": "Concrete example from this conversation",
    "tags": ["relevant", "tags"]
  }
]

## Rules

1. Extract 0-5 lessons MAX (quality over quantity)
2. Skip obvious/trivial learnings
3. Focus on REUSABLE knowledge (not project-specific)
4. Each lesson MUST have a concrete example from the transcript
5. If no valuable lessons found, return empty array: []
6. Return ONLY valid JSON - no markdown code blocks, no explanation text

## Conversation Transcript

'''


def parse_conversation(file_path: Path) -> str:
    """Parse JSONL conversation into readable format."""
    messages = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                msg_type = entry.get('type', '')

                if msg_type in ('human', 'user'):
                    content = entry.get('message', {}).get('content') or entry.get('content', '')
                    if isinstance(content, list):
                        content = ' '.join(c.get('text', '') for c in content if c.get('type') == 'text')
                    messages.append(f"USER: {content[:2000]}")  # Truncate long messages

                elif msg_type == 'assistant':
                    content = entry.get('message', {}).get('content') or entry.get('content', '')
                    if isinstance(content, list):
                        text_parts = []
                        for c in content:
                            if c.get('type') == 'text':
                                text_parts.append(c.get('text', ''))
                            elif c.get('type') == 'tool_use':
                                text_parts.append(f"[Tool: {c.get('name', 'unknown')}]")
                        content = ' '.join(text_parts)
                    messages.append(f"ASSISTANT: {content[:2000]}")

            except json.JSONDecodeError:
                continue

    return '\n\n'.join(messages[-100:])  # Last 100 exchanges max


def extract_lessons_via_cli(conversation_text: str, session_id: str, conv_file: str) -> list:
    """Call Claude Code CLI in non-interactive mode to extract lessons."""

    full_prompt = EXTRACTION_PROMPT + conversation_text

    try:
        # Call Claude CLI with --print for non-interactive mode
        result = subprocess.run(
            [
                'claude',
                '--print',
                '--model', MODEL,
                '--no-session-persistence',
                '--dangerously-skip-permissions',
                full_prompt
            ],
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(Path.home())  # Run from home to avoid project-specific settings
        )

        if result.returncode != 0:
            print(f"[analyze-lessons] Claude CLI error: {result.stderr}", file=sys.stderr)
            return []

        text = result.stdout.strip()

        # Handle markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 2:
                text = parts[1]

        text = text.strip()

        # Try to find JSON array
        if not text.startswith('['):
            # Try to find array start
            idx = text.find('[')
            if idx != -1:
                text = text[idx:]
                # Find matching end
                end_idx = text.rfind(']')
                if end_idx != -1:
                    text = text[:end_idx + 1]

        lessons = json.loads(text)

        if not isinstance(lessons, list):
            lessons = [lessons] if lessons else []

        # Add metadata to each lesson
        timestamp = datetime.now().isoformat()
        for lesson in lessons:
            # Generate unique ID
            hash_input = f"{timestamp}{lesson.get('title', '')}{session_id}"
            lesson_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]

            lesson['id'] = f"lesson-{datetime.now().strftime('%Y%m%d')}-{lesson_hash}"
            lesson['source'] = {
                'session_id': session_id,
                'timestamp': timestamp,
                'conversation_file': conv_file
            }
            lesson['metadata'] = {
                'seen_count': 1,
                'last_seen': timestamp,
                'status': 'pending_review',
                'extracted_by': f'claude-{MODEL}',
                'supersedes': None
            }

        return lessons

    except subprocess.TimeoutExpired:
        print("[analyze-lessons] Claude CLI timed out", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"[analyze-lessons] Failed to parse response as JSON: {e}", file=sys.stderr)
        print(f"[analyze-lessons] Raw output: {text[:500]}", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("[analyze-lessons] 'claude' command not found. Is Claude Code installed?", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[analyze-lessons] Error: {e}", file=sys.stderr)
        return []


def save_lessons(lessons: list) -> dict:
    """Save lessons with confidence-based routing and duplicate detection.

    Returns dict with counts: {auto_approved, pending_review, archived, skipped_duplicate}
    """
    counts = {'auto_approved': 0, 'pending_review': 0, 'archived': 0, 'skipped_duplicate': 0}

    # Load existing lessons and embeddings for duplicate detection
    existing_lessons, embeddings = load_existing_lessons()
    print(f"[analyze-lessons] Loaded {len(existing_lessons)} existing lessons for dedup check", file=sys.stderr)

    for lesson in lessons:
        # Check for duplicates first
        is_dup, reason = is_duplicate(lesson, existing_lessons, embeddings)
        if is_dup:
            counts['skipped_duplicate'] += 1
            print(f"[analyze-lessons] SKIPPED DUPLICATE: {lesson.get('title', 'Unknown')}", file=sys.stderr)
            print(f"  Reason: {reason}", file=sys.stderr)
            continue
        lesson_id = lesson.get('id', f"lesson-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        filename = f"{lesson_id}.json"
        confidence = lesson.get('confidence', 0.5)
        timestamp = datetime.now().isoformat()

        if confidence >= AUTO_APPROVE_THRESHOLD:
            # HIGH CONFIDENCE: Auto-approve and add to lessons.jsonl
            lesson['status'] = 'approved'
            lesson['approved_at'] = timestamp
            lesson['metadata']['status'] = 'approved'
            lesson['metadata']['auto_approved'] = True
            lesson['metadata']['approval_reason'] = f'confidence >= {AUTO_APPROVE_THRESHOLD}'

            # Append to lessons.jsonl
            with open(LESSONS_FILE, 'a') as f:
                f.write(json.dumps(lesson) + '\n')

            counts['auto_approved'] += 1
            print(f"[analyze-lessons] AUTO-APPROVED (conf={confidence:.2f}): {lesson.get('title', 'Unknown')}", file=sys.stderr)

            # Save embedding for future duplicate detection
            new_text = f"{lesson.get('title', '')}. {lesson.get('lesson', '')}"
            new_embedding = get_embedding(new_text)
            if new_embedding:
                save_embedding(lesson_id, new_embedding)

            # Also index to RAG if available
            _index_lesson_to_rag(lesson)

            # Add to existing lessons list to catch duplicates within same batch
            existing_lessons.append(lesson)

        elif confidence >= ARCHIVE_THRESHOLD:
            # MEDIUM CONFIDENCE: Queue for manual review
            filepath = REVIEW_DIR / filename
            with open(filepath, 'w') as f:
                json.dump(lesson, f, indent=2)

            counts['pending_review'] += 1
            print(f"[analyze-lessons] PENDING REVIEW (conf={confidence:.2f}): {lesson.get('title', 'Unknown')}", file=sys.stderr)

        else:
            # LOW CONFIDENCE: Archive (needs validation)
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            lesson['metadata']['status'] = 'archived'
            lesson['metadata']['archive_reason'] = f'confidence < {ARCHIVE_THRESHOLD}'
            filepath = ARCHIVE_DIR / filename

            with open(filepath, 'w') as f:
                json.dump(lesson, f, indent=2)

            counts['archived'] += 1
            print(f"[analyze-lessons] ARCHIVED (conf={confidence:.2f}): {lesson.get('title', 'Unknown')}", file=sys.stderr)

    return counts


def _index_lesson_to_rag(lesson: dict):
    """Index auto-approved lesson to RAG for searchability."""
    try:
        # Check if RAG is initialized for lessons
        rag_dir = LESSONS_DIR / ".rag"
        if not rag_dir.exists():
            print("[analyze-lessons] RAG not initialized for lessons, skipping indexing", file=sys.stderr)
            return

        # Create a temporary markdown file for indexing
        lesson_md = f"""# {lesson.get('title', 'Untitled Lesson')}

**Type:** {lesson.get('type', 'unknown')} | **Category:** {lesson.get('category', 'unknown')} | **Confidence:** {lesson.get('confidence', 0)}

## Context
{lesson.get('context', 'N/A')}

## Lesson
{lesson.get('lesson', 'N/A')}

## Rationale
{lesson.get('rationale', 'N/A')}

## Example
{lesson.get('example', 'N/A')}

**Tags:** {', '.join(lesson.get('tags', []))}
"""
        # Write temp file
        temp_file = LESSONS_DIR / f".temp_{lesson.get('id', 'lesson')}.md"
        temp_file.write_text(lesson_md)

        # Call RAG index
        subprocess.run(
            ['rag', 'index', str(temp_file), '--project', str(LESSONS_DIR)],
            capture_output=True,
            timeout=30
        )

        # Cleanup temp file
        temp_file.unlink(missing_ok=True)

        print(f"[analyze-lessons] Indexed to RAG: {lesson.get('id')}", file=sys.stderr)

    except Exception as e:
        print(f"[analyze-lessons] RAG indexing failed: {e}", file=sys.stderr)


def cleanup_pending_marker(conv_file: str):
    """Remove the pending analysis marker if it exists."""
    for marker in PENDING_DIR.glob("*.json"):
        try:
            with open(marker) as f:
                data = json.load(f)
            if data.get('conversation_file') == conv_file:
                marker.unlink()
                print(f"[analyze-lessons] Removed pending marker: {marker.name}", file=sys.stderr)
                break
        except (json.JSONDecodeError, KeyError):
            continue


def main():
    if len(sys.argv) < 2:
        print("Usage: analyze-lessons.py <conversation-file> [session-id]", file=sys.stderr)
        sys.exit(1)

    conv_file = sys.argv[1]
    session_id = sys.argv[2] if len(sys.argv) > 2 else "unknown"

    if not os.path.exists(conv_file):
        print(f"[analyze-lessons] File not found: {conv_file}", file=sys.stderr)
        sys.exit(1)

    print(f"[analyze-lessons] Analyzing: {conv_file}", file=sys.stderr)
    print(f"[analyze-lessons] Using Claude CLI with model: {MODEL}", file=sys.stderr)

    # Parse conversation
    conversation_text = parse_conversation(Path(conv_file))

    if len(conversation_text) < 500:
        print("[analyze-lessons] Conversation too short, skipping", file=sys.stderr)
        sys.exit(0)

    # Extract lessons via Claude CLI
    lessons = extract_lessons_via_cli(conversation_text, session_id, conv_file)

    if not lessons:
        print("[analyze-lessons] No lessons extracted", file=sys.stderr)
        cleanup_pending_marker(conv_file)
        sys.exit(0)

    # Save with confidence-based routing
    counts = save_lessons(lessons)
    total = sum(counts.values())

    print(f"[analyze-lessons] Processed {total} lesson(s):", file=sys.stderr)
    print(f"  - Auto-approved (≥{AUTO_APPROVE_THRESHOLD}): {counts['auto_approved']}", file=sys.stderr)
    print(f"  - Pending review: {counts['pending_review']}", file=sys.stderr)
    print(f"  - Archived (<{ARCHIVE_THRESHOLD}): {counts['archived']}", file=sys.stderr)
    print(f"  - Skipped (duplicate): {counts['skipped_duplicate']}", file=sys.stderr)

    # Cleanup pending marker
    cleanup_pending_marker(conv_file)

    if counts['pending_review'] > 0:
        print("[analyze-lessons] Run 'cc lessons review' to review pending lessons.", file=sys.stderr)
    else:
        print("[analyze-lessons] Done. All lessons processed automatically.", file=sys.stderr)


if __name__ == "__main__":
    main()
