# PRD: Phase 3 - Multi-Agent Coordination

> **Parent PRD:** `PRD-openclaw-inspired-improvements.md`
> **Created:** 2026-01-30 | **Status:** Ready for Implementation
> **Estimated Effort:** 3 days | **Priority:** Medium
> **Depends On:** Phase 1 & 2 completed

---

## Overview

Phase 3 focuses on **enabling real-time agent collaboration** and **improving multi-session coordination**. These features allow agents to communicate and share context more effectively.

### Features in This Phase

| ID | Feature | Impact | Effort |
|----|---------|--------|--------|
| F04 | Lazy Skill Loading | MEDIUM | 2h |
| F07 | Session-to-Session Messaging | HIGH | 1d |
| F09 | State Versioning | MEDIUM | 4h |
| F12 | Workspace Bootstrap Files | MEDIUM | 2h |
| F14 | Agent Spawn with Isolation | MEDIUM | 4h |
| F18 | Agent-to-Agent Reply Loops | MEDIUM | 4h |

---

## F04: Lazy Skill Loading

### Problem
Large SKILL.md files consume tokens even when not used.

### Solution
Split skills into compact triggers + on-demand references.

### Implementation

#### 4.1 Refactor large skills

**Target skills (>150 lines):**
- `hubspot-specialist` (~800 lines)
- `solution-architect` (~600 lines)
- `project-discovery` (~400 lines)

**Pattern:**
```
skills/example/
├── SKILL.md           # <100 lines - triggers only
└── references/
    ├── detailed.md    # Loaded on demand
    └── examples.md    # Loaded on demand
```

#### 4.2 Create migration script

**File:** `~/.claude/scripts/migrate-skills-lazy.sh`

```bash
#!/bin/bash
# Migrate large skills to lazy loading pattern

SKILLS_DIR="$HOME/.claude/skills"
THRESHOLD=150

echo "Scanning skills for lazy loading candidates..."

for skill_dir in "$SKILLS_DIR"/*/; do
    skill_file="$skill_dir/SKILL.md"
    if [ -f "$skill_file" ]; then
        line_count=$(wc -l < "$skill_file")
        if [ "$line_count" -gt "$THRESHOLD" ]; then
            skill_name=$(basename "$skill_dir")
            echo "[$skill_name] $line_count lines - CANDIDATE"

            # Check if already has references
            if [ -d "$skill_dir/references" ]; then
                echo "  → Already has references/ directory"
            else
                echo "  → Needs migration"
            fi
        fi
    fi
done
```

#### 4.3 Update skill loading documentation

**Add to CLAUDE.md:**
```markdown
## Lazy Skill Loading

Large skills use lazy loading:
- SKILL.md contains triggers and summary only
- Detailed docs in `references/` loaded on demand
- Read reference files when depth is needed

**Pattern:** If skill says "For details, read references/X.md", use Read tool.
```

### Acceptance Criteria
- [ ] Large skills split into trigger + references
- [ ] References only loaded when needed
- [ ] Token savings measured (target: 2-3K)
- [ ] No functionality regression

---

## F07: Session-to-Session Messaging

### Problem
CDP is async-only; no real-time agent coordination.

### Solution
CTM-based messaging system for agent communication.

### Implementation

#### 7.1 Create messaging module

**File:** `~/.claude/ctm/lib/messaging.py`

