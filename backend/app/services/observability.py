from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.state import TrackingWorkflowState
from app.db.models import AgentTrace, Conversation, Message, ToolLog


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12].upper()}"


def persist_workflow_observability(
    db: Session,
    state: TrackingWorkflowState,
    workflow_name: str,
    *,
    case_id: str | None = None,
    confidence: float = 0.95,
) -> str:
    now = datetime.utcnow()
    trace_id = state.trace_id or _new_id("TRACE")
    state.trace_id = trace_id
    conversation = db.get(Conversation, state.conversation_id) if state.conversation_id else None

    trace = AgentTrace(
        id=trace_id,
        conversation_id=conversation.id if conversation is not None else None,
        case_id=case_id,
        workflow_name=workflow_name,
        intent=state.detected_intent,
        confidence=confidence,
        status="completed" if not state.fallback_reason else "fallback",
        requires_human_approval=(state.fallback_reason == "requires_human_approval"),
        final_response=state.response_text,
        state_snapshot=state.model_dump(),
        started_at=now,
        ended_at=now,
    )
    db.add(trace)

    for tool_entry in state.tool_logs:
        db.add(
            ToolLog(
                id=_new_id("LOG"),
                trace_id=trace_id,
                agent_name=tool_entry.get("node"),
                tool_name=tool_entry.get("tool"),
                input_payload={"conversation_id": state.conversation_id, "customer_id": state.customer_id},
                output_payload=tool_entry,
                status="success",
                latency_ms=0,
                error_message=None,
                created_at=now,
            )
        )

    if conversation is not None:
        conversation.latest_intent = state.detected_intent
        conversation.updated_at = now

    if conversation is not None:
        db.add(
            Message(
                id=_new_id("MSG"),
                conversation_id=state.conversation_id,
                sender_type="customer",
                sender_id=state.customer_id,
                content=state.raw_message,
                metadata_json={"source": "api_request", "workflow_name": workflow_name},
                created_at=now,
            )
        )
        db.add(
            Message(
                id=_new_id("MSG"),
                conversation_id=state.conversation_id,
                sender_type="ai",
                sender_id="system",
                content=state.response_text or "No response generated.",
                metadata_json={"source": "workflow_response", "workflow_name": workflow_name, "trace_id": trace_id},
                created_at=now,
            )
        )

    db.flush()
    return trace_id
