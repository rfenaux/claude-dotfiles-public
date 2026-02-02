#!/usr/bin/env python3
"""
CTM - Cognitive Task Manager

Main CLI entry point for the Cognitive Task Manager system.
Provides commands for managing task contexts (agents) with
bio-inspired priority scheduling.

Usage:
    ctm status              Show current state
    ctm list [--all]        List agents
    ctm show <id>           Show agent details
    ctm spawn <title>       Create new agent
    ctm switch <id>         Switch to agent
    ctm pause [id]          Pause agent
    ctm resume <id>         Resume agent
    ctm complete [id]       Mark agent complete
    ctm cancel <id>         Cancel agent
    ctm priority <id> <+/-> Adjust priority
    ctm brief               Generate session briefing
    ctm queue               Show priority queue
    ctm help                Show help
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from config import load_config, get_ctm_dir
from agents import (
    create_agent, get_agent, list_agents, update_agent, delete_agent,
    AgentStatus, AgentIndex
)
from scheduler import get_scheduler


def cmd_status(args) -> int:
    """Show current CTM status."""
    from style import (
        bold, success, warning, info, muted, dim,
        status_icon, progress_bar, header, section
    )

    scheduler = get_scheduler()
    status = scheduler.get_status()
    index = AgentIndex()

    print(bold("═══ CTM Status ═══"))
    print()

    # Active agent
    if status["active_agent"]:
        agent = get_agent(status["active_agent"])
        if agent:
            print(f"{success('▶ Active:')} {bold(f'[{agent.id}]')} {agent.task['title']}")
            print(f"  {progress_bar(agent.state['progress_pct'])}")
            if agent.state.get("current_step"):
                print(f"  {muted('Step:')} {agent.state['current_step']}")
    else:
        print(muted("▷ No active agent"))

    print()

    # Queue summary
    queue = scheduler.get_queue()
    active_count = len(index.get_by_status("active"))
    paused_count = len(index.get_by_status("paused"))
    blocked_count = len(index.get_by_status("blocked"))

    parts = []
    if active_count:
        parts.append(success(f"{active_count} active"))
    if paused_count:
        parts.append(warning(f"{paused_count} paused"))
    if blocked_count:
        parts.append(f"{blocked_count} blocked")

    print(f"{bold('Queue:')} {len(queue)} agents ({', '.join(parts)})")

    if queue and len(queue) > 1:
        print(muted("  Next up:"))
        for item in queue[1:4]:  # Show top 3 waiting
            icon = status_icon(item['status'])
            score = item['score']
            print(f"    {icon} [{item['id']}] {item['title']} {muted(f'({score:.2f})')}")

    print()

    # Session stats
    session = status["session"]
    if session.get("started_at"):
        print(muted(f"Session: {session['switches']} switches, {session['checkpoints']} checkpoints"))

    return 0


def cmd_list(args) -> int:
    """List agents."""
    from style import bold, success, warning, error, muted, status_icon

    status_filter = None if args.all else "active"

    if args.status:
        status_filter = args.status

    agents = list_agents(status=status_filter, project=args.project)

    if not agents:
        print(muted("No agents found."))
        return 0

    print(bold("═══ Agents ═══"))
    print()

    # Group by status
    by_status = {}
    for agent in agents:
        s = agent["status"]
        if s not in by_status:
            by_status[s] = []
        by_status[s].append(agent)

    status_order = ["active", "paused", "blocked", "completed", "cancelled"]
    status_colors = {
        "active": success,
        "paused": warning,
        "blocked": error,
        "completed": muted,
        "cancelled": muted
    }

    for status in status_order:
        if status in by_status:
            color_fn = status_colors.get(status, lambda x: x)
            print(color_fn(f"── {status.upper()} ──"))
            for a in by_status[status]:
                score = a.get("priority_score", 0)
                icon = status_icon(status)
                print(f"  {icon} [{a['id']}] {a['title']} {muted(f'({score:.2f})')}")
            print()

    return 0


def cmd_show(args) -> int:
    """Show agent details."""
    agent = get_agent(args.id)
    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    print(f"═══ Agent: {agent.id} ═══")
    print()
    print(f"Title:    {agent.task['title']}")
    print(f"Goal:     {agent.task['goal']}")
    print(f"Status:   {agent.state['status']}")
    print(f"Progress: {agent.state['progress_pct']}%")
    print(f"Priority: {agent.priority['level']} (score: {agent.priority['computed_score']:.3f})")
    print()
    print(f"Created:  {agent.timing['created_at']}")
    print(f"Active:   {agent.timing['last_active']}")
    print(f"Sessions: {agent.timing['session_count']}")
    print()

    if agent.state.get("current_step"):
        print(f"Current Step: {agent.state['current_step']}")

    if agent.context.get("decisions"):
        print()
        print("Decisions:")
        for d in agent.context["decisions"][-5:]:  # Last 5
            print(f"  • {d['text']}")

    if agent.context.get("key_files"):
        print()
        print("Key Files:")
        for f in agent.context["key_files"][:10]:
            print(f"  • {f}")

    if agent.triggers:
        print()
        print(f"Triggers: {', '.join(agent.triggers)}")

    return 0


def cmd_spawn(args) -> int:
    """Create a new agent."""
    from style import success, bold, info, warning

    title = args.title
    goal = args.goal or f"Complete: {title}"

    # v3.0: Load template if specified
    template = None
    if hasattr(args, 'template') and args.template:
        from templates import load_template, apply_template_to_agent
        template = load_template(args.template)
        if not template:
            print(warning(f"Template not found: {args.template}"))
            print(info("Use 'ctm templates' to list available templates"))
            return 1

    # Build source tracking dict if any source args provided
    source = None
    if hasattr(args, 'source') and args.source:
        source = {
            "type": args.source,
            "reference_id": getattr(args, 'source_ref', None),
            "extracted_by": getattr(args, 'extracted_by', None) or "ctm-spawn"
        }

    agent = create_agent(
        title=title,
        goal=goal,
        project=args.project,
        priority=args.priority or "normal",
        tags=args.tags.split(",") if args.tags else None,
        triggers=args.triggers.split(",") if args.triggers else None,
        source=source
    )

    # v3.0: Apply template if loaded
    if template:
        from templates import apply_template_to_agent
        apply_template_to_agent(agent, template)
        update_agent(agent)

    # v3.0: Handle --blocked-by for task dependencies
    blocked_by_ids = []
    if hasattr(args, 'blocked_by') and args.blocked_by:
        from dependencies import add_blocker, validate_no_cycles

        blocker_ids = [b.strip() for b in args.blocked_by.split(",")]

        for blocker_id in blocker_ids:
            resolved_id = resolve_agent_id(blocker_id)
            if not resolved_id:
                print(warning(f"Blocker not found: {blocker_id}"))
                continue

            blocker = get_agent(resolved_id)
            if not blocker:
                print(warning(f"Blocker agent not found: {resolved_id}"))
                continue

            # Add to blockers list
            if "blockers" not in agent.task:
                agent.task["blockers"] = []
            agent.task["blockers"].append(resolved_id)
            blocked_by_ids.append(resolved_id)

        # Set status to blocked if there are active blockers
        if blocked_by_ids:
            from dependencies import is_blocked
            agent.set_status(AgentStatus.BLOCKED)
            update_agent(agent)

    print(f"{success('✓')} Created agent {bold(f'[{agent.id}]')}: {title}")

    if template:
        print(f"  📋 Template: {template.name}")
        if template.phases:
            print(f"  📊 Phases: {len(template.phases)}")

    if blocked_by_ids:
        print(f"  ⛔ Blocked by: {', '.join(blocked_by_ids)}")

    if args.switch and not blocked_by_ids:
        scheduler = get_scheduler()
        scheduler.switch_to(agent.id)
        print(f"{success('✓')} Switched to {bold(f'[{agent.id}]')}")
    elif args.switch and blocked_by_ids:
        print(warning("  Cannot switch to blocked task"))

    return 0


def cmd_switch(args) -> int:
    """Switch to an agent."""
    scheduler = get_scheduler()

    # Handle partial ID match
    agent_id = resolve_agent_id(args.id)
    if not agent_id:
        print(f"Agent not found: {args.id}")
        return 1

    old_active = scheduler.get_active()

    if scheduler.switch_to(agent_id):
        agent = get_agent(agent_id)
        print(f"✓ Switched to [{agent_id}]: {agent.task['title']}")

        if old_active and old_active != agent_id:
            old_agent = get_agent(old_active)
            if old_agent:
                print(f"  (paused [{old_active}]: {old_agent.task['title']})")

        # Show resumption cue if not a brand new agent
        if agent.timing.get("session_count", 0) > 1 or agent.state.get("progress_pct", 0) > 0:
            try:
                from resumption import generate_resumption_cue
                print()
                # Use brief cue for quick switches
                brief = not getattr(args, 'full', False)
                cue = generate_resumption_cue(agent_id, brief=brief)
                print(cue)
            except ImportError:
                pass

        return 0
    else:
        print(f"Failed to switch to agent: {agent_id}")
        return 1


def cmd_pause(args) -> int:
    """Pause an agent."""
    scheduler = get_scheduler()

    agent_id = args.id
    if not agent_id:
        agent_id = scheduler.get_active()

    if not agent_id:
        print("No agent to pause (none active)")
        return 1

    agent_id = resolve_agent_id(agent_id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {agent_id}")
        return 1

    agent.set_status(AgentStatus.PAUSED)
    update_agent(agent)

    if scheduler.get_active() == agent_id:
        scheduler.set_active(None)

    print(f"✓ Paused [{agent_id}]: {agent.task['title']}")
    return 0


def cmd_resume(args) -> int:
    """Resume a paused agent."""
    agent_id = resolve_agent_id(args.id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    scheduler = get_scheduler()
    old_active = scheduler.get_active()
    scheduler.switch_to(agent_id)

    print(f"✓ Resumed [{agent_id}]: {agent.task['title']}")

    if old_active and old_active != agent_id:
        old_agent = get_agent(old_active)
        if old_agent:
            print(f"  (paused [{old_active}]: {old_agent.task['title']})")

    # Show full resumption cue for resume (implies longer break)
    try:
        from resumption import generate_resumption_cue
        print()
        cue = generate_resumption_cue(agent_id, brief=False)
        print(cue)
    except ImportError:
        pass

    return 0


def cmd_complete(args) -> int:
    """Mark agent as complete with reflection."""
    scheduler = get_scheduler()

    agent_id = args.id
    if not agent_id:
        agent_id = scheduler.get_active()

    if not agent_id:
        print("No agent to complete (none active)")
        return 1

    agent_id = resolve_agent_id(agent_id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {agent_id}")
        return 1

    # Run reflection before completion (v2.0)
    try:
        from reflection import reflect_before_complete
        reflection, summary = reflect_before_complete(agent_id)
        if reflection and not reflection.ready_to_complete:
            print(f"⚠ Reflection suggests task not ready:")
            for blocker in reflection.blockers[:3]:
                print(f"  • {blocker}")
            if not getattr(args, 'force', False):
                print("  Use --force to complete anyway")
                return 1
        elif reflection:
            print(f"✓ Reflection: {reflection.completion_score:.0%} complete")
    except ImportError:
        pass
    except Exception as e:
        pass  # Silent fail, proceed with completion

    agent.set_status(AgentStatus.COMPLETED)
    agent.state["progress_pct"] = 100
    update_agent(agent)

    print(f"✓ Completed [{agent_id}]: {agent.task['title']}")

    # Auto-consolidate decisions from completed agent
    try:
        from extraction import extract_decisions, extract_learnings

        decisions = extract_decisions(agent_id)
        learnings = extract_learnings(agent_id)

        if decisions or learnings:
            print(f"  Extracted: {len(decisions)} decision(s), {len(learnings)} learning(s)")

            # Try to consolidate to project memory if available
            try:
                from consolidation import consolidate_agent
                from pathlib import Path
                project_path = Path(agent.context.get("project", "."))
                result = consolidate_agent(agent_id, project_path)
                if result.get("decisions_extracted"):
                    print(f"  → {result['decisions_extracted']} decision(s) saved to DECISIONS.md")
                if result.get("rag_indexed"):
                    print(f"  → Indexed to RAG")
            except Exception:
                pass  # Silent fail for auto-consolidation
    except ImportError:
        pass

    # v3.0: Auto-unblock dependent tasks
    try:
        from dependencies import unblock_dependents
        unblocked = unblock_dependents(agent_id)
        for dep_id, fully_unblocked in unblocked:
            dep_agent = get_agent(dep_id)
            if dep_agent:
                if fully_unblocked:
                    print(f"  ✓ Unblocked: [{dep_id}] {dep_agent.task['title'][:30]}")
                else:
                    remaining = len(dep_agent.task.get("blockers", []))
                    print(f"  ○ Partially unblocked: [{dep_id}] ({remaining} blocker(s) remaining)")
    except ImportError:
        pass
    except Exception:
        pass  # Silent fail

    if scheduler.get_active() == agent_id:
        scheduler.set_active(None)
        scheduler.rebuild_queue()

        # Suggest next agent
        next_agent = scheduler.get_next()
        if next_agent:
            next_a = get_agent(next_agent[0])
            if next_a:
                print(f"  Next: [{next_agent[0]}] {next_a.task['title']} (score: {next_agent[1]:.3f})")

    return 0


def cmd_cancel(args) -> int:
    """Cancel an agent."""
    agent_id = resolve_agent_id(args.id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    agent.set_status(AgentStatus.CANCELLED)
    update_agent(agent)

    scheduler = get_scheduler()
    if scheduler.get_active() == agent_id:
        scheduler.set_active(None)

    print(f"✓ Cancelled [{agent_id}]: {agent.task['title']}")
    return 0


def cmd_priority(args) -> int:
    """Adjust agent priority."""
    agent_id = resolve_agent_id(args.id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    # Adjust user_signal
    current = agent.priority.get("user_signal", 0)

    if args.direction == "+":
        new_signal = min(1.0, current + 0.25)
    elif args.direction == "-":
        new_signal = max(-1.0, current - 0.25)
    else:
        print(f"Invalid direction: {args.direction} (use + or -)")
        return 1

    agent.priority["user_signal"] = new_signal
    update_agent(agent)

    # Recalculate
    scheduler = get_scheduler()
    scheduler.rebuild_queue()

    new_score = agent.priority.get("computed_score", 0)
    print(f"✓ Priority adjusted for [{agent_id}]: signal={new_signal:+.2f}, score={new_score:.3f}")

    return 0


def cmd_deadline(args) -> int:
    """
    Manage task deadlines (v3.0).

    Commands:
        ctm deadline <id> <date>    - Set deadline (ISO date or relative)
        ctm deadline <id> clear     - Remove deadline
        ctm deadlines               - List all deadlines
    """
    from style import bold, success, muted, info, warning
    from datetime import datetime, timezone, timedelta
    import re

    # List all deadlines mode
    if args.action == "list" or (not args.id and not args.date):
        index = AgentIndex()
        now = datetime.now(timezone.utc)

        tasks_with_deadlines = []
        for aid in index.get_all_active():
            agent = get_agent(aid)
            if agent and agent.timing.get("deadline"):
                try:
                    deadline = datetime.fromisoformat(agent.timing["deadline"].rstrip("Z")).replace(tzinfo=timezone.utc)
                    delta = deadline - now
                    tasks_with_deadlines.append((aid, agent, deadline, delta))
                except (ValueError, TypeError):
                    continue

        if not tasks_with_deadlines:
            print(muted("No tasks have deadlines set."))
            return 0

        print(bold("═══ Task Deadlines ═══"))
        print()

        # Sort by deadline
        tasks_with_deadlines.sort(key=lambda x: x[2])

        for aid, agent, deadline, delta in tasks_with_deadlines:
            hours = delta.total_seconds() / 3600
            days = delta.days

            if hours < 0:
                icon = "🔴"
                time_str = f"{abs(days)}d overdue" if days < 0 else f"{abs(int(hours))}h overdue"
            elif hours <= 24:
                icon = "🟠"
                time_str = f"due in {int(hours)}h"
            elif days <= 3:
                icon = "🟡"
                time_str = f"due in {days}d"
            else:
                icon = "🟢"
                time_str = f"due in {days}d"

            deadline_str = deadline.strftime("%Y-%m-%d %H:%M")
            print(f"{icon} [{aid}] {agent.task['title'][:35]}")
            print(f"   {muted(deadline_str)} — {time_str}")

        return 0

    # Single task deadline management
    if not args.id:
        print(warning("Specify agent ID"))
        return 1

    agent_id = resolve_agent_id(args.id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    # Clear deadline
    if args.date and args.date.lower() == "clear":
        agent.timing["deadline"] = None
        update_agent(agent)
        print(f"{success('✓')} Deadline cleared for [{agent_id}]")
        return 0

    # Set deadline
    if not args.date:
        # Show current deadline
        current = agent.timing.get("deadline")
        if current:
            try:
                deadline = datetime.fromisoformat(current.rstrip("Z")).replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                delta = deadline - now
                hours = delta.total_seconds() / 3600
                days = delta.days

                if hours < 0:
                    status = warning(f"{abs(days)}d overdue")
                elif hours <= 24:
                    status = warning(f"due in {int(hours)}h")
                else:
                    status = info(f"due in {days}d")

                print(f"[{agent_id}] Deadline: {deadline.strftime('%Y-%m-%d %H:%M')} — {status}")
            except (ValueError, TypeError):
                print(f"[{agent_id}] Invalid deadline format: {current}")
        else:
            print(muted(f"[{agent_id}] No deadline set"))
        return 0

    # Parse date
    now = datetime.now(timezone.utc)
    deadline = None

    # Relative format: +1d, +2w, +1m, +3h
    relative_match = re.match(r'^\+(\d+)([hdwm])$', args.date.lower())
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)

        if unit == 'h':
            deadline = now + timedelta(hours=amount)
        elif unit == 'd':
            deadline = now + timedelta(days=amount)
        elif unit == 'w':
            deadline = now + timedelta(weeks=amount)
        elif unit == 'm':
            deadline = now + timedelta(days=amount * 30)  # Approximate month
    else:
        # Try ISO format
        try:
            # Support various formats
            for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M"]:
                try:
                    deadline = datetime.strptime(args.date, fmt).replace(tzinfo=timezone.utc)
                    break
                except ValueError:
                    continue
        except Exception:
            pass

    if not deadline:
        print(warning(f"Invalid date format: {args.date}"))
        print(muted("Formats: YYYY-MM-DD, +1d, +2w, +1m, +3h"))
        return 1

    agent.timing["deadline"] = deadline.isoformat()
    update_agent(agent)

    # Recalculate priority
    scheduler = get_scheduler()
    scheduler.rebuild_queue()

    delta = deadline - now
    days = delta.days
    print(f"{success('✓')} Deadline set for [{agent_id}]: {deadline.strftime('%Y-%m-%d %H:%M')} (in {days}d)")

    return 0


def cmd_block(args) -> int:
    """
    Add a blocker to a task (v3.0).

    Usage: ctm block <agent_id> --by <blocker_id>
    """
    from style import success, warning, muted
    from dependencies import add_blocker

    if not args.id or not args.by:
        print(warning("Usage: ctm block <agent_id> --by <blocker_id>"))
        return 1

    agent_id = resolve_agent_id(args.id)
    blocker_id = resolve_agent_id(args.by)

    if not agent_id:
        print(f"Agent not found: {args.id}")
        return 1

    if not blocker_id:
        print(f"Blocker not found: {args.by}")
        return 1

    success_result, message = add_blocker(agent_id, blocker_id)

    if success_result:
        print(f"{success('✓')} {message}")
    else:
        print(warning(f"✗ {message}"))
        return 1

    return 0


def cmd_unblock(args) -> int:
    """
    Remove a blocker from a task (v3.0).

    Usage: ctm unblock <agent_id> --from <blocker_id>
    """
    from style import success, warning
    from dependencies import remove_blocker

    if not args.id:
        print(warning("Usage: ctm unblock <agent_id> --from <blocker_id>"))
        return 1

    agent_id = resolve_agent_id(args.id)
    if not agent_id:
        print(f"Agent not found: {args.id}")
        return 1

    # If --from not specified, remove all blockers
    if not args.blocker:
        agent = get_agent(agent_id)
        if not agent:
            print(f"Agent not found: {agent_id}")
            return 1

        blockers = agent.task.get("blockers", [])
        if not blockers:
            print(f"[{agent_id}] has no blockers")
            return 0

        for blocker_id in blockers.copy():
            remove_blocker(agent_id, blocker_id)

        print(f"{success('✓')} Removed all {len(blockers)} blocker(s) from [{agent_id}]")
        return 0

    blocker_id = resolve_agent_id(args.blocker)
    if not blocker_id:
        print(f"Blocker not found: {args.blocker}")
        return 1

    success_result, message = remove_blocker(agent_id, blocker_id)

    if success_result:
        print(f"{success('✓')} {message}")
    else:
        print(warning(f"✗ {message}"))
        return 1

    return 0


def cmd_deps(args) -> int:
    """
    Show task dependencies (v3.0).

    Usage:
        ctm deps <agent_id>  - Show dependencies for a task
        ctm deps --all       - Show all dependencies as a graph
    """
    from style import bold, success, muted, info, warning
    from dependencies import (
        get_dependency_info, get_all_dependencies, find_blockers,
        find_dependents, get_high_impact_blockers, format_dependency_tree,
        DependencyInfo
    )

    # Show all dependencies
    if args.all:
        all_deps = get_all_dependencies()

        print(bold("═══ Task Dependencies ═══"))
        print()

        # High-impact blockers first
        high_impact = get_high_impact_blockers(min_dependents=1)
        if high_impact:
            print(info("High-impact tasks (complete to unblock others):"))
            for aid, count in high_impact[:5]:
                agent = get_agent(aid)
                if agent:
                    status = "active" if agent.state["status"] == "active" else agent.state["status"]
                    print(f"  ⚡ [{aid}] {agent.task['title'][:35]} → unblocks {count}")
            print()

        # Blocked tasks
        blocked = [(aid, dep_info) for aid, dep_info in all_deps.items() if dep_info.is_blocked]
        if blocked:
            print(warning("Blocked tasks:"))
            for aid, dep_info in blocked[:5]:
                agent = get_agent(aid)
                if agent:
                    blocker_str = ", ".join(dep_info.blockers[:3])
                    if len(dep_info.blockers) > 3:
                        blocker_str += f" +{len(dep_info.blockers) - 3}"
                    print(f"  ⛔ [{aid}] {agent.task['title'][:30]}")
                    print(f"     ← waiting on: {blocker_str}")
            print()

        # Show ASCII tree for top tasks
        if high_impact:
            print(muted("─" * 40))
            print(info("Dependency Tree:"))
            for aid, _ in high_impact[:2]:
                tree = format_dependency_tree(aid)
                for line in tree.split('\n'):
                    print(f"  {line}")
                print()

        return 0

    # Show dependencies for a specific task
    if not args.id:
        print(warning("Specify agent ID or use --all"))
        return 1

    agent_id = resolve_agent_id(args.id)
    if not agent_id:
        print(f"Agent not found: {args.id}")
        return 1

    agent = get_agent(agent_id)
    if not agent:
        print(f"Agent not found: {agent_id}")
        return 1

    info_data = get_dependency_info(agent_id)
    if not info_data:
        print(f"Could not get dependency info for [{agent_id}]")
        return 1

    print(bold(f"═══ Dependencies: [{agent_id}] ═══"))
    print(f"{agent.task['title']}")
    print()

    # Show blockers (what this task is waiting on)
    if info_data.blockers:
        print(warning("Blocked by:"))
        for b_id in info_data.blockers:
            b_agent = get_agent(b_id)
            if b_agent:
                status = b_agent.state["status"]
                icon = "✓" if status == "completed" else "○"
                print(f"  {icon} [{b_id}] {b_agent.task['title'][:40]} ({status})")
            else:
                print(f"  ? [{b_id}] (not found)")
        print()

    # Show dependents (what's waiting on this task)
    if info_data.dependents:
        print(info("Blocks:"))
        for d_id in info_data.dependents:
            d_agent = get_agent(d_id)
            if d_agent:
                print(f"  ⛔ [{d_id}] {d_agent.task['title'][:40]}")
        print()

    if not info_data.blockers and not info_data.dependents:
        print(muted("No dependencies"))

    return 0


def cmd_progress(args) -> int:
    """Show task progress breakdown or set key files for tracking."""
    from progress import get_progress_breakdown, get_tracker
    from style import header, success, warning, error, muted

    # Get agent
    agent_id = args.id
    if not agent_id:
        scheduler = get_scheduler()
        queue = scheduler.get_queue()
        if queue:
            agent_id = queue[0]["id"]
        else:
            print(warning("No active tasks"))
            return 1

    agent = get_agent(agent_id)
    if not agent:
        print(error(f"Agent not found: {agent_id}"))
        return 1

    # Setting key files?
    if hasattr(args, 'files') and args.files is not None:
        if not agent.context:
            agent.context = {}
        agent.context["key_files"] = args.files
        agent.save()
        print(success(f"Set {len(args.files)} key files for tracking"))
        for f in args.files[:5]:
            print(f"  • {f}")
        if len(args.files) > 5:
            print(f"  ... and {len(args.files) - 5} more")
        # Clear cache so next inference uses new files
        get_tracker().clear_cache(agent.id)
        return 0

    # Show progress breakdown
    print(header(f"Progress: [{agent.id}] {agent.task.get('title', 'Unknown')}"))
    print()

    breakdown = get_progress_breakdown(agent)

    # Manual progress
    manual = breakdown["signals"].get("manual", {})
    manual_val = manual.get("value", 0)
    print(f"📊 Manual Progress: {manual_val}%")
    print()

    # File-based progress
    files_info = breakdown["signals"].get("files", {})
    if files_info:
        touched = files_info.get("files_touched", 0)
        total = files_info.get("key_files_total", 0)
        file_pct = files_info.get("value", 0)
        print(f"📁 File Activity: {file_pct:.0f}% ({touched}/{total} files touched)")
    else:
        print(muted("📁 File Activity: No key files set (use --files to set)"))
    print()

    # Git commit progress
    commits_info = breakdown["signals"].get("commits", {})
    commit_count = commits_info.get("count", 0)
    commit_pct = commits_info.get("value", 0)
    if commit_count > 0:
        print(f"📝 Git Commits: {commit_pct}% ({commit_count} commits mentioning task)")
    else:
        print(muted("📝 Git Commits: 0 (no commits mention this task)"))
    print()

    # Inferred total
    inferred = breakdown.get("inferred")
    if inferred is not None:
        print("─" * 40)
        if inferred != manual_val:
            print(f"🎯 Inferred Progress: {inferred}% (vs {manual_val}% manual)")
        else:
            print(f"🎯 Inferred Progress: {inferred}%")
    else:
        print(muted("🎯 Inferred Progress: Unable to calculate"))

    return 0


def cmd_snapshot(args) -> int:
    """Manage session snapshots for cross-session continuity."""
    from session_snapshot import (
        capture_snapshot, load_snapshot, load_all_snapshots, get_recent_snapshots
    )
    from style import header, success, warning, muted, bold

    action = args.action if hasattr(args, 'action') else "show"

    # List recent snapshots
    if action == "list":
        snapshots = get_recent_snapshots(10)
        if not snapshots:
            print(muted("No snapshots found"))
            return 0

        print(header("Recent Snapshots"))
        print()
        for snap in snapshots:
            ts = snap.timestamp[:19].replace("T", " ")
            action_str = snap.last_action or "working"
            print(f"[{snap.agent_id}] {ts} - {action_str}")
            if snap.last_file:
                print(f"  └─ {snap.last_file[:50]}")
        return 0

    # Get agent ID
    agent_id = args.id if hasattr(args, 'id') and args.id else None
    if not agent_id:
        scheduler = get_scheduler()
        queue = scheduler.get_queue()
        if queue:
            agent_id = queue[0]["id"]
        else:
            print(warning("No active tasks"))
            return 1

    agent = get_agent(agent_id)
    if not agent:
        print(warning(f"Agent not found: {agent_id}"))
        return 1

    # Capture snapshot
    if action == "capture":
        summary = args.summary if hasattr(args, 'summary') else None
        next_step = getattr(args, 'next', None)
        questions = args.question if hasattr(args, 'question') else None

        snapshot = capture_snapshot(
            agent_id,
            context_summary=summary,
            open_questions=questions,
            next_step=next_step
        )

        if snapshot:
            print(success(f"Snapshot captured for [{agent_id}]"))
            if snapshot.last_file:
                print(f"  └─ Last file: {snapshot.last_file}")
            if snapshot.next_step:
                print(f"  └─ Next step: {snapshot.next_step}")
        else:
            print(warning("Failed to capture snapshot"))
        return 0

    # Show snapshot (default)
    snapshot = load_snapshot(agent_id)
    if not snapshot:
        print(muted(f"No snapshot for [{agent_id}]"))
        print(muted("Use 'ctm snapshot capture' to create one"))
        return 0

    print(header(f"Snapshot: [{agent_id}]"))
    print()

    # Timestamp
    ts = snapshot.timestamp[:19].replace("T", " ")
    print(f"Captured: {ts}")
    print()

    # Where you stopped
    print(bold("Where you stopped:"))
    if snapshot.last_file:
        line_info = f":{snapshot.last_line}" if snapshot.last_line else ""
        print(f"├─ File: {snapshot.last_file}{line_info}")
    print(f"├─ Action: {snapshot.last_action}")
    if snapshot.context_summary:
        print(f"└─ Context: {snapshot.context_summary[:60]}")
    print()

    # Git context
    if snapshot.last_commit or snapshot.uncommitted_files:
        print(bold("Git context:"))
        if snapshot.last_commit:
            print(f"├─ Last commit: {snapshot.last_commit[:50]}")
        if snapshot.uncommitted_files:
            print(f"└─ Uncommitted: {len(snapshot.uncommitted_files)} file(s)")
            for f in snapshot.uncommitted_files[:3]:
                print(f"    • {f}")
            if len(snapshot.uncommitted_files) > 3:
                print(f"    ... and {len(snapshot.uncommitted_files) - 3} more")
        print()

    # Recent decisions
    if snapshot.recent_decisions:
        print(bold("Recent decisions:"))
        for dec in snapshot.recent_decisions:
            print(f"• {dec[:60]}")
        print()

    # Open questions
    if snapshot.open_questions:
        print(bold("Open questions:"))
        for q in snapshot.open_questions:
            print(f"? {q}")
        print()

    # Next step
    if snapshot.next_step:
        print(bold("Next suggested step:"))
        print(f"→ {snapshot.next_step}")

    return 0


def cmd_templates(args) -> int:
    """List and manage task templates."""
    from templates import (
        list_templates, load_template, save_template,
        create_template_from_agent, validate_template, get_template_info
    )
    from style import header, success, warning, muted, bold, info

    action = args.action if hasattr(args, 'action') else "list"

    # List templates
    if action == "list":
        templates = list_templates()
        if not templates:
            print(muted("No templates found"))
            print(info("Templates directory: ~/.claude/ctm/templates/"))
            return 0

        print(header("Available Templates"))
        print()
        for name in templates:
            template_info = get_template_info(name)
            if template_info:
                desc = template_info.get("description", "")[:50]
                phases = template_info.get("phases", 0)
                print(f"  {bold(name)}")
                if desc:
                    print(f"    {desc}")
                print(f"    {phases} phases | {template_info.get('total_steps', 0)} steps")
                print()
        return 0

    # Show template details
    if action == "show":
        name = args.name if hasattr(args, 'name') and args.name else None
        if not name:
            print(warning("Usage: ctm templates show <name>"))
            return 1

        template = load_template(name)
        if not template:
            print(warning(f"Template not found: {name}"))
            return 1

        print(header(f"Template: {template.name}"))
        print()
        if template.description:
            print(template.description)
            print()

        print(bold("Defaults:"))
        print(f"  Priority: {template.defaults.priority_value}")
        print(f"  Urgency: {template.defaults.priority_urgency}")
        if template.defaults.key_files:
            print(f"  Key files: {len(template.defaults.key_files)}")
        print()

        if template.tags:
            print(f"Tags: {', '.join(template.tags)}")
            print()

        print(bold("Phases:"))
        for i, phase in enumerate(template.phases, 1):
            deps = f" ← {', '.join(phase.blocked_by)}" if phase.blocked_by else ""
            print(f"  {i}. {phase.title} ({phase.progress_weight}%){deps}")
            for step in phase.steps:
                print(f"     • {step}")
        print()

        # Validate
        errors = validate_template(template)
        if errors:
            print(warning("Validation issues:"))
            for err in errors:
                print(f"  ⚠ {err}")

        return 0

    # Create template from agent
    if action == "create":
        name = args.name if hasattr(args, 'name') and args.name else None
        from_agent = args.from_agent if hasattr(args, 'from_agent') and args.from_agent else None

        if not name:
            print(warning("Usage: ctm templates create <name> --from <agent_id>"))
            return 1

        if not from_agent:
            print(warning("Must specify --from <agent_id>"))
            return 1

        agent_id = resolve_agent_id(from_agent)
        if not agent_id:
            print(warning(f"Agent not found: {from_agent}"))
            return 1

        agent = get_agent(agent_id)
        if not agent:
            print(warning(f"Agent not found: {agent_id}"))
            return 1

        template = create_template_from_agent(agent, name)
        path = save_template(template, name)

        print(success(f"Template created: {name}"))
        print(f"  Saved to: {path}")
        print(f"  Phases: {len(template.phases)}")

        return 0

    return 0


def cmd_queue(args) -> int:
    """Show priority queue."""
    scheduler = get_scheduler()
    scheduler.rebuild_queue()
    queue = scheduler.get_queue()

    if not queue:
        print("Queue is empty.")
        return 0

    print("═══ Priority Queue ═══")
    print()

    for i, item in enumerate(queue, 1):
        marker = "▶" if item["status"] == "active" else "○"
        print(f"{i}. {marker} [{item['id']}] {item['title']}")
        print(f"      Score: {item['score']:.3f} | Status: {item['status']}")

    return 0


def cmd_brief(args) -> int:
    """Generate session briefing."""
    try:
        from briefing import generate_briefing
        verbose = getattr(args, 'verbose', False)
        briefing = generate_briefing(verbose=verbose)
        print(briefing)
        return 0
    except ImportError:
        # Fallback to simple briefing
        scheduler = get_scheduler()
        index = AgentIndex()

        print("═══ Session Briefing ═══")
        print()

        active_ids = index.get_all_active()
        if not active_ids:
            print("No active tasks. Ready for new work!")
            return 0

        print(f"You have {len(active_ids)} active task(s):")
        print()

        scheduler.rebuild_queue()
        queue = scheduler.get_queue()

        for i, item in enumerate(queue[:5], 1):
            agent = get_agent(item["id"])
            if agent:
                print(f"{i}. [{agent.id}] {agent.task['title']} ({agent.state['progress_pct']}%)")

        if queue:
            top = queue[0]
            print()
            print(f"Recommendation: Continue with [{top['id']}] {top['title']}")

        return 0


def cmd_consolidate(args) -> int:
    """Consolidate agent context into project memory."""
    try:
        from consolidation import consolidate_agent, consolidate_session
        from pathlib import Path

        project_path = Path(args.project) if args.project else Path.cwd()

        if args.id:
            # Consolidate specific agent
            result = consolidate_agent(args.id, project_path)
        else:
            # Consolidate all active agents
            result = consolidate_session(project_path)

        if "error" in result:
            print(f"✗ {result['error']}")
            return 1

        print("✓ Consolidation complete")
        if result.get("decisions_extracted"):
            print(f"  - {result['decisions_extracted']} decision(s) → DECISIONS.md")
        if result.get("session_logged"):
            print(f"  - Session logged → SESSIONS.md")
        if result.get("rag_indexed"):
            count = result["rag_indexed"] if isinstance(result["rag_indexed"], int) else 1
            print(f"  - {count} agent(s) indexed → RAG")

        return 0
    except ImportError as e:
        print(f"Consolidation module not available: {e}")
        return 1


def cmd_memory(args) -> int:
    """Show working memory status."""
    try:
        from memory import get_working_memory
        wm = get_working_memory()
        stats = wm.get_stats()

        print("═══ Working Memory ═══")
        print()
        print(f"Loaded: {stats['loaded_count']}/{stats['max_capacity']} agents")
        print(f"Tokens: {stats['token_usage']}/{stats['token_budget']} ({stats['usage_pct']}%)")
        print(f"Evictions: {stats['eviction_count']}")

        if stats['last_eviction']:
            print(f"Last eviction: {stats['last_eviction'][:19]}")

        loaded = wm.get_loaded_agents()
        if loaded:
            print()
            print("Hot agents:")
            for aid in loaded:
                slot = wm.get_slot(aid)
                agent = get_agent(aid)
                if agent and slot:
                    print(f"  [{aid}] {agent.task['title'][:40]} ({slot['token_estimate']} tokens)")

        return 0
    except ImportError:
        print("Working memory module not available")
        return 1


def cmd_hooks(args) -> int:
    """Manage CTM hooks."""
    try:
        from integration import get_hook_integration
        hi = get_hook_integration()

        if args.action == "install":
            hi.ensure_hooks_dir()
            if hi.install_hooks():
                print("✓ CTM hooks installed")
                print("  - SessionStart: Show briefing")
                print("  - PreCompact: Checkpoint agents")
                print("  - SessionEnd: Final save")
                return 0
            else:
                print("✗ Failed to install hooks")
                return 1

        elif args.action == "status":
            import json
            settings_path = hi.settings_path
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    settings = json.load(f)
                hooks = settings.get("hooks", {})

                print("═══ CTM Hooks Status ═══")
                print()

                for hook_type in ["SessionStart", "PreCompact", "SessionEnd"]:
                    hook_list = hooks.get(hook_type, [])
                    ctm_hooks = [h for h in hook_list
                                if any("ctm-" in hk.get("command", "") for hk in h.get("hooks", []))]
                    status = "✓ Installed" if ctm_hooks else "✗ Not installed"
                    print(f"  {hook_type}: {status}")

                return 0
            else:
                print("Settings file not found")
                return 1

        return 0
    except ImportError as e:
        print(f"Integration module not available: {e}")
        return 1


def cmd_repair(args) -> int:
    """Repair CTM data files."""
    from errors import handle_error, ErrorLogger
    import shutil
    from datetime import datetime

    ctm_dir = get_ctm_dir()
    backup_dir = ctm_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")
    repairs_made = []
    errors_found = []

    print("═══ CTM Repair ═══")
    print()

    # Determine what to repair
    repair_all = not any([args.config, args.agents, args.scheduler, args.index, args.memory])

    # 1. Repair config
    if repair_all or args.config:
        print("Checking config...")
        config_path = ctm_dir / "config.json"
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    json.loads(f.read())
                print("  ✓ config.json is valid")
            else:
                # Create default config
                default_config = {
                    "version": "1.0",
                    "max_active_agents": 10,
                    "working_memory": {"max_agents": 5, "token_budget": 8000},
                    "priority": {"decay_rate": 0.1, "recency_weight": 0.3},
                    "auto_checkpoint": True,
                    "auto_consolidate": True
                }
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                repairs_made.append("Created default config.json")
                print("  ✓ Created default config.json")
        except json.JSONDecodeError as e:
            errors_found.append(f"config.json: {e}")
            # Backup and recreate
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(config_path, backup_dir / "config.json.bak")
            default_config = {
                "version": "1.0",
                "max_active_agents": 10,
                "working_memory": {"max_agents": 5, "token_budget": 8000},
                "priority": {"decay_rate": 0.1, "recency_weight": 0.3},
                "auto_checkpoint": True,
                "auto_consolidate": True
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            repairs_made.append("Rebuilt config.json (backup saved)")
            print("  ⚠ Rebuilt config.json (backup saved)")

    # 2. Repair index
    if repair_all or args.index:
        print("Checking index...")
        index_path = ctm_dir / "index.json"
        agents_dir = ctm_dir / "agents"

        try:
            if index_path.exists():
                with open(index_path, 'r') as f:
                    index_data = json.load(f)
            else:
                index_data = {"agents": {}, "by_status": {}, "by_project": {}}

            # Scan agents directory for actual files
            actual_agents = {}
            if agents_dir.exists():
                for agent_file in agents_dir.glob("*.json"):
                    try:
                        with open(agent_file, 'r') as f:
                            agent_data = json.load(f)
                        aid = agent_file.stem
                        actual_agents[aid] = agent_data
                    except:
                        errors_found.append(f"Corrupted agent file: {agent_file.name}")

            # Rebuild index from actual files
            indexed_ids = set(index_data.get("agents", {}).keys())
            actual_ids = set(actual_agents.keys())

            missing_from_index = actual_ids - indexed_ids
            orphaned_in_index = indexed_ids - actual_ids

            if missing_from_index:
                for aid in missing_from_index:
                    agent = actual_agents[aid]
                    status = agent.get("state", {}).get("status", "active")
                    project = agent.get("context", {}).get("project", "")

                    index_data["agents"][aid] = {
                        "status": status,
                        "project": project,
                        "title": agent.get("task", {}).get("title", "Unknown")
                    }
                repairs_made.append(f"Re-indexed {len(missing_from_index)} agent(s)")
                print(f"  ⚠ Re-indexed {len(missing_from_index)} agent(s)")

            if orphaned_in_index:
                for aid in orphaned_in_index:
                    del index_data["agents"][aid]
                repairs_made.append(f"Removed {len(orphaned_in_index)} orphaned index entries")
                print(f"  ⚠ Removed {len(orphaned_in_index)} orphaned index entries")

            # Rebuild by_status and by_project
            by_status = {}
            by_project = {}
            for aid, info in index_data["agents"].items():
                status = info.get("status", "active")
                project = info.get("project", "")

                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(aid)

                if project:
                    if project not in by_project:
                        by_project[project] = []
                    by_project[project].append(aid)

            index_data["by_status"] = by_status
            index_data["by_project"] = by_project

            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)

            if not missing_from_index and not orphaned_in_index:
                print("  ✓ index.json is valid")

        except json.JSONDecodeError as e:
            errors_found.append(f"index.json: {e}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            if index_path.exists():
                shutil.copy(index_path, backup_dir / "index.json.bak")
            # Rebuild from scratch
            index_data = {"agents": {}, "by_status": {}, "by_project": {}}
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
            repairs_made.append("Rebuilt index.json (backup saved)")
            print("  ⚠ Rebuilt index.json (backup saved)")

    # 3. Repair scheduler
    if repair_all or args.scheduler:
        print("Checking scheduler...")
        scheduler_path = ctm_dir / "scheduler.json"
        try:
            if scheduler_path.exists():
                with open(scheduler_path, 'r') as f:
                    sched_data = json.load(f)

                # Validate active_agent exists
                active = sched_data.get("active_agent")
                if active:
                    index = AgentIndex()
                    if active not in index._data.get("agents", {}):
                        sched_data["active_agent"] = None
                        repairs_made.append("Cleared invalid active_agent reference")
                        print("  ⚠ Cleared invalid active_agent reference")

                with open(scheduler_path, 'w') as f:
                    json.dump(sched_data, f, indent=2)
                print("  ✓ scheduler.json is valid")
            else:
                default_scheduler = {
                    "active_agent": None,
                    "queue": [],
                    "session": {"started_at": None, "switches": 0, "checkpoints": 0}
                }
                with open(scheduler_path, 'w') as f:
                    json.dump(default_scheduler, f, indent=2)
                repairs_made.append("Created default scheduler.json")
                print("  ✓ Created default scheduler.json")
        except json.JSONDecodeError as e:
            errors_found.append(f"scheduler.json: {e}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(scheduler_path, backup_dir / "scheduler.json.bak")
            default_scheduler = {
                "active_agent": None,
                "queue": [],
                "session": {"started_at": None, "switches": 0, "checkpoints": 0}
            }
            with open(scheduler_path, 'w') as f:
                json.dump(default_scheduler, f, indent=2)
            repairs_made.append("Rebuilt scheduler.json (backup saved)")
            print("  ⚠ Rebuilt scheduler.json (backup saved)")

    # 4. Repair agents
    if repair_all or args.agents:
        print("Checking agents...")
        agents_dir = ctm_dir / "agents"
        if agents_dir.exists():
            repaired_count = 0
            for agent_file in agents_dir.glob("*.json"):
                try:
                    with open(agent_file, 'r') as f:
                        agent_data = json.load(f)

                    # Validate required fields
                    modified = False
                    if "task" not in agent_data:
                        agent_data["task"] = {"title": "Unknown", "goal": ""}
                        modified = True
                    if "state" not in agent_data:
                        agent_data["state"] = {"status": "active", "progress_pct": 0}
                        modified = True
                    if "priority" not in agent_data:
                        agent_data["priority"] = {"level": "normal", "user_signal": 0}
                        modified = True
                    if "timing" not in agent_data:
                        now = datetime.now().isoformat()
                        agent_data["timing"] = {
                            "created_at": now,
                            "last_active": now,
                            "session_count": 0
                        }
                        modified = True
                    if "context" not in agent_data:
                        agent_data["context"] = {}
                        modified = True

                    if modified:
                        with open(agent_file, 'w') as f:
                            json.dump(agent_data, f, indent=2)
                        repaired_count += 1

                except json.JSONDecodeError:
                    backup_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy(agent_file, backup_dir / agent_file.name)
                    agent_file.unlink()
                    errors_found.append(f"Removed corrupted {agent_file.name}")

            if repaired_count > 0:
                repairs_made.append(f"Repaired {repaired_count} agent file(s)")
                print(f"  ⚠ Repaired {repaired_count} agent file(s)")
            else:
                print("  ✓ All agent files valid")
        else:
            agents_dir.mkdir(parents=True, exist_ok=True)
            print("  ✓ Created agents directory")

    # 5. Repair memory
    if repair_all or args.memory:
        print("Checking memory...")
        memory_path = ctm_dir / "memory.json"
        try:
            if memory_path.exists():
                with open(memory_path, 'r') as f:
                    json.load(f)
                print("  ✓ memory.json is valid")
            else:
                print("  ✓ No memory.json (optional)")
        except json.JSONDecodeError:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy(memory_path, backup_dir / "memory.json.bak")
            memory_path.unlink()
            repairs_made.append("Removed corrupted memory.json")
            print("  ⚠ Removed corrupted memory.json (backup saved)")

    # Summary
    print()
    if repairs_made:
        print(f"Repairs made: {len(repairs_made)}")
        for r in repairs_made:
            print(f"  • {r}")
    else:
        print("✓ No repairs needed")

    if errors_found:
        print()
        print(f"Errors found: {len(errors_found)}")
        for e in errors_found:
            print(f"  • {e}")

    if backup_dir.exists():
        print()
        print(f"Backups saved to: {backup_dir}")

    # Clear error log if requested
    if args.clear_log:
        logger = ErrorLogger()
        logger.clear()
        print("✓ Error log cleared")

    return 0 if not errors_found else 1


def cmd_context(args) -> int:
    """Manage agent context (decisions, learnings)."""
    from style import bold, success, muted, info, warning

    scheduler = get_scheduler()

    # Get agent ID
    agent_id = args.id
    if not agent_id:
        agent_id = scheduler.get_active()

    if not agent_id:
        print(warning("No agent specified and none active."))
        return 1

    agent_id = resolve_agent_id(agent_id)
    agent = get_agent(agent_id)

    if not agent:
        print(f"Agent not found: {args.id}")
        return 1

    # Handle subcommands
    if args.action == "show":
        print(bold(f"═══ Context: [{agent.id}] ═══"))
        print()

        decisions = agent.context.get("decisions", [])
        learnings = agent.context.get("learnings", [])
        files = agent.context.get("key_files", [])

        if decisions:
            print(info("Decisions:"))
            for d in decisions[-5:]:
                ts = d.get("timestamp", "")[:10]
                print(f"  • {d['text']} {muted(f'({ts})')}")
            if len(decisions) > 5:
                print(muted(f"  ... and {len(decisions) - 5} more"))
            print()

        if learnings:
            print(info("Learnings:"))
            for l in learnings[-5:]:
                print(f"  • {l['text']}")
            if len(learnings) > 5:
                print(muted(f"  ... and {len(learnings) - 5} more"))
            print()

        if files:
            print(info("Key Files:"))
            for f in files[:10]:
                print(f"  • {f}")
            if len(files) > 10:
                print(muted(f"  ... and {len(files) - 10} more"))

        if not decisions and not learnings and not files:
            print(muted("No context recorded yet."))

        return 0

    elif args.action == "add":
        if args.decision:
            agent.add_decision(args.decision)
            update_agent(agent)
            print(f"{success('✓')} Decision added to [{agent.id}]")
        elif args.learning:
            agent.add_learning(args.learning)
            update_agent(agent)
            print(f"{success('✓')} Learning added to [{agent.id}]")
        elif args.file:
            if args.file not in agent.context.get("key_files", []):
                if "key_files" not in agent.context:
                    agent.context["key_files"] = []
                agent.context["key_files"].append(args.file)
                update_agent(agent)
                print(f"{success('✓')} File added to [{agent.id}]")
            else:
                print(muted("File already in context"))
        else:
            print(warning("Specify --decision, --learning, or --file"))
            return 1
        return 0

    elif args.action == "clear":
        if args.decisions:
            agent.context["decisions"] = []
            update_agent(agent)
            print(f"{success('✓')} Decisions cleared for [{agent.id}]")
        elif args.learnings:
            agent.context["learnings"] = []
            update_agent(agent)
            print(f"{success('✓')} Learnings cleared for [{agent.id}]")
        else:
            print(warning("Specify --decisions or --learnings"))
            return 1
        return 0

    return 0


def cmd_checkpoint(args) -> int:
    """Create a checkpoint of current agent state."""
    from style import success, bold, muted, warning
    import shutil

    ctm_dir = get_ctm_dir()
    checkpoint_dir = ctm_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    checkpoint_path = checkpoint_dir / timestamp

    scheduler = get_scheduler()
    index = AgentIndex()

    # Get agents to checkpoint
    if args.id:
        agent_ids = [resolve_agent_id(args.id)]
    else:
        agent_ids = index.get_all_active()

    if not agent_ids:
        print(muted("No agents to checkpoint."))
        return 0

    # Create checkpoint directory
    checkpoint_path.mkdir(parents=True, exist_ok=True)

    # Save each agent's state
    saved = 0
    for aid in agent_ids:
        if not aid:
            continue
        agent = get_agent(aid)
        if agent:
            # Update last_active before checkpoint
            agent.update_activity()
            agent.save()

            # Copy to checkpoint
            src = ctm_dir / "agents" / f"{aid}.json"
            dst = checkpoint_path / f"{aid}.json"
            if src.exists():
                shutil.copy(src, dst)
                saved += 1

    # Save scheduler state
    scheduler_src = ctm_dir / "scheduler.json"
    if scheduler_src.exists():
        shutil.copy(scheduler_src, checkpoint_path / "scheduler.json")

    # Save index
    index_src = ctm_dir / "index.json"
    if index_src.exists():
        shutil.copy(index_src, checkpoint_path / "index.json")

    # Update session stats
    scheduler._state["session"]["checkpoints"] += 1
    scheduler._save_state()

    print(f"{success('✓')} Checkpoint created: {bold(timestamp)}")
    print(f"  {muted(f'{saved} agent(s) saved')}")

    # Prune old checkpoints (keep last 10)
    checkpoints = sorted(checkpoint_dir.iterdir(), reverse=True)
    if len(checkpoints) > 10:
        for old_cp in checkpoints[10:]:
            if old_cp.is_dir():
                shutil.rmtree(old_cp)
        print(muted(f"  (pruned {len(checkpoints) - 10} old checkpoints)"))

    return 0


def cmd_restore(args) -> int:
    """Restore agents from a checkpoint."""
    from style import success, bold, muted, warning, error
    import shutil

    ctm_dir = get_ctm_dir()
    checkpoint_dir = ctm_dir / "checkpoints"

    if not checkpoint_dir.exists():
        print(error("No checkpoints found."))
        return 1

    checkpoints = sorted([d for d in checkpoint_dir.iterdir() if d.is_dir()], reverse=True)
    if not checkpoints:
        print(error("No checkpoints found."))
        return 1

    # Select checkpoint
    if args.checkpoint:
        checkpoint_path = checkpoint_dir / args.checkpoint
        if not checkpoint_path.exists():
            print(error(f"Checkpoint not found: {args.checkpoint}"))
            return 1
    else:
        # Use latest
        checkpoint_path = checkpoints[0]

    if args.list:
        print(bold("═══ Checkpoints ═══"))
        print()
        for i, cp in enumerate(checkpoints[:10]):
            marker = "→" if cp == checkpoint_path else " "
            print(f"  {marker} {cp.name}")
        return 0

    # Restore from checkpoint
    agents_restored = 0
    for agent_file in checkpoint_path.glob("*.json"):
        if agent_file.name in ("scheduler.json", "index.json"):
            continue
        dst = ctm_dir / "agents" / agent_file.name
        shutil.copy(agent_file, dst)
        agents_restored += 1

    # Invalidate caches
    from agents import invalidate_agent_cache
    from scheduler import invalidate_scheduler_cache
    invalidate_agent_cache()
    invalidate_scheduler_cache()

    print(f"{success('✓')} Restored from checkpoint: {bold(checkpoint_path.name)}")
    print(f"  {muted(f'{agents_restored} agent(s) restored')}")

    return 0


def cmd_delegate(args) -> int:
    """Delegate a task to a worker agent using CDP protocol."""
    from style import success, bold, muted, info

    # Generate task ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    agent_type = args.agent or "worker"
    task_id = f"{agent_type}-{timestamp}"

    # Determine workspace location
    project_path = Path(args.project) if args.project else Path.cwd()
    workspace_dir = project_path / ".agent-workspaces" / task_id
    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Build HANDOFF.md content
    handoff_content = f"""# Task Handoff

