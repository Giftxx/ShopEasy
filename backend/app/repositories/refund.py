from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Attachment, Case, Conversation, Customer, Order, Policy, RefundRequest


@dataclass
class RefundContext:
    customer: Customer
    conversation: Conversation
    order: Order
    existing_case: Case | None
    existing_refund_request: RefundRequest | None
    policies: list[Policy]
    attachments: list[Attachment]


def get_refund_context(db: Session, customer_id: str, conversation_id: str, order_id: str | None = None) -> RefundContext | None:
    from datetime import datetime

    customer = db.get(Customer, customer_id)
    if customer is None:
        return None

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_id == customer_id,
        )
    )
    if conversation is None:
        # Auto-create a conversation so the refund form works even without prior chat
        now = datetime.utcnow()
        conversation = Conversation(
            id=conversation_id,
            customer_id=customer_id,
            channel="web_chat",
            status="open",
            latest_intent="refund_request",
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
        db.flush()

    order_stmt = (
        select(Order)
        .options(joinedload(Order.seller), joinedload(Order.items))
        .where(Order.customer_id == customer_id)
    )
    if order_id:
        order_stmt = order_stmt.where(Order.id == order_id)
    order = db.scalar(order_stmt.order_by(Order.created_at.asc(), Order.id.asc()))
    if order is None:
        return None

    existing_case = db.scalar(
        select(Case)
        .where(
            Case.customer_id == customer_id,
            Case.order_id == order.id,
            Case.case_type == "refund",
        )
        .order_by(Case.created_at.desc())
    )
    existing_refund_request = db.scalar(
        select(RefundRequest)
        .where(RefundRequest.customer_id == customer_id, RefundRequest.order_id == order.id)
        .order_by(RefundRequest.created_at.desc())
    )

    policies = list(
        db.scalars(
            select(Policy)
            .where(Policy.category.in_(["refund", "return", "compensation"]), Policy.status == "active")
            .order_by(Policy.category.asc(), Policy.title.asc())
        )
    )

    attachments: list[Attachment] = []
    if existing_refund_request is not None:
        attachments = list(
            db.scalars(
                select(Attachment)
                .where(Attachment.refund_request_id == existing_refund_request.id)
                .order_by(Attachment.display_order.asc(), Attachment.created_at.asc())
            )
        )

    return RefundContext(
        customer=customer,
        conversation=conversation,
        order=order,
        existing_case=existing_case,
        existing_refund_request=existing_refund_request,
        policies=policies,
        attachments=attachments,
    )
