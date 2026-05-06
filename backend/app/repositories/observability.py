from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import AgentTrace, Case, RefundRequest, ToolLog


def list_agent_traces(
    db: Session,
    limit: int = 20,
    *,
    workflow_name: str | None = None,
    status: str | None = None,
    intent: str | None = None,
    case_id: str | None = None,
) -> list[AgentTrace]:
    stmt: Select[tuple[AgentTrace]] = select(AgentTrace)
    if workflow_name:
        stmt = stmt.where(AgentTrace.workflow_name == workflow_name)
    if status:
        stmt = stmt.where(AgentTrace.status == status)
    if intent:
        stmt = stmt.where(AgentTrace.intent == intent)
    if case_id:
        stmt = stmt.where(AgentTrace.case_id == case_id)
    stmt = stmt.order_by(AgentTrace.started_at.desc(), AgentTrace.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_agent_trace(db: Session, trace_id: str) -> AgentTrace | None:
    stmt: Select[tuple[AgentTrace]] = (
        select(AgentTrace)
        .options(joinedload(AgentTrace.tool_logs), joinedload(AgentTrace.conversation))
        .where(AgentTrace.id == trace_id)
    )
    return db.scalar(stmt)


def list_tool_logs(
    db: Session,
    trace_id: str | None = None,
    limit: int = 50,
    *,
    agent_name: str | None = None,
    tool_name: str | None = None,
    status: str | None = None,
) -> list[ToolLog]:
    stmt: Select[tuple[ToolLog]] = select(ToolLog)
    if trace_id:
        stmt = stmt.where(ToolLog.trace_id == trace_id)
    if agent_name:
        stmt = stmt.where(ToolLog.agent_name == agent_name)
    if tool_name:
        stmt = stmt.where(ToolLog.tool_name == tool_name)
    if status:
        stmt = stmt.where(ToolLog.status == status)
    stmt = stmt.order_by(ToolLog.created_at.desc(), ToolLog.id.desc()).limit(limit)
    return list(db.scalars(stmt))


def get_case_for_trace(db: Session, case_id: str | None) -> Case | None:
    if not case_id:
        return None

    stmt: Select[tuple[Case]] = (
        select(Case)
        .options(
            joinedload(Case.attachments),
            joinedload(Case.refund_requests).joinedload(RefundRequest.attachments),
        )
        .where(Case.id == case_id)
    )
    return db.scalar(stmt)