**Task ID:** {task_id}
**Agent:** {agent_type}
**Created:** {datetime.now().isoformat()}

## Task
{args.title}

## Context
{args.context or "No additional context provided."}

## Key Files
"""

    if args.files:
        for f in args.files.split(","):
            handoff_content += f"- `{f.strip()}`\n"
    else:
        handoff_content += "- None specified\n"

    handoff_content += "\n## Constraints\n"
    if args.constraints:
        for c in args.constraints.split(","):
            handoff_content += f"- {c.strip()}\n"
    else:
        handoff_content += "- None specified\n"

    handoff_content += "\n## Expected Deliverables\n"
    if args.deliverables:
        for d in args.deliverables.split(","):
            handoff_content += f"- [ ] {d.strip()}\n"
    else:
        handoff_content += "- [ ] Task completion\n"

    handoff_content += """
## Return Requirements
Write OUTPUT.md with:
- Summary (1-3 sentences)
- Deliverables table with file paths
- Decisions made
- Notes for primary conversation
"""

    # Write HANDOFF.md
    handoff_path = workspace_dir / "HANDOFF.md"
    with open(handoff_path, 'w') as f:
        f.write(handoff_content)

    # Create empty OUTPUT.md template
    output_template = f"""# Task: {args.title}

**Status:** pending
**Agent:** {agent_type}

