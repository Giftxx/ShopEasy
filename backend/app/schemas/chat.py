from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    customer_id: str = Field(..., examples=["CUST-001"])
    conversation_id: str = Field(..., examples=["CONV-001"])
    message: str = Field(..., examples=["ของฉันอยู่ไหนแล้ว"])
    target_order_id: str | None = Field(default=None, examples=["SP-1024"])


class ShipmentSummary(BaseModel):
    order_id: str
    seller_name: str
    item_names: list[str]
    shipment_status: str
    note: str


class ChatResponse(BaseModel):
    workflow_name: str
    intent: str
    response_text: str
    active_shipments: list[ShipmentSummary] = Field(default_factory=list)
    state_snapshot: dict[str, Any]