```python
#!/usr/bin/env python3
"""
CTM Messaging System

Enables real-time communication between agents/sessions.
Uses filesystem-based message queue for simplicity.
"""

import json
import time
import os
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Callable
from enum import Enum
import threading

class MessageStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    REPLIED = "replied"
    EXPIRED = "expired"

@dataclass
class Message:
    """A message between agents."""
    id: str
    from_agent: str
    to_agent: str
    content: str
    timestamp: float
    status: str = "pending"
    reply_to: Optional[str] = None
    ttl_seconds: int = 300
    metadata: dict = field(default_factory=dict)

    def is_expired(self) -> bool:
        return time.time() - self.timestamp > self.ttl_seconds

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "content": self.content,
            "timestamp": self.timestamp,
            "status": self.status,
            "reply_to": self.reply_to,
            "ttl_seconds": self.ttl_seconds,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(**data)

class MessageBus:
    """Filesystem-based message bus for agent communication."""

    def __init__(self, base_dir: str = "~/.claude/ctm/messages"):
        self.base_dir = Path(base_dir).expanduser()
        self.inbox_dir = self.base_dir / "inbox"
        self.archive_dir = self.base_dir / "archive"
        self._ensure_dirs()
        self._subscribers: List[Callable] = []

    def _ensure_dirs(self):
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, from_agent: str, to_agent: str) -> str:
        ts = int(time.time() * 1000)
        short_uuid = uuid.uuid4().hex[:8]
        return f"{from_agent}-{to_agent}-{ts}-{short_uuid}"

    def send(
        self,
        from_agent: str,
        to_agent: str,
        content: str,
        reply_to: str = None,
        ttl_seconds: int = 300,
        metadata: dict = None
    ) -> Message:
        """
        Send a message to another agent.

        Args:
            from_agent: Sender agent ID
            to_agent: Recipient agent ID
            content: Message content
            reply_to: Optional message ID this replies to
            ttl_seconds: Time-to-live in seconds
            metadata: Optional metadata dict

        Returns:
            The sent Message object
        """
        msg = Message(
            id=self._generate_id(from_agent, to_agent),
            from_agent=from_agent,
            to_agent=to_agent,
            content=content,
            timestamp=time.time(),
            reply_to=reply_to,
            ttl_seconds=ttl_seconds,
            metadata=metadata or {}
        )

        # Write to filesystem
        msg_file = self.inbox_dir / f"{msg.id}.json"
        with open(msg_file, 'w') as f:
            json.dump(msg.to_dict(), f, indent=2)

        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(msg)
            except Exception:
                pass

        return msg

    def receive(
        self,
        agent_id: str,
        from_agent: str = None,
        include_read: bool = False
    ) -> List[Message]:
        """
        Receive messages for an agent.

        Args:
            agent_id: The receiving agent's ID
            from_agent: Optional filter by sender
            include_read: Include already-read messages

        Returns:
            List of Message objects
        """
        messages = []
        to_archive = []

        for msg_file in sorted(self.inbox_dir.glob("*.json")):
            try:
                with open(msg_file) as f:
                    data = json.load(f)
                msg = Message.from_dict(data)

                # Check expiration
                if msg.is_expired():
                    to_archive.append(msg_file)
                    continue

                # Filter by recipient
                if msg.to_agent != agent_id:
                    continue

                # Filter by sender
                if from_agent and msg.from_agent != from_agent:
                    continue

                # Filter by read status
                if not include_read and msg.status == "read":
                    continue

                messages.append(msg)

                # Mark as delivered
                if msg.status == "pending":
                    msg.status = "delivered"
                    with open(msg_file, 'w') as f:
                        json.dump(msg.to_dict(), f, indent=2)

            except Exception as e:
                continue

        # Archive expired messages
        for f in to_archive:
            try:
                f.rename(self.archive_dir / f.name)
            except:
                pass

        return messages

    def mark_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        msg_file = self.inbox_dir / f"{message_id}.json"
        if not msg_file.exists():
            return False

        with open(msg_file) as f:
            data = json.load(f)

        data["status"] = "read"

        with open(msg_file, 'w') as f:
            json.dump(data, f, indent=2)

        return True

    def reply(
        self,
        original_id: str,
        from_agent: str,
        content: str
    ) -> Optional[Message]:
        """Reply to a message."""
        # Find original to get sender
        msg_file = self.inbox_dir / f"{original_id}.json"
        if not msg_file.exists():
            # Check archive
            msg_file = self.archive_dir / f"{original_id}.json"
            if not msg_file.exists():
                return None

        with open(msg_file) as f:
            original = json.load(f)

        # Mark original as replied
        original["status"] = "replied"
        with open(msg_file, 'w') as f:
            json.dump(original, f, indent=2)

        # Send reply
        return self.send(
            from_agent=from_agent,
            to_agent=original["from_agent"],
            content=content,
            reply_to=original_id
        )

    def wait_for_reply(
        self,
        message_id: str,
        timeout_seconds: int = 30,
        poll_interval: float = 0.5
    ) -> Optional[Message]:
        """
        Wait for a reply to a message.

        Args:
            message_id: The message ID to wait for reply to
            timeout_seconds: Maximum wait time
            poll_interval: How often to check

        Returns:
            Reply Message if received, None if timeout
        """
        start = time.time()

        while time.time() - start < timeout_seconds:
            for msg_file in self.inbox_dir.glob("*.json"):
                try:
                    with open(msg_file) as f:
                        data = json.load(f)
                    if data.get("reply_to") == message_id:
                        return Message.from_dict(data)
                except:
                    continue

            time.sleep(poll_interval)

        return None

    def subscribe(self, callback: Callable[[Message], None]):
        """Subscribe to new messages."""
        self._subscribers.append(callback)

    def cleanup_expired(self) -> int:
        """Clean up expired messages."""
        archived = 0
        for msg_file in self.inbox_dir.glob("*.json"):
            try:
                with open(msg_file) as f:
                    data = json.load(f)
                msg = Message.from_dict(data)
                if msg.is_expired():
                    msg_file.rename(self.archive_dir / msg_file.name)
                    archived += 1
            except:
                pass
        return archived

    def get_conversation(
        self,
        agent1: str,
        agent2: str,
        limit: int = 20
    ) -> List[Message]:
        """Get conversation between two agents."""
        messages = []

        for msg_file in sorted(self.inbox_dir.glob("*.json"), reverse=True):
            if len(messages) >= limit:
                break

            try:
                with open(msg_file) as f:
                    data = json.load(f)
                msg = Message.from_dict(data)

                # Check if between the two agents
                if (msg.from_agent == agent1 and msg.to_agent == agent2) or \
                   (msg.from_agent == agent2 and msg.to_agent == agent1):
                    messages.append(msg)
            except:
                continue

        return sorted(messages, key=lambda m: m.timestamp)

# Default bus instance
_default_bus: Optional[MessageBus] = None

def get_message_bus() -> MessageBus:
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus
```