## Summary
[Agent will fill this in]

## Deliverables
| File | Description |
|------|-------------|
| | |

## Decisions Made
-

## For Primary
[Information the main conversation needs]

## Files Modified
-
"""
    output_path = workspace_dir / "OUTPUT.md"
    with open(output_path, 'w') as f:
        f.write(output_template)

    # Create CTM agent to track this delegation
    agent = create_agent(
        title=f"[CDP] {args.title}",
        goal=f"Delegated task: {args.title}",
        project=str(project_path),
        priority="normal",
        tags=["cdp", "delegated", agent_type]
    )

    # Store workspace reference in agent context
    agent.context["cdp_workspace"] = str(workspace_dir)
    agent.context["cdp_task_id"] = task_id
    update_agent(agent)

    print(f"{success('✓')} Delegation prepared: {bold(task_id)}")
    print(f"  {info('Workspace:')} {workspace_dir}")
    print(f"  {info('Agent:')} {agent_type}")
    print(f"  {info('CTM ID:')} [{agent.id}]")
    print()
    print(muted("To execute, use Task tool with:"))
    print(f"  subagent_type: {agent_type}")
    print(f"  prompt: Read HANDOFF.md at {handoff_path}")
    print()
    print(muted("Agent will write results to:"))
    print(f"  {workspace_dir}/OUTPUT.md")

    return 0


def cmd_project(args) -> int:
    """
    Manage project context for CTM.

    v2.1: Project-aware task scheduling - tasks from the current project
    get priority boost and are shown first in briefings.
    """
    from style import bold, success, muted, info, warning

    scheduler = get_scheduler()

    if args.action == "show" or args.action is None:
        # Show current project context
        project_context = scheduler.get_project_context()
        status = scheduler.get_status()

        print(bold("═══ Project Context ═══"))
        print()

        if project_context:
            project_name = Path(project_context).name
            print(f"📁 Current Project: {info(project_name)}")
            print(f"   Path: {muted(project_context)}")
            print(f"   Tasks: {status.get('project_tasks', 0)} in this project")
            print()

            # Show tasks grouped by project
            by_project = scheduler.get_agents_by_project()

            if project_context in by_project:
                print(info("Tasks in this project:"))
                for aid in by_project[project_context][:5]:
                    agent = get_agent(aid)
                    if agent:
                        pct = agent.state.get("progress_pct", 0)
                        print(f"  • [{aid}] {agent.task['title'][:40]} ({pct}%)")

            # Show other projects
            other_projects = {k: v for k, v in by_project.items() if k != project_context}
            if other_projects:
                print()
                print(muted("Other projects:"))
                for proj, agents in list(other_projects.items())[:3]:
                    proj_name = Path(proj).name if proj else "unknown"
                    print(f"  • {proj_name}: {len(agents)} task(s)")
        else:
            print(muted("No project context set."))
            print()
            print("Use 'ctm project set <path>' to set project context,")
            print("or start Claude from a project directory to auto-detect.")

        return 0

    elif args.action == "set":
        # Set project context
        if not args.path:
            print(warning("Specify a path to set project context"))
            return 1

        path = Path(args.path).expanduser().resolve()
        if not path.exists():
            print(f"Path not found: {args.path}")
            return 1

        scheduler.set_project_context(str(path))
        scheduler.rebuild_queue()

        project_name = path.name
        status = scheduler.get_status()
        print(f"{success('✓')} Project context set to: {info(project_name)}")
        print(f"   {status.get('project_tasks', 0)} task(s) in this project")

        return 0

    elif args.action == "clear":
        # Clear project context
        scheduler.set_project_context(None)
        scheduler.rebuild_queue()
        print(f"{success('✓')} Project context cleared")
        return 0

    elif args.action == "detect":
        # Auto-detect project context from cwd
        detected = scheduler.detect_project_context()
        if detected:
            scheduler.set_project_context(detected)
            scheduler.rebuild_queue()

            project_name = Path(detected).name
            status = scheduler.get_status()
            print(f"{success('✓')} Detected project: {info(project_name)}")
            print(f"   Path: {muted(detected)}")
            print(f"   {status.get('project_tasks', 0)} task(s) in this project")
        else:
            print(muted("Could not detect project context from current directory."))
        return 0

    return 0


def cmd_workspace(args) -> int:
    """Manage CDP workspaces."""
    from style import bold, success, muted, info, warning
    import shutil

    # Find all workspace directories in current project and common locations
    workspaces = []

    # Check current directory
    cwd_workspaces = Path.cwd() / ".agent-workspaces"
    if cwd_workspaces.exists():
        for ws in cwd_workspaces.iterdir():
            if ws.is_dir():
                workspaces.append(ws)

    # Check home directory projects
    home_projects = Path.home() / "Documents" / "Projects - Pro"
    if home_projects.exists():
        for project in home_projects.rglob(".agent-workspaces"):
            if project.is_dir():
                for ws in project.iterdir():
                    if ws.is_dir():
                        workspaces.append(ws)

    if args.action == "list":
        if not workspaces:
            print(muted("No workspaces found."))
            return 0

        print(bold("═══ CDP Workspaces ═══"))
        print()

        for ws in sorted(workspaces, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
            output_file = ws / "OUTPUT.md"
            handoff_file = ws / "HANDOFF.md"

            # Determine status
            if output_file.exists():
                with open(output_file, 'r') as f:
                    content = f.read()
                if "completed" in content.lower():
                    status = success("completed")
                elif "blocked" in content.lower():
                    status = warning("blocked")
                else:
                    status = info("pending")
            else:
                status = muted("no output")

            # Get task title from HANDOFF.md
            title = ws.name
            if handoff_file.exists():
                with open(handoff_file, 'r') as f:
                    for line in f:
                        if line.startswith("## Task"):
                            title = next(f, ws.name).strip()
                            break

            print(f"  [{ws.name}] {title[:50]}")
            print(f"    {muted('Status:')} {status}  {muted('Path:')} {ws.parent.parent.name}/")

        return 0

    elif args.action == "show":
        if not args.task_id:
            print(warning("Specify task_id to show"))
            return 1

        # Find workspace
        target = None
        for ws in workspaces:
            if args.task_id in ws.name:
                target = ws
                break

        if not target:
            print(f"Workspace not found: {args.task_id}")
            return 1

        print(bold(f"═══ Workspace: {target.name} ═══"))
        print()

        # Show HANDOFF.md
        handoff = target / "HANDOFF.md"
        if handoff.exists():
            print(info("── HANDOFF.md ──"))
            with open(handoff, 'r') as f:
                print(f.read()[:1000])
            print()

        # Show OUTPUT.md
        output = target / "OUTPUT.md"
        if output.exists():
            print(info("── OUTPUT.md ──"))
            with open(output, 'r') as f:
                print(f.read())

        return 0

    elif args.action == "clean":
        # Remove completed workspaces older than 7 days
        cleaned = 0
        now = datetime.now().timestamp()
        seven_days = 7 * 24 * 60 * 60

        for ws in workspaces:
            output = ws / "OUTPUT.md"
            if output.exists():
                with open(output, 'r') as f:
                    content = f.read()
                if "completed" in content.lower():
                    age = now - ws.stat().st_mtime
                    if age > seven_days:
                        shutil.rmtree(ws)
                        cleaned += 1

        print(f"{success('✓')} Cleaned {cleaned} old workspace(s)")
        return 0

    return 0


def cmd_help(args) -> int:
    """Show help."""
    print("""
