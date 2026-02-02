#!/usr/bin/env python3
"""
CTM Messaging System

Enables real-time communication between agents/sessions.
Uses filesystem-based message queue for simplicity and reliability.

Part of: OpenClaw-inspired improvements (Phase 3, F07)
Created: 2026-01-30
"""

import json
import time
import os
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageStatus(Enum):
    """Status of a message."""
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
    ttl_seconds: int = 300  # 5 minutes default
    metadata: Dict = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if message has expired."""
        return time.time() - self.timestamp > self.ttl_seconds

    def age_seconds(self) -> float:
        """Get message age in seconds."""
        return time.time() - self.timestamp

    def to_dict(self) -> dict:
        """Convert to dictionary."""
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
        """Create from dictionary."""
        return cls(
            id=data["id"],
            from_agent=data["from_agent"],
            to_agent=data["to_agent"],
            content=data["content"],
            timestamp=data["timestamp"],
            status=data.get("status", "pending"),
            reply_to=data.get("reply_to"),
            ttl_seconds=data.get("ttl_seconds", 300),
            metadata=data.get("metadata", {})
        )


class MessageBus:
    """Filesystem-based message bus for agent communication."""

    def __init__(self, base_dir: str = "~/.claude/ctm/messages"):
        """
        Initialize the message bus.

        Args:
            base_dir: Base directory for message storage
        """
        self.base_dir = Path(base_dir).expanduser()
        self.inbox_dir = self.base_dir / "inbox"
        self.archive_dir = self.base_dir / "archive"
        self._ensure_dirs()
        self._subscribers: List[Callable[[Message], None]] = []

    def _ensure_dirs(self):
        """Ensure required directories exist."""
        self.inbox_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def _generate_id(self, from_agent: str, to_agent: str) -> str:
        """Generate unique message ID."""
        ts = int(time.time() * 1000)
        short_uuid = uuid.uuid4().hex[:8]
        # Sanitize agent names for filesystem
        from_safe = "".join(c if c.isalnum() else "-" for c in from_agent)[:20]
        to_safe = "".join(c if c.isalnum() else "-" for c in to_agent)[:20]
        return f"{from_safe}-{to_safe}-{ts}-{short_uuid}"

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
            ttl_seconds: Time-to-live in seconds (default 5 min)
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

        logger.info(f"Sent message {msg.id[:20]}... from {from_agent} to {to_agent}")

        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(msg)
            except Exception as e:
                logger.warning(f"Subscriber callback failed: {e}")

        return msg

    def receive(
        self,
        agent_id: str,
        from_agent: str = None,
        include_read: bool = False,
        mark_delivered: bool = True
    ) -> List[Message]:
        """
        Receive messages for an agent.

        Args:
            agent_id: The receiving agent's ID
            from_agent: Optional filter by sender
            include_read: Include already-read messages
            mark_delivered: Mark messages as delivered

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
                if mark_delivered and msg.status == "pending":
                    msg.status = "delivered"
                    with open(msg_file, 'w') as f:
                        json.dump(msg.to_dict(), f, indent=2)

            except Exception as e:
                logger.warning(f"Failed to read message {msg_file}: {e}")
                continue

        # Archive expired messages
        for f in to_archive:
            try:
                f.rename(self.archive_dir / f.name)
            except Exception as e:
                logger.warning(f"Failed to archive {f}: {e}")

        return messages

    def mark_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        msg_file = self.inbox_dir / f"{message_id}.json"
        if not msg_file.exists():
            return False

        try:
            with open(msg_file) as f:
                data = json.load(f)

            data["status"] = "read"

            with open(msg_file, 'w') as f:
                json.dump(data, f, indent=2)

            return True
        except Exception as e:
            logger.warning(f"Failed to mark message read: {e}")
            return False

    def reply(
        self,
        original_id: str,
        from_agent: str,
        content: str,
        ttl_seconds: int = 300
    ) -> Optional[Message]:
        """
        Reply to a message.

        Args:
            original_id: ID of the message to reply to
            from_agent: The replying agent's ID
            content: Reply content
            ttl_seconds: Time-to-live for reply

        Returns:
            The reply Message, or None if original not found
        """
        # Find original message
        msg_file = self.inbox_dir / f"{original_id}.json"
        if not msg_file.exists():
            # Check archive
            msg_file = self.archive_dir / f"{original_id}.json"
            if not msg_file.exists():
                logger.warning(f"Original message not found: {original_id}")
                return None

        try:
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
                reply_to=original_id,
                ttl_seconds=ttl_seconds
            )
        except Exception as e:
            logger.warning(f"Failed to reply: {e}")
            return None

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
            poll_interval: How often to check (seconds)

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

    def unsubscribe(self, callback: Callable[[Message], None]):
        """Unsubscribe from messages."""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def cleanup_expired(self) -> int:
        """
        Clean up expired messages.

        Returns:
            Number of messages archived
        """
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
        limit: int = 20,
        include_archived: bool = False
    ) -> List[Message]:
        """
        Get conversation between two agents.

        Args:
            agent1: First agent ID
            agent2: Second agent ID
            limit: Maximum messages to return
            include_archived: Include archived messages

        Returns:
            List of Messages sorted by timestamp
        """
        messages = []
        dirs = [self.inbox_dir]
        if include_archived:
            dirs.append(self.archive_dir)

        for directory in dirs:
            for msg_file in sorted(directory.glob("*.json"), reverse=True):
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

    def get_stats(self) -> dict:
        """Get message bus statistics."""
        inbox_count = len(list(self.inbox_dir.glob("*.json")))
        archive_count = len(list(self.archive_dir.glob("*.json")))

        return {
            "inbox_messages": inbox_count,
            "archived_messages": archive_count,
            "subscribers": len(self._subscribers)
        }


