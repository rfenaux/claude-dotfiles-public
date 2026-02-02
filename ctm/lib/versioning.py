#!/usr/bin/env python3
"""
State Versioning

Provides optimistic concurrency control for CTM state files.
Prevents race conditions when multiple agents modify shared state.

Part of: OpenClaw-inspired improvements (Phase 3, F09)
Created: 2026-01-30
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Callable
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class VersionConflictError(Exception):
    """Raised when state version doesn't match expected."""

    def __init__(self, expected: int, actual: int, path: str):
        self.expected = expected
        self.actual = actual
        self.path = path
        super().__init__(
            f"Version conflict in {path}: expected {expected}, found {actual}. "
            "Reload state and retry."
        )


@dataclass
class VersionedState:
    """State with version metadata."""
    version: int
    data: Any
    last_modified: str
    modified_by: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "_version": self.version,
            "_last_modified": self.last_modified,
            "_modified_by": self.modified_by,
            "data": self.data
        }


class VersionedStore:
    """Versioned JSON file store with optimistic concurrency."""

    def __init__(self, filepath: str):
        """
        Initialize store for a file.

        Args:
            filepath: Path to the JSON file (can use ~)
        """
        self.filepath = Path(filepath).expanduser()

    def read(self) -> VersionedState:
        """
        Read state with version.

        Returns:
            VersionedState with current data and version
        """
        if not self.filepath.exists():
            return VersionedState(
                version=0,
                data={},
                last_modified=datetime.utcnow().isoformat()
            )

        try:
            with open(self.filepath) as f:
                raw = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read {self.filepath}: {e}")
            return VersionedState(
                version=0,
                data={},
                last_modified=datetime.utcnow().isoformat()
            )

        # Handle legacy files without versioning
        if "_version" not in raw:
            return VersionedState(
                version=0,
                data=raw,
                last_modified=raw.get("_last_modified", "")
            )

        return VersionedState(
            version=raw["_version"],
            data=raw.get("data", {}),
            last_modified=raw.get("_last_modified", ""),
            modified_by=raw.get("_modified_by")
        )

    def write(
        self,
        data: Any,
        expected_version: int,
        modifier: str = None
    ) -> int:
        """
        Write state with version check.

        Args:
            data: Data to write
            expected_version: Expected current version
            modifier: Identifier of modifier (e.g., agent ID)

        Returns:
            New version number

        Raises:
            VersionConflictError: If versions don't match
        """
        current = self.read()

        if current.version != expected_version:
            raise VersionConflictError(
                expected_version,
                current.version,
                str(self.filepath)
            )

        new_version = current.version + 1

        state = {
            "_version": new_version,
            "_last_modified": datetime.utcnow().isoformat(),
            "_modified_by": modifier or f"pid-{os.getpid()}",
            "data": data
        }

        # Ensure directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write atomically via temp file
        tmp_path = self.filepath.with_suffix('.tmp')
        try:
            with open(tmp_path, 'w') as f:
                json.dump(state, f, indent=2)
            tmp_path.rename(self.filepath)
        except Exception as e:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        logger.debug(f"Wrote version {new_version} to {self.filepath}")
        return new_version

    def update(
        self,
        updater: Callable[[Any], Any],
        modifier: str = None,
        max_retries: int = 3
    ) -> Any:
        """
        Atomic update with automatic retry on conflict.

        Args:
            updater: Function that takes current data and returns new data
            modifier: Identifier of modifier
            max_retries: Maximum retry attempts

        Returns:
            Updated data

        Raises:
            VersionConflictError: If max retries exceeded
        """
        for attempt in range(max_retries):
            try:
                current = self.read()
                new_data = updater(current.data)
                self.write(new_data, current.version, modifier)
                return new_data
            except VersionConflictError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded for {self.filepath}")
                    raise
                logger.warning(f"Version conflict, retrying ({attempt + 1}/{max_retries})")
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff

    def get_version(self) -> int:
        """Get current version without full data read."""
        return self.read().version

    def exists(self) -> bool:
        """Check if the file exists."""
        return self.filepath.exists()


