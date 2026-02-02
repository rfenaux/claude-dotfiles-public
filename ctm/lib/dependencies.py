"""
CTM Task Dependencies

Manages task dependency graphs with:
- Blocker/dependent relationships
- Auto-unblocking on completion
- Circular dependency detection
- Dependency chain visualization

v3.0.0 Feature
"""

from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from config import get_ctm_dir
from agents import Agent, get_agent, AgentIndex, AgentStatus


@dataclass
class DependencyInfo:
    """Information about a task's dependencies."""
    agent_id: str
    blockers: List[str]        # Tasks this agent is waiting on
    dependents: List[str]      # Tasks waiting on this agent
    is_blocked: bool
    blocking_count: int        # How many tasks this blocks


def find_blockers(agent_id: str) -> List[str]:
    """
    Find all tasks that block this agent.

    Returns list of agent IDs that must complete before this agent can proceed.
    """
    agent = get_agent(agent_id)
    if not agent:
        return []

    return agent.task.get("blockers", [])


def find_dependents(agent_id: str) -> List[str]:
    """
    Find all tasks that depend on (are blocked by) this agent.

    Returns list of agent IDs that are waiting for this agent to complete.
    """
    index = AgentIndex()
    dependents = []

    # Check all active agents
    for aid in index.get_all_active():
        agent = get_agent(aid)
        if agent:
            blockers = agent.task.get("blockers", [])
            if agent_id in blockers:
                dependents.append(aid)

    return dependents


def is_blocked(agent_id: str) -> bool:
    """
    Check if an agent is blocked by unresolved dependencies.
    """
    agent = get_agent(agent_id)
    if not agent:
        return False

    blockers = agent.task.get("blockers", [])
    if not blockers:
        return False

    # Check if any blocker is still active (not completed/cancelled)
    for blocker_id in blockers:
        blocker = get_agent(blocker_id)
        if blocker and blocker.state["status"] not in (
            AgentStatus.COMPLETED.value,
            AgentStatus.CANCELLED.value
        ):
            return True

    return False


def get_blocking_chain(agent_id: str, visited: Optional[Set[str]] = None) -> List[str]:
    """
    Get the full chain of blockers for an agent (recursive).

    Returns ordered list from immediate blockers to root blockers.
    """
    if visited is None:
        visited = set()

    if agent_id in visited:
        return []  # Avoid cycles

    visited.add(agent_id)
    chain = []

    blockers = find_blockers(agent_id)
    for blocker_id in blockers:
        chain.append(blocker_id)
        # Recursively get blockers of blockers
        chain.extend(get_blocking_chain(blocker_id, visited))

    return chain


def get_dependent_chain(agent_id: str, visited: Optional[Set[str]] = None) -> List[str]:
    """
    Get the full chain of dependents for an agent (recursive).

    Returns ordered list of all tasks that would be unblocked (directly or indirectly)
    if this agent completes.
    """
    if visited is None:
        visited = set()

    if agent_id in visited:
        return []  # Avoid cycles

    visited.add(agent_id)
    chain = []

    dependents = find_dependents(agent_id)
    for dep_id in dependents:
        chain.append(dep_id)
        # Recursively get dependents of dependents
        chain.extend(get_dependent_chain(dep_id, visited))

    return chain


def validate_no_cycles(agent_id: str, new_blocker_id: str) -> Tuple[bool, Optional[List[str]]]:
    """
    Check if adding a blocker would create a circular dependency.

    Returns:
        (is_valid, cycle_path) - True if no cycle, False with cycle path if would create cycle
    """
    # Check if the new blocker (or any of its blockers) depends on agent_id
    visited = set()
    path = [new_blocker_id]

    def check_cycle(check_id: str) -> bool:
        if check_id == agent_id:
            return True  # Found cycle!

        if check_id in visited:
            return False

        visited.add(check_id)

        blockers = find_blockers(check_id)
        for b_id in blockers:
            path.append(b_id)
            if check_cycle(b_id):
                return True
            path.pop()

        return False

    if check_cycle(new_blocker_id):
        return False, path + [agent_id]

    return True, None


