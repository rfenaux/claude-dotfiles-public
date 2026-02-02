"""
CTM Multi-Agent Shared Memory

Enables related agents to share context through:
- Shared memory pools (by project or tag)
- Private vs shared fragments with provenance
- Pub/Sub pattern for synchronization
- Access control with versioning

Based on research:
- ICML Collaborative Memory (asymmetric access control)
- Google ADK (context engineering patterns)
- Blackboard-style coordination

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Shared Memory Pool                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Fragment   │  │  Fragment   │  │  Fragment   │         │
│  │ (decision)  │  │ (learning)  │  │ (context)   │         │
│  │ owner: A    │  │ owner: B    │  │ owner: A    │         │
│  │ shared: yes │  │ shared: yes │  │ shared: no  │ ← private│
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
         ↑ publish              ↓ subscribe
    ┌────┴────┐            ┌────┴────┐
    │ Agent A │            │ Agent B │
    │ (active)│            │ (paused)│
    └─────────┘            └─────────┘
"""

import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Callable
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock

from config import load_config, get_ctm_dir


class FragmentType(str, Enum):
    """Types of memory fragments."""
    DECISION = "decision"
    LEARNING = "learning"
    CONTEXT = "context"
    FILE_REF = "file_ref"
    BLOCKER = "blocker"


class AccessLevel(str, Enum):
    """Access levels for memory fragments."""
    PRIVATE = "private"      # Only owner can read
    PROJECT = "project"      # All agents in same project
    TAGGED = "tagged"        # Agents with matching tags
    PUBLIC = "public"        # All agents


@dataclass
class Provenance:
    """Tracks origin and history of a fragment."""
    created_by: str           # Agent ID
    created_at: str           # ISO timestamp
    modified_by: List[str] = field(default_factory=list)
    modified_at: List[str] = field(default_factory=list)
    accessed_by: List[str] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "created_by": self.created_by,
            "created_at": self.created_at,
            "modified_by": self.modified_by,
            "modified_at": self.modified_at,
            "accessed_by": self.accessed_by,
            "source_files": self.source_files
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'Provenance':
        return cls(
            created_by=d["created_by"],
            created_at=d["created_at"],
            modified_by=d.get("modified_by", []),
            modified_at=d.get("modified_at", []),
            accessed_by=d.get("accessed_by", []),
            source_files=d.get("source_files", [])
        )


@dataclass
class MemoryFragment:
    """A unit of shared memory."""
    id: str
    type: FragmentType
    content: str
    access: AccessLevel
    provenance: Provenance
    version: int = 1
    tags: List[str] = field(default_factory=list)
    project: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "access": self.access.value,
            "provenance": self.provenance.to_dict(),
            "version": self.version,
            "tags": self.tags,
            "project": self.project,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, d: dict) -> 'MemoryFragment':
        return cls(
            id=d["id"],
            type=FragmentType(d["type"]),
            content=d["content"],
            access=AccessLevel(d["access"]),
            provenance=Provenance.from_dict(d["provenance"]),
            version=d.get("version", 1),
            tags=d.get("tags", []),
            project=d.get("project"),
            metadata=d.get("metadata", {})
        )


@dataclass
class Subscription:
    """A subscription to memory updates."""
    agent_id: str
    filter_types: Optional[List[FragmentType]] = None
    filter_tags: Optional[List[str]] = None
    filter_project: Optional[str] = None
    callback: Optional[Callable[[MemoryFragment], None]] = None


