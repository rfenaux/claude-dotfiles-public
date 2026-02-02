"""
CTM Agent Management

Handles CRUD operations for agents (task contexts) including:
- Creating new agents from task descriptions
- Loading/saving agent state
- Managing the agent index
- Agent lifecycle (active → paused → completed)
"""

import json
import os
import uuid
import tempfile
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

from config import get_ctm_dir


class AgentStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AgentPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


@dataclass
class Agent:
    """Represents a task context (agent) in the CTM system."""

    id: str
    task: Dict[str, Any]
    context: Dict[str, Any]
    state: Dict[str, Any]
    priority: Dict[str, Any]
    timing: Dict[str, Any]
    triggers: List[str]
    outputs: Dict[str, Any]
    metadata: Dict[str, Any]
    checkpoints: Dict[str, Any] = field(default_factory=dict)  # Inline checkpoint history

    @classmethod
    def create(
        cls,
        title: str,
        goal: str,
        project: Optional[str] = None,
        priority_level: str = "normal",
        tags: Optional[List[str]] = None,
        triggers: Optional[List[str]] = None,
        source: Optional[Dict[str, Any]] = None
    ) -> 'Agent':
        """Create a new agent with default values.

        Args:
            source: Optional source tracking dict with keys:
                - type: 'claude-session' | 'fathom-transcript' | 'email' | 'manual'
                - reference_id: Optional ID (meeting_id, session_id, etc.)
                - timestamp: When task was extracted (ISO format)
                - extracted_by: Tool/skill that created task
        """
        now = datetime.utcnow().isoformat() + "Z"
        agent_id = str(uuid.uuid4())[:8]

        # Build source with defaults
        default_source = {
            "type": "claude-session",
            "reference_id": None,
            "timestamp": now,
            "extracted_by": "ctm-spawn"
        }
        if source:
            default_source.update(source)

        return cls(
            id=agent_id,
            task={
                "title": title,
                "goal": goal,
                "acceptance_criteria": [],
                "dependencies": [],
                "blockers": []
            },
            context={
                "project": project or os.getcwd(),
                "key_files": [],
                "decisions": [],
                "learnings": []
            },
            state={
                "status": AgentStatus.ACTIVE.value,
                "progress_pct": 0,
                "current_step": None,
                "pending_actions": [],
                "last_error": None
            },
            priority={
                "level": priority_level,
                "urgency": 0.5,
                "value": 0.5,
                "novelty": 1.0,
                "user_signal": 0.0,
                "computed_score": 0.5
            },
            timing={
                "created_at": now,
                "last_active": now,
                "total_active_seconds": 0,
                "session_count": 1,
                "estimated_remaining": None
            },
            triggers=triggers or [],
            outputs={
                "files_created": [],
                "files_modified": [],
                "commits": [],
                "summary": None
            },
            metadata={
                "tags": tags or [],
                "parent_agent": None,
                "child_agents": [],
                "source": default_source,
                "version": "1.0.0"
            }
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def _migrate_v0_to_v1(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate v0 (flat) schema to v1 (nested) schema.

        v0 schema had flat fields: title, status, progress, checkpoints, blockers, etc.
        v1 schema has nested: task, context, state, priority, timing, triggers, outputs, metadata
        """
        from datetime import datetime
        now = datetime.utcnow().isoformat() + "Z"

        # Extract v0 fields with defaults
        agent_id = data.get('id', 'unknown')
        title = data.get('title', 'Untitled Task')
        project = data.get('project', '')
        status = data.get('status', 'active')
        progress = data.get('progress', 0)
        created = data.get('created', now)
        last_active = data.get('last_active', now)
        deadline = data.get('deadline')
        tags = data.get('tags', [])
        blockers = data.get('blockers', [])
        next_actions = data.get('next_actions', [])
        checkpoints = data.get('checkpoints', [])
        old_context = data.get('context', {})

        # Build v1 structure
        return {
            'id': agent_id,
            'task': {
                'title': title,
                'goal': old_context.get('deliverable', title),
                'acceptance_criteria': [],
                'dependencies': [],
                'blockers': blockers
            },
            'context': {
                'project': project,
                'key_files': [],
                'decisions': [],
                'learnings': [],
                # Preserve v0 context data
                'legacy': old_context
            },
            'state': {
                'status': status,
                'progress_pct': progress,
                'current_step': next_actions[0] if next_actions else None,
                'pending_actions': next_actions,
                'last_error': None,
                # Preserve checkpoints in state
                'checkpoints': checkpoints
            },
            'priority': {
                'level': data.get('priority', 'normal') if isinstance(data.get('priority'), str) else 'normal',
                'urgency': 0.8 if deadline else 0.5,
                'value': 0.5,
                'novelty': 0.0,  # Migrated agent, not novel
                'user_signal': 0.0,
                'computed_score': 0.7 if deadline else 0.5
            },
            'timing': {
                'created_at': created,
                'last_active': last_active,
                'total_active_seconds': 0,
                'session_count': 1,
                'estimated_remaining': None,
                'deadline': deadline
            },
            'triggers': [],
            'outputs': {
                'files_created': [],
                'files_modified': [],
                'commits': [],
                'summary': None
            },
            'metadata': {
                'tags': tags,
                'parent_agent': None,
                'child_agents': [],
                'version': '1.0.0',
                'migrated_from': 'v0',
                'migration_date': now
            }
        }

    @classmethod
    def _is_v0_schema(cls, data: Dict[str, Any]) -> bool:
        """Detect if data uses v0 (flat) schema."""
        v0_markers = {'title', 'status', 'progress', 'checkpoints', 'blockers', 'next_actions'}
        v1_markers = {'task', 'state', 'timing', 'outputs', 'metadata'}

        has_v0 = bool(v0_markers & set(data.keys()))
        has_v1 = bool(v1_markers & set(data.keys()))

        return has_v0 and not has_v1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Agent':
        """Create agent from dictionary.

        Handles schema migration and filters unexpected fields.
        """
        import sys

        # Check for v0 schema and migrate if needed
        if cls._is_v0_schema(data):
            agent_id = data.get('id', 'unknown')
            print(f"[CTM] Migrating agent {agent_id} from v0 to v1 schema", file=sys.stderr)
            data = cls._migrate_v0_to_v1(data)

        # Expected fields for the Agent dataclass
        required_fields = {'id', 'task', 'context', 'state', 'priority',
                          'timing', 'triggers', 'outputs', 'metadata'}
        optional_fields = {'checkpoints'}  # Fields with defaults
        expected_fields = required_fields | optional_fields

        # Filter to only expected fields
        filtered_data = {k: v for k, v in data.items() if k in expected_fields}

        # Log warning if we had to filter fields (only for non-migrated unexpected fields)
        unexpected = set(data.keys()) - expected_fields
        if unexpected:
            print(f"[CTM] Warning: Agent {data.get('id', 'unknown')} has unexpected fields: {unexpected}",
                  file=sys.stderr)

        # Check for missing required fields only (not optional)
        missing = required_fields - set(filtered_data.keys())
        if missing:
            raise ValueError(f"Agent {data.get('id', 'unknown')} missing required fields: {missing}")

        # Set defaults for optional fields
        if 'checkpoints' not in filtered_data:
            filtered_data['checkpoints'] = {}

        return cls(**filtered_data)

    def save(self) -> Path:
        """Save agent to file using atomic write with validation.

        Uses write-to-temp-then-rename pattern to prevent corruption
        from interrupted writes or concurrent access.
        """
        agents_dir = get_ctm_dir() / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)

        filepath = agents_dir / f"{self.id}.json"

        # Serialize to dict first
        data = self.to_dict()

        # Atomic write: temp file -> validate -> rename
        fd, temp_path = tempfile.mkstemp(
            suffix='.json',
            prefix=f'.{self.id}_',
            dir=agents_dir
        )
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=2)

            # Validate written JSON before committing
            with open(temp_path, 'r') as f:
                validated = json.load(f)

            # Verify key fields survived round-trip
            if validated.get('id') != self.id:
                raise ValueError(f"JSON validation failed: id mismatch")

            # Atomic rename (on POSIX, this is atomic)
            shutil.move(temp_path, filepath)

        except Exception as e:
            # Clean up temp file on failure
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise RuntimeError(f"Failed to save agent {self.id}: {e}") from e

        return filepath

    @classmethod
    def load(cls, agent_id: str) -> Optional['Agent']:
        """Load agent from file."""
        filepath = get_ctm_dir() / "agents" / f"{agent_id}.json"
        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            data = json.load(f)

        return cls.from_dict(data)

    def update_activity(self) -> None:
        """Update last_active timestamp."""
        self.timing["last_active"] = datetime.utcnow().isoformat() + "Z"

    def set_status(self, status: AgentStatus) -> None:
        """Update agent status."""
        self.state["status"] = status.value
        self.update_activity()

    def add_progress(self, step: str, pct: int) -> None:
        """Update progress information."""
        self.state["current_step"] = step
        self.state["progress_pct"] = min(100, max(0, pct))
        self.update_activity()

    def add_decision(self, decision: str) -> None:
        """Add a decision to the context."""
        self.context["decisions"].append({
            "text": decision,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    def add_learning(self, learning: str) -> None:
        """Add a learning to the context."""
        self.context["learnings"].append({
            "text": learning,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })


class AgentIndex:
    """Manages the global agent index for fast lookups."""

    def __init__(self):
        self.index_path = get_ctm_dir() / "index.json"
        self._data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load index from file."""
        default_structure = {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "total_agents": 0,
            "agents": {},
            "by_project": {},
            "by_status": {
                "active": [],
                "paused": [],
                "blocked": [],
                "completed": [],
                "cancelled": [],
                "pending": []
            }
        }

        if not self.index_path.exists():
            return default_structure

        with open(self.index_path, 'r') as f:
            data = json.load(f)

        # Ensure all required keys exist (schema migration/repair)
        for key, default_value in default_structure.items():
            if key not in data:
                data[key] = default_value

        # Ensure all status categories exist in by_status
        for status in default_structure["by_status"]:
            if status not in data["by_status"]:
                data["by_status"][status] = []

        return data

    def save(self) -> None:
        """Save index to file using atomic write with validation."""
        self._data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: temp file -> validate -> rename
        fd, temp_path = tempfile.mkstemp(
            suffix='.json',
            prefix='.index_',
            dir=self.index_path.parent
        )
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(self._data, f, indent=2)

            # Validate written JSON
            with open(temp_path, 'r') as f:
                json.load(f)  # Will raise if invalid

            # Atomic rename
            shutil.move(temp_path, self.index_path)

        except Exception as e:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise RuntimeError(f"Failed to save index: {e}") from e

    def add(self, agent: Agent) -> None:
        """Add agent to index."""
        # Add to main agents dict
        self._data["agents"][agent.id] = {
            "title": agent.task["title"],
            "project": agent.context["project"],
            "status": agent.state["status"],
            "priority_score": agent.priority["computed_score"],
            "last_active": agent.timing["last_active"],
            "tags": agent.metadata["tags"]
        }

        # Add to by_project index
        project = agent.context["project"]
        if project not in self._data["by_project"]:
            self._data["by_project"][project] = []
        if agent.id not in self._data["by_project"][project]:
            self._data["by_project"][project].append(agent.id)

        # Add to by_status index
        status = agent.state["status"]
        if agent.id not in self._data["by_status"][status]:
            self._data["by_status"][status].append(agent.id)

        self._data["total_agents"] = len(self._data["agents"])
        self.save()

    def update(self, agent: Agent) -> None:
        """Update agent in index."""
        if agent.id not in self._data["agents"]:
            self.add(agent)
            return

        old_status = self._data["agents"][agent.id]["status"]
        new_status = agent.state["status"]

        # Update main entry
        self._data["agents"][agent.id] = {
            "title": agent.task["title"],
            "project": agent.context["project"],
            "status": new_status,
            "priority_score": agent.priority["computed_score"],
            "last_active": agent.timing["last_active"],
            "tags": agent.metadata["tags"]
        }

        # Update by_status if changed
        if old_status != new_status:
            if agent.id in self._data["by_status"][old_status]:
                self._data["by_status"][old_status].remove(agent.id)
            if agent.id not in self._data["by_status"][new_status]:
                self._data["by_status"][new_status].append(agent.id)

        self.save()

    def remove(self, agent_id: str) -> None:
        """Remove agent from index."""
        if agent_id not in self._data["agents"]:
            return

        agent_info = self._data["agents"][agent_id]

        # Remove from by_project
        project = agent_info["project"]
        if project in self._data["by_project"]:
            if agent_id in self._data["by_project"][project]:
                self._data["by_project"][project].remove(agent_id)

        # Remove from by_status
        status = agent_info["status"]
        if agent_id in self._data["by_status"][status]:
            self._data["by_status"][status].remove(agent_id)

        # Remove from main dict
        del self._data["agents"][agent_id]
        self._data["total_agents"] = len(self._data["agents"])

        self.save()

    def get_by_status(self, status: str) -> List[str]:
        """Get agent IDs by status."""
        return self._data["by_status"].get(status, [])

    def get_by_project(self, project: str) -> List[str]:
        """Get agent IDs by project."""
        return self._data["by_project"].get(project, [])

    def get_all_active(self) -> List[str]:
        """Get all active agent IDs (active + paused + blocked)."""
        active = self._data["by_status"].get("active", [])
        paused = self._data["by_status"].get("paused", [])
        blocked = self._data["by_status"].get("blocked", [])
        return active + paused + blocked

    def get_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent info from index without loading full agent."""
        return self._data["agents"].get(agent_id)

    @property
    def total(self) -> int:
        return self._data["total_agents"]


def create_agent(
    title: str,
    goal: str,
    project: Optional[str] = None,
    priority: str = "normal",
    tags: Optional[List[str]] = None,
    triggers: Optional[List[str]] = None,
    source: Optional[Dict[str, Any]] = None
) -> Agent:
    """Create and register a new agent.

    Args:
        source: Optional source tracking dict with keys:
            - type: 'claude-session' | 'fathom-transcript' | 'email' | 'manual'
            - reference_id: Optional ID (meeting_id, session_id, etc.)
            - timestamp: When task was extracted
            - extracted_by: Tool/skill that created task
    """
    agent = Agent.create(
        title=title,
        goal=goal,
        project=project,
        priority_level=priority,
        tags=tags,
        triggers=triggers,
        source=source
    )

    # Save agent file
    agent.save()

    # Update index
    index = AgentIndex()
    index.add(agent)

    return agent


# Agent cache for reducing file I/O
_agent_cache: Dict[str, Agent] = {}
_agent_cache_mtime: Dict[str, float] = {}
_MAX_CACHE_SIZE = 20


def get_agent(agent_id: str, use_cache: bool = True) -> Optional[Agent]:
    """
    Load an agent by ID with optional caching.

    Args:
        agent_id: The agent ID to load
        use_cache: If True, use cached version if available and fresh

    Returns:
        Agent instance or None if not found
    """
    filepath = get_ctm_dir() / "agents" / f"{agent_id}.json"

    if not filepath.exists():
        # Remove from cache if it was there
        _agent_cache.pop(agent_id, None)
        _agent_cache_mtime.pop(agent_id, None)
        return None

    current_mtime = filepath.stat().st_mtime

    # Check cache
    if use_cache and agent_id in _agent_cache:
        if _agent_cache_mtime.get(agent_id) == current_mtime:
            return _agent_cache[agent_id]

    # Load from file
    agent = Agent.load(agent_id)
    if agent:
        # Evict oldest if cache is full
        if len(_agent_cache) >= _MAX_CACHE_SIZE:
            oldest = next(iter(_agent_cache))
            del _agent_cache[oldest]
            del _agent_cache_mtime[oldest]

        _agent_cache[agent_id] = agent
        _agent_cache_mtime[agent_id] = current_mtime

    return agent


def invalidate_agent_cache(agent_id: Optional[str] = None) -> None:
    """
    Invalidate agent cache.

    Args:
        agent_id: Specific agent to invalidate, or None to clear all
    """
    if agent_id:
        _agent_cache.pop(agent_id, None)
        _agent_cache_mtime.pop(agent_id, None)
    else:
        _agent_cache.clear()
        _agent_cache_mtime.clear()


def list_agents(
    status: Optional[str] = None,
    project: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List agents with optional filters."""
    index = AgentIndex()

    if status:
        agent_ids = index.get_by_status(status)
    elif project:
        agent_ids = index.get_by_project(project)
    else:
        agent_ids = list(index._data["agents"].keys())

    return [index.get_info(aid) | {"id": aid} for aid in agent_ids if index.get_info(aid)]


def update_agent(agent: Agent) -> None:
    """Save agent and update index."""
    agent.save()
    # Invalidate cache for this agent so next get_agent loads fresh
    invalidate_agent_cache(agent.id)
    index = AgentIndex()
    index.update(agent)


def delete_agent(agent_id: str) -> bool:
    """Delete an agent and remove from index."""
    agent_file = get_ctm_dir() / "agents" / f"{agent_id}.json"

    if agent_file.exists():
        agent_file.unlink()

    # Invalidate cache
    invalidate_agent_cache(agent_id)

    index = AgentIndex()
    index.remove(agent_id)

    return True


# === Shared Memory Integration (v2.1) ===

def share_agent_decision(agent_id: str, decision: str, tags: Optional[List[str]] = None) -> Optional[str]:
    """
    Share a decision from an agent to the project's shared memory pool.

    Other agents in the same project can then access this decision.
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    try:
        from shared_memory import share_decision
        project = agent.context.get("project", "")
        agent_tags = agent.metadata.get("tags", [])
        all_tags = list(set((tags or []) + agent_tags))

        return share_decision(agent_id, decision, project, all_tags)
    except ImportError:
        return None


def share_agent_learning(agent_id: str, learning: str, tags: Optional[List[str]] = None) -> Optional[str]:
    """
    Share a learning from an agent to the project's shared memory pool.
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    try:
        from shared_memory import share_learning
        project = agent.context.get("project", "")
        agent_tags = agent.metadata.get("tags", [])
        all_tags = list(set((tags or []) + agent_tags))

        return share_learning(agent_id, learning, project, all_tags)
    except ImportError:
        return None


def get_agent_shared_context(agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get shared context from other agents in the same project.

    Returns decisions, learnings, and blockers shared by other agents.
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    try:
        from shared_memory import get_shared_context
        project = agent.context.get("project", "")
        return get_shared_context(agent_id, project)
    except ImportError:
        return None


def sync_agent_to_shared(agent_id: str) -> Dict[str, int]:
    """
    Sync an agent's decisions and learnings to shared memory.

    Returns counts of items synced.
    """
    agent = get_agent(agent_id)
    if not agent:
        return {"decisions": 0, "learnings": 0}

    decisions_synced = 0
    learnings_synced = 0

    # Sync decisions
    for d in agent.context.get("decisions", []):
        text = d.get("text", "") if isinstance(d, dict) else str(d)
        if text and share_agent_decision(agent_id, text):
            decisions_synced += 1

    # Sync learnings
    for l in agent.context.get("learnings", []):
        text = l.get("text", "") if isinstance(l, dict) else str(l)
        if text and share_agent_learning(agent_id, text):
            learnings_synced += 1

    return {"decisions": decisions_synced, "learnings": learnings_synced}
