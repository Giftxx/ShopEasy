from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AgentTrace, Approval, Case, ProactiveAlert, RefundRequest, ToolLog


def _new_trace_id() -> str:
    return f"TRACE-{uuid4().hex[:12].upper()}"


def _new_log_id() -> str:
    return f"LOG-{uuid4().hex[:12].upper()}"


def _log_admin_action(
    db: Session,
    *,
    case_id: str,
    subject_id: str,
    action: str,
    reason: str | None,
    status: str,
    workflow_name: str = "admin_action",
) -> str:
    now = datetime.utcnow()
    trace_id = _new_trace_id()
    trace = AgentTrace(
        id=trace_id,
        conversation_id=None,
        case_id=case_id,
        workflow_name=workflow_name,
        intent=action,
        confidence=1.0,
        status="completed",
        requires_human_approval=False,
        final_response=f"{subject_id} marked as {status}.",
        state_snapshot={
            "subject_id": subject_id,
            "case_id": case_id,
            "action": action,
            "reason": reason,
            "status": status,
        },
        started_at=now,
        ended_at=now,
    )
    db.add(trace)
    db.add(
        ToolLog(
            id=_new_log_id(),
            trace_id=trace_id,
            agent_name="admin_action",
            tool_name=action,
            input_payload={"subject_id": subject_id, "reason": reason},
            output_payload={"status": status, "case_id": case_id},
            status="success",
            latency_ms=0,
            error_message=None,
            created_at=now,
        )
    )
    return trace_id


def _sync_case_after_approval(db: Session, approval: Approval) -> None:
    case = db.get(Case, approval.case_id)
    if case is None:
        return

    all_approvals = list(
        db.scalars(
            select(Approval)
            .where(Approval.case_id == approval.case_id)
            .order_by(Approval.created_at.desc(), Approval.id.desc())
        )
    )
    statuses = {item.status for item in all_approvals if item.status}

    if "rejected" in statuses:
        case.status = "rejected"
    elif statuses and statuses.issubset({"approved"}):
        case.status = "approved"
    else:
        case.status = "pending_review"

    case.updated_at = datetime.utcnow()

    refund_requests = list(
        db.scalars(
            select(RefundRequest)
            .where(RefundRequest.case_id == approval.case_id)
            .order_by(RefundRequest.created_at.desc(), RefundRequest.id.desc())
        )
    )
    for refund in refund_requests:
        if approval.status == "approved":
            refund.status = "approved"
            refund.eligibility_status = "eligible"
            refund.ai_recommendation = "Approved by admin reviewer."
        elif approval.status == "rejected":
            refund.status = "rejected"
            refund.eligibility_status = "ineligible"
            refund.ai_recommendation = "Rejected by admin reviewer."
        refund.updated_at = datetime.utcnow()


def approve_approval(db: Session, approval_id: str, reason: str | None = None) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if approval.status == "approved":
        return approval

    approval.status = "approved"
    approval.review_note = reason or approval.review_note
    approval.reviewed_at = datetime.utcnow()
    _sync_case_after_approval(db, approval)
    _log_admin_action(
        db,
        case_id=approval.case_id,
        subject_id=approval.id,
        action="approve_approval",
        reason=reason,
        status=approval.status or "approved",
        workflow_name="admin_approval_action",
    )
    db.commit()
    db.refresh(approval)
    return approval


def reject_approval(db: Session, approval_id: str, reason: str | None = None) -> Approval:
    approval = db.get(Approval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found.")
    if approval.status == "rejected":
        return approval

    approval.status = "rejected"
    approval.review_note = reason or approval.review_note
    approval.reviewed_at = datetime.utcnow()
    _sync_case_after_approval(db, approval)
    _log_admin_action(
        db,
        case_id=approval.case_id,
        subject_id=approval.id,
        action="reject_approval",
        reason=reason,
        status=approval.status or "rejected",
        workflow_name="admin_approval_action",
    )
    db.commit()
    db.refresh(approval)
    return approval


def close_case(db: Session, case_id: str, reason: str | None = None) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    if case.status == "closed":
        return case

    case.status = "closed"
    case.resolution_note = reason or case.resolution_note
    case.updated_at = datetime.utcnow()
    _log_admin_action(
        db,
        case_id=case.id,
        subject_id=case.id,
        action="close_case",
        reason=reason,
        status=case.status,
        workflow_name="admin_case_action",
    )
    db.commit()
    db.refresh(case)
    return case


def resolve_proactive_alert(db: Session, alert_id: str, reason: str | None = None) -> ProactiveAlert:
    alert = db.get(ProactiveAlert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Proactive alert not found.")
    if alert.status == "resolved":
        return alert

    alert.status = "resolved"
    alert.resolution_note = reason or alert.resolution_note
    alert.resolved_at = datetime.utcnow()

    if alert.case_id:
        case = db.get(Case, alert.case_id)
        if case is not None and case.status not in ("closed", "approved", "rejected"):
            case.status = "closed"
            case.updated_at = datetime.utcnow()

    _log_admin_action(
        db,
        case_id=alert.case_id or "NO-CASE",
        subject_id=alert.id,
        action="resolve_proactive_alert",
        reason=reason,
        status=alert.status,
        workflow_name="admin_proactive_action",
    )
    db.commit()
    db.refresh(alert)
    return alert
