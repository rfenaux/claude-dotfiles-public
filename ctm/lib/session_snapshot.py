"""
Session Snapshot Module (CTM v3.0 - Phase 5)

Captures and restores session state for cross-session continuity.
Stores snapshots in ~/.claude/ctm/snapshots/ for enhanced resume context.
"""

import json
import os
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from config import get_ctm_dir
from agents import get_agent, Agent


SNAPSHOTS_DIR = "snapshots"
MAX_SNAPSHOTS_PER_AGENT = 5  # Keep last N snapshots per agent


@dataclass
class SessionSnapshot:
    """Captures session state for resume context."""
    agent_id: str
    timestamp: str  # ISO format

    # Where you stopped
    last_file: Optional[str] = None
    last_line: Optional[int] = None
    last_action: str = "working"  # editing, testing, debugging, reviewing

    # Context
    context_summary: str = ""
    recent_decisions: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    # Next step
    next_step: Optional[str] = None

    # Git context
    last_commit: Optional[str] = None
    uncommitted_files: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionSnapshot":
        return cls(**data)


def get_snapshots_dir() -> Path:
    """Get the snapshots directory, creating if needed."""
    ctm_dir = get_ctm_dir()
    snapshots_dir = ctm_dir / SNAPSHOTS_DIR
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    return snapshots_dir


def get_snapshot_path(agent_id: str) -> Path:
    """Get path to an agent's latest snapshot."""
    return get_snapshots_dir() / f"{agent_id}.json"


def get_last_modified_file(project_path: Optional[str] = None) -> Optional[str]:
    """Get the most recently modified tracked file from git."""
    try:
        cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split('\n')
            return files[0] if files else None
    except Exception:
        pass

    # Fallback: check uncommitted changes
    try:
        cmd = ["git", "diff", "--name-only"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split('\n')
            return files[0] if files else None
    except Exception:
        pass

    return None


def get_uncommitted_files(project_path: Optional[str] = None) -> List[str]:
    """Get list of uncommitted files."""
    try:
        cmd = ["git", "status", "--porcelain"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=5
        )
        if result.returncode == 0:
            files = []
            for line in result.stdout.strip().split('\n'):
                if line and len(line) > 3:
                    files.append(line[3:].strip())
            return files[:10]  # Cap at 10 files
    except Exception:
        pass
    return []


def get_last_commit_message(project_path: Optional[str] = None) -> Optional[str]:
    """Get the last commit message."""
    try:
        cmd = ["git", "log", "-1", "--pretty=%s"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_path,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _extract_decision_texts(decisions: List) -> List[str]:
    """Extract text from decision objects (can be strings or dicts)."""
    texts = []
    for dec in decisions:
        if isinstance(dec, str):
            texts.append(dec)
        elif isinstance(dec, dict) and "text" in dec:
            texts.append(dec["text"])
    return texts


def infer_action_type(agent: Agent) -> str:
    """Infer what type of action was being done based on agent state."""
    current_step = agent.state.get("current_step", "").lower()

    if any(word in current_step for word in ["test", "verify", "check"]):
        return "testing"
    elif any(word in current_step for word in ["debug", "fix", "investigate"]):
        return "debugging"
    elif any(word in current_step for word in ["review", "audit", "analyze"]):
        return "reviewing"
    elif any(word in current_step for word in ["deploy", "release", "ship"]):
        return "deploying"
    elif any(word in current_step for word in ["plan", "design", "architect"]):
        return "planning"
    else:
        return "editing"


def capture_snapshot(
    agent_id: str,
    context_summary: Optional[str] = None,
    open_questions: Optional[List[str]] = None,
    next_step: Optional[str] = None
) -> Optional[SessionSnapshot]:
    """
    Capture a session snapshot for an agent.

    Args:
        agent_id: The agent to capture
        context_summary: Optional AI-generated summary of session
        open_questions: Optional list of unresolved questions
        next_step: Optional suggested next action

    Returns:
        The created snapshot, or None if agent not found
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    project_path = agent.context.get("project_path") if agent.context else None

    # Build snapshot
    snapshot = SessionSnapshot(
        agent_id=agent_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        last_file=get_last_modified_file(project_path),
        last_action=infer_action_type(agent),
        context_summary=context_summary or agent.state.get("current_step", ""),
        recent_decisions=_extract_decision_texts(agent.context.get("decisions", [])[-3:]) if agent.context else [],
        open_questions=open_questions or [],
        next_step=next_step or agent.state.get("next_action"),
        last_commit=get_last_commit_message(project_path),
        uncommitted_files=get_uncommitted_files(project_path)
    )

    # Save snapshot
    save_snapshot(snapshot)

    return snapshot


def save_snapshot(snapshot: SessionSnapshot) -> None:
    """Save a snapshot to disk."""
    path = get_snapshot_path(snapshot.agent_id)

    # Load existing snapshots for this agent
    snapshots = []
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
                if isinstance(data, list):
                    snapshots = data
                else:
                    # Old format - single snapshot
                    snapshots = [data]
        except Exception:
            pass

    # Add new snapshot
    snapshots.append(snapshot.to_dict())

    # Keep only last N snapshots
    snapshots = snapshots[-MAX_SNAPSHOTS_PER_AGENT:]

    # Save
    with open(path, 'w') as f:
        json.dump(snapshots, f, indent=2)


def load_snapshot(agent_id: str) -> Optional[SessionSnapshot]:
    """Load the latest snapshot for an agent."""
    path = get_snapshot_path(agent_id)

    if not path.exists():
        return None

    try:
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, list) and data:
                return SessionSnapshot.from_dict(data[-1])
            elif isinstance(data, dict):
                return SessionSnapshot.from_dict(data)
    except Exception:
        pass

    return None


def load_all_snapshots(agent_id: str) -> List[SessionSnapshot]:
    """Load all snapshots for an agent."""
    path = get_snapshot_path(agent_id)

    if not path.exists():
        return []

    try:
        with open(path) as f:
            data = json.load(f)
            if isinstance(data, list):
                return [SessionSnapshot.from_dict(s) for s in data]
            elif isinstance(data, dict):
                return [SessionSnapshot.from_dict(data)]
    except Exception:
        pass

    return []


def delete_snapshots(agent_id: str) -> bool:
    """Delete all snapshots for an agent."""
    path = get_snapshot_path(agent_id)
    if path.exists():
        path.unlink()
        return True
    return False


def get_recent_snapshots(limit: int = 5) -> List[SessionSnapshot]:
    """Get the most recent snapshots across all agents."""
    snapshots_dir = get_snapshots_dir()
    all_snapshots = []

    for path in snapshots_dir.glob("*.json"):
        try:
            with open(path) as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    all_snapshots.append(SessionSnapshot.from_dict(data[-1]))
                elif isinstance(data, dict):
                    all_snapshots.append(SessionSnapshot.from_dict(data))
        except Exception:
            continue

    # Sort by timestamp descending
    all_snapshots.sort(key=lambda s: s.timestamp, reverse=True)
    return all_snapshots[:limit]
