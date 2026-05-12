"""Inter-Agent Communication Protocol — message passing between agents/workflows."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HANDOFF = "handoff"
    ESCALATION = "escalation"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class AgentMessage:
    """A message exchanged between agents or workflows."""

    id: str = field(default_factory=lambda: f"MSG-{uuid.uuid4().hex[:8].upper()}")
    source_agent: str = ""
    target_agent: str = ""
    message_type: MessageType = MessageType.EVENT
    priority: Priority = Priority.NORMAL
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None  # links request → response
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_agent": self.source_agent,
            "target_agent": self.target_agent,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "created_at": str(self.created_at),
            "metadata": self.metadata,
        }


class MessageBus:
    """
    In-process message bus for inter-agent communication.

    Supports:
    - publish/subscribe to topics
    - direct agent-to-agent messaging
    - event broadcasting
    - message history for observability
    """

    _instance: MessageBus | None = None

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._agent_handlers: dict[str, Callable] = {}
        self._history: list[AgentMessage] = []
        self._max_history = 1000

    @classmethod
    def get_instance(cls) -> MessageBus:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    # ── Topic-based pub/sub ──────────────────────────────────────────────

    def subscribe(self, topic: str, handler: Callable[[AgentMessage], None]):
        """Subscribe to a topic."""
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, message: AgentMessage):
        """Publish a message to all subscribers of a topic."""
        self._record(message)
        for handler in self._subscribers.get(topic, []):
            try:
                handler(message)
            except Exception as e:
                logger.warning("MessageBus handler error on topic '%s': %s", topic, e)

    # ── Direct agent messaging ───────────────────────────────────────────

    def register_agent(self, agent_name: str, handler: Callable[[AgentMessage], AgentMessage | None]):
        """Register an agent to receive direct messages."""
        self._agent_handlers[agent_name] = handler

    def send(self, message: AgentMessage) -> AgentMessage | None:
        """Send a direct message to a specific agent. Returns response if any."""
        self._record(message)
        handler = self._agent_handlers.get(message.target_agent)
        if handler is None:
            logger.warning("No handler registered for agent '%s'", message.target_agent)
            return None
        try:
            response = handler(message)
            if response:
                response.correlation_id = message.id
                self._record(response)
            return response
        except Exception as e:
            logger.warning("MessageBus send error to '%s': %s", message.target_agent, e)
            return None

    # ── Event broadcasting ───────────────────────────────────────────────

    def broadcast(self, message: AgentMessage):
        """Broadcast an event to all registered agents and topic subscribers."""
        self._record(message)
        # Notify all agent handlers
        for name, handler in self._agent_handlers.items():
            if name != message.source_agent:
                try:
                    handler(message)
                except Exception as e:
                    logger.debug("Broadcast error to '%s': %s", name, e)
        # Notify topic subscribers for the message type
        for handler in self._subscribers.get(message.message_type.value, []):
            try:
                handler(message)
            except Exception as e:
                logger.debug("Broadcast topic error: %s", e)

    # ── Workflow handoff ─────────────────────────────────────────────────

    def handoff(self, source: str, target: str, context: dict, reason: str = "") -> AgentMessage:
        """Hand off a conversation/task from one workflow to another."""
        message = AgentMessage(
            source_agent=source,
            target_agent=target,
            message_type=MessageType.HANDOFF,
            priority=Priority.HIGH,
            payload={"context": context, "reason": reason},
        )
        self.publish("handoff", message)
        return message

    def escalate(self, source: str, context: dict, reason: str = "", risk_score: int = 0) -> AgentMessage:
        """Escalate a case to human review."""
        message = AgentMessage(
            source_agent=source,
            target_agent="human_supervisor",
            message_type=MessageType.ESCALATION,
            priority=Priority.URGENT if risk_score >= 80 else Priority.HIGH,
            payload={"context": context, "reason": reason, "risk_score": risk_score},
        )
        self.publish("escalation", message)
        return message

    # ── Observability ────────────────────────────────────────────────────

    def get_history(self, limit: int = 50, source: str | None = None, target: str | None = None) -> list[dict]:
        """Get message history for observability."""
        msgs = self._history
        if source:
            msgs = [m for m in msgs if m.source_agent == source]
        if target:
            msgs = [m for m in msgs if m.target_agent == target]
        return [m.to_dict() for m in msgs[-limit:]]

    def _record(self, message: AgentMessage):
        """Record a message in history."""
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