def migrate_to_versioned(filepath: str, backup: bool = True) -> int:
    """
    Migrate a legacy (non-versioned) file to versioned format.

    Args:
        filepath: Path to the file
        backup: Create backup before migration

    Returns:
        New version number (1)
    """
    path = Path(filepath).expanduser()

    if not path.exists():
        return 0

    with open(path) as f:
        data = json.load(f)

    # Already versioned
    if "_version" in data:
        return data["_version"]

    # Create backup
    if backup:
        backup_path = path.with_suffix(f'.backup-{int(time.time())}')
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Created backup: {backup_path}")

    # Migrate
    versioned = {
        "_version": 1,
        "_last_modified": datetime.utcnow().isoformat(),
        "_modified_by": "migration",
        "data": data
    }

    with open(path, 'w') as f:
        json.dump(versioned, f, indent=2)

    logger.info(f"Migrated {path} to versioned format")
    return 1


def batch_migrate(directory: str, pattern: str = "*.json") -> dict:
    """
    Migrate all JSON files in a directory.

    Args:
        directory: Directory to scan
        pattern: Glob pattern for files

    Returns:
        Dict with migration statistics
    """
    dir_path = Path(directory).expanduser()
    stats = {"migrated": 0, "already_versioned": 0, "failed": 0}

    for filepath in dir_path.glob(pattern):
        try:
            with open(filepath) as f:
                data = json.load(f)

            if "_version" in data:
                stats["already_versioned"] += 1
            else:
                migrate_to_versioned(str(filepath))
                stats["migrated"] += 1
        except Exception as e:
            logger.warning(f"Failed to process {filepath}: {e}")
            stats["failed"] += 1

    return stats


if __name__ == "__main__":
    import sys

    print("State Versioning Utility")
    print("=" * 40)

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "migrate" and len(sys.argv) >= 3:
            filepath = sys.argv[2]
            version = migrate_to_versioned(filepath)
            print(f"✓ Migrated to version {version}")

        elif cmd == "check" and len(sys.argv) >= 3:
            filepath = sys.argv[2]
            store = VersionedStore(filepath)
            state = store.read()
            print(f"File: {filepath}")
            print(f"Version: {state.version}")
            print(f"Last modified: {state.last_modified}")
            print(f"Modified by: {state.modified_by}")

        elif cmd == "migrate-dir" and len(sys.argv) >= 3:
            directory = sys.argv[2]
            stats = batch_migrate(directory)
            print(f"✓ Migrated: {stats['migrated']}")
            print(f"  Already versioned: {stats['already_versioned']}")
            print(f"  Failed: {stats['failed']}")

        else:
            print("\nUsage:")
            print("  versioning.py migrate <filepath>    - Migrate single file")
            print("  versioning.py check <filepath>      - Check file version")
            print("  versioning.py migrate-dir <dir>     - Migrate all JSON in directory")
    else:
        # Demo
        print("\nDemo: Testing optimistic concurrency")

        test_file = "/tmp/versioning-test.json"
        store = VersionedStore(test_file)

        # Write initial data
        store.write({"count": 0}, expected_version=0, modifier="demo")
        print(f"  Initial write: version 1")

        # Update with correct version
        def increment(data):
            data["count"] = data.get("count", 0) + 1
            return data

        store.update(increment, modifier="demo")
        print(f"  Update 1: version {store.get_version()}")

        store.update(increment, modifier="demo")
        print(f"  Update 2: version {store.get_version()}")

        # Try to write with wrong version (should fail)
        try:
            store.write({"count": 999}, expected_version=1, modifier="demo")
            print("  ERROR: Should have raised VersionConflictError")
        except VersionConflictError as e:
            print(f"  ✓ Correctly caught conflict: expected 1, found {e.actual}")

        # Cleanup
        Path(test_file).unlink()
        print("\n✓ Demo complete")
