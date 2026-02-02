"""
CTM Integration Module

Connects CTM with:
- Project memory files (DECISIONS.md, SESSIONS.md, CHANGELOG.md)
- Temporal RAG system
- Existing hooks infrastructure

This enables CTM to:
1. Auto-extract decisions from completed agents
2. Generate session summaries for SESSIONS.md
3. Index agent context to RAG
4. Surface relevant past context when switching agents
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from config import get_ctm_dir, load_config
from agents import Agent, get_agent, AgentIndex


class ProjectMemoryIntegration:
    """
    Integrates CTM with project memory files.

    Project structure expected:
    project/.claude/context/
    ├── DECISIONS.md
    ├── SESSIONS.md
    ├── CHANGELOG.md
    └── STAKEHOLDERS.md
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.context_dir = self.project_path / ".claude" / "context"

    def has_memory_structure(self) -> bool:
        """Check if project has memory structure initialized."""
        return self.context_dir.exists() and (self.context_dir / "DECISIONS.md").exists()

    def extract_decisions(self, agent: Agent) -> List[Dict[str, str]]:
        """
        Extract decisions from an agent's context.

        Returns list of decisions in DECISIONS.md format.
        """
        decisions = []
        for d in agent.context.get("decisions", []):
            decisions.append({
                "title": d.get("text", "")[:50] + "..." if len(d.get("text", "")) > 50 else d.get("text", ""),
                "decided": d.get("timestamp", datetime.now(timezone.utc).isoformat())[:10],
                "context": f"From CTM agent [{agent.id}]: {agent.task['title']}",
                "choice": d.get("text", ""),
                "references": f"Session via CTM agent {agent.id}"
            })
        return decisions

    def append_decision(self, decision: Dict[str, str]) -> bool:
        """
        Append a decision to DECISIONS.md.

        Returns True if successful.
        """
        if not self.has_memory_structure():
            return False

        decisions_path = self.context_dir / "DECISIONS.md"

        try:
            content = decisions_path.read_text()

            # Find insertion point (after "## Active Decisions" line)
            marker = "## Active Decisions"
            if marker not in content:
                return False

            insertion_point = content.index(marker) + len(marker)

            # Build decision entry
            entry = f"""

### {decision['title']}
- **Decided**: {decision['decided']}
- **Context**: {decision['context']}
- **Choice**: {decision['choice']}
- **References**: {decision['references']}
"""
            # Insert after marker (and any template comments)
            new_content = content[:insertion_point] + entry + content[insertion_point:]
            decisions_path.write_text(new_content)
            return True

        except Exception as e:
            print(f"Error appending decision: {e}")
            return False

    def generate_session_summary(self, agents: List[Agent]) -> str:
        """
        Generate a session summary for SESSIONS.md from agents worked on.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        # Collect outcomes
        completed = [a for a in agents if a.state["status"] == "completed"]
        in_progress = [a for a in agents if a.state["status"] in ["active", "paused"]]

        # Collect decisions
        all_decisions = []
        for agent in agents:
            all_decisions.extend(agent.context.get("decisions", []))

        summary = f"""### {date_str} — CTM Session
**Focus**: {', '.join(a.task['title'] for a in agents[:3])}{'...' if len(agents) > 3 else ''}

