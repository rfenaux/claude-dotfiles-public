"""
CTM Memory Consolidation

Implements the "sleep-like" consolidation process that:
1. Extracts important decisions from completed agents
2. Generates summaries for long-term memory (DECISIONS.md, SESSIONS.md)
3. Indexes content to RAG for future retrieval
4. Cleans up stale agent data

Like the brain's memory consolidation during sleep, this process
transforms episodic (conversation) memory into semantic (knowledge) memory.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from config import load_config, get_ctm_dir
from agents import Agent, get_agent, AgentIndex, update_agent, AgentStatus


class Consolidator:
    """
    Consolidates agent context into long-term memory structures.
    """

    def __init__(self, project_path: Optional[Path] = None):
        self.config = load_config()
        self.project_path = project_path or Path.cwd()
        self.context_dir = self.project_path / ".claude" / "context"
        self.rag_dir = self.project_path / ".rag"

    def has_memory_structure(self) -> bool:
        """Check if project has memory structure."""
        return self.context_dir.exists()

    def has_rag(self) -> bool:
        """Check if project has RAG initialized."""
        return self.rag_dir.exists()

    def extract_decisions(self, agent: Agent) -> List[Dict[str, str]]:
        """
        Extract decision records from agent context.

        Returns formatted decision entries ready for DECISIONS.md.
        """
        decisions = []

        for d in agent.context.get("decisions", []):
            text = d.get("text", "")
            timestamp = d.get("timestamp", datetime.now(timezone.utc).isoformat())

            # Create a short title from the first part of the decision
            title = text[:60] + "..." if len(text) > 60 else text
            title = title.replace("\n", " ").strip()

            decisions.append({
                "title": title,
                "decided": timestamp[:10],
                "context": f"CTM Agent [{agent.id}]: {agent.task['title']}",
                "choice": text,
                "references": f"Agent {agent.id}, Session {timestamp[:10]}"
            })

        return decisions

    def format_decision_md(self, decision: Dict[str, str]) -> str:
        """Format a decision for DECISIONS.md."""
        return f"""