#### 7.2 Add CTM commands

**Update:** `~/.claude/ctm/lib/ctm.py`

```python
# Add to imports
from messaging import get_message_bus, Message

# Add commands

def cmd_send(args):
    """Send a message to another agent."""
    bus = get_message_bus()

    to_agent = args.to_agent
    content = args.message
    wait = args.wait
    timeout = args.timeout or 30

    # Get current agent ID
    from_agent = get_current_agent_id() or f"session-{os.getpid()}"

    msg = bus.send(
        from_agent=from_agent,
        to_agent=to_agent,
        content=content
    )

    print(f"✓ Sent message {msg.id[:12]}... to {to_agent}")

    if wait:
        print(f"Waiting for reply (timeout: {timeout}s)...")
        reply = bus.wait_for_reply(msg.id, timeout)
        if reply:
            print(f"\n─── Reply from {reply.from_agent} ───")
            print(reply.content)
            print("─" * 40)
        else:
            print("✗ No reply received (timeout)")

def cmd_receive(args):
    """Receive messages for current agent."""
    bus = get_message_bus()

    agent_id = args.agent_id or get_current_agent_id() or f"session-{os.getpid()}"
    from_agent = args.from_agent

    messages = bus.receive(agent_id, from_agent=from_agent)

    if not messages:
        print("No new messages.")
        return

    print(f"═══ Messages for {agent_id} ═══\n")
    for msg in messages:
        age = int(time.time() - msg.timestamp)
        print(f"[{msg.id[:12]}...] From: {msg.from_agent}")
        print(f"  Age: {age}s | Status: {msg.status}")
        if msg.reply_to:
            print(f"  Reply to: {msg.reply_to[:12]}...")
        print(f"  Content: {msg.content[:200]}{'...' if len(msg.content) > 200 else ''}")
        print()

def cmd_reply(args):
    """Reply to a message."""
    bus = get_message_bus()

    message_id = args.message_id
    content = args.content
    from_agent = get_current_agent_id() or f"session-{os.getpid()}"

    reply = bus.reply(message_id, from_agent, content)
    if reply:
        print(f"✓ Reply sent: {reply.id[:12]}...")
    else:
        print("✗ Original message not found")

# Add to argument parser
send_parser = subparsers.add_parser('send', help='Send message to agent')
send_parser.add_argument('to_agent', help='Target agent ID')
send_parser.add_argument('message', help='Message content')
send_parser.add_argument('--wait', action='store_true', help='Wait for reply')
send_parser.add_argument('--timeout', type=int, default=30, help='Wait timeout')

receive_parser = subparsers.add_parser('receive', help='Receive messages')
receive_parser.add_argument('--agent-id', help='Agent ID (default: current)')
receive_parser.add_argument('--from-agent', help='Filter by sender')

reply_parser = subparsers.add_parser('reply', help='Reply to message')
reply_parser.add_argument('message_id', help='Message ID to reply to')
reply_parser.add_argument('content', help='Reply content')
```

### Acceptance Criteria
- [ ] `ctm send` delivers messages
- [ ] `ctm receive` retrieves messages
- [ ] `ctm reply` works correctly
- [ ] `--wait` blocks for reply
- [ ] Messages expire after TTL
- [ ] Conversation threading works

---

## F09: State Versioning

### Problem
Risk of race conditions with concurrent agents modifying shared state.

### Solution
Optimistic concurrency control with version numbers.

### Implementation

#### 9.1 Create versioning module

**File:** `~/.claude/ctm/lib/versioning.py`