**Key Outcomes**:
"""
        for agent in completed:
            summary += f"- Completed [{agent.id}]: {agent.task['title']}\n"

        for agent in in_progress:
            summary += f"- In progress [{agent.id}]: {agent.task['title']} ({agent.state['progress_pct']}%)\n"

        if all_decisions:
            summary += "\n**Decisions Made**:\n"
            for d in all_decisions[:5]:  # Top 5 decisions
                summary += f"- {d.get('text', '')[:80]}\n"

        # Open questions from pending actions
        open_questions = []
        for agent in agents:
            for action in agent.state.get("pending_actions", [])[:2]:
                open_questions.append(action)

        if open_questions:
            summary += "\n**Open Questions**:\n"
            for q in open_questions[:5]:
                summary += f"- {q}\n"

        # Next steps from incomplete agents
        summary += "\n**Next Steps**:\n"
        for agent in in_progress[:3]:
            summary += f"- [ ] Continue [{agent.id}]: {agent.task['title']}\n"

        return summary

    def append_session(self, summary: str) -> bool:
        """
        Append a session summary to SESSIONS.md.
        """
        if not self.has_memory_structure():
            return False

        sessions_path = self.context_dir / "SESSIONS.md"

        try:
            content = sessions_path.read_text()

            # Find insertion point (after "## Recent Sessions" line)
            marker = "## Recent Sessions"
            if marker not in content:
                return False

            insertion_point = content.index(marker) + len(marker)

            new_content = content[:insertion_point] + "\n\n" + summary + content[insertion_point:]
            sessions_path.write_text(new_content)
            return True

        except Exception as e:
            print(f"Error appending session: {e}")
            return False


class RAGIntegration:
    """
    Integrates CTM with the temporal RAG system.

    Uses the rag-server MCP tool for indexing and search.
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.rag_dir = self.project_path / ".rag"

    def has_rag(self) -> bool:
        """Check if project has RAG initialized."""
        return self.rag_dir.exists()

    def index_agent(self, agent: Agent) -> bool:
        """
        Index agent context to RAG.

        Creates a temporary markdown file with agent context
        and indexes it to the project's RAG database.
        """
        if not self.has_rag():
            return False

        # Create agent context document
        doc_content = f"""# CTM Agent: {agent.task['title']}

> Created: {agent.timing['created_at'][:10]} | Last Active: {agent.timing['last_active'][:10]}

## Goal
{agent.task['goal']}

## Status
- Status: {agent.state['status']}
- Progress: {agent.state['progress_pct']}%
- Current Step: {agent.state.get('current_step', 'N/A')}

## Decisions
"""
        for d in agent.context.get("decisions", []):
            doc_content += f"- [{d.get('timestamp', '')[:10]}] {d.get('text', '')}\n"

        doc_content += "\n## Learnings\n"
        for l in agent.context.get("learnings", []):
            doc_content += f"- {l.get('text', '')}\n"

        doc_content += "\n## Key Files\n"
        for f in agent.context.get("key_files", []):
            doc_content += f"- `{f}`\n"

        # Write to CTM context directory
        ctm_context_dir = get_ctm_dir() / "context"
        ctm_context_dir.mkdir(parents=True, exist_ok=True)

        doc_path = ctm_context_dir / f"agent-{agent.id}.md"
        doc_path.write_text(doc_content)

        # Note: Actual RAG indexing happens via hook or manual call
        return True

    def search_related(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search RAG for related context.

        Note: This requires the rag-server MCP to be running.
        Returns empty list if RAG not available.
        """
        # This would be called via MCP tool in Claude
        # For now, return empty - actual search happens in Claude context
        return []


class HookIntegration:
    """
    Manages CTM integration with Claude Code hooks.
    """

    def __init__(self):
        self.hooks_dir = Path.home() / ".claude" / "hooks" / "ctm"
        self.settings_path = Path.home() / ".claude" / "settings.json"

    def ensure_hooks_dir(self) -> None:
        """Create CTM hooks directory if needed."""
        self.hooks_dir.mkdir(parents=True, exist_ok=True)

    def install_hooks(self) -> bool:
        """
        Install CTM hooks into Claude Code settings.

        Adds hooks for:
        - SessionStart: Load CTM state, show briefing
        - PreCompact: Checkpoint active agents, consolidate
        - SessionEnd: Final checkpoint, update SESSIONS.md
        """
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)

            hooks = settings.setdefault("hooks", {})

            # SessionStart hook - show briefing
            session_start = hooks.setdefault("SessionStart", [])
            ctm_start_hook = {
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": str(self.hooks_dir / "ctm-session-start.sh")
                }]
            }
            if not any(h.get("hooks", [{}])[0].get("command", "").endswith("ctm-session-start.sh")
                      for h in session_start):
                session_start.append(ctm_start_hook)

            # PreCompact hook - checkpoint
            pre_compact = hooks.setdefault("PreCompact", [])
            ctm_checkpoint_hook = {
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": str(self.hooks_dir / "ctm-pre-compact.sh")
                }]
            }
            if not any(h.get("hooks", [{}])[0].get("command", "").endswith("ctm-pre-compact.sh")
                      for h in pre_compact):
                pre_compact.append(ctm_checkpoint_hook)

            # SessionEnd hook - final save
            session_end = hooks.setdefault("SessionEnd", [])
            ctm_end_hook = {
                "matcher": "",
                "hooks": [{
                    "type": "command",
                    "command": str(self.hooks_dir / "ctm-session-end.sh")
                }]
            }
            if not any(h.get("hooks", [{}])[0].get("command", "").endswith("ctm-session-end.sh")
                      for h in session_end):
                session_end.append(ctm_end_hook)

            with open(self.settings_path, 'w') as f:
                json.dump(settings, f, indent=2)

            return True

        except Exception as e:
            print(f"Error installing hooks: {e}")
            return False


def get_project_memory(project_path: Optional[Path] = None) -> ProjectMemoryIntegration:
    """Get project memory integration instance."""
    return ProjectMemoryIntegration(project_path)


def get_rag_integration(project_path: Optional[Path] = None) -> RAGIntegration:
    """Get RAG integration instance."""
    return RAGIntegration(project_path)


def get_hook_integration() -> HookIntegration:
    """Get hook integration instance."""
    return HookIntegration()
