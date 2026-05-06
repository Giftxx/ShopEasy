from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.admin import (
    get_case,
    list_approvals,
    list_cases,
    list_proactive_alerts,
    list_refund_requests,
)
from app.services.admin_actions import approve_approval, close_case, reject_approval, resolve_proactive_alert
from app.schemas.admin import (
    ApprovalActionRequest,
    ApprovalResponse,
    AttachmentResponse,
    CaseActionRequest,
    CaseDetailResponse,
    CaseSummaryResponse,
    ProactiveAlertResponse,
    ProactiveAlertActionRequest,
    RefundRequestDetailResponse,
    RefundRequestResponse,
)


router = APIRouter()


@router.get("/cases", response_model=list[CaseSummaryResponse])
def read_cases(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[CaseSummaryResponse]:
    cases = list_cases(db, limit=limit)
    return [
        CaseSummaryResponse(
            id=item.id,
            customer_id=item.customer_id,
            order_id=item.order_id,
            case_type=item.case_type,
            priority=item.priority,
            status=item.status,
            ai_summary=item.ai_summary,
            resolution_note=item.resolution_note,
            assigned_role=item.assigned_role,
            created_by=item.created_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in cases
    ]


@router.get("/cases/{case_id}", response_model=CaseDetailResponse)
def read_case(case_id: str, db: Session = Depends(get_db)) -> CaseDetailResponse:
    item = get_case(db, case_id=case_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Case not found.")

    return CaseDetailResponse(
        id=item.id,
        customer_id=item.customer_id,
        order_id=item.order_id,
        case_type=item.case_type,
        priority=item.priority,
        status=item.status,
        ai_summary=item.ai_summary,
        resolution_note=item.resolution_note,
        assigned_role=item.assigned_role,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        approvals=[
            ApprovalResponse(
                id=approval.id,
                case_id=approval.case_id,
                approval_type=approval.approval_type,
                requested_action=approval.requested_action,
                amount=float(approval.amount) if approval.amount is not None else None,
                currency=approval.currency,
                risk_level=approval.risk_level,
                status=approval.status,
                ai_reason=approval.ai_reason,
                review_note=approval.review_note,
                policy_citation=approval.policy_citation,
                created_at=approval.created_at,
            )
            for approval in item.approvals
        ],
        refund_requests=[
            RefundRequestDetailResponse(
                id=refund.id,
                order_id=refund.order_id,
                customer_id=refund.customer_id,
                case_id=refund.case_id,
                reason=refund.reason,
                requested_resolution=refund.requested_resolution,
                eligibility_status=refund.eligibility_status,
                risk_score=refund.risk_score,
                ai_recommendation=refund.ai_recommendation,
                status=refund.status,
                created_at=refund.created_at,
                updated_at=refund.updated_at,
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
                    for attachment in sorted(
                        refund.attachments,
                        key=lambda entry: ((entry.display_order or 0), entry.id),
                    )
                ],
            )
            for refund in item.refund_requests
        ],
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
            for attachment in sorted(
                item.attachments,
                key=lambda entry: ((entry.display_order or 0), entry.id),
            )
        ],
    )


@router.get("/approvals", response_model=list[ApprovalResponse])
def read_approvals(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ApprovalResponse]:
    approvals = list_approvals(db, limit=limit, status=status)
    return [
        ApprovalResponse(
            id=item.id,
            case_id=item.case_id,
            approval_type=item.approval_type,
            requested_action=item.requested_action,
            amount=float(item.amount) if item.amount is not None else None,
            currency=item.currency,
            risk_level=item.risk_level,
            status=item.status,
            ai_reason=item.ai_reason,
            review_note=item.review_note,
            policy_citation=item.policy_citation,
            created_at=item.created_at,
        )
        for item in approvals
    ]


@router.get("/refund-requests", response_model=list[RefundRequestResponse])
def read_refund_requests(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[RefundRequestResponse]:
    refunds = list_refund_requests(db, limit=limit, status=status)
    return [
        RefundRequestResponse(
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
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in refunds
    ]


@router.get("/proactive-alerts", response_model=list[ProactiveAlertResponse])
def read_proactive_alerts(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[ProactiveAlertResponse]:
    alerts = list_proactive_alerts(db, limit=limit, status=status)
    return [
        ProactiveAlertResponse(
            id=item.id,
            order_id=item.order_id,
            shipment_id=item.shipment_id,
            alert_type=item.alert_type,
            risk_score=item.risk_score,
            status=item.status,
            recommended_action=item.recommended_action,
            resolution_note=item.resolution_note,
            message_draft=item.message_draft,
            case_id=item.case_id,
            created_at=item.created_at,
            resolved_at=item.resolved_at,
        )
        for item in alerts
    ]


@router.post("/approvals/{approval_id}/approve", response_model=ApprovalResponse)
def approve_admin_approval(
    approval_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    item = approve_approval(db, approval_id=approval_id, reason=payload.reason)
    return ApprovalResponse(
        id=item.id,
        case_id=item.case_id,
        approval_type=item.approval_type,
        requested_action=item.requested_action,
        amount=float(item.amount) if item.amount is not None else None,
        currency=item.currency,
        risk_level=item.risk_level,
        status=item.status,
        ai_reason=item.ai_reason,
        review_note=item.review_note,
        policy_citation=item.policy_citation,
        created_at=item.created_at,
    )


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
def reject_admin_approval(
    approval_id: str,
    payload: ApprovalActionRequest,
    db: Session = Depends(get_db),
) -> ApprovalResponse:
    item = reject_approval(db, approval_id=approval_id, reason=payload.reason)
    return ApprovalResponse(
        id=item.id,
        case_id=item.case_id,
        approval_type=item.approval_type,
        requested_action=item.requested_action,
        amount=float(item.amount) if item.amount is not None else None,
        currency=item.currency,
        risk_level=item.risk_level,
        status=item.status,
        ai_reason=item.ai_reason,
        policy_citation=item.policy_citation,
        created_at=item.created_at,
    )


@router.post("/cases/{case_id}/close", response_model=CaseSummaryResponse)
def close_admin_case(
    case_id: str,
    payload: CaseActionRequest,
    db: Session = Depends(get_db),
) -> CaseSummaryResponse:
    item = close_case(db, case_id=case_id, reason=payload.reason)
    return CaseSummaryResponse(
        id=item.id,
        customer_id=item.customer_id,
        order_id=item.order_id,
        case_type=item.case_type,
        priority=item.priority,
        status=item.status,
        ai_summary=item.ai_summary,
        resolution_note=item.resolution_note,
        assigned_role=item.assigned_role,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.post("/proactive-alerts/{alert_id}/resolve", response_model=ProactiveAlertResponse)
def resolve_admin_proactive_alert(
    alert_id: str,
    payload: ProactiveAlertActionRequest,
    db: Session = Depends(get_db),
) -> ProactiveAlertResponse:
    item = resolve_proactive_alert(db, alert_id=alert_id, reason=payload.reason)
    return ProactiveAlertResponse(
        id=item.id,
        order_id=item.order_id,
        shipment_id=item.shipment_id,
        alert_type=item.alert_type,
        risk_score=item.risk_score,
        status=item.status,
        recommended_action=item.recommended_action,
        resolution_note=item.resolution_note,
        message_draft=item.message_draft,
        case_id=item.case_id,
        created_at=item.created_at,
        resolved_at=item.resolved_at,
    )