```python
#!/usr/bin/env python3
"""
State Versioning

Provides optimistic concurrency control for CTM state files.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Callable
from dataclasses import dataclass

class VersionConflictError(Exception):
    """Raised when state version doesn't match expected."""
    def __init__(self, expected: int, actual: int, path: str):
        self.expected = expected
        self.actual = actual
        self.path = path
        super().__init__(
            f"Version conflict in {path}: expected {expected}, found {actual}. "
            "Reload state and retry."
        )

@dataclass
class VersionedState:
    """State with version metadata."""
    version: int
    data: Any
    last_modified: str
    modified_by: Optional[str] = None

class VersionedStore:
    """Versioned JSON file store."""

    def __init__(self, filepath: str):
        self.filepath = Path(filepath).expanduser()

    def read(self) -> VersionedState:
        """Read state with version."""
        if not self.filepath.exists():
            return VersionedState(
                version=0,
                data={},
                last_modified=datetime.utcnow().isoformat()
            )

        with open(self.filepath) as f:
            raw = json.load(f)

        # Handle legacy files without versioning
        if "_version" not in raw:
            return VersionedState(
                version=0,
                data=raw,
                last_modified=raw.get("_last_modified", "")
            )

        return VersionedState(
            version=raw["_version"],
            data=raw.get("data", {}),
            last_modified=raw.get("_last_modified", ""),
            modified_by=raw.get("_modified_by")
        )

    def write(
        self,
        data: Any,
        expected_version: int,
        modifier: str = None
    ) -> int:
        """
        Write state with version check.

        Args:
            data: Data to write
            expected_version: Expected current version
            modifier: Identifier of modifier

        Returns:
            New version number

        Raises:
            VersionConflictError: If versions don't match
        """
        current = self.read()

        if current.version != expected_version:
            raise VersionConflictError(
                expected_version,
                current.version,
                str(self.filepath)
            )

        new_version = current.version + 1

        state = {
            "_version": new_version,
            "_last_modified": datetime.utcnow().isoformat(),
            "_modified_by": modifier or f"pid-{os.getpid()}",
            "data": data
        }

        # Write atomically
        tmp_path = self.filepath.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(state, f, indent=2)
        tmp_path.rename(self.filepath)

        return new_version

    def update(
        self,
        updater: Callable[[Any], Any],
        modifier: str = None,
        max_retries: int = 3
    ) -> Any:
        """
        Atomic update with automatic retry.

        Args:
            updater: Function that takes current data and returns new data
            modifier: Identifier of modifier
            max_retries: Maximum retry attempts

        Returns:
            Updated data

        Raises:
            VersionConflictError: If max retries exceeded
        """
        for attempt in range(max_retries):
            try:
                current = self.read()
                new_data = updater(current.data)
                self.write(new_data, current.version, modifier)
                return new_data
            except VersionConflictError:
                if attempt == max_retries - 1:
                    raise
                # Small delay before retry
                import time
                time.sleep(0.1 * (attempt + 1))

    def get_version(self) -> int:
        """Get current version without full read."""
        return self.read().version

def migrate_to_versioned(filepath: str) -> int:
    """Migrate a legacy file to versioned format."""
    path = Path(filepath).expanduser()

    if not path.exists():
        return 0

    with open(path) as f:
        data = json.load(f)

    # Already versioned
    if "_version" in data:
        return data["_version"]

    # Migrate
    versioned = {
        "_version": 1,
        "_last_modified": datetime.utcnow().isoformat(),
        "_modified_by": "migration",
        "data": data
    }

    with open(path, 'w') as f:
        json.dump(versioned, f, indent=2)

    return 1
```

#### 9.2 Integrate with CTM

**Update agent operations to use versioning.**

### Acceptance Criteria
- [ ] State files include version numbers
- [ ] Concurrent writes detected and rejected
- [ ] Automatic retry on conflict
- [ ] Migration script for legacy files
- [ ] No data corruption with concurrent access

---

## F12: Workspace Bootstrap Files

### Problem
Inconsistent context injection across projects.

### Solution
Define standard bootstrap files injected at session start.

### Implementation

#### 12.1 Create configuration

**File:** `~/.claude/config/bootstrap.json`

```json
{
  "files": [
    {
      "name": "IDENTITY.md",
      "description": "Project identity and purpose",
      "max_chars": 5000,
      "required": false
    },
    {
      "name": "CONTEXT.md",
      "description": "Current project context",
      "max_chars": 10000,
      "required": false
    },
    {
      "name": "DECISIONS.md",
      "description": "Architecture decisions",
      "max_chars": 20000,
      "required": false,
      "path": ".claude/context/DECISIONS.md"
    },
    {
      "name": "CONVENTIONS.md",
      "description": "Coding conventions",
      "max_chars": 5000,
      "required": false
    }
  ],
  "total_max_chars": 30000,
  "inject_on": "SessionStart"
}
```

