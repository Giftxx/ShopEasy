"""Memory models — CustomerLongTermMemory and CustomerEpisodicMemory."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base


class CustomerLongTermMemory(Base):
    __tablename__ = "customer_long_term_memory"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type = sa.Column(sa.String(50))  # behavior | preference | pattern | risk
    key = sa.Column(sa.String(100), index=True)
    value = sa.Column(JSONB)
    confidence = sa.Column(sa.Float, default=1.0)
    source_agent = sa.Column(sa.String(50))
    updated_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        onupdate=sa.text("now()"),
    )


class CustomerEpisodicMemory(Base):
    __tablename__ = "customer_episodic_memory"

    id = sa.Column(sa.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = sa.Column(
        sa.String(36),
        sa.ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = sa.Column(sa.String(50), nullable=False)  # fraud | escalation | dispute | refund_abuse
    summary = sa.Column(sa.Text)
    metadata_ = sa.Column("metadata", JSONB)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
    )


class ExecutionPlanRecord(Base):
    __tablename__ = "execution_plans"

    id = sa.Column(sa.String(50), primary_key=True, default=lambda: f"PLAN-{uuid.uuid4().hex[:8].upper()}")
    trace_id = sa.Column(sa.String(100), sa.ForeignKey("agent_traces.id"), nullable=True)
    intent = sa.Column(sa.String(100))
    plan_json = sa.Column(JSONB)
    risk_level = sa.Column(sa.String(20))
    replan_count = sa.Column(sa.Integer, default=0)
    created_at = sa.Column(
        sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
    )