def add_blocker(agent_id: str, blocker_id: str) -> Tuple[bool, str]:
    """
    Add a blocker to an agent.

    Returns:
        (success, message)
    """
    from agents import update_agent

    agent = get_agent(agent_id)
    if not agent:
        return False, f"Agent not found: {agent_id}"

    blocker = get_agent(blocker_id)
    if not blocker:
        return False, f"Blocker not found: {blocker_id}"

    # Check for cycles
    is_valid, cycle = validate_no_cycles(agent_id, blocker_id)
    if not is_valid:
        cycle_str = " -> ".join(cycle)
        return False, f"Would create circular dependency: {cycle_str}"

    # Add blocker
    if "blockers" not in agent.task:
        agent.task["blockers"] = []

    if blocker_id not in agent.task["blockers"]:
        agent.task["blockers"].append(blocker_id)

        # Update status to blocked if blocker is active
        if blocker.state["status"] not in (
            AgentStatus.COMPLETED.value,
            AgentStatus.CANCELLED.value
        ):
            agent.set_status(AgentStatus.BLOCKED)

        update_agent(agent)
        return True, f"Added blocker [{blocker_id}] to [{agent_id}]"

    return False, f"[{blocker_id}] already blocks [{agent_id}]"


def remove_blocker(agent_id: str, blocker_id: str) -> Tuple[bool, str]:
    """
    Remove a blocker from an agent.

    Returns:
        (success, message)
    """
    from agents import update_agent

    agent = get_agent(agent_id)
    if not agent:
        return False, f"Agent not found: {agent_id}"

    blockers = agent.task.get("blockers", [])
    if blocker_id not in blockers:
        return False, f"[{blocker_id}] does not block [{agent_id}]"

    agent.task["blockers"].remove(blocker_id)

    # Check if agent should be unblocked
    if not is_blocked(agent_id):
        if agent.state["status"] == AgentStatus.BLOCKED.value:
            agent.set_status(AgentStatus.PAUSED)

    update_agent(agent)
    return True, f"Removed blocker [{blocker_id}] from [{agent_id}]"


def unblock_dependents(completed_agent_id: str) -> List[Tuple[str, bool]]:
    """
    Remove completed agent from all dependents' blocker lists.

    Called when an agent completes to auto-unblock waiting tasks.

    Returns:
        List of (agent_id, was_fully_unblocked) tuples
    """
    from agents import update_agent

    results = []
    dependents = find_dependents(completed_agent_id)

    for dep_id in dependents:
        dep_agent = get_agent(dep_id)
        if not dep_agent:
            continue

        # Remove completed agent from blockers
        if completed_agent_id in dep_agent.task.get("blockers", []):
            dep_agent.task["blockers"].remove(completed_agent_id)

            # Check if fully unblocked
            fully_unblocked = not is_blocked(dep_id)

            if fully_unblocked and dep_agent.state["status"] == AgentStatus.BLOCKED.value:
                dep_agent.set_status(AgentStatus.PAUSED)

            update_agent(dep_agent)
            results.append((dep_id, fully_unblocked))

    return results


def get_dependency_info(agent_id: str) -> Optional[DependencyInfo]:
    """
    Get complete dependency information for an agent.
    """
    agent = get_agent(agent_id)
    if not agent:
        return None

    blockers = find_blockers(agent_id)
    dependents = find_dependents(agent_id)

    return DependencyInfo(
        agent_id=agent_id,
        blockers=blockers,
        dependents=dependents,
        is_blocked=is_blocked(agent_id),
        blocking_count=len(dependents)
    )


def get_all_dependencies() -> Dict[str, DependencyInfo]:
    """
    Get dependency information for all active agents.
    """
    index = AgentIndex()
    result = {}

    for aid in index.get_all_active():
        info = get_dependency_info(aid)
        if info:
            result[aid] = info

    return result


def get_high_impact_blockers(min_dependents: int = 2) -> List[Tuple[str, int]]:
    """
    Find agents that block multiple other tasks.

    Returns:
        List of (agent_id, dependent_count) sorted by impact
    """
    deps = get_all_dependencies()

    high_impact = [
        (aid, info.blocking_count)
        for aid, info in deps.items()
        if info.blocking_count >= min_dependents
    ]

    return sorted(high_impact, key=lambda x: -x[1])


def format_dependency_tree(agent_id: str, depth: int = 0, visited: Optional[Set[str]] = None) -> str:
    """
    Format a task's dependencies as an ASCII tree.
    """
    if visited is None:
        visited = set()

    if agent_id in visited:
        return ""

    visited.add(agent_id)

    agent = get_agent(agent_id)
    if not agent:
        return ""

    indent = "  " * depth
    prefix = "└─ " if depth > 0 else ""

    status_icon = "✓" if agent.state["status"] == AgentStatus.COMPLETED.value else "○"
    if agent.state["status"] == AgentStatus.BLOCKED.value:
        status_icon = "⛔"

    lines = [f"{indent}{prefix}{status_icon} [{agent_id}] {agent.task['title'][:40]}"]

    # Show dependents (what this blocks)
    dependents = find_dependents(agent_id)
    for dep_id in dependents:
        lines.append(format_dependency_tree(dep_id, depth + 1, visited))

    return "\n".join(filter(None, lines))