#### 12.2 Create injection hook

**File:** `~/.claude/hooks/bootstrap-inject.sh`

```bash
#!/bin/bash
# Inject bootstrap files into context

PROJECT_PATH="${CLAUDE_PROJECT_PATH:-$(pwd)}"
CONFIG="$HOME/.claude/config/bootstrap.json"

if [ ! -f "$CONFIG" ]; then
    exit 0
fi

# Read config and inject files
python3 << EOF
import json
from pathlib import Path

project = Path("$PROJECT_PATH")
config_path = Path("$CONFIG")

with open(config_path) as f:
    config = json.load(f)

total_chars = 0
max_total = config.get("total_max_chars", 30000)

print("=== Bootstrap Files ===")

for file_config in config.get("files", []):
    name = file_config["name"]
    path = file_config.get("path", name)
    max_chars = file_config.get("max_chars", 5000)

    file_path = project / path
    if not file_path.exists():
        file_path = project / ".claude" / name
        if not file_path.exists():
            continue

    if total_chars >= max_total:
        print(f"[SKIP] {name} - total limit reached")
        continue

    try:
        content = file_path.read_text()
        if len(content) > max_chars:
            content = content[:max_chars] + f"\\n\\n[Truncated at {max_chars} chars]"

        remaining = max_total - total_chars
        if len(content) > remaining:
            content = content[:remaining] + "\\n\\n[Truncated - total limit]"

        print(f"\\n### {name}")
        print(content)
        total_chars += len(content)
    except Exception as e:
        pass

print(f"\\n[Bootstrap: {total_chars:,} chars injected]")
EOF
```

### Acceptance Criteria
- [ ] Bootstrap files defined in config
- [ ] Files injected at session start
- [ ] Truncation respects limits
- [ ] Missing files handled gracefully

---

## F14 & F18: Agent Isolation & Reply Loops

### Implementation

These features build on F07 (messaging) and F09 (versioning).

**Agent Isolation:**
- Agents run with isolated filesystem view
- Configurable sandbox level (none, directory, docker)

**Reply Loops:**
- Support up to N back-and-forth exchanges
- Configurable max rounds (default: 5)
- Automatic timeout after total time limit

### Acceptance Criteria
- [ ] Agents can be sandboxed
- [ ] Reply loops work up to max rounds
- [ ] Timeout prevents infinite loops

---

## Task Checklist

### F04: Lazy Skill Loading
- [ ] T4.1: Create migration assessment script
- [ ] T4.2: Refactor hubspot-specialist
- [ ] T4.3: Refactor solution-architect
- [ ] T4.4: Refactor project-discovery
- [ ] T4.5: Measure token savings
- [ ] T4.6: Update CLAUDE.md docs

### F07: Session Messaging
- [ ] T7.1: Create messaging.py module
- [ ] T7.2: Create messages/ directory structure
- [ ] T7.3: Add CTM send command
- [ ] T7.4: Add CTM receive command
- [ ] T7.5: Add CTM reply command
- [ ] T7.6: Test message delivery
- [ ] T7.7: Test wait-for-reply
- [ ] T7.8: Test message expiration

### F09: State Versioning
- [ ] T9.1: Create versioning.py module
- [ ] T9.2: Integrate with agent operations
- [ ] T9.3: Create migration script
- [ ] T9.4: Test concurrent access
- [ ] T9.5: Test conflict detection

### F12: Workspace Bootstrap Files
- [ ] T12.1: Create bootstrap.json config
- [ ] T12.2: Create bootstrap-inject.sh hook
- [ ] T12.3: Test file injection
- [ ] T12.4: Test truncation limits

### F14: Agent Isolation
- [ ] T14.1: Design isolation levels
- [ ] T14.2: Implement directory isolation
- [ ] T14.3: Document sandbox options

### F18: Reply Loops
- [ ] T18.1: Add max_rounds config
- [ ] T18.2: Implement loop control
- [ ] T18.3: Add timeout handling
- [ ] T18.4: Test multi-round conversations

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Skill token savings | 2-3K tokens | Compare before/after |
| Message latency | <500ms | Timing logs |
| State conflicts handled | 100% | Concurrent tests |
| Reply loop completion | 95% | Test suite |

---

## Rollback Plan

1. Revert skill changes (restore from git)
2. Remove messaging module
3. Remove versioning (files still readable)
4. Remove bootstrap config
