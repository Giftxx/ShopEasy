from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Approval, Case, ProactiveAlert, RefundRequest


def list_cases(db: Session, limit: int = 20) -> list[Case]:
    stmt: Select[tuple[Case]] = (
        select(Case)
        .order_by(Case.created_at.desc(), Case.id.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt))


def get_case(db: Session, case_id: str) -> Case | None:
    stmt: Select[tuple[Case]] = (
        select(Case)
        .options(
            joinedload(Case.approvals),
            joinedload(Case.attachments),
            joinedload(Case.refund_requests).joinedload(RefundRequest.attachments),
        )
        .where(Case.id == case_id)
    )
    return db.scalar(stmt)


def list_approvals(db: Session, limit: int = 20, status: str | None = None) -> list[Approval]:
    stmt: Select[tuple[Approval]] = select(Approval)
    if status:
        stmt = stmt.where(Approval.status == status)
    stmt = stmt.order_by(Approval.created_at.desc(), Approval.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def list_refund_requests(db: Session, limit: int = 20, status: str | None = None) -> list[RefundRequest]:
    stmt: Select[tuple[RefundRequest]] = select(RefundRequest)
    if status:
        stmt = stmt.where(RefundRequest.status == status)
    stmt = stmt.order_by(RefundRequest.created_at.desc(), RefundRequest.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def list_proactive_alerts(db: Session, limit: int = 20, status: str | None = None) -> list[ProactiveAlert]:
    stmt: Select[tuple[ProactiveAlert]] = select(ProactiveAlert)
    if status:
        stmt = stmt.where(ProactiveAlert.status == status)
    stmt = stmt.order_by(ProactiveAlert.created_at.desc(), ProactiveAlert.id.desc()).limit(limit)
    return list(db.scalars(stmt))