CTM - Cognitive Task Manager (Cognitive Continuity)

Commands:
  status              Show current state and active agent
  list [--all]        List agents (active by default, --all for all)
  show <id>           Show detailed agent info
  spawn <title>       Create new agent
  switch <id>         Switch to an agent
  pause [id]          Pause agent (current if no id)
  resume <id>         Resume a paused agent
  complete [id]       Mark agent complete (current if no id)
  cancel <id>         Cancel an agent
  priority <id> <+/-> Adjust priority up (+) or down (-)
  queue               Show full priority queue
  brief               Generate session briefing
  memory              Show working memory status
  checkpoint [id]     Save current agent state (all active if no id)
  restore [name]      Restore from checkpoint (latest if no name)
  consolidate [id]    Consolidate to DECISIONS.md, SESSIONS.md, RAG
  hooks install       Install CTM hooks for auto-invocation
  hooks status        Check hook installation status
  repair              Check and repair CTM data files

Cognitive Delegation Protocol (CDP):
  delegate <title>    Delegate task to worker agent
  workspace list      List all CDP workspaces
  workspace show <id> Show workspace details (HANDOFF.md + OUTPUT.md)
  workspace clean     Remove completed workspaces older than 7 days

Options:
  --project PATH      Filter by project path
  --status STATUS     Filter by status (active/paused/blocked/completed)
  --priority LEVEL    Set priority (critical/high/normal/low/background)
  --tags TAGS         Comma-separated tags
  --switch            Switch to agent after spawning