# Module-level singleton
_default_bus: Optional[MessageBus] = None


def get_message_bus() -> MessageBus:
    """Get or create the default message bus."""
    global _default_bus
    if _default_bus is None:
        _default_bus = MessageBus()
    return _default_bus


def send_message(
    from_agent: str,
    to_agent: str,
    content: str,
    **kwargs
) -> Message:
    """Convenience function to send a message."""
    return get_message_bus().send(from_agent, to_agent, content, **kwargs)


def receive_messages(agent_id: str, **kwargs) -> List[Message]:
    """Convenience function to receive messages."""
    return get_message_bus().receive(agent_id, **kwargs)


if __name__ == "__main__":
    # CLI for testing
    import sys

    bus = MessageBus()
    stats = bus.get_stats()

    print("CTM Message Bus Status")
    print("=" * 40)
    print(f"Inbox messages: {stats['inbox_messages']}")
    print(f"Archived messages: {stats['archived_messages']}")

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "send" and len(sys.argv) >= 5:
            from_agent, to_agent, content = sys.argv[2], sys.argv[3], " ".join(sys.argv[4:])
            msg = bus.send(from_agent, to_agent, content)
            print(f"\n✓ Sent message: {msg.id}")

        elif cmd == "receive" and len(sys.argv) >= 3:
            agent_id = sys.argv[2]
            messages = bus.receive(agent_id)
            print(f"\n{len(messages)} message(s) for {agent_id}:")
            for msg in messages:
                print(f"  [{msg.id[:12]}...] From: {msg.from_agent}")
                print(f"    {msg.content[:80]}{'...' if len(msg.content) > 80 else ''}")

        elif cmd == "cleanup":
            archived = bus.cleanup_expired()
            print(f"\n✓ Archived {archived} expired message(s)")

        else:
            print("\nUsage:")
            print("  messaging.py send <from> <to> <content>")
            print("  messaging.py receive <agent_id>")
            print("  messaging.py cleanup")
