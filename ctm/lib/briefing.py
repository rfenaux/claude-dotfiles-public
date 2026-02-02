"""
CTM Briefing Generation

Generates intelligent session briefings that:
- Summarize pending work by priority
- Highlight stale tasks that need attention
- Surface recent decisions for context
- Suggest what to work on next
- Health check for system consistency

Like a morning briefing, this helps orient the user at session start.
"""

import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from config import load_config, get_ctm_dir
from agents import Agent, get_agent, AgentIndex, list_agents
from scheduler import get_scheduler
from memory import get_working_memory

# Lazy import for cognitive load
_cognitive_tracker = None

# Lazy import for progress tracking
_progress_tracker = None

def get_progress_tracker():
    global _progress_tracker
    if _progress_tracker is None:
        from progress import get_tracker
        _progress_tracker = get_tracker()
    return _progress_tracker

def get_cognitive_load_tracker():
    global _cognitive_tracker
    if _cognitive_tracker is None:
        try:
            from cognitive_load import CognitiveLoadTracker
            _cognitive_tracker = CognitiveLoadTracker()
        except ImportError:
            _cognitive_tracker = None
    return _cognitive_tracker


def _run_command(cmd: List[str], timeout: int = 5) -> tuple[bool, str]:
    """Run a command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


@dataclass
class BriefingSection:
    """A section of the briefing."""
    title: str
    content: str
    priority: int  # Lower = shown first


class BriefingGenerator:
    """
    Generates comprehensive session briefings.

    v2.1: Project-context aware - prioritizes and groups tasks by current project.
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.config = load_config()
        self.project_path = project_path or Path.cwd()
        self.index = AgentIndex()
        self.scheduler = get_scheduler()

        # v2.1: Set project context for context-aware prioritization
        if project_path:
            self.scheduler.set_project_context(str(project_path))

    def generate(self, verbose: bool = False) -> str:
        """
        Generate a full session briefing.

        Args:
            verbose: If True, include more detail

        Returns:
            Formatted briefing string
        """
        sections = []

        # 1. Quick status
        sections.append(self._generate_status_section())

        # 2. Deadline alerts (v3.0)
        deadlines_section = self._generate_deadlines_section()
        if deadlines_section:
            sections.append(deadlines_section)

        # 3. Resume point (where we left off)
        resume_section = self._generate_resume_section()
        if resume_section:
            sections.append(resume_section)

        # 4. Priority tasks
        sections.append(self._generate_priority_section())

        # 4. Recent decisions (with WHY)
        decisions_section = self._generate_decisions_section()
        if decisions_section:
            sections.append(decisions_section)

        # 5. Open blockers
        blockers_section = self._generate_blockers_section()
        if blockers_section:
            sections.append(blockers_section)

        # 5.5. Dependencies visualization (v3.0)
        deps_section = self._generate_dependencies_section()
        if deps_section:
            sections.append(deps_section)

        # 6. Correction patterns (mistakes to avoid)
        corrections_section = self._generate_corrections_section()
        if corrections_section:
            sections.append(corrections_section)

        # 7. Stale tasks (if any)
        stale_section = self._generate_stale_section()
        if stale_section:
            sections.append(stale_section)

        # 8. Recent progress (if verbose)
        if verbose:
            progress_section = self._generate_progress_section()
            if progress_section:
                sections.append(progress_section)

        # 9. Health check
        health_section = self._generate_health_section()
        if health_section:
            sections.append(health_section)

        # 10. Cognitive Load
        cognitive_section = self._generate_cognitive_load_section()
        if cognitive_section:
            sections.append(cognitive_section)

        # 11. Recommendation
        sections.append(self._generate_recommendation_section())

        # Sort by priority and format
        sections.sort(key=lambda s: s.priority)

        output = ["═══ Session Briefing ═══", ""]
        for section in sections:
            if section.content:
                output.append(f"**{section.title}**")
                output.append(section.content)
                output.append("")

        return "\n".join(output)

    def _generate_status_section(self) -> BriefingSection:
        """Generate quick status overview with project context."""
        active = len(self.index.get_by_status("active"))
        paused = len(self.index.get_by_status("paused"))
        blocked = len(self.index.get_by_status("blocked"))

        total = active + paused + blocked

        if total == 0:
            content = "No pending tasks. Ready for new work!"
        else:
            parts = []
            if active:
                parts.append(f"{active} active")
            if paused:
                parts.append(f"{paused} paused")
            if blocked:
                parts.append(f"{blocked} blocked")
            content = f"{total} task(s): {', '.join(parts)}"

        # v2.1: Add project context info
        project_context = self.scheduler.get_project_context()
        if project_context:
            project_name = Path(project_context).name
            status = self.scheduler.get_status()
            project_tasks = status.get("project_tasks", 0)
            if project_tasks > 0:
                content += f"\n📁 Project: {project_name} ({project_tasks} task{'s' if project_tasks != 1 else ''})"
            else:
                content += f"\n📁 Project: {project_name} (no tasks)"

        return BriefingSection(
            title="Status",
            content=content,
            priority=1
        )

    def _generate_deadlines_section(self) -> Optional[BriefingSection]:
        """
        Generate deadline alerts section (v3.0).

        Shows tasks grouped by urgency:
        - 🔴 OVERDUE: Past deadline
        - 🟠 TODAY: Due within 24 hours
        - 🟡 SOON: Due within 3 days
        - 🟢 WEEK: Due within 7 days
        """
        now = datetime.now(timezone.utc)

        overdue = []
        today = []
        soon = []
        week = []

        for aid in self.index.get_all_active():
            agent = get_agent(aid)
            if not agent:
                continue

            deadline_str = agent.timing.get("deadline")
            if not deadline_str:
                continue

            try:
                deadline = datetime.fromisoformat(deadline_str.rstrip("Z")).replace(tzinfo=timezone.utc)
                delta = deadline - now
                hours = delta.total_seconds() / 3600
                days = delta.days

                task_info = {
                    "id": aid,
                    "title": agent.task["title"][:35],
                    "deadline": deadline,
                    "hours": hours,
                    "days": days
                }

                if hours < 0:
                    # Overdue
                    overdue_days = abs(days) if days < 0 else 0
                    task_info["overdue_str"] = f"{overdue_days}d overdue" if overdue_days > 0 else f"{abs(int(hours))}h overdue"
                    overdue.append(task_info)
                elif hours <= 24:
                    # Due today
                    task_info["due_str"] = f"due in {int(hours)}h" if hours > 1 else "due in <1h"
                    today.append(task_info)
                elif days <= 3:
                    # Soon
                    task_info["due_str"] = f"due in {days}d"
                    soon.append(task_info)
                elif days <= 7:
                    # This week
                    task_info["due_str"] = f"due in {days}d"
                    week.append(task_info)

            except (ValueError, TypeError):
                continue

        # Build output only if there are deadline items to show
        if not any([overdue, today, soon]):
            return None

        lines = []

        if overdue:
            for t in sorted(overdue, key=lambda x: x["hours"]):
                lines.append(f"🔴 OVERDUE: [{t['id']}] {t['title']} — {t['overdue_str']}")

        if today:
            for t in sorted(today, key=lambda x: x["hours"]):
                lines.append(f"🟠 TODAY: [{t['id']}] {t['title']} — {t['due_str']}")

        if soon:
            for t in sorted(soon, key=lambda x: x["days"]):
                lines.append(f"🟡 SOON: [{t['id']}] {t['title']} — {t['due_str']}")

        # Only show week items if there's room and nothing more urgent
        if week and len(lines) < 5:
            remaining = 5 - len(lines)
            for t in sorted(week, key=lambda x: x["days"])[:remaining]:
                lines.append(f"🟢 [{t['id']}] {t['title']} — {t['due_str']}")

        return BriefingSection(
            title="⏰ Deadlines",
            content="\n".join(lines),
            priority=0  # Show at top, before status
        )

    def _generate_priority_section(self) -> BriefingSection:
        """
        Generate priority task list and load into working memory.

        v2.1: Groups tasks by project context - current project tasks shown first,
        then "Other Projects" section for remaining tasks.
        """
        self.scheduler.rebuild_queue()
        queue = self.scheduler.get_queue()

        if not queue:
            return BriefingSection(title="Tasks", content="", priority=2)

        # Load top priority agents into working memory
        wm = get_working_memory()
        for item in queue[:5]:
            wm.load(item["id"])

        # v2.1: Separate tasks by project context
        project_context = self.scheduler.get_project_context()
        current_project_tasks = []
        other_project_tasks = []

        for item in queue:
            agent = get_agent(item["id"])
            if agent:
                if project_context and self.scheduler.is_project_match(agent):
                    current_project_tasks.append((item, agent))
                else:
                    other_project_tasks.append((item, agent))

        def format_task(item, agent, index):
            status_icon = "▶" if item["status"] == "active" else "○"
            manual_progress = agent.state.get("progress_pct", 0)
            step = agent.state.get("current_step", "")

            # Try to get inferred progress
            inferred = None
            try:
                tracker = get_progress_tracker()
                inferred = tracker.infer_progress(agent)
            except Exception:
                pass

            # Show inferred progress if different from manual
            if inferred is not None and inferred != manual_progress and inferred > 0:
                progress_str = f"{manual_progress}%→{inferred}%"
            else:
                progress_str = f"{manual_progress}%"

            line = f"{index}. {status_icon} [{agent.id}] {agent.task['title']} ({progress_str})"
            if step:
                line += f"\n      └─ {step[:50]}"
            return line

        lines = []

        # Show current project tasks first (if project context is set)
        if project_context and current_project_tasks:
            project_name = Path(project_context).name
            lines.append(f"📁 {project_name}:")
            for i, (item, agent) in enumerate(current_project_tasks[:4], 1):
                lines.append("  " + format_task(item, agent, i))
            if len(current_project_tasks) > 4:
                lines.append(f"     ... and {len(current_project_tasks) - 4} more in this project")
            lines.append("")

        # Show other projects (collapsed)
        if other_project_tasks:
            if project_context and current_project_tasks:
                lines.append("📂 Other Projects:")
                # Show just top 2 from other projects
                for i, (item, agent) in enumerate(other_project_tasks[:2], 1):
                    project_name = Path(agent.context.get("project", "unknown")).name
                    status_icon = "○"
                    progress = agent.state.get("progress_pct", 0)
                    lines.append(f"  {i}. {status_icon} [{agent.id}] {agent.task['title'][:25]}.. ({project_name})")
                if len(other_project_tasks) > 2:
                    lines.append(f"     ... and {len(other_project_tasks) - 2} more in other projects")
            else:
                # No project context - show all tasks normally
                for i, item in enumerate(queue[:5], 1):
                    agent = get_agent(item["id"])
                    if agent:
                        lines.append(format_task(item, agent, i))
                if len(queue) > 5:
                    lines.append(f"   ... and {len(queue) - 5} more")

        return BriefingSection(
            title="Priority Queue",
            content="\n".join(lines),
            priority=2
        )

    def _generate_stale_section(self) -> Optional[BriefingSection]:
        """Generate section for stale tasks that need attention."""
        stale_threshold = timedelta(days=7)
        now = datetime.now(timezone.utc)

        stale_agents = []
        for aid in self.index.get_all_active():
            agent = get_agent(aid)
            if agent:
                last_active = datetime.fromisoformat(
                    agent.timing["last_active"].rstrip("Z")
                ).replace(tzinfo=timezone.utc)

                if now - last_active > stale_threshold:
                    days = (now - last_active).days
                    stale_agents.append((agent, days))

        if not stale_agents:
            return None

        lines = []
        for agent, days in sorted(stale_agents, key=lambda x: -x[1])[:3]:
            lines.append(f"⚠ [{agent.id}] {agent.task['title']} — {days} days inactive")

        return BriefingSection(
            title="Needs Attention",
            content="\n".join(lines),
            priority=3
        )

    def _generate_decisions_section(self) -> Optional[BriefingSection]:
        """Generate section showing recent decisions with context (WHY)."""
        decisions_file = Path.home() / ".claude" / "ctm" / "context" / "decisions.json"

        if not decisions_file.exists():
            return None

        try:
            data = json.loads(decisions_file.read_text())
            decisions = data.get("decisions", [])

            if not decisions:
                return None

            # Get last 3 decisions
            recent = decisions[-3:]
            lines = []
            for d in reversed(recent):
                summary = d.get("summary", "Unknown decision")[:60]
                context = d.get("context", d.get("rationale", ""))[:40]
                status = "✓"
                line = f"{status} {summary}"
                if context:
                    line += f"\n      (Why: {context})"
                lines.append(line)

            return BriefingSection(
                title="Recent Decisions",
                content="\n".join(lines),
                priority=3
            )
        except Exception:
            return None

    def _generate_blockers_section(self) -> Optional[BriefingSection]:
        """Generate section showing open questions and blockers."""
        lines = []

        # Check blocked agents
        blocked_agents = self.index.get_by_status("blocked")
        for aid in blocked_agents[:3]:
            agent = get_agent(aid)
            if agent:
                error = agent.state.get("last_error", "Unknown blocker")[:50]
                lines.append(f"• [{agent.id}] {agent.task['title'][:30]}: {error}")

        # Check for pending_actions in context
        context_file = Path.home() / ".claude" / "ctm" / "context" / "pending_actions.json"
        if context_file.exists():
            try:
                data = json.loads(context_file.read_text())
                actions = data.get("actions", [])
                for action in actions[:2]:
                    lines.append(f"• Pending: {action.get('description', 'Unknown')[:50]}")
            except Exception:
                pass

        if not lines:
            return None

        return BriefingSection(
            title="Needs Resolution",
            content="\n".join(lines),
            priority=4
        )

    def _generate_dependencies_section(self) -> Optional[BriefingSection]:
        """
        Generate section showing task dependencies (v3.0).

        Shows:
        - High-impact blockers (tasks that block multiple others)
        - Blocked tasks and what they're waiting on
        """
        try:
            from dependencies import get_high_impact_blockers, find_blockers, find_dependents, is_blocked
        except ImportError:
            return None

        lines = []

        # Find high-impact blockers (tasks that block 2+ other tasks)
        high_impact = get_high_impact_blockers(min_dependents=2)
        if high_impact:
            lines.append("High-impact (complete to unblock multiple tasks):")
            for aid, count in high_impact[:3]:
                agent = get_agent(aid)
                if agent:
                    lines.append(f"  ⚡ [{aid}] {agent.task['title'][:30]} → unblocks {count} tasks")

        # Find blocked tasks and their blockers
        blocked_tasks = []
        for aid in self.index.get_all_active():
            agent = get_agent(aid)
            if agent and is_blocked(aid):
                blockers = find_blockers(aid)
                blocked_tasks.append((aid, agent, blockers))

        if blocked_tasks and len(lines) > 0:
            lines.append("")  # Separator

        if blocked_tasks:
            lines.append("Blocked tasks:")
            for aid, agent, blockers in blocked_tasks[:3]:
                blocker_names = []
                for b_id in blockers[:2]:
                    b_agent = get_agent(b_id)
                    if b_agent:
                        blocker_names.append(f"[{b_id}]")
                    else:
                        blocker_names.append(b_id[:10])

                blockers_str = ", ".join(blocker_names)
                if len(blockers) > 2:
                    blockers_str += f" +{len(blockers) - 2}"

                lines.append(f"  ⛔ [{aid}] {agent.task['title'][:25]} ← {blockers_str}")

        if not lines:
            return None

        return BriefingSection(
            title="🔗 Dependencies",
            content="\n".join(lines),
            priority=5
        )

    def _generate_corrections_section(self) -> Optional[BriefingSection]:
        """Generate section showing patterns to avoid from recent corrections."""
        corrections_file = Path.home() / ".claude" / "correction-history.jsonl"

        if not corrections_file.exists():
            return None

        try:
            # Read last 10 corrections
            lines_read = []
            with open(corrections_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        lines_read.append(line)

            if not lines_read:
                return None

            # Get last 5 unique correction types
            recent = lines_read[-10:]
            seen_types = set()
            patterns = []

            for line in reversed(recent):
                try:
                    entry = json.loads(line)
                    ctype = entry.get("type", "unknown")
                    if ctype not in seen_types:
                        seen_types.add(ctype)
                        trigger = entry.get("trigger_phrase", "")
                        hint = entry.get("pattern_hint", "")
                        pattern = hint if hint else f"{ctype}: {trigger}"
                        patterns.append(f"• {pattern}")
                except json.JSONDecodeError:
                    continue

                if len(patterns) >= 3:
                    break

            if not patterns:
                return None

            return BriefingSection(
                title="Patterns to Avoid",
                content="\n".join(patterns),
                priority=5
            )
        except Exception:
            return None

    def _generate_resume_section(self) -> Optional[BriefingSection]:
        """Generate section showing exactly where we left off."""
        # Find most recently active agent
        self.scheduler.rebuild_queue()
        queue = self.scheduler.get_queue()

        if not queue:
            return None

        # Get top active agent
        top_agent = None
        for item in queue:
            agent = get_agent(item["id"])
            if agent and agent.state["status"] == "active":
                top_agent = agent
                break

        if not top_agent:
            # Try paused
            for item in queue:
                agent = get_agent(item["id"])
                if agent and agent.state["status"] == "paused":
                    top_agent = agent
                    break

        if not top_agent:
            return None

        # Build resume info
        title = top_agent.task.get("title", "Unknown task")
        progress = top_agent.state.get("progress_pct", 0)
        current_step = top_agent.state.get("current_step", "")
        last_active_str = top_agent.timing.get("last_active", "")

        # Calculate time since last active
        time_ago = ""
        if last_active_str:
            try:
                last_active = datetime.fromisoformat(
                    last_active_str.rstrip("Z")
                ).replace(tzinfo=timezone.utc)
                delta = datetime.now(timezone.utc) - last_active
                if delta.days > 0:
                    time_ago = f"{delta.days}d ago"
                elif delta.seconds >= 3600:
                    time_ago = f"{delta.seconds // 3600}h ago"
                else:
                    time_ago = f"{delta.seconds // 60}m ago"
            except Exception:
                pass

        lines = [f"Last session{' (' + time_ago + ')' if time_ago else ''}: {title}"]

        # Show both manual and inferred progress if available
        inferred = None
        try:
            tracker = get_progress_tracker()
            inferred = tracker.infer_progress(top_agent)
        except Exception:
            pass

        if inferred is not None and inferred != progress:
            lines.append(f"├─ Progress: {progress}% (manual) / {inferred}% (inferred)")
        else:
            lines.append(f"├─ Progress: {progress}%")
        if current_step:
            lines.append(f"├─ Current: {current_step[:50]}")

        # v3.0: Load session snapshot for rich resume context
        snapshot = None
        try:
            from session_snapshot import load_snapshot
            snapshot = load_snapshot(top_agent.id)
        except Exception:
            pass

        if snapshot:
            # Where you stopped
            if snapshot.last_file:
                action = snapshot.last_action or "editing"
                file_info = snapshot.last_file
                if len(file_info) > 40:
                    file_info = "..." + file_info[-37:]
                lines.append(f"├─ Last: {action} {file_info}")

            # Recent decisions
            if snapshot.recent_decisions:
                lines.append("├─ Recent decisions:")
                for dec in snapshot.recent_decisions[:2]:
                    dec_short = dec[:45] + "..." if len(dec) > 45 else dec
                    lines.append(f"│   • {dec_short}")

            # Open questions
            if snapshot.open_questions:
                lines.append("├─ Open questions:")
                for q in snapshot.open_questions[:2]:
                    q_short = q[:45] + "..." if len(q) > 45 else q
                    lines.append(f"│   ? {q_short}")

            # Git context
            if snapshot.uncommitted_files:
                count = len(snapshot.uncommitted_files)
                lines.append(f"├─ Uncommitted: {count} file(s)")

            # Next step (prefer snapshot, fall back to checkpoint)
            if snapshot.next_step:
                lines.append(f"└─ Next: {snapshot.next_step[:50]}")
            elif snapshot.context_summary:
                lines.append(f"└─ Context: {snapshot.context_summary[:50]}")
        else:
            # Fallback: Get next step from checkpoints if available
            checkpoints = top_agent.state.get("checkpoints", [])
            if checkpoints:
                last_cp = checkpoints[-1]
                next_action = last_cp.get("next_action", "")
                if next_action:
                    lines.append(f"└─ Next: {next_action[:50]}")

        return BriefingSection(
            title="Resume Point",
            content="\n".join(lines),
            priority=2
        )

    def _generate_progress_section(self) -> Optional[BriefingSection]:
        """Generate recent progress summary."""
        recent_threshold = timedelta(hours=24)
        now = datetime.now(timezone.utc)

        recent_activity = []
        for aid in list(self.index._data["agents"].keys()):
            agent = get_agent(aid)
            if agent:
                last_active = datetime.fromisoformat(
                    agent.timing["last_active"].rstrip("Z")
                ).replace(tzinfo=timezone.utc)

                if now - last_active < recent_threshold:
                    recent_activity.append(agent)

        if not recent_activity:
            return None

        lines = []
        for agent in recent_activity[:3]:
            status = agent.state["status"]
            progress = agent.state.get("progress_pct", 0)
            lines.append(f"• [{agent.id}] {agent.task['title']}: {status} ({progress}%)")

        return BriefingSection(
            title="Recent Activity (24h)",
            content="\n".join(lines),
            priority=4
        )

    def _generate_health_section(self) -> Optional[BriefingSection]:
        """
        Generate health check section.
        Checks system consistency and reports issues.
        """
        issues = []
        claude_dir = Path.home() / ".claude"

        # 1. Check agent count consistency
        try:
            agents_dir = claude_dir / "agents"
            actual_count = len(list(agents_dir.glob("*.md")))

            # Check AGENTS_INDEX.md
            agents_index = claude_dir / "AGENTS_INDEX.md"
            if agents_index.exists():
                content = agents_index.read_text()
                import re
                match = re.search(r"Total Agents: (\d+)", content)
                if match:
                    doc_count = int(match.group(1))
                    if actual_count != doc_count:
                        issues.append(f"Agent count drift: {actual_count} actual vs {doc_count} in docs")
        except Exception:
            pass

        # 2. Check RAG status for current project
        try:
            rag_dir = self.project_path / ".rag"
            if rag_dir.exists():
                # RAG is enabled - check if Ollama is running
                success, _ = _run_command(["pgrep", "-x", "ollama"])
                if not success:
                    issues.append("RAG enabled but Ollama not running")
        except Exception:
            pass

        # 3. Check for agents missing async frontmatter (sample check)
        try:
            agents_dir = claude_dir / "agents"
            missing_async = 0
            for agent_file in list(agents_dir.glob("*.md"))[:20]:  # Sample first 20
                content = agent_file.read_text()
                if "\nasync:" not in content and content.startswith("---"):
                    missing_async += 1
            if missing_async > 0:
                issues.append(f"{missing_async}+ agents missing async frontmatter")
        except Exception:
            pass

        # 4. Check if validation script exists
        validate_script = claude_dir / "scripts" / "validate-setup.sh"
        if not validate_script.exists():
            issues.append("Validation script not installed")

        # Return section only if there are issues
        if not issues:
            return None

        content = "\n".join(f"⚠ {issue}" for issue in issues[:3])
        if len(issues) > 3:
            content += f"\n   ... and {len(issues) - 3} more (run validate-setup.sh)"

        return BriefingSection(
            title="Health Check",
            content=content,
            priority=5
        )

    def _generate_cognitive_load_section(self) -> Optional[BriefingSection]:
        """
        Generate cognitive load and focus section.

        Shows attention residue, switch count, and focus recommendations.
        Based on research: 23min refocus time, 40% productivity loss from context switching.
        """
        tracker = get_cognitive_load_tracker()
        if not tracker:
            return None

        try:
            session_stats = tracker.get_session_stats()
            recommendation = tracker.get_focus_recommendation()

            lines = []

            # Session stats
            switches = session_stats.get("switches", 0)
            residue = session_stats.get("total_residue", 0)
            impact = session_stats.get("productivity_impact", "minimal")

            if switches > 0 or residue > 0.2:
                lines.append(f"Session: {switches} switches, {residue:.0%} residue")

                if impact != "minimal":
                    lines.append(f"Productivity impact: ~{impact}")

            # Focus recommendation
            if recommendation.action == "clear_residue":
                lines.append(f"⚠ {recommendation.reason}")
            elif recommendation.action == "continue" and switches > 3:
                lines.append(f"→ {recommendation.reason}")

            # High residue agents
            for aid in self.index.get_all_active()[:3]:
                load = tracker.get_agent_load(aid)
                if load.get("attention_residue", 0) > 0.3:
                    lines.append(f"  • [{aid}] has {load['attention_residue']:.0%} residue")

            if not lines:
                return None

            return BriefingSection(
                title="Cognitive Load",
                content="\n".join(lines),
                priority=6
            )
        except Exception:
            return None

    def _generate_recommendation_section(self) -> BriefingSection:
        """Generate recommendation for what to work on."""
        self.scheduler.rebuild_queue()
        queue = self.scheduler.get_queue()

        if not queue:
            return BriefingSection(
                title="Recommendation",
                content="Ready for new tasks. Use `/ctm spawn` to create one.",
                priority=10
            )

        top = queue[0]
        agent = get_agent(top["id"])

        if not agent:
            return BriefingSection(title="Recommendation", content="", priority=10)

        # Build recommendation based on agent state
        if agent.state["status"] == "blocked":
            content = f"Unblock [{agent.id}]: {agent.task['title']}"
            if agent.state.get("last_error"):
                content += f"\n   Error: {agent.state['last_error'][:50]}"
        elif agent.state.get("progress_pct", 0) > 80:
            content = f"Finish [{agent.id}]: {agent.task['title']} — {agent.state['progress_pct']}% done"
        else:
            content = f"Continue [{agent.id}]: {agent.task['title']}"
            if agent.state.get("current_step"):
                content += f"\n   From: {agent.state['current_step'][:50]}"

        return BriefingSection(
            title="Recommendation",
            content=content,
            priority=10
        )

    def generate_compact(self) -> str:
        """
        Generate a compact one-line briefing for status bar or quick display.

        v2.1: Shows project context and task counts.
        """
        active = len(self.index.get_by_status("active"))
        paused = len(self.index.get_by_status("paused"))

        self.scheduler.rebuild_queue()
        queue = self.scheduler.get_queue()

        if not queue:
            return "[CTM] No tasks"

        # v2.1: Count tasks in current project
        project_context = self.scheduler.get_project_context()
        project_count = 0
        if project_context:
            for item in queue:
                agent = get_agent(item["id"])
                if agent and self.scheduler.is_project_match(agent):
                    project_count += 1

        top = queue[0]
        agent = get_agent(top["id"])

        if agent:
            # v2.1: Show project context in compact format
            if project_context and project_count > 0:
                project_name = Path(project_context).name
                return f"[CTM] {project_count}/{active+paused} tasks in {project_name[:15]} | Top: {agent.task['title'][:30]}"
            else:
                return f"[CTM] {active}+{paused} tasks | Top: {agent.task['title'][:30]}"
        else:
            return f"[CTM] {active}+{paused} tasks"


def generate_briefing(verbose: bool = False, project_path: Optional[Path] = None) -> str:
    """Generate a session briefing."""
    generator = BriefingGenerator(project_path)
    return generator.generate(verbose)


def generate_compact_briefing(project_path: Optional[Path] = None) -> str:
    """Generate a compact one-line briefing."""
    generator = BriefingGenerator(project_path)
    return generator.generate_compact()