Delegate Options:
  --agent TYPE        Agent type (default: worker)
  --context TEXT      Context to pass to agent
  --files FILES       Comma-separated key files
  --constraints TEXT  Comma-separated constraints
  --deliverables TEXT Comma-separated expected deliverables

Examples:
  ctm spawn "Fix login bug" --priority high --switch
  ctm list --all
  ctm switch abc123
  ctm complete
  ctm priority abc123 +
  ctm hooks install

  # CDP delegation
  ctm delegate "Create CSV parser" --files data/sample.csv --deliverables "scripts/parser.py,tests/test_parser.py"
  ctm workspace list
  ctm workspace show worker-20260108
""")
    return 0


def resolve_agent_id(partial_id: str) -> Optional[str]:
    """Resolve a partial agent ID to full ID."""
    index = AgentIndex()

    # Check exact match first
    if partial_id in index._data["agents"]:
        return partial_id

    # Check prefix match
    matches = [aid for aid in index._data["agents"] if aid.startswith(partial_id)]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"Ambiguous ID '{partial_id}', matches: {', '.join(matches)}")
        return None

    return None


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="ctm",
        description="Cognitive Task Manager - Bio-inspired task management"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status
    subparsers.add_parser("status", help="Show current state")

    # list
    list_parser = subparsers.add_parser("list", help="List agents")
    list_parser.add_argument("--all", "-a", action="store_true", help="Show all agents")
    list_parser.add_argument("--status", "-s", help="Filter by status")
    list_parser.add_argument("--project", "-p", help="Filter by project")

    # show
    show_parser = subparsers.add_parser("show", help="Show agent details")
    show_parser.add_argument("id", help="Agent ID")

    # spawn
    spawn_parser = subparsers.add_parser("spawn", help="Create new agent")
    spawn_parser.add_argument("title", help="Task title")
    spawn_parser.add_argument("--goal", "-g", help="Task goal")
    spawn_parser.add_argument("--project", "-p", help="Project path")
    spawn_parser.add_argument("--priority", help="Priority level")
    spawn_parser.add_argument("--tags", "-t", help="Comma-separated tags")
    spawn_parser.add_argument("--triggers", help="Comma-separated triggers")
    spawn_parser.add_argument("--switch", "-s", action="store_true", help="Switch to agent after creating")
    spawn_parser.add_argument("--blocked-by", "-b", help="Comma-separated blocker agent IDs (v3.0)")
    spawn_parser.add_argument("--template", help="Create from template (v3.0)")
    spawn_parser.add_argument("--source", help="Source type: claude-session|fathom-transcript|email|manual")
    spawn_parser.add_argument("--source-ref", help="Source reference ID (meeting_id, email_id, etc.)")
    spawn_parser.add_argument("--extracted-by", help="Tool/skill that created task")

    # switch
    switch_parser = subparsers.add_parser("switch", help="Switch to agent")
    switch_parser.add_argument("id", help="Agent ID")

    # pause
    pause_parser = subparsers.add_parser("pause", help="Pause agent")
    pause_parser.add_argument("id", nargs="?", help="Agent ID (current if omitted)")

    # resume
    resume_parser = subparsers.add_parser("resume", help="Resume agent")
    resume_parser.add_argument("id", help="Agent ID")

    # complete
    complete_parser = subparsers.add_parser("complete", help="Mark agent complete")
    complete_parser.add_argument("id", nargs="?", help="Agent ID (current if omitted)")
    complete_parser.add_argument("--force", "-f", action="store_true", help="Force completion even if reflection suggests not ready")

    # cancel
    cancel_parser = subparsers.add_parser("cancel", help="Cancel agent")
    cancel_parser.add_argument("id", help="Agent ID")

    # priority
    priority_parser = subparsers.add_parser("priority", help="Adjust priority")
    priority_parser.add_argument("id", help="Agent ID")
    priority_parser.add_argument("direction", choices=["+", "-"], help="Direction")

    # deadline (v3.0)
    deadline_parser = subparsers.add_parser("deadline", help="Manage task deadlines")
    deadline_parser.add_argument("id", nargs="?", help="Agent ID")
    deadline_parser.add_argument("date", nargs="?", help="Date (YYYY-MM-DD, +1d, +2w, +1m) or 'clear'")
    deadline_parser.add_argument("--action", "-a", choices=["list"], help="List all deadlines")

    # deadlines (alias for deadline list)
    subparsers.add_parser("deadlines", help="List all deadlines")

    # block (v3.0)
    block_parser = subparsers.add_parser("block", help="Add a blocker to a task")
    block_parser.add_argument("id", help="Agent ID to block")
    block_parser.add_argument("--by", "-b", required=True, help="Blocker agent ID")

    # unblock (v3.0)
    unblock_parser = subparsers.add_parser("unblock", help="Remove a blocker from a task")
    unblock_parser.add_argument("id", help="Agent ID to unblock")
    unblock_parser.add_argument("--from", "-f", dest="blocker", help="Blocker ID to remove (all if omitted)")

    # deps (v3.0)
    deps_parser = subparsers.add_parser("deps", help="Show task dependencies")
    deps_parser.add_argument("id", nargs="?", help="Agent ID")
    deps_parser.add_argument("--all", "-a", action="store_true", help="Show all dependencies")

    # progress
    progress_parser = subparsers.add_parser("progress", help="Show task progress breakdown")
    progress_parser.add_argument("id", nargs="?", help="Agent ID (active if omitted)")
    progress_parser.add_argument("--files", "-f", nargs="*", help="Set key files to track")

    # snapshot
    snapshot_parser = subparsers.add_parser("snapshot", help="Manage session snapshots")
    snapshot_parser.add_argument("action", nargs="?", default="show", choices=["show", "capture", "list"], help="Action to perform")
    snapshot_parser.add_argument("id", nargs="?", help="Agent ID (active if omitted)")
    snapshot_parser.add_argument("--summary", "-s", help="Context summary for capture")
    snapshot_parser.add_argument("--next", "-n", help="Suggested next step")
    snapshot_parser.add_argument("--question", "-q", action="append", help="Open question (can repeat)")

    # templates
    templates_parser = subparsers.add_parser("templates", help="List and manage task templates")
    templates_parser.add_argument("action", nargs="?", default="list", choices=["list", "show", "create"], help="Action")
    templates_parser.add_argument("name", nargs="?", help="Template name (for show/create)")
    templates_parser.add_argument("--from", dest="from_agent", help="Create template from agent ID")

    # queue
    subparsers.add_parser("queue", help="Show priority queue")

    # brief
    subparsers.add_parser("brief", help="Generate session briefing")

    # memory
    subparsers.add_parser("memory", help="Show working memory status")

    # consolidate
    consolidate_parser = subparsers.add_parser("consolidate", help="Consolidate to project memory")
    consolidate_parser.add_argument("id", nargs="?", help="Agent ID (all active if omitted)")
    consolidate_parser.add_argument("--project", "-p", help="Project path")

    # hooks
    hooks_parser = subparsers.add_parser("hooks", help="Manage CTM hooks")
    hooks_parser.add_argument("action", choices=["install", "status"], help="Hook action")

    # repair
    repair_parser = subparsers.add_parser("repair", help="Check and repair CTM data")
    repair_parser.add_argument("--config", action="store_true", help="Repair config only")
    repair_parser.add_argument("--agents", action="store_true", help="Repair agents only")
    repair_parser.add_argument("--scheduler", action="store_true", help="Repair scheduler only")
    repair_parser.add_argument("--index", action="store_true", help="Repair index only")
    repair_parser.add_argument("--memory", action="store_true", help="Repair memory only")
    repair_parser.add_argument("--clear-log", action="store_true", help="Clear error log")

    # context
    context_parser = subparsers.add_parser("context", help="Manage agent context")
    context_parser.add_argument("action", choices=["show", "add", "clear"], help="Context action")
    context_parser.add_argument("id", nargs="?", help="Agent ID (active if omitted)")
    context_parser.add_argument("--decision", "-d", help="Decision text to add")
    context_parser.add_argument("--learning", "-l", help="Learning text to add")
    context_parser.add_argument("--file", "-f", help="File path to add")
    context_parser.add_argument("--decisions", action="store_true", help="Clear decisions")
    context_parser.add_argument("--learnings", action="store_true", help="Clear learnings")

    # checkpoint
    checkpoint_parser = subparsers.add_parser("checkpoint", help="Save agent state")
    checkpoint_parser.add_argument("id", nargs="?", help="Agent ID (all active if omitted)")

    # restore
    restore_parser = subparsers.add_parser("restore", help="Restore from checkpoint")
    restore_parser.add_argument("checkpoint", nargs="?", help="Checkpoint name (latest if omitted)")
    restore_parser.add_argument("--list", "-l", action="store_true", help="List available checkpoints")

    # delegate
    delegate_parser = subparsers.add_parser("delegate", help="Delegate task to worker agent (CDP)")
    delegate_parser.add_argument("title", help="Task title")
    delegate_parser.add_argument("--agent", "-a", default="worker", help="Agent type (default: worker)")
    delegate_parser.add_argument("--context", "-c", help="Context to pass to agent")
    delegate_parser.add_argument("--files", "-f", help="Comma-separated key files")
    delegate_parser.add_argument("--constraints", help="Comma-separated constraints")
    delegate_parser.add_argument("--deliverables", "-d", help="Comma-separated expected deliverables")
    delegate_parser.add_argument("--project", "-p", help="Project path")

    # workspace
    workspace_parser = subparsers.add_parser("workspace", help="Manage CDP workspaces")
    workspace_parser.add_argument("action", choices=["list", "show", "clean"], help="Workspace action")
    workspace_parser.add_argument("task_id", nargs="?", help="Task ID for show action")

    # project (v2.1)
    project_parser = subparsers.add_parser("project", help="Manage project context")
    project_parser.add_argument("action", nargs="?", choices=["show", "set", "clear", "detect"],
                                default="show", help="Project action (default: show)")
    project_parser.add_argument("path", nargs="?", help="Project path (for set action)")

    # help
    subparsers.add_parser("help", help="Show help")

    args = parser.parse_args(argv)

    if not args.command:
        return cmd_status(args)

    commands = {
        "status": cmd_status,
        "list": cmd_list,
        "show": cmd_show,
        "spawn": cmd_spawn,
        "switch": cmd_switch,
        "pause": cmd_pause,
        "resume": cmd_resume,
        "complete": cmd_complete,
        "cancel": cmd_cancel,
        "priority": cmd_priority,
        "deadline": cmd_deadline,
        "deadlines": lambda args: cmd_deadline(type('Args', (), {'id': None, 'date': None, 'action': 'list'})()),
        "block": cmd_block,
        "unblock": cmd_unblock,
        "deps": cmd_deps,
        "progress": cmd_progress,
        "snapshot": cmd_snapshot,
        "templates": cmd_templates,
        "queue": cmd_queue,
        "brief": cmd_brief,
        "memory": cmd_memory,
        "consolidate": cmd_consolidate,
        "hooks": cmd_hooks,
        "repair": cmd_repair,
        "context": cmd_context,
        "checkpoint": cmd_checkpoint,
        "restore": cmd_restore,
        "delegate": cmd_delegate,
        "workspace": cmd_workspace,
        "project": cmd_project,
        "help": cmd_help,
    }

    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
