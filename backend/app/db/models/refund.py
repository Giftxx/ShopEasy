from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import AgentTrace, Message
    from app.db.models.customer import Customer, User
    from app.db.models.order import Order, Shipment


class Case(TimestampMixin, Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    order_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("orders.id"))
    case_type: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(50))
    ai_summary: Mapped[str | None] = mapped_column(Text)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    assigned_role: Mapped[str | None] = mapped_column(String(50))
    assigned_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    created_by: Mapped[str | None] = mapped_column(String(50), default="ai")

    customer: Mapped["Customer"] = relationship()
    order: Mapped["Order | None"] = relationship()
    assigned_user: Mapped["User | None"] = relationship()
    approvals: Mapped[list["Approval"]] = relationship(back_populates="case")
    refund_requests: Mapped[list["RefundRequest"]] = relationship(back_populates="case")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="case")

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


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(50), ForeignKey("cases.id"), nullable=False)
    approval_type: Mapped[str] = mapped_column(String(50), nullable=False)
    requested_action: Mapped[str | None] = mapped_column(Text)
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10), default="THB")
    risk_level: Mapped[str | None] = mapped_column(String(50))
    status: Mapped[str | None] = mapped_column(String(50), default="pending")
    ai_reason: Mapped[str | None] = mapped_column(Text)
    review_note: Mapped[str | None] = mapped_column(Text)
    policy_citation: Mapped[dict | None] = mapped_column(JSON)
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    case: Mapped["Case"] = relationship(back_populates="approvals")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class RefundRequest(TimestampMixin, Base):
    __tablename__ = "refund_requests"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    case_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("cases.id"))
    reason: Mapped[str | None] = mapped_column(Text)
    requested_resolution: Mapped[str | None] = mapped_column(String(50))
    eligibility_status: Mapped[str | None] = mapped_column(String(50))
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ai_recommendation: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50), default="pending")

    order: Mapped["Order"] = relationship()
    customer: Mapped["Customer"] = relationship()
    case: Mapped["Case | None"] = relationship(back_populates="refund_requests")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="refund_request")

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


class Policy(TimestampMixin, Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(50))
    version: Mapped[str | None] = mapped_column(String(50))
    content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str | None] = mapped_column(String(50), default="active")
    effective_from: Mapped[date | None] = mapped_column(Date)
    effective_to: Mapped[date | None] = mapped_column(Date)
    # File storage (MinIO)
    source_file_path: Mapped[str | None] = mapped_column(String(500))
    source_filename: Mapped[str | None] = mapped_column(String(255))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)

    chunks: Mapped[list["PolicyChunk"]] = relationship(back_populates="policy")
    attachments: Mapped[list["Attachment"]] = relationship(back_populates="policy")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    policy_id: Mapped[str] = mapped_column(String(36), ForeignKey("policies.id"), nullable=False)
    chunk_index: Mapped[int | None] = mapped_column(Integer)
    chunk_text: Mapped[str | None] = mapped_column(Text)
    heading: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list | None] = mapped_column(JSON)
    page_number: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON)
    embedding_id: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    policy: Mapped["Policy"] = relationship(back_populates="chunks")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class Attachment(TimestampMixin, Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("messages.id"))
    case_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("cases.id"))
    refund_request_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("refund_requests.id"))
    policy_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("policies.id"))
    attachment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_group: Mapped[str | None] = mapped_column(String(50))
    display_order: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)
    bucket_name: Mapped[str] = mapped_column(String(100), nullable=False)
    object_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    mime_type: Mapped[str | None] = mapped_column(String(100))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    uploaded_by_type: Mapped[str | None] = mapped_column(String(50))
    uploaded_by_customer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("customers.id"))
    uploaded_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    upload_status: Mapped[str | None] = mapped_column(String(50), default="uploaded")

    message: Mapped["Message | None"] = relationship()
    case: Mapped["Case | None"] = relationship(back_populates="attachments")
    refund_request: Mapped["RefundRequest | None"] = relationship(back_populates="attachments")
    policy: Mapped["Policy | None"] = relationship(back_populates="attachments")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class ProactiveAlert(Base):
    __tablename__ = "proactive_alerts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    order_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("orders.id"))
    shipment_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("shipments.id"))
    alert_type: Mapped[str | None] = mapped_column(String(50))
    risk_score: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str | None] = mapped_column(String(50), default="open")
    recommended_action: Mapped[str | None] = mapped_column(Text)
    resolution_note: Mapped[str | None] = mapped_column(Text)
    message_draft: Mapped[str | None] = mapped_column(Text)
    case_id: Mapped[str | None] = mapped_column(String(50), ForeignKey("cases.id"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    order: Mapped["Order | None"] = relationship()
    shipment: Mapped["Shipment | None"] = relationship()
    case: Mapped["Case | None"] = relationship()

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}
