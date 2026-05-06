from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Attachment
from app.db.session import get_db
from app.repositories.business import (
    get_conversation,
    get_order,
    get_refund_request,
    get_shipment,
    list_customer_conversations,
    list_customer_orders,
    list_customer_refund_requests,
    list_customer_shipments,
    list_messages,
)
from app.schemas.business import (
    AttachmentResponse,
    ConversationDetailResponse,
    ConversationSummaryResponse,
    CustomerRefundCreateRequest,
    CustomerRefundCreateResponse,
    MessageResponse,
    OrderDetailResponse,
    OrderItemResponse,
    OrderSummaryResponse,
    RefundRequestDetailResponse,
    RefundRequestSummaryResponse,
    ShipmentDetailResponse,
    ShipmentEventResponse,
    ShipmentSummaryResponse,
)
from app.schemas.chat import ChatRequest
from app.services.workflow_02_refund import handle_refund_chat


router = APIRouter()


def _build_refund_response(item, evidence_count: int = 0) -> RefundRequestSummaryResponse:
    return RefundRequestSummaryResponse(
        id=item.id,
        order_id=item.order_id,
        customer_id=item.customer_id,
        case_id=item.case_id,
        reason=item.reason,
        requested_resolution=item.requested_resolution,
        eligibility_status=item.eligibility_status,
        risk_score=item.risk_score,
        ai_recommendation=item.ai_recommendation,
        status=item.status,
        evidence_count=evidence_count,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("/customers/{customer_id}/orders", response_model=list[OrderSummaryResponse])
def read_customer_orders(customer_id: str, db: Session = Depends(get_db)) -> list[OrderSummaryResponse]:
    orders = list_customer_orders(db, customer_id)
    return [
        OrderSummaryResponse(
            id=order.id,
            customer_id=order.customer_id,
            seller_id=order.seller_id,
            seller_name=order.seller.name if order.seller else None,
            order_status=order.order_status,
            payment_status=order.payment_status,
            total_amount=float(order.total_amount) if order.total_amount is not None else None,
            currency=order.currency,
            promised_delivery_date=order.promised_delivery_date,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        for order in orders
    ]


@router.get("/orders/{order_id}", response_model=OrderDetailResponse)
def read_order(order_id: str, db: Session = Depends(get_db)) -> OrderDetailResponse:
    order = get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")

    return OrderDetailResponse(
        id=order.id,
        customer_id=order.customer_id,
        seller_id=order.seller_id,
        seller_name=order.seller.name if order.seller else None,
        order_status=order.order_status,
        payment_status=order.payment_status,
        total_amount=float(order.total_amount) if order.total_amount is not None else None,
        currency=order.currency,
        promised_delivery_date=order.promised_delivery_date,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[
            OrderItemResponse(
                id=item.id,
                product_name=item.product_name,
                sku=item.sku,
                quantity=item.quantity,
                unit_price=float(item.unit_price) if item.unit_price is not None else None,
                created_at=item.created_at,
            )
            for item in order.items
        ],
        shipments=[
            ShipmentSummaryResponse(
                id=shipment.id,
                order_id=shipment.order_id,
                carrier=shipment.carrier,
                tracking_no=shipment.tracking_no,
                shipment_status=shipment.shipment_status,
                eta=shipment.eta,
                last_update=shipment.last_update,
                delay_risk_score=shipment.delay_risk_score,
                created_at=shipment.created_at,
                updated_at=shipment.updated_at,
            )
            for shipment in order.shipments
        ],
    )


@router.get("/customers/{customer_id}/shipments", response_model=list[ShipmentSummaryResponse])
def read_customer_shipments(customer_id: str, db: Session = Depends(get_db)) -> list[ShipmentSummaryResponse]:
    shipments = list_customer_shipments(db, customer_id)
    return [
        ShipmentSummaryResponse(
            id=shipment.id,
            order_id=shipment.order_id,
            carrier=shipment.carrier,
            tracking_no=shipment.tracking_no,
            shipment_status=shipment.shipment_status,
            eta=shipment.eta,
            last_update=shipment.last_update,
            delay_risk_score=shipment.delay_risk_score,
            created_at=shipment.created_at,
            updated_at=shipment.updated_at,
        )
        for shipment in shipments
    ]


@router.get("/shipments/{shipment_id}", response_model=ShipmentDetailResponse)
def read_shipment(shipment_id: str, db: Session = Depends(get_db)) -> ShipmentDetailResponse:
    shipment = get_shipment(db, shipment_id)
    if shipment is None:
        raise HTTPException(status_code=404, detail="Shipment not found.")

    return ShipmentDetailResponse(
        id=shipment.id,
        order_id=shipment.order_id,
        carrier=shipment.carrier,
        tracking_no=shipment.tracking_no,
        shipment_status=shipment.shipment_status,
        eta=shipment.eta,
        last_update=shipment.last_update,
        delay_risk_score=shipment.delay_risk_score,
        created_at=shipment.created_at,
        updated_at=shipment.updated_at,
        events=[
            ShipmentEventResponse(
                id=event.id,
                event_type=event.event_type,
                event_message=event.event_message,
                location=event.location,
                event_time=event.event_time,
                raw_payload=event.raw_payload,
                created_at=event.created_at,
            )
            for event in sorted(shipment.events, key=lambda item: ((item.event_time or item.created_at), item.id))
        ],
    )


@router.get("/customers/{customer_id}/conversations", response_model=list[ConversationSummaryResponse])
def read_customer_conversations(customer_id: str, db: Session = Depends(get_db)) -> list[ConversationSummaryResponse]:
    conversations = list_customer_conversations(db, customer_id)
    return [
        ConversationSummaryResponse(
            id=item.id,
            customer_id=item.customer_id,
            channel=item.channel,
            status=item.status,
            latest_intent=item.latest_intent,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def read_conversation(conversation_id: str, db: Session = Depends(get_db)) -> ConversationDetailResponse:
    conversation = get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    return ConversationDetailResponse(
        id=conversation.id,
        customer_id=conversation.customer_id,
        channel=conversation.channel,
        status=conversation.status,
        latest_intent=conversation.latest_intent,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            MessageResponse(
                id=message.id,
                conversation_id=message.conversation_id,
                sender_type=message.sender_type,
                sender_id=message.sender_id,
                content=message.content,
                metadata_json=message.metadata_json,
                created_at=message.created_at,
            )
            for message in sorted(conversation.messages, key=lambda item: ((item.created_at or 0), item.id))
        ],
    )


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def read_messages(conversation_id: str, db: Session = Depends(get_db)) -> list[MessageResponse]:
    messages = list_messages(db, conversation_id)
    return [
        MessageResponse(
            id=message.id,
            conversation_id=message.conversation_id,
            sender_type=message.sender_type,
            sender_id=message.sender_id,
            content=message.content,
            metadata_json=message.metadata_json,
            created_at=message.created_at,
        )
        for message in messages
    ]


@router.get("/customers/{customer_id}/refund-requests", response_model=list[RefundRequestSummaryResponse])
def read_customer_refund_requests(customer_id: str, db: Session = Depends(get_db)) -> list[RefundRequestSummaryResponse]:
    requests = list_customer_refund_requests(db, customer_id)
    return [
        _build_refund_response(item, evidence_count=len(item.attachments))
        for item in requests
    ]


@router.get("/customers/{customer_id}/refund-requests/{refund_request_id}", response_model=RefundRequestDetailResponse)
def read_customer_refund_request_detail(
    customer_id: str,
    refund_request_id: str,
    db: Session = Depends(get_db),
) -> RefundRequestDetailResponse:
    item = get_refund_request(db, refund_request_id)
    if item is None or item.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Refund request not found for this customer.")

    return RefundRequestDetailResponse(
        **_build_refund_response(item, evidence_count=len(item.attachments)).model_dump(),
        attachments=[
            AttachmentResponse(
                id=attachment.id,
                evidence_group=attachment.evidence_group,
                description=attachment.description,
                file_name=attachment.file_name,
                mime_type=attachment.mime_type,
                object_key=attachment.object_key,
                upload_status=attachment.upload_status,
                created_at=attachment.created_at,
            )
            for attachment in sorted(item.attachments, key=lambda entry: ((entry.display_order or 0), entry.id))
        ],
    )


@router.post("/customers/{customer_id}/refund-requests", response_model=CustomerRefundCreateResponse)
def create_customer_refund_request(
    customer_id: str,
    payload: CustomerRefundCreateRequest,
    db: Session = Depends(get_db),
) -> CustomerRefundCreateResponse:
    order = get_order(db, payload.order_id)
    if order is None or order.customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Order not found for this customer.")

    chat_payload = ChatRequest(
        customer_id=customer_id,
        conversation_id=payload.conversation_id,
        message=f"สินค้าเสียหาย ขอคืนเงิน สำหรับออเดอร์ {payload.order_id}. เหตุผล: {payload.reason}",
        target_order_id=payload.order_id,
    )
    result = handle_refund_chat(db, chat_payload)
    refund_request_id = result.state_snapshot.get("refund_request_id")
    if not isinstance(refund_request_id, str):
        raise HTTPException(status_code=500, detail="Refund workflow did not return a refund request id.")

    refund_request = get_refund_request(db, refund_request_id)
    if refund_request is None:
        raise HTTPException(status_code=404, detail="Created refund request not found.")

    created_attachments: list[Attachment] = []
    now = datetime.utcnow()
    for index, evidence_item in enumerate(payload.evidence_items, start=1):
        attachment = Attachment(
            id=f"ATT-{uuid4().hex[:8].upper()}",
            owner_type="refund_request",
            message_id=None,
            case_id=refund_request.case_id,
            refund_request_id=refund_request.id,
            policy_id=None,
            attachment_type="image",
            evidence_group=evidence_item.evidence_group,
            display_order=index,
            description=evidence_item.description,
            bucket_name="customer-evidence",
            object_key=f"refund_request/{refund_request.id}/{evidence_item.evidence_group}/{evidence_item.file_name}",
            file_name=evidence_item.file_name,
            mime_type=evidence_item.mime_type,
            file_size_bytes=None,
            uploaded_by_type="customer",
            uploaded_by_customer_id=customer_id,
            uploaded_by_user_id=None,
            upload_status="uploaded",
            created_at=now,
            updated_at=now,
        )
        db.add(attachment)
        created_attachments.append(attachment)

    db.commit()
    db.refresh(refund_request)

    return CustomerRefundCreateResponse(
        workflow_name=result.workflow_name,
        assistant_message=result.response_text,
        trace_id=result.state_snapshot.get("trace_id") if isinstance(result.state_snapshot.get("trace_id"), str) else None,
        case_id=result.state_snapshot.get("case_id") if isinstance(result.state_snapshot.get("case_id"), str) else None,
        refund_request=_build_refund_response(refund_request, evidence_count=len(created_attachments)),
    )
