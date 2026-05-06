from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OrderItemResponse(BaseModel):
    id: str
    product_name: str | None = None
    sku: str | None = None
    quantity: int | None = None
    unit_price: float | None = None
    created_at: datetime | None = None


class ShipmentEventResponse(BaseModel):
    id: str
    event_type: str | None = None
    event_message: str | None = None
    location: str | None = None
    event_time: datetime | None = None
    raw_payload: dict[str, Any] | None = None
    created_at: datetime | None = None


class ShipmentSummaryResponse(BaseModel):
    id: str
    order_id: str
    carrier: str | None = None
    tracking_no: str | None = None
    shipment_status: str | None = None
    eta: date | None = None
    last_update: datetime | None = None
    delay_risk_score: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ShipmentDetailResponse(ShipmentSummaryResponse):
    events: list[ShipmentEventResponse] = Field(default_factory=list)


class OrderSummaryResponse(BaseModel):
    id: str
    customer_id: str
    seller_id: str
    seller_name: str | None = None
    order_status: str
    payment_status: str | None = None
    total_amount: float | None = None
    currency: str
    promised_delivery_date: date | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class OrderDetailResponse(OrderSummaryResponse):
    items: list[OrderItemResponse] = Field(default_factory=list)
    shipments: list[ShipmentSummaryResponse] = Field(default_factory=list)


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    sender_type: str
    sender_id: str | None = None
    content: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime | None = None


class ConversationSummaryResponse(BaseModel):
    id: str
    customer_id: str
    channel: str
    status: str
    latest_intent: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ConversationDetailResponse(ConversationSummaryResponse):
    messages: list[MessageResponse] = Field(default_factory=list)


class RefundRequestSummaryResponse(BaseModel):
    id: str
    order_id: str
    customer_id: str
    case_id: str | None = None
    reason: str | None = None
    requested_resolution: str | None = None
    eligibility_status: str | None = None
    risk_score: int
    ai_recommendation: str | None = None
    status: str | None = None
    evidence_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AttachmentResponse(BaseModel):
    id: str
    evidence_group: str | None = None
    description: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    object_key: str
    upload_status: str | None = None
    created_at: datetime | None = None


class EvidenceItemRequest(BaseModel):
    evidence_group: str
    description: str | None = None
    file_name: str
    mime_type: str = "image/jpeg"


class CustomerRefundCreateRequest(BaseModel):
    conversation_id: str
    order_id: str
    reason: str
    requested_resolution: str = "refund"
    evidence_items: list[EvidenceItemRequest] = Field(default_factory=list)


class CustomerRefundCreateResponse(BaseModel):
    workflow_name: str
    assistant_message: str
    trace_id: str | None = None
    case_id: str | None = None
    refund_request: RefundRequestSummaryResponse


class RefundRequestDetailResponse(RefundRequestSummaryResponse):
    attachments: list[AttachmentResponse] = Field(default_factory=list)
