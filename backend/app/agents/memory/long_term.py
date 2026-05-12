"""Long-term Memory — PostgreSQL-based persistent customer memory."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class LongTermMemory:
    """PostgreSQL-based persistent memory for customer behaviors and preferences."""

    def __init__(self, db: Session, customer_id: str):
        self.db = db
        self.customer_id = customer_id

    def save(self, memory_type: str, key: str, value: Any, source_agent: str = "system"):
        """Upsert a memory entry (insert or update by customer_id + key)."""
        from app.db.models.memory import CustomerLongTermMemory

        existing = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id, key=key)
            .first()
        )
        if existing:
            existing.value = value
            existing.source_agent = source_agent
            existing.memory_type = memory_type
        else:
            self.db.add(CustomerLongTermMemory(
                customer_id=self.customer_id,
                memory_type=memory_type,
                key=key,
                value=value,
                source_agent=source_agent,
            ))
        self.db.flush()

    def get(self, key: str) -> Any | None:
        """Get a specific memory by key."""
        from app.db.models.memory import CustomerLongTermMemory

        record = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id, key=key)
            .first()
        )
        return record.value if record else None

    def get_all(self) -> list[dict]:
        """Get all memories for this customer."""
        from app.db.models.memory import CustomerLongTermMemory

        records = (
            self.db.query(CustomerLongTermMemory)
            .filter_by(customer_id=self.customer_id)
            .all()
        )
        return [
            {"key": r.key, "value": r.value, "type": r.memory_type, "source": r.source_agent}
            for r in records
        ]

    def build_summary(self) -> str:
        """Build a human-readable summary of the top 10 memories."""
        all_mem = self.get_all()
        if not all_mem:
            return "ไม่มี memory ของลูกค้าคนนี้"
        lines = [f"- {m['key']}: {m['value']}" for m in all_mem[:10]]
        return "Long-term memory:\n" + "\n".join(lines)