class SharedMemoryPool:
    """
    Shared memory pool for multi-agent coordination.

    Provides:
    - Fragment storage with access control
    - Pub/Sub for synchronization
    - Version tracking for coherence
    - Project and tag-based grouping
    """

    def __init__(self, pool_id: Optional[str] = None):
        self.ctm_dir = get_ctm_dir()
        self.pool_id = pool_id or "default"
        self.pool_dir = self.ctm_dir / "shared_memory"
        self.pool_path = self.pool_dir / f"{self.pool_id}.json"
        self._state = self._load_state()
        self._subscriptions: List[Subscription] = []
        self._lock = Lock()

    def _load_state(self) -> Dict[str, Any]:
        self.pool_dir.mkdir(parents=True, exist_ok=True)
        if not self.pool_path.exists():
            return {
                "version": "1.0.0",
                "pool_id": self.pool_id,
                "fragments": {},
                "projects": {},  # project -> [fragment_ids]
                "tags": {},      # tag -> [fragment_ids]
                "stats": {
                    "total_fragments": 0,
                    "total_reads": 0,
                    "total_writes": 0
                },
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        with open(self.pool_path, 'r') as f:
            return json.load(f)

    def _save_state(self) -> None:
        with self._lock:
            self._state["stats"]["total_fragments"] = len(self._state["fragments"])
            with open(self.pool_path, 'w') as f:
                json.dump(self._state, f, indent=2)

    def _generate_id(self, ftype: FragmentType, content: str) -> str:
        h = hashlib.md5(f"{ftype.value}:{content[:100]}:{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        return f"{ftype.value[:3]}-{h}"

    def publish(self, agent_id: str, ftype: FragmentType, content: str,
                access: AccessLevel = AccessLevel.PROJECT,
                tags: Optional[List[str]] = None,
                project: Optional[str] = None,
                source_files: Optional[List[str]] = None,
                metadata: Optional[Dict[str, Any]] = None) -> MemoryFragment:
        """
        Publish a fragment to the shared memory pool.

        Returns the created fragment.
        """
        now = datetime.now(timezone.utc).isoformat()
        fid = self._generate_id(ftype, content)

        provenance = Provenance(
            created_by=agent_id,
            created_at=now,
            source_files=source_files or []
        )

        fragment = MemoryFragment(
            id=fid,
            type=ftype,
            content=content,
            access=access,
            provenance=provenance,
            tags=tags or [],
            project=project,
            metadata=metadata or {}
        )

        # Store fragment
        self._state["fragments"][fid] = fragment.to_dict()

        # Index by project
        if project:
            if project not in self._state["projects"]:
                self._state["projects"][project] = []
            self._state["projects"][project].append(fid)

        # Index by tags
        for tag in (tags or []):
            if tag not in self._state["tags"]:
                self._state["tags"][tag] = []
            self._state["tags"][tag].append(fid)

        self._state["stats"]["total_writes"] += 1
        self._save_state()

        # Notify subscribers
        self._notify_subscribers(fragment)

        return fragment

    def read(self, fragment_id: str, reader_agent: str) -> Optional[MemoryFragment]:
        """
        Read a fragment by ID.

        Checks access control and updates provenance.
        """
        if fragment_id not in self._state["fragments"]:
            return None

        fdata = self._state["fragments"][fragment_id]
        fragment = MemoryFragment.from_dict(fdata)

        # Check access
        if not self._can_access(fragment, reader_agent):
            return None

        # Update provenance
        if reader_agent not in fragment.provenance.accessed_by:
            fragment.provenance.accessed_by.append(reader_agent)
            self._state["fragments"][fragment_id] = fragment.to_dict()

        self._state["stats"]["total_reads"] += 1
        self._save_state()

        return fragment

    def _can_access(self, fragment: MemoryFragment, agent_id: str) -> bool:
        """Check if agent can access fragment."""
        if fragment.access == AccessLevel.PUBLIC:
            return True

        if fragment.access == AccessLevel.PRIVATE:
            return fragment.provenance.created_by == agent_id

        if fragment.access == AccessLevel.PROJECT:
            # Check if agent is in same project
            # For now, allow if agent exists
            return True

        if fragment.access == AccessLevel.TAGGED:
            # Would need to check agent tags
            return True

        return False

    def query(self, agent_id: str,
              project: Optional[str] = None,
              tags: Optional[List[str]] = None,
              ftypes: Optional[List[FragmentType]] = None,
              limit: int = 50) -> List[MemoryFragment]:
        """
        Query fragments with filters.

        Returns accessible fragments matching criteria.
        """
        results = []
        candidate_ids = set()

        # Filter by project
        if project and project in self._state["projects"]:
            candidate_ids.update(self._state["projects"][project])
        elif project is None:
            candidate_ids.update(self._state["fragments"].keys())

        # Filter by tags (intersection)
        if tags:
            tag_ids = set()
            for tag in tags:
                if tag in self._state["tags"]:
                    if not tag_ids:
                        tag_ids = set(self._state["tags"][tag])
                    else:
                        tag_ids &= set(self._state["tags"][tag])
            if candidate_ids:
                candidate_ids &= tag_ids
            else:
                candidate_ids = tag_ids

        # Check each candidate
        for fid in list(candidate_ids)[:limit * 2]:  # Over-fetch for filtering
            fdata = self._state["fragments"].get(fid)
            if not fdata:
                continue

            fragment = MemoryFragment.from_dict(fdata)

            # Filter by type
            if ftypes and fragment.type not in ftypes:
                continue

            # Check access
            if not self._can_access(fragment, agent_id):
                continue

            results.append(fragment)

            if len(results) >= limit:
                break

        return results

    def subscribe(self, agent_id: str,
                  filter_types: Optional[List[FragmentType]] = None,
                  filter_tags: Optional[List[str]] = None,
                  filter_project: Optional[str] = None,
                  callback: Optional[Callable[[MemoryFragment], None]] = None) -> str:
        """
        Subscribe to memory updates.

        Returns subscription ID.
        """
        sub = Subscription(
            agent_id=agent_id,
            filter_types=filter_types,
            filter_tags=filter_tags,
            filter_project=filter_project,
            callback=callback
        )
        self._subscriptions.append(sub)
        return f"sub-{agent_id}-{len(self._subscriptions)}"

    def unsubscribe(self, agent_id: str) -> None:
        """Remove all subscriptions for an agent."""
        self._subscriptions = [s for s in self._subscriptions if s.agent_id != agent_id]

    def _notify_subscribers(self, fragment: MemoryFragment) -> None:
        """Notify relevant subscribers of new fragment."""
        for sub in self._subscriptions:
            # Skip if owner (don't notify self)
            if sub.agent_id == fragment.provenance.created_by:
                continue

            # Check type filter
            if sub.filter_types and fragment.type not in sub.filter_types:
                continue

            # Check tag filter
            if sub.filter_tags:
                if not any(t in fragment.tags for t in sub.filter_tags):
                    continue

            # Check project filter
            if sub.filter_project and fragment.project != sub.filter_project:
                continue

            # Invoke callback if provided
            if sub.callback:
                try:
                    sub.callback(fragment)
                except Exception:
                    pass

    def update(self, fragment_id: str, updater_agent: str,
               content: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> Optional[MemoryFragment]:
        """
        Update an existing fragment.

        Increments version and updates provenance.
        """
        if fragment_id not in self._state["fragments"]:
            return None

        fdata = self._state["fragments"][fragment_id]
        fragment = MemoryFragment.from_dict(fdata)

        # Check access (must be owner or have write access)
        if fragment.access == AccessLevel.PRIVATE:
            if fragment.provenance.created_by != updater_agent:
                return None

        # Update content
        if content is not None:
            fragment.content = content

        # Update metadata
        if metadata:
            fragment.metadata.update(metadata)

        # Update provenance
        now = datetime.now(timezone.utc).isoformat()
        fragment.provenance.modified_by.append(updater_agent)
        fragment.provenance.modified_at.append(now)

        # Increment version
        fragment.version += 1

        # Save
        self._state["fragments"][fragment_id] = fragment.to_dict()
        self._save_state()

        # Notify
        self._notify_subscribers(fragment)

        return fragment

    def get_project_context(self, project: str, agent_id: str) -> Dict[str, Any]:
        """
        Get aggregated context for a project.

        Returns summary of decisions, learnings, blockers.
        """
        fragments = self.query(agent_id, project=project, limit=100)

        decisions = [f for f in fragments if f.type == FragmentType.DECISION]
        learnings = [f for f in fragments if f.type == FragmentType.LEARNING]
        blockers = [f for f in fragments if f.type == FragmentType.BLOCKER]

        return {
            "project": project,
            "total_fragments": len(fragments),
            "decisions": [{"id": d.id, "content": d.content[:100], "by": d.provenance.created_by} for d in decisions],
            "learnings": [{"id": l.id, "content": l.content[:100], "by": l.provenance.created_by} for l in learnings],
            "active_blockers": [{"id": b.id, "content": b.content, "by": b.provenance.created_by} for b in blockers],
            "contributors": list(set(f.provenance.created_by for f in fragments))
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        type_counts = {}
        for fdata in self._state["fragments"].values():
            ftype = fdata.get("type", "unknown")
            type_counts[ftype] = type_counts.get(ftype, 0) + 1

        return {
            "pool_id": self.pool_id,
            "total_fragments": self._state["stats"]["total_fragments"],
            "total_reads": self._state["stats"]["total_reads"],
            "total_writes": self._state["stats"]["total_writes"],
            "by_type": type_counts,
            "projects": list(self._state["projects"].keys()),
            "tags": list(self._state["tags"].keys()),
            "active_subscriptions": len(self._subscriptions)
        }


def get_shared_pool(pool_id: str = "default") -> SharedMemoryPool:
    """Get or create a shared memory pool."""
    return SharedMemoryPool(pool_id)


def get_project_pool(project_path: str) -> SharedMemoryPool:
    """Get shared pool for a project."""
    # Use project path hash as pool ID
    pool_id = hashlib.md5(project_path.encode()).hexdigest()[:8]
    return SharedMemoryPool(f"project-{pool_id}")


# Convenience functions for agents
def share_decision(agent_id: str, decision: str, project: str, tags: Optional[List[str]] = None) -> str:
    """Share a decision with other agents in the project."""
    pool = get_project_pool(project)
    fragment = pool.publish(
        agent_id=agent_id,
        ftype=FragmentType.DECISION,
        content=decision,
        access=AccessLevel.PROJECT,
        tags=tags,
        project=project
    )
    return fragment.id


def share_learning(agent_id: str, learning: str, project: str, tags: Optional[List[str]] = None) -> str:
    """Share a learning with other agents in the project."""
    pool = get_project_pool(project)
    fragment = pool.publish(
        agent_id=agent_id,
        ftype=FragmentType.LEARNING,
        content=learning,
        access=AccessLevel.PROJECT,
        tags=tags,
        project=project
    )
    return fragment.id


def get_shared_context(agent_id: str, project: str) -> Dict[str, Any]:
    """Get shared context from other agents in the project."""
    pool = get_project_pool(project)
    return pool.get_project_context(project, agent_id)
