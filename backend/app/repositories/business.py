from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Attachment, Conversation, Message, Order, RefundRequest, Shipment, User
from app.schemas.attachment import ConfirmUploadRequest


def list_customer_orders(db: Session, customer_id: str) -> list[Order]:
    stmt: Select[tuple[Order]] = (
        select(Order)
        .options(joinedload(Order.seller))
        .where(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    return list(db.scalars(stmt).unique())


def get_order(db: Session, order_id: str) -> Order | None:
    stmt: Select[tuple[Order]] = (
        select(Order)
        .options(
            joinedload(Order.seller),
            joinedload(Order.items),
            joinedload(Order.shipments),
        )
        .where(Order.id == order_id)
    )
    return db.scalar(stmt)


def list_customer_shipments(db: Session, customer_id: str) -> list[Shipment]:
    stmt: Select[tuple[Shipment]] = (
        select(Shipment)
        .options(joinedload(Shipment.order))
        .join(Order, Shipment.order_id == Order.id)
        .where(Order.customer_id == customer_id)
        .order_by(Shipment.created_at.desc(), Shipment.id.desc())
    )
    return list(db.scalars(stmt).unique())


def get_shipment(db: Session, shipment_id: str) -> Shipment | None:
    stmt: Select[tuple[Shipment]] = (
        select(Shipment)
        .options(joinedload(Shipment.events))
        .where(Shipment.id == shipment_id)
    )
    return db.scalar(stmt)


def list_customer_conversations(db: Session, customer_id: str) -> list[Conversation]:
    stmt: Select[tuple[Conversation]] = (
        select(Conversation)
        .where(Conversation.customer_id == customer_id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
    )
    return list(db.scalars(stmt))


def get_conversation(db: Session, conversation_id: str) -> Conversation | None:
    stmt: Select[tuple[Conversation]] = (
        select(Conversation)
        .options(joinedload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    return db.scalar(stmt)


def list_messages(db: Session, conversation_id: str) -> list[Message]:
    stmt: Select[tuple[Message]] = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc(), Message.id.asc())
    )
    return list(db.scalars(stmt))


def list_customer_refund_requests(db: Session, customer_id: str) -> list[RefundRequest]:
    stmt: Select[tuple[RefundRequest]] = (
        select(RefundRequest)
        .where(RefundRequest.customer_id == customer_id)
        .order_by(RefundRequest.created_at.desc(), RefundRequest.id.desc())
    )
    return list(db.scalars(stmt))


def get_refund_request(db: Session, refund_request_id: str) -> RefundRequest | None:
    stmt: Select[tuple[RefundRequest]] = (
        select(RefundRequest)
        .options(joinedload(RefundRequest.attachments))
        .where(RefundRequest.id == refund_request_id)
    )
    return db.scalar(stmt)


def create_attachment(db: Session, data: ConfirmUploadRequest) -> Attachment:
    refund_request = db.get(RefundRequest, data.refund_request_id)
    if refund_request is None:
        raise ValueError("Refund request not found.")

    attachment = Attachment(
        id=f"ATT-{uuid4().hex[:8].upper()}",
        owner_type="refund_request",
        message_id=None,
        case_id=refund_request.case_id,
        policy_id=None,
        attachment_type="image",
        bucket_name="evidence",
        object_key=data.object_name,
        file_name=data.file_name,
        mime_type=data.content_type,
        refund_request_id=data.refund_request_id,
        evidence_group=data.evidence_group,
        description=data.description,
        display_order=len(refund_request.attachments) + 1,
        file_size_bytes=data.file_size_bytes,
        uploaded_by_type="customer",
        uploaded_by_customer_id=refund_request.customer_id,
        uploaded_by_user_id=None,
        upload_status="uploaded",
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment_by_id(db: Session, attachment_id: str) -> Attachment | None:
    stmt: Select[tuple[Attachment]] = select(Attachment).where(Attachment.id == attachment_id)
    return db.scalar(stmt)


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt: Select[tuple[User]] = select(User).where((User.name == username) | (User.email == username))
    return db.scalar(stmt)


def get_attachments_by_refund_request_id(db: Session, refund_request_id: str) -> list[Attachment]:
    stmt: Select[tuple[Attachment]] = (
        select(Attachment)
        .where(Attachment.refund_request_id == refund_request_id)
        .order_by(Attachment.created_at.desc(), Attachment.id.desc())
    )
    return list(db.scalars(stmt))


def delete_attachment(db: Session, attachment_id: str) -> Attachment | None:
    attachment = get_attachment_by_id(db, attachment_id)
    if attachment:
        db.delete(attachment)
        db.commit()
    return attachment
