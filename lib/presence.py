#!/usr/bin/env python3
"""
Presence Tracking

Tracks active Claude sessions on the same machine.
Enables conflict detection and multi-session awareness.

Part of: OpenClaw-inspired improvements (Phase 4, F20)
Created: 2026-01-30
"""

import json
import os
import time
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Information about an active session."""
    pid: int
    session_id: str
    project_path: str
    started_at: float
    last_heartbeat: float
    model: str = "unknown"
    user: str = ""

    def age_seconds(self) -> float:
        """Get session age in seconds."""
        return time.time() - self.started_at

    def heartbeat_age(self) -> float:
        """Get time since last heartbeat."""
        return time.time() - self.last_heartbeat

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "session_id": self.session_id,
            "project_path": self.project_path,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
            "model": self.model,
            "user": self.user
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionInfo":
        return cls(**data)


class PresenceTracker:
    """Tracks active Claude sessions."""

    HEARTBEAT_INTERVAL = 30  # seconds
    STALE_THRESHOLD = 90  # seconds - session considered dead if no heartbeat

    def __init__(self, presence_dir: str = "~/.claude/presence"):
        """
        Initialize tracker.

        Args:
            presence_dir: Directory for presence files
        """
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
        """
        Register current session.

        Args:
            session_id: Unique session identifier
            project_path: Path to the project directory
            model: Model being used
        """
        info = SessionInfo(
            pid=self.pid,
            session_id=session_id,
            project_path=str(Path(project_path).resolve()),
            started_at=time.time(),
            last_heartbeat=time.time(),
            model=model,
            user=os.getenv("USER", "")
        )

        with open(self.session_file, 'w') as f:
            json.dump(info.to_dict(), f, indent=2)

        logger.info(f"Registered session {session_id} (PID {self.pid})")

    def heartbeat(self):
        """Update heartbeat timestamp."""
        if not self.session_file.exists():
            return

        try:
            with open(self.session_file) as f:
                data = json.load(f)

            data["last_heartbeat"] = time.time()

            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Heartbeat failed: {e}")

    def unregister(self):
        """Remove current session."""
        if self.session_file.exists():
            try:
                self.session_file.unlink()
                logger.info(f"Unregistered session (PID {self.pid})")
            except Exception as e:
                logger.warning(f"Failed to unregister: {e}")

    def get_active_sessions(self, cleanup: bool = True) -> List[SessionInfo]:
        """
        Get all active sessions.

        Args:
            cleanup: Remove stale sessions

        Returns:
            List of active SessionInfo objects
        """
        sessions = []
        now = time.time()
        to_remove = []

        for f in self.presence_dir.glob("*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)

                info = SessionInfo.from_dict(data)

                # Check if stale
                if now - info.last_heartbeat > self.STALE_THRESHOLD:
                    to_remove.append(f)
                    continue

                # Check if process still running
                try:
                    os.kill(info.pid, 0)  # Signal 0 = check existence
                except OSError:
                    to_remove.append(f)
                    continue

                sessions.append(info)

            except Exception as e:
                logger.debug(f"Failed to read {f}: {e}")
                continue

        # Cleanup stale files
        if cleanup:
            for f in to_remove:
                try:
                    f.unlink()
                    logger.debug(f"Removed stale presence file: {f}")
                except:
                    pass

        return sessions

    def get_sessions_in_project(self, project_path: str) -> List[SessionInfo]:
        """
        Get sessions working in the same project.

        Args:
            project_path: Path to the project

        Returns:
            List of SessionInfo (excluding current session)
        """
        project_path = str(Path(project_path).resolve())
        return [
            s for s in self.get_active_sessions()
            if s.project_path == project_path and s.pid != self.pid
        ]

    def is_project_busy(self, project_path: str) -> bool:
        """Check if another session is working in the project."""
        return len(self.get_sessions_in_project(project_path)) > 0

    def get_file_conflict(self, file_path: str) -> Optional[SessionInfo]:
        """
        Check if another session might be editing a file.

        Args:
            file_path: Path to the file

        Returns:
            SessionInfo of conflicting session, or None
        """
        file_path = Path(file_path).resolve()

        for session in self.get_active_sessions():
            if session.pid == self.pid:
                continue

            session_project = Path(session.project_path).resolve()
            if str(file_path).startswith(str(session_project)):
                return session

        return None

    def get_summary(self) -> dict:
        """Get summary of active sessions."""
        sessions = self.get_active_sessions()

        by_project = {}
        for s in sessions:
            project = s.project_path
            if project not in by_project:
                by_project[project] = []
            by_project[project].append(s)

        return {
            "total_sessions": len(sessions),
            "current_pid": self.pid,
            "by_project": {
                p: len(ss) for p, ss in by_project.items()
            },
            "sessions": [s.to_dict() for s in sessions]
        }


# Module-level singleton
_tracker: Optional[PresenceTracker] = None


def get_tracker() -> PresenceTracker:
    """Get or create the default tracker."""
    global _tracker
    if _tracker is None:
        _tracker = PresenceTracker()
    return _tracker


def register_session(session_id: str, project_path: str, model: str = "unknown"):
    """Register the current session."""
    get_tracker().register(session_id, project_path, model)


def unregister_session():
    """Unregister the current session."""
    get_tracker().unregister()


def heartbeat():
    """Update session heartbeat."""
    get_tracker().heartbeat()


def get_active_sessions() -> List[SessionInfo]:
    """Get all active sessions."""
    return get_tracker().get_active_sessions()


if __name__ == "__main__":
    import sys

    tracker = PresenceTracker()
    summary = tracker.get_summary()

    print("Session Presence Tracker")
    print("=" * 40)
    print(f"Active sessions: {summary['total_sessions']}")
    print(f"Current PID: {summary['current_pid']}")

    if summary['by_project']:
        print("\nSessions by project:")
        for project, count in summary['by_project'].items():
            print(f"  {project}: {count} session(s)")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "register" and len(sys.argv) >= 4:
            session_id = sys.argv[2]
            project_path = sys.argv[3]
            model = sys.argv[4] if len(sys.argv) > 4 else "unknown"
            tracker.register(session_id, project_path, model)
            print(f"\n✓ Registered session {session_id}")

        elif cmd == "unregister":
            tracker.unregister()
            print("\n✓ Unregistered")

        elif cmd == "heartbeat":
            tracker.heartbeat()
            print("\n✓ Heartbeat updated")

        elif cmd == "list":
            sessions = tracker.get_active_sessions()
            print(f"\n{len(sessions)} active session(s):")
            for s in sessions:
                age = int(s.age_seconds())
                hb_age = int(s.heartbeat_age())
                me = " (me)" if s.pid == tracker.pid else ""
                print(f"  PID {s.pid}{me}: {s.session_id[:12]}...")
                print(f"    Project: {s.project_path}")
                print(f"    Age: {age}s, Last heartbeat: {hb_age}s ago")

        elif cmd == "check" and len(sys.argv) >= 3:
            project_path = sys.argv[2]
            others = tracker.get_sessions_in_project(project_path)
            if others:
                print(f"\n⚠ {len(others)} other session(s) in this project:")
                for s in others:
                    print(f"  PID {s.pid}: {s.session_id[:12]}...")
            else:
                print("\n✓ No other sessions in this project")

        else:
            print("\nUsage:")
            print("  presence.py register <session_id> <project_path> [model]")
            print("  presence.py unregister")
            print("  presence.py heartbeat")
            print("  presence.py list")
            print("  presence.py check <project_path>")
