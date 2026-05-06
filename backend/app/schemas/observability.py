from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ToolLogResponse(BaseModel):
    id: str
    trace_id: str
    agent_name: str | None = None
    tool_name: str | None = None
    input_payload: dict[str, Any] | None = None
    output_payload: dict[str, Any] | None = None
    status: str | None = None
    latency_ms: int | None = None
    error_message: str | None = None
    created_at: datetime | None = None


class TraceAttachmentResponse(BaseModel):
    id: str
    evidence_group: str | None = None
    description: str | None = None
    file_name: str | None = None
    mime_type: str | None = None
    object_key: str
    upload_status: str | None = None
    created_at: datetime | None = None


class TraceRefundRequestResponse(BaseModel):
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
    attachments: list[TraceAttachmentResponse] = Field(default_factory=list)


class TraceCaseContextResponse(BaseModel):
    id: str
    customer_id: str
    order_id: str | None = None
    case_type: str | None = None
    priority: str | None = None
    status: str | None = None
    ai_summary: str | None = None
    resolution_note: str | None = None
    refund_requests: list[TraceRefundRequestResponse] = Field(default_factory=list)
    attachments: list[TraceAttachmentResponse] = Field(default_factory=list)


class TraceConversationContextResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str | None = None
    channel: str
    status: str
    latest_intent: str | None = None


class TraceBusinessContextResponse(BaseModel):
    conversation: TraceConversationContextResponse | None = None
    case: TraceCaseContextResponse | None = None
    active_order_ids: list[str] = Field(default_factory=list)
    active_shipment_ids: list[str] = Field(default_factory=list)
    refund_request_id: str | None = None
    alert_id: str | None = None


class AgentTraceSummaryResponse(BaseModel):
    id: str
    conversation_id: str | None = None
    case_id: str | None = None
    workflow_name: str | None = None
    intent: str | None = None
    confidence: float | None = None
    status: str | None = None
    requires_human_approval: bool
    started_at: datetime | None = None
    ended_at: datetime | None = None


class AgentTraceDetailResponse(AgentTraceSummaryResponse):
    final_response: str | None = None
    state_snapshot: dict[str, Any] | None = None
    tool_logs: list[ToolLogResponse] = Field(default_factory=list)
    business_context: TraceBusinessContextResponse | None = None