### {decision['title']}
- **Decided**: {decision['decided']}
- **Context**: {decision['context']}
- **Choice**: {decision['choice']}
- **References**: {decision['references']}
"""

    def append_decisions(self, decisions: List[Dict[str, str]]) -> int:
        """
        Append decisions to DECISIONS.md.

        Returns count of decisions appended.
        """
        if not self.has_memory_structure():
            return 0

        decisions_path = self.context_dir / "DECISIONS.md"
        if not decisions_path.exists():
            return 0

        try:
            content = decisions_path.read_text()

            # Find insertion point after "## Active Decisions"
            marker = "## Active Decisions"
            if marker not in content:
                return 0

            # Find end of marker line
            marker_end = content.index(marker) + len(marker)

            # Skip any template comments (<!-- ... -->)
            rest = content[marker_end:]
            insertion_offset = 0
            if "<!--" in rest[:200]:
                # Find end of comment
                comment_end = rest.find("-->")
                if comment_end != -1:
                    insertion_offset = comment_end + 3

            insertion_point = marker_end + insertion_offset

            # Build new content
            new_decisions = ""
            for d in decisions:
                new_decisions += self.format_decision_md(d)

            new_content = content[:insertion_point] + new_decisions + content[insertion_point:]
            decisions_path.write_text(new_content)

            return len(decisions)

        except Exception as e:
            print(f"Error appending decisions: {e}")
            return 0

    def generate_session_entry(self, agents: List[Agent]) -> str:
        """
        Generate a SESSIONS.md entry from a list of agents.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")

        completed = [a for a in agents if a.state["status"] == "completed"]
        in_progress = [a for a in agents if a.state["status"] in ["active", "paused"]]

        # Collect all decisions
        all_decisions = []
        for agent in agents:
            all_decisions.extend(agent.context.get("decisions", []))

        # Build entry
        focus_tasks = [a.task["title"][:30] for a in agents[:3]]
        focus = ", ".join(focus_tasks)
        if len(agents) > 3:
            focus += f" (+{len(agents) - 3} more)"

        entry = f"""### {date_str} — CTM Session
**Focus**: {focus}

**Key Outcomes**:
"""

        for a in completed:
            entry += f"- Completed [{a.id}]: {a.task['title']}\n"

        for a in in_progress:
            entry += f"- In progress [{a.id}]: {a.task['title']} ({a.state['progress_pct']}%)\n"

        if all_decisions:
            entry += "\n**Decisions Made**:\n"
            for d in all_decisions[:5]:
                text = d.get("text", "")[:80]
                entry += f"- {text}\n"

        # Collect open questions from pending actions
        open_questions = []
        for a in agents:
            for action in a.state.get("pending_actions", [])[:2]:
                if action not in open_questions:
                    open_questions.append(action)

        if open_questions:
            entry += "\n**Open Questions**:\n"
            for q in open_questions[:5]:
                entry += f"- {q}\n"

        entry += "\n**Next Steps**:\n"
        for a in in_progress[:3]:
            entry += f"- [ ] Continue [{a.id}]: {a.task['title']}\n"

        return entry

    def append_session(self, entry: str) -> bool:
        """
        Append a session entry to SESSIONS.md.
        """
        if not self.has_memory_structure():
            return False

        sessions_path = self.context_dir / "SESSIONS.md"
        if not sessions_path.exists():
            return False

        try:
            content = sessions_path.read_text()

            marker = "## Recent Sessions"
            if marker not in content:
                return False

            marker_end = content.index(marker) + len(marker)
            new_content = content[:marker_end] + "\n\n" + entry + content[marker_end:]
            sessions_path.write_text(new_content)

            return True

        except Exception as e:
            print(f"Error appending session: {e}")
            return False

    def index_to_rag(self, agent: Agent) -> bool:
        """
        Index agent context to RAG.

        Creates a markdown document and triggers RAG indexing.
        """
        if not self.has_rag():
            return False

        # Create context document
        doc_content = f"""# CTM Agent: {agent.task['title']}

> Agent ID: {agent.id} | Status: {agent.state['status']}
> Created: {agent.timing['created_at'][:10]} | Last Active: {agent.timing['last_active'][:10]}

## Goal
{agent.task['goal']}

## Progress
- Status: {agent.state['status']}
- Progress: {agent.state['progress_pct']}%
"""

        if agent.state.get("current_step"):
            doc_content += f"- Current Step: {agent.state['current_step']}\n"

        if agent.context.get("decisions"):
            doc_content += "\n## Decisions\n"
            for d in agent.context["decisions"]:
                doc_content += f"- [{d.get('timestamp', '')[:10]}] {d.get('text', '')}\n"

        if agent.context.get("learnings"):
            doc_content += "\n## Learnings\n"
            for l in agent.context["learnings"]:
                doc_content += f"- {l.get('text', '')}\n"

        if agent.context.get("key_files"):
            doc_content += "\n## Key Files\n"
            for f in agent.context["key_files"]:
                doc_content += f"- `{f}`\n"

        if agent.outputs.get("files_created"):
            doc_content += "\n## Files Created\n"
            for f in agent.outputs["files_created"]:
                doc_content += f"- `{f}`\n"

        if agent.outputs.get("files_modified"):
            doc_content += "\n## Files Modified\n"
            for f in agent.outputs["files_modified"]:
                doc_content += f"- `{f}`\n"

        # Write to CTM context directory for RAG indexing
        ctm_context_dir = get_ctm_dir() / "context"
        ctm_context_dir.mkdir(parents=True, exist_ok=True)

        doc_path = ctm_context_dir / f"agent-{agent.id}.md"
        doc_path.write_text(doc_content)

        # The actual RAG indexing is done via MCP or hook
        return True

    def consolidate_agent(self, agent: Agent) -> Dict[str, Any]:
        """
        Perform full consolidation for a completed agent.

        Returns summary of what was consolidated.
        """
        result = {
            "decisions_extracted": 0,
            "session_logged": False,
            "rag_indexed": False
        }

        # Extract and append decisions
        decisions = self.extract_decisions(agent)
        if decisions:
            count = self.append_decisions(decisions)
            result["decisions_extracted"] = count

        # Index to RAG
        if self.index_to_rag(agent):
            result["rag_indexed"] = True

        return result

    def consolidate_session(self, agent_ids: List[str]) -> Dict[str, Any]:
        """
        Consolidate a session with multiple agents.
        """
        result = {
            "agents_processed": 0,
            "decisions_extracted": 0,
            "session_logged": False,
            "rag_indexed": 0
        }

        agents = []
        for aid in agent_ids:
            agent = get_agent(aid)
            if agent:
                agents.append(agent)

        if not agents:
            return result

        result["agents_processed"] = len(agents)

        # Extract decisions from all agents
        all_decisions = []
        for agent in agents:
            all_decisions.extend(self.extract_decisions(agent))

        if all_decisions:
            result["decisions_extracted"] = self.append_decisions(all_decisions)

        # Generate session entry
        session_entry = self.generate_session_entry(agents)
        if self.append_session(session_entry):
            result["session_logged"] = True

        # Index each agent to RAG
        for agent in agents:
            if self.index_to_rag(agent):
                result["rag_indexed"] += 1

        return result


def consolidate_agent(agent_id: str, project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Consolidate a single agent."""
    agent = get_agent(agent_id)
    if not agent:
        return {"error": "Agent not found"}

    consolidator = Consolidator(project_path)
    return consolidator.consolidate_agent(agent)


def consolidate_session(project_path: Optional[Path] = None) -> Dict[str, Any]:
    """Consolidate all active agents for current session."""
    index = AgentIndex()
    active_ids = index.get_all_active()

    if not active_ids:
        return {"error": "No active agents"}

    consolidator = Consolidator(project_path)
    return consolidator.consolidate_session(active_ids)
