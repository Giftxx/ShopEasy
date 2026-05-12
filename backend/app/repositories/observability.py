from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import Select, case, cast, func, select, Date
from sqlalchemy.orm import Session, joinedload

from app.db.models import AgentTrace, Case, Conversation, RefundRequest, ToolLog


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


# ── Analytics Aggregation ────────────────────────────────────────────────────


def get_analytics_stats(db: Session) -> dict:
    """Aggregate real stats from conversations and traces."""
    total_conversations = db.scalar(select(func.count(Conversation.id))) or 0
    total_traces = db.scalar(select(func.count(AgentTrace.id))) or 0

    auto_resolved = db.scalar(
        select(func.count(AgentTrace.id)).where(
            AgentTrace.requires_human_approval == False  # noqa: E712
        )
    ) or 0

    handoff_count = db.scalar(
        select(func.count(AgentTrace.id)).where(
            AgentTrace.requires_human_approval == True  # noqa: E712
        )
    ) or 0

    auto_rate = round((auto_resolved / total_traces * 100), 1) if total_traces > 0 else 0.0
    handoff_rate = round((handoff_count / total_traces * 100), 1) if total_traces > 0 else 0.0

    avg_latency_ms = db.scalar(
        select(func.avg(ToolLog.latency_ms)).where(ToolLog.latency_ms.is_not(None))
    )
    avg_response = f"{(avg_latency_ms / 1000):.1f}s" if avg_latency_ms else "N/A"

    return {
        "total_conversations": total_conversations,
        "auto_resolution_rate": auto_rate,
        "handoff_rate": handoff_rate,
        "avg_response_time": avg_response,
        "total_traces": total_traces,
    }


def get_analytics_trend(db: Session, days: int = 12) -> list[dict]:
    """Conversation count per day for the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.execute(
            select(
                cast(Conversation.created_at, Date).label("day"),
                func.count(Conversation.id).label("cnt"),
            )
            .where(Conversation.created_at >= cutoff)
            .group_by(cast(Conversation.created_at, Date))
            .order_by(cast(Conversation.created_at, Date))
        )
        .all()
    )
    return [{"date": str(r.day), "count": r.cnt} for r in rows]


def get_analytics_intents(db: Session) -> list[dict]:
    """Top intents by trace count."""
    rows = (
        db.execute(
            select(
                AgentTrace.intent,
                func.count(AgentTrace.id).label("cnt"),
            )
            .where(AgentTrace.intent.is_not(None))
            .group_by(AgentTrace.intent)
            .order_by(func.count(AgentTrace.id).desc())
            .limit(10)
        )
        .all()
    )
    total = sum(r.cnt for r in rows) or 1
    return [
        {"label": r.intent, "pct": round(r.cnt / total * 100, 1), "count": r.cnt}
        for r in rows
    ]


def get_eval_summary(db: Session) -> dict:
    """Evaluation-like summary computed from trace statuses."""
    total = db.scalar(select(func.count(AgentTrace.id))) or 0

    success = db.scalar(
        select(func.count(AgentTrace.id)).where(AgentTrace.status == "success")
    ) or 0

    failed = db.scalar(
        select(func.count(AgentTrace.id)).where(AgentTrace.status == "failed")
    ) or 0

    partial = total - success - failed

    success_pct = round(success / total * 100, 1) if total > 0 else 0.0
    failed_pct = round(failed / total * 100, 1) if total > 0 else 0.0
    partial_pct = round(partial / total * 100, 1) if total > 0 else 0.0

    latest_trace = db.scalar(
        select(AgentTrace.ended_at)
        .where(AgentTrace.ended_at.is_not(None))
        .order_by(AgentTrace.ended_at.desc())
        .limit(1)
    )

    return {
        "total_traces": total,
        "success": success,
        "failed": failed,
        "partial": partial,
        "success_pct": success_pct,
        "failed_pct": failed_pct,
        "partial_pct": partial_pct,
        "last_run": str(latest_trace) if latest_trace else None,
    }


def get_recent_runs_with_tools(db: Session, limit: int = 10) -> list[dict]:
    """Recent agent traces with their tool calls for the Workspace live feed."""
    traces = (
        db.scalars(
            select(AgentTrace)
            .options(joinedload(AgentTrace.tool_logs))
            .order_by(AgentTrace.started_at.desc(), AgentTrace.id.desc())
            .limit(limit)
        )
        .unique()
        .all()
    )

    result = []
    for t in traces:
        duration_ms = None
        if t.started_at and t.ended_at:
            duration_ms = int((t.ended_at - t.started_at).total_seconds() * 1000)

        tools = sorted(t.tool_logs, key=lambda l: l.created_at or l.id)
        result.append({
            "trace_id": t.id,
            "workflow_name": t.workflow_name,
            "intent": t.intent,
            "confidence": float(t.confidence) if t.confidence is not None else None,
            "status": t.status,
            "requires_human_approval": t.requires_human_approval,
            "duration_ms": duration_ms,
            "started_at": t.started_at.isoformat() if t.started_at else None,
            "tools": [
                {
                    "agent": tl.agent_name,
                    "tool": tl.tool_name,
                    "status": tl.status,
                    "latency_ms": tl.latency_ms,
                }
                for tl in tools
            ],
        })
    return result
