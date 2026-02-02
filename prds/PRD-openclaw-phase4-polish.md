# PRD: Phase 4 - Polish & Reliability

> **Parent PRD:** `PRD-openclaw-inspired-improvements.md`
> **Created:** 2026-01-30 | **Status:** Ready for Implementation
> **Estimated Effort:** 2 days | **Priority:** Low
> **Depends On:** Phase 1, 2, 3 completed

---

## Overview

Phase 4 focuses on **edge cases**, **performance optimization**, and **reliability improvements**. These are quality-of-life enhancements that polish the system.

### Features in This Phase

| ID | Feature | Impact | Effort |
|----|---------|--------|--------|
| F13 | Idempotency Keys for Hooks | LOW | 2h |
| F15 | Per-Agent SQLite | MEDIUM | 1d |
| F16 | Batch Embedding API | LOW | 2h |
| F20 | Presence Tracking | LOW | 2h |

---

## F13: Idempotency Keys for Hooks

### Problem
Hooks may execute multiple times on retry, causing duplicate operations.

### Solution
Track hook executions with idempotency keys and skip duplicates.

### Implementation

#### 13.1 Create idempotency module

**File:** `~/.claude/lib/idempotency.py`

```python
#!/usr/bin/env python3
"""
Hook Idempotency

Prevents duplicate hook execution using time-based keys.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class IdempotencyConfig:
    cache_dir: str = "~/.claude/cache/idempotency"
    ttl_seconds: int = 300  # 5 minutes
    max_entries: int = 1000

class IdempotencyCache:
    """Cache for idempotency keys."""

    def __init__(self, config: IdempotencyConfig = None):
        self.config = config or IdempotencyConfig()
        self.cache_dir = Path(self.config.cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "keys.json"
        self._cache = self._load()

    def _load(self) -> dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self._cache, f)

    def _cleanup(self):
        """Remove expired entries."""
        now = time.time()
        expired = [
            k for k, v in self._cache.items()
            if now - v > self.config.ttl_seconds
        ]
        for k in expired:
            del self._cache[k]

        # Trim if too many
        if len(self._cache) > self.config.max_entries:
            # Keep most recent
            sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k])
            for k in sorted_keys[:-self.config.max_entries]:
                del self._cache[k]

    def generate_key(self, hook_name: str, context: str) -> str:
        """Generate idempotency key from hook name and context."""
        content = f"{hook_name}:{context}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def check_and_set(self, key: str) -> bool:
        """
        Check if key exists; if not, set it.

        Returns:
            True if this is a new key (proceed with hook)
            False if key exists (skip hook)
        """
        self._cleanup()

        if key in self._cache:
            return False  # Already executed

        self._cache[key] = time.time()
        self._save()
        return True  # Proceed

    def clear(self, key: str = None):
        """Clear a specific key or all keys."""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache = {}
        self._save()

# Default instance
_cache: Optional[IdempotencyCache] = None

def get_cache() -> IdempotencyCache:
    global _cache
    if _cache is None:
        _cache = IdempotencyCache()
    return _cache

def check_idempotency(hook_name: str, context: str) -> bool:
    """
    Check if hook should execute.

    Usage in hook scripts:
        if ! python3 -c "from idempotency import check_idempotency; exit(0 if check_idempotency('$HOOK_NAME', '$CONTEXT') else 1)"; then
            exit 0  # Skip - already executed
        fi
    """
    cache = get_cache()
    key = cache.generate_key(hook_name, context)
    return cache.check_and_set(key)
```

#### 13.2 Create shell helper

**File:** `~/.claude/hooks/lib/idempotency.sh`

```bash
#!/bin/bash
# Idempotency helper for hooks
# Usage: source idempotency.sh; check_idempotency "hook-name" "context-string"

check_idempotency() {
    local hook_name="$1"
    local context="$2"

    python3 -c "
import sys
sys.path.insert(0, '$HOME/.claude/lib')
from idempotency import check_idempotency
result = check_idempotency('$hook_name', '$context')
sys.exit(0 if result else 1)
" 2>/dev/null

    return $?
}
```

### Acceptance Criteria
- [ ] Duplicate hooks detected and skipped
- [ ] Cache cleaned up after TTL
- [ ] No performance impact on normal execution
- [ ] Easy to integrate with existing hooks

