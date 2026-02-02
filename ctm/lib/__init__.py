"""
Cognitive Task Manager (CTM) - Core Library

A bio-inspired task management system for Claude Code that mimics
human working memory and executive function.

v2.0.0 Features:
- 4-tier memory hierarchy (L1-L4)
- Knowledge graph with embeddings
- Cognitive load tracking
- Reflection patterns
- Semantic triggers

v2.1.0 Features:
- Multi-agent shared memory pools
- Pub/sub pattern for agent synchronization

v2.2.0 Features:
- Project-context awareness
- Auto-detect project from working directory
- Priority boost for current-project tasks
- Project-grouped briefings
- `ctm project` command for context management

v3.0.0 Features:
- Deadline alerts in briefings (🔴🟠🟡🟢 urgency indicators)
- `ctm deadline` command for setting/viewing deadlines
- Task dependencies with `--blocked-by` flag
- Auto-unblocking when blocker tasks complete
- `ctm block/unblock/deps` commands
- Dependency visualization in briefings
- Progress auto-tracking from files/git commits
- `ctm progress` command with key file tracking
- Cross-session continuity with snapshots
- `ctm snapshot` command for session state
- Enhanced Resume Point in briefings
- Task templates (YAML-based)
- `ctm templates` and `ctm spawn --template`
- Default templates: hubspot-impl, integration, feature, migration
"""

__version__ = "3.0.0"

# Core modules
from .config import load_config, get_ctm_dir
from .agents import Agent, get_agent, list_agents
from .scheduler import get_scheduler
from .memory import get_working_memory, check_memory_pressure

# v2.0 modules
from .memory_tiers import get_tiered_memory, MemoryTier, check_memory_pressure as check_tier_pressure
from .knowledge_graph import get_knowledge_graph, EntityType, RelationType
from .cognitive_load import get_cognitive_tracker
from .reflection import reflect_before_complete, extract_agent_learnings
from .triggers import detect_triggers_semantic, check_for_switch_semantic
from .shared_memory import get_shared_pool, get_project_pool, share_decision, share_learning
from .agents import share_agent_decision, share_agent_learning, get_agent_shared_context
