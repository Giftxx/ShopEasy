from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.customer import Customer


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), default="web_chat", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open", nullable=False)
    latest_intent: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    customer: Mapped["Customer"] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation")
    traces: Mapped[list["AgentTrace"]] = relationship(back_populates="conversation")

    def to_dict(self, exclude: list[str] | None = None, include_relationships: bool = False) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)

        columns = [c.key for c in mapper.columns if c.key not in exclude]
        data = {c: getattr(self, c) for c in columns}

        if include_relationships:
            for prop in object_mapper(self).iterate_properties:
                if isinstance(prop, RelationshipProperty) and prop.key not in exclude:
                    related_obj = getattr(self, prop.key)
                    if related_obj is None:
                        data[prop.key] = None
                    elif isinstance(related_obj, list):
                        data[prop.key] = [
                            item.to_dict(exclude=exclude, include_relationships=False)
                            for item in related_obj
                        ]
                    else:
                        data[prop.key] = related_obj.to_dict(
                            exclude=exclude, include_relationships=False
                        )
        return data


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    sender_type: Mapped[str] = mapped_column(String(50), nullable=False)
    sender_id: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("conversations.id"))
    case_id: Mapped[str | None] = mapped_column(String(50))
    workflow_name: Mapped[str | None] = mapped_column(String(100))
    intent: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    status: Mapped[str | None] = mapped_column(String(50))
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    final_response: Mapped[str | None] = mapped_column(Text)
    state_snapshot: Mapped[dict | None] = mapped_column(JSON)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    conversation: Mapped["Conversation | None"] = relationship(back_populates="traces")
    tool_logs: Mapped[list["ToolLog"]] = relationship(back_populates="trace")

    def to_dict(self, exclude: list[str] | None = None, include_relationships: bool = False) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)

        columns = [c.key for c in mapper.columns if c.key not in exclude]
        data = {c: getattr(self, c) for c in columns}

        if include_relationships:
            for prop in object_mapper(self).iterate_properties:
                if isinstance(prop, RelationshipProperty) and prop.key not in exclude:
                    related_obj = getattr(self, prop.key)
                    if related_obj is None:
                        data[prop.key] = None
                    elif isinstance(related_obj, list):
                        data[prop.key] = [
                            item.to_dict(exclude=exclude, include_relationships=False)
                            for item in related_obj
                        ]
                    else:
                        data[prop.key] = related_obj.to_dict(
                            exclude=exclude, include_relationships=False
                        )
        return data


class ToolLog(Base):
    __tablename__ = "tool_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    trace_id: Mapped[str] = mapped_column(String(100), ForeignKey("agent_traces.id"), nullable=False)
    agent_name: Mapped[str | None] = mapped_column(String(100))
    tool_name: Mapped[str | None] = mapped_column(String(100))
    input_payload: Mapped[dict | None] = mapped_column(JSON)
    output_payload: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str | None] = mapped_column(String(50))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    trace: Mapped["AgentTrace"] = relationship(back_populates="tool_logs")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}
