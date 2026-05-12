"""Episodic Memory — stores significant events for a customer."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EpisodicMemory:
    """PostgreSQL-based episodic memory for significant customer events."""

    def __init__(self, db: Session, customer_id: str):
        self.db = db
        self.customer_id = customer_id

    def store(self, event_type: str, summary: str, metadata: dict | None = None):
        """Store an episode (fraud, escalation, dispute, etc.)."""
        from app.db.models.memory import CustomerEpisodicMemory

        self.db.add(CustomerEpisodicMemory(
            customer_id=self.customer_id,
            event_type=event_type,
            summary=summary,
            metadata_=metadata or {},
        ))
        self.db.flush()

    def recall(self, event_types: list[str] | None = None, limit: int = 10) -> list[dict]:
        """Recall recent episodes, optionally filtered by type."""
        from app.db.models.memory import CustomerEpisodicMemory

        q = self.db.query(CustomerEpisodicMemory).filter_by(customer_id=self.customer_id)
        if event_types:
            q = q.filter(CustomerEpisodicMemory.event_type.in_(event_types))
        episodes = q.order_by(CustomerEpisodicMemory.created_at.desc()).limit(limit).all()
        return [
            {
                "type": e.event_type,
                "summary": e.summary,
                "metadata": e.metadata_,
                "created_at": str(e.created_at),
            }
            for e in episodes
        ]

    def has_history(self, event_type: str) -> bool:
        """Check if customer has any episodes of a specific type."""
        from app.db.models.memory import CustomerEpisodicMemory

        return (
            self.db.query(CustomerEpisodicMemory)
            .filter_by(customer_id=self.customer_id, event_type=event_type)
            .first()
        ) is not None
