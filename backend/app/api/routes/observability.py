from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.observability import get_agent_trace, get_case_for_trace, list_agent_traces, list_tool_logs
from app.schemas.observability import (
    AgentTraceDetailResponse,
    AgentTraceSummaryResponse,
    TraceAttachmentResponse,
    TraceBusinessContextResponse,
    TraceCaseContextResponse,
    TraceConversationContextResponse,
    TraceRefundRequestResponse,
    ToolLogResponse,
)


router = APIRouter()


@router.get("/agent-traces", response_model=list[AgentTraceSummaryResponse])
def read_agent_traces(
    limit: int = Query(default=20, ge=1, le=100),
    workflow_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    intent: str | None = Query(default=None),
    case_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AgentTraceSummaryResponse]:
    traces = list_agent_traces(
        db,
        limit=limit,
        workflow_name=workflow_name,
        status=status,
        intent=intent,
        case_id=case_id,
    )
    return [
        AgentTraceSummaryResponse(
            id=trace.id,
            conversation_id=trace.conversation_id,
            case_id=trace.case_id,
            workflow_name=trace.workflow_name,
            intent=trace.intent,
            confidence=float(trace.confidence) if trace.confidence is not None else None,
            status=trace.status,
            requires_human_approval=trace.requires_human_approval,
            started_at=trace.started_at,
            ended_at=trace.ended_at,
        )
        for trace in traces
    ]


@router.get("/agent-traces/{trace_id}", response_model=AgentTraceDetailResponse)
def read_agent_trace(trace_id: str, db: Session = Depends(get_db)) -> AgentTraceDetailResponse:
    trace = get_agent_trace(db, trace_id=trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found.")

    state_snapshot = trace.state_snapshot or {}
    trace_case = get_case_for_trace(db, trace.case_id)

    derived_refund_request_id = state_snapshot.get("refund_request_id")
    if derived_refund_request_id is None and trace_case is not None and trace_case.refund_requests:
        derived_refund_request_id = trace_case.refund_requests[0].id

    business_context = TraceBusinessContextResponse(
        conversation=(
            TraceConversationContextResponse(
                id=trace.conversation.id,
                customer_id=trace.conversation.customer_id,
                customer_name=state_snapshot.get("customer_name"),
                channel=trace.conversation.channel,
                status=trace.conversation.status,
                latest_intent=trace.conversation.latest_intent,
            )
            if trace.conversation is not None
            else None
        ),
        case=(
            TraceCaseContextResponse(
                id=trace_case.id,
                customer_id=trace_case.customer_id,
                order_id=trace_case.order_id,
                case_type=trace_case.case_type,
                priority=trace_case.priority,
                status=trace_case.status,
                ai_summary=trace_case.ai_summary,
                resolution_note=trace_case.resolution_note,
                refund_requests=[
                    TraceRefundRequestResponse(
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
                        attachments=[
                            TraceAttachmentResponse(
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
                    for refund in trace_case.refund_requests
                ],
                attachments=[
                    TraceAttachmentResponse(
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
                        trace_case.attachments,
                        key=lambda entry: ((entry.display_order or 0), entry.id),
                    )
                ],
            )
            if trace_case is not None
            else None
        ),
        active_order_ids=state_snapshot.get("active_order_ids", []),
        active_shipment_ids=state_snapshot.get("active_shipment_ids", []),
        refund_request_id=derived_refund_request_id,
        alert_id=state_snapshot.get("alert_id"),
    )

    return AgentTraceDetailResponse(
        id=trace.id,
        conversation_id=trace.conversation_id,
        case_id=trace.case_id,
        workflow_name=trace.workflow_name,
        intent=trace.intent,
        confidence=float(trace.confidence) if trace.confidence is not None else None,
        status=trace.status,
        requires_human_approval=trace.requires_human_approval,
        started_at=trace.started_at,
        ended_at=trace.ended_at,
        final_response=trace.final_response,
        state_snapshot=state_snapshot,
        tool_logs=[
            ToolLogResponse(
                id=log.id,
                trace_id=log.trace_id,
                agent_name=log.agent_name,
                tool_name=log.tool_name,
                input_payload=log.input_payload,
                output_payload=log.output_payload,
                status=log.status,
                latency_ms=log.latency_ms,
                error_message=log.error_message,
                created_at=log.created_at,
            )
            for log in sorted(trace.tool_logs, key=lambda item: ((item.created_at or 0), item.id))
        ],
        business_context=business_context,
    )


@router.get("/tool-logs", response_model=list[ToolLogResponse])
def read_tool_logs(
    trace_id: str | None = Query(default=None),
    agent_name: str | None = Query(default=None),
    tool_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ToolLogResponse]:
    logs = list_tool_logs(
        db,
        trace_id=trace_id,
        limit=limit,
        agent_name=agent_name,
        tool_name=tool_name,
        status=status,
    )
    return [
        ToolLogResponse(
            id=log.id,
            trace_id=log.trace_id,
            agent_name=log.agent_name,
            tool_name=log.tool_name,
            input_payload=log.input_payload,
            output_payload=log.output_payload,
            status=log.status,
            latency_ms=log.latency_ms,
            error_message=log.error_message,
            created_at=log.created_at,
        )
        for log in logs
    ]
