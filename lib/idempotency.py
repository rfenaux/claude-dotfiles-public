#!/usr/bin/env python3
"""
Hook Idempotency

Prevents duplicate hook execution using time-based keys.
Uses a simple file-based cache with TTL expiration.

Part of: OpenClaw-inspired improvements (Phase 4, F13)
Created: 2026-01-30
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyConfig:
    """Configuration for idempotency cache."""
    cache_dir: str = "~/.claude/cache/idempotency"
    ttl_seconds: int = 300  # 5 minutes
    max_entries: int = 1000


class IdempotencyCache:
    """Cache for idempotency keys to prevent duplicate hook execution."""

    def __init__(self, config: Optional[IdempotencyConfig] = None):
        """
        Initialize the cache.

        Args:
            config: Optional configuration
        """
        self.config = config or IdempotencyConfig()
        self.cache_dir = Path(self.config.cache_dir).expanduser()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "keys.json"
        self._cache = self._load()

    def _load(self) -> dict:
        """Load cache from file."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load cache: {e}")
                return {}
        return {}

    def _save(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f)
        except IOError as e:
            logger.warning(f"Failed to save cache: {e}")

    def _cleanup(self):
        """Remove expired entries and trim to max size."""
        now = time.time()

        # Remove expired
        expired = [
            k for k, v in self._cache.items()
            if now - v > self.config.ttl_seconds
        ]
        for k in expired:
            del self._cache[k]

        # Trim if too many (keep most recent)
        if len(self._cache) > self.config.max_entries:
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k],
                reverse=True
            )
            # Keep only max_entries most recent
            to_remove = sorted_keys[self.config.max_entries:]
            for k in to_remove:
                del self._cache[k]

    def generate_key(self, hook_name: str, context: str) -> str:
        """
        Generate idempotency key from hook name and context.

        Args:
            hook_name: Name of the hook
            context: Context string (e.g., file path, tool input)

        Returns:
            16-character hex key
        """
        content = f"{hook_name}:{context}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def check_and_set(self, key: str) -> bool:
        """
        Check if key exists; if not, set it.

        Args:
            key: The idempotency key

        Returns:
            True if this is a new key (proceed with hook)
            False if key exists (skip hook - duplicate)
        """
        self._cleanup()

        if key in self._cache:
            logger.debug(f"Duplicate key detected: {key}")
            return False  # Already executed

        self._cache[key] = time.time()
        self._save()
        return True  # Proceed

    def check(self, key: str) -> bool:
        """
        Check if key exists without setting.

        Args:
            key: The idempotency key

        Returns:
            True if key exists (was already executed)
            False if key doesn't exist
        """
        self._cleanup()
        return key in self._cache

    def clear(self, key: str = None):
        """
        Clear a specific key or all keys.

        Args:
            key: Optional specific key to clear
        """
        if key:
            self._cache.pop(key, None)
        else:
            self._cache = {}
        self._save()

    def get_stats(self) -> dict:
        """Get cache statistics."""
        self._cleanup()
        return {
            "entries": len(self._cache),
            "max_entries": self.config.max_entries,
            "ttl_seconds": self.config.ttl_seconds
        }


# Module-level singleton
_cache: Optional[IdempotencyCache] = None


def get_cache() -> IdempotencyCache:
    """Get or create the default cache."""
    global _cache
    if _cache is None:
        _cache = IdempotencyCache()
    return _cache


def check_idempotency(hook_name: str, context: str) -> bool:
    """
    Check if hook should execute.

    Args:
        hook_name: Name of the hook
        context: Context string

    Returns:
        True if hook should proceed (first execution)
        False if hook should skip (duplicate)

    Usage in shell scripts:
        if python3 -c "from idempotency import check_idempotency; exit(0 if check_idempotency('$HOOK', '$CTX') else 1)"; then
            # Execute hook
        else
            exit 0  # Skip duplicate
        fi
    """
    cache = get_cache()
    key = cache.generate_key(hook_name, context)
    return cache.check_and_set(key)


def clear_idempotency(hook_name: str = None, context: str = None):
    """Clear idempotency cache."""
    cache = get_cache()
    if hook_name and context:
        key = cache.generate_key(hook_name, context)
        cache.clear(key)
    else:
        cache.clear()


if __name__ == "__main__":
    import sys

    cache = IdempotencyCache()
    stats = cache.get_stats()

    print("Idempotency Cache")
    print("=" * 40)
    print(f"Entries: {stats['entries']}")
    print(f"Max entries: {stats['max_entries']}")
    print(f"TTL: {stats['ttl_seconds']}s")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "check" and len(sys.argv) >= 4:
            hook_name = sys.argv[2]
            context = sys.argv[3]
            result = check_idempotency(hook_name, context)
            print(f"\n{'✓ Proceed' if result else '✗ Skip (duplicate)'}")
            sys.exit(0 if result else 1)

        elif cmd == "clear":
            cache.clear()
            print("\n✓ Cache cleared")

        elif cmd == "stats":
            pass  # Already printed above

        else:
            print("\nUsage:")
            print("  idempotency.py check <hook_name> <context>")
            print("  idempotency.py clear")
            print("  idempotency.py stats")