---

## F15: Per-Agent SQLite

### Problem
All RAG embeddings in single database can cause cross-contamination.

### Solution
Separate SQLite database per agent for isolated embeddings.

### Implementation

#### 15.1 Update RAG server structure

**Directory:** `~/.claude/rag/agents/`

```
~/.claude/rag/
├── global/           # Shared knowledge (lessons, docs)
│   └── embeddings.sqlite
└── agents/           # Per-agent stores
    ├── worker-abc123.sqlite
    ├── explorer-def456.sqlite
    └── ...
```

#### 15.2 Modify embedding storage

**Update:** `~/.claude/mcp-servers/rag-server/storage.py`

```python
class AgentEmbeddingStore:
    """Per-agent embedding storage."""

    def __init__(self, agent_id: str, base_dir: str = "~/.claude/rag/agents"):
        self.agent_id = agent_id
        self.base_dir = Path(base_dir).expanduser()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / f"{agent_id}.sqlite"
        self._init_db()

    def _init_db(self):
        # Initialize SQLite with sqlite-vec
        pass

    @classmethod
    def get_or_create(cls, agent_id: str) -> "AgentEmbeddingStore":
        # Factory method
        pass

    def add_embeddings(self, documents, embeddings):
        # Store embeddings
        pass

    def search(self, query_embedding, top_k=5):
        # Vector search
        pass

    def delete(self):
        # Remove database
        if self.db_path.exists():
            self.db_path.unlink()
```

### Acceptance Criteria
- [ ] Each agent gets isolated database
- [ ] No cross-contamination of embeddings
- [ ] Cleanup removes agent database
- [ ] Global store still available for shared knowledge

---

## F16: Batch Embedding API

### Problem
Large indexing jobs make many small API calls.

### Solution
Use batch APIs for OpenAI/Gemini to reduce cost and latency.

### Implementation

#### 16.1 Add batch support to providers

**Update:** `~/.claude/mcp-servers/rag-server/embeddings.py`

```python
class OpenAIProvider(EmbeddingProvider):
    # ... existing code ...

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed texts in batches for efficiency."""
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = client.embeddings.create(
                input=batch,
                model=self.model
            )
            all_embeddings.extend([e.embedding for e in response.data])

        return all_embeddings

class GeminiProvider(EmbeddingProvider):
    # ... existing code ...

    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """Embed texts in batches."""
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            result = genai.embed_content(
                model=self.model,
                content=batch,
                task_type="retrieval_document"
            )
            # Handle batch response format
            if isinstance(result['embedding'][0], list):
                all_embeddings.extend(result['embedding'])
            else:
                all_embeddings.append(result['embedding'])

        return all_embeddings
```

### Acceptance Criteria
- [ ] Batch embedding for large jobs
- [ ] Configurable batch size
- [ ] Progress reporting for long jobs
- [ ] Cost savings measured

---

## F20: Presence Tracking

### Problem
Multiple Claude sessions may conflict without awareness of each other.

### Solution
Track active sessions and show presence in status.

### Implementation

#### 20.1 Create presence module

**File:** `~/.claude/lib/presence.py`

