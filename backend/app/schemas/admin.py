from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CaseSummaryResponse(BaseModel):
    id: str
    customer_id: str
    order_id: str | None = None
    case_type: str | None = None
    priority: str | None = None
    status: str | None = None
    ai_summary: str | None = None
    resolution_note: str | None = None
    assigned_role: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ApprovalResponse(BaseModel):
    id: str
    case_id: str
    approval_type: str
    requested_action: str | None = None
    amount: float | None = None
    currency: str | None = None
    risk_level: str | None = None
    status: str | None = None
    ai_reason: str | None = None
    review_note: str | None = None
    policy_citation: dict[str, Any] | None = None
    created_at: datetime | None = None


class ApprovalActionRequest(BaseModel):
    reason: str | None = Field(default=None, examples=["Approved after manual review."])


class CaseActionRequest(BaseModel):
    reason: str | None = Field(default=None, examples=["Issue resolved by operations team."])


class ProactiveAlertActionRequest(BaseModel):
    reason: str | None = Field(default=None, examples=["Customer notified and monitoring completed."])


class RefundRequestResponse(BaseModel):
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


class RefundRequestDetailResponse(RefundRequestResponse):
    attachments: list[AttachmentResponse] = Field(default_factory=list)


class ProactiveAlertResponse(BaseModel):
    id: str
    order_id: str | None = None
    shipment_id: str | None = None
    alert_type: str | None = None
    risk_score: int | None = None
    status: str | None = None
    recommended_action: str | None = None
    resolution_note: str | None = None
    message_draft: str | None = None
    case_id: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


class CaseDetailResponse(CaseSummaryResponse):
    approvals: list[ApprovalResponse] = Field(default_factory=list)
    refund_requests: list[RefundRequestDetailResponse] = Field(default_factory=list)
    attachments: list[AttachmentResponse] = Field(default_factory=list)