```python
#!/usr/bin/env python3
"""
Presence Tracking

Tracks active Claude sessions on the same machine.
"""

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SessionInfo:
    """Information about an active session."""
    pid: int
    session_id: str
    project_path: str
    started_at: float
    last_heartbeat: float
    model: str = "unknown"

class PresenceTracker:
    """Tracks active Claude sessions."""

    HEARTBEAT_INTERVAL = 30  # seconds
    STALE_THRESHOLD = 90  # seconds

    def __init__(self, presence_dir: str = "~/.claude/presence"):
        self.presence_dir = Path(presence_dir).expanduser()
        self.presence_dir.mkdir(parents=True, exist_ok=True)
        self.pid = os.getpid()
        self.session_file = self.presence_dir / f"{self.pid}.json"

    def register(
        self,
        session_id: str,
        project_path: str,
        model: str = "unknown"
    ):
        """Register current session."""
        info = SessionInfo(
            pid=self.pid,
            session_id=session_id,
            project_path=project_path,
            started_at=time.time(),
            last_heartbeat=time.time(),
            model=model
        )

        with open(self.session_file, 'w') as f:
            json.dump({
                "pid": info.pid,
                "session_id": info.session_id,
                "project_path": info.project_path,
                "started_at": info.started_at,
                "last_heartbeat": info.last_heartbeat,
                "model": info.model
            }, f)

    def heartbeat(self):
        """Update heartbeat timestamp."""
        if not self.session_file.exists():
            return

        with open(self.session_file) as f:
            data = json.load(f)

        data["last_heartbeat"] = time.time()

        with open(self.session_file, 'w') as f:
            json.dump(data, f)

    def unregister(self):
        """Remove current session."""
        if self.session_file.exists():
            self.session_file.unlink()

    def get_active_sessions(self) -> List[SessionInfo]:
        """Get all active sessions."""
        sessions = []
        now = time.time()

        for f in self.presence_dir.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)

                # Check if stale
                if now - data["last_heartbeat"] > self.STALE_THRESHOLD:
                    # Clean up stale file
                    f.unlink()
                    continue

                # Check if process still running
                pid = data["pid"]
                try:
                    os.kill(pid, 0)  # Check if process exists
                except OSError:
                    f.unlink()
                    continue

                sessions.append(SessionInfo(**data))
            except:
                continue

        return sessions

    def get_sessions_in_project(self, project_path: str) -> List[SessionInfo]:
        """Get sessions working in same project."""
        return [
            s for s in self.get_active_sessions()
            if s.project_path == project_path and s.pid != self.pid
        ]

    def is_conflict(self, file_path: str) -> bool:
        """Check if another session might be editing this file."""
        # Get project from file path
        file_path = Path(file_path).resolve()

        for session in self.get_active_sessions():
            if session.pid == self.pid:
                continue

            session_project = Path(session.project_path).resolve()
            if str(file_path).startswith(str(session_project)):
                return True

        return False

# Default tracker
_tracker: Optional[PresenceTracker] = None

def get_tracker() -> PresenceTracker:
    global _tracker
    if _tracker is None:
        _tracker = PresenceTracker()
    return _tracker
```

#### 20.2 Add to session start/end hooks

**SessionStart:** Register presence
**SessionEnd:** Unregister presence
**Periodic:** Heartbeat (via background process or hook)

### Acceptance Criteria
- [ ] Sessions registered on start
- [ ] Sessions unregistered on end
- [ ] Stale sessions cleaned up
- [ ] Conflict detection works
- [ ] `/status` shows other sessions

---

## Task Checklist

### F13: Idempotency Keys
- [ ] T13.1: Create idempotency.py module
- [ ] T13.2: Create shell helper
- [ ] T13.3: Create cache directory
- [ ] T13.4: Test duplicate detection
- [ ] T13.5: Add to critical hooks

### F15: Per-Agent SQLite
- [ ] T15.1: Create agents/ directory structure
- [ ] T15.2: Implement AgentEmbeddingStore
- [ ] T15.3: Update RAG server to use per-agent stores
- [ ] T15.4: Add cleanup on agent deletion
- [ ] T15.5: Test isolation

### F16: Batch Embedding API
- [ ] T16.1: Add embed_batch to OpenAIProvider
- [ ] T16.2: Add embed_batch to GeminiProvider
- [ ] T16.3: Update indexing to use batch
- [ ] T16.4: Add progress reporting
- [ ] T16.5: Measure cost savings

### F20: Presence Tracking
- [ ] T20.1: Create presence.py module
- [ ] T20.2: Create presence/ directory
- [ ] T20.3: Add to SessionStart hook
- [ ] T20.4: Add to SessionEnd hook
- [ ] T20.5: Test multi-session detection
- [ ] T20.6: Add to /status output

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Hook duplicate prevention | 100% | Test repeated calls |
| Agent embedding isolation | 100% | Cross-search test |
| Batch API cost savings | 30%+ | Compare billing |
| Presence accuracy | 95%+ | Manual verification |

---

## Rollback Plan

1. Remove idempotency module (hooks still work, may duplicate)
2. Revert to single RAG database
3. Disable batch mode (use single calls)
4. Remove presence tracking
