from sqlalchemy.orm import Session

from app.agents.nodes.proactive_nodes import (
    event_ingestion_node,
    proactive_alert_node,
    proactive_approval_node,
    proactive_case_node,
    proactive_context_resolution_node,
    proactive_logging_node,
    proactive_memory_write_node,
    proactive_policy_rag_node,
    proactive_shipping_node,
    proactive_supervisor_node,
)
from app.agents.state import TrackingWorkflowState
from app.schemas.proactive import ProactiveEventRequest, ProactiveEventResponse
from app.services.observability import persist_workflow_observability


def handle_proactive_event(db: Session, payload: ProactiveEventRequest) -> ProactiveEventResponse:
    graph_definition = {
        "workflow_name": "workflow_03_proactive_delay_alert",
        "nodes": [
            "event_ingestion_node",
            "context_resolution_node",
            "shipping_node",
            "policy_rag_node",
            "proactive_alert_node",
            "supervisor_node",
            "approval_node",
            "support_response_node",
            "memory_write_node",
            "logging_node",
        ],
    }

    state = TrackingWorkflowState(
        conversation_id="SYSTEM-EVENT",
        customer_id="SYSTEM",
        raw_message=payload.event_type,
    )
    state = event_ingestion_node(state, payload.event_type)
    state, context = proactive_context_resolution_node(db, state, payload.shipment_id)
    state.conversation_id = f"SYSTEM-{payload.shipment_id}"
    state, stale_update, risk_score = proactive_shipping_node(state, context)
    state = proactive_policy_rag_node(state, context)
    state, alert = proactive_alert_node(db, state, context, risk_score)
    state = proactive_supervisor_node(state, risk_score)
    state, case = proactive_case_node(db, state, context, alert)
    state = proactive_approval_node(db, state, case, risk_score)
    state = proactive_memory_write_node(state, case, alert)
    state = proactive_logging_node(state)
    trace_id = persist_workflow_observability(db, state, graph_definition["workflow_name"], case_id=case.id)
    db.commit()

    return ProactiveEventResponse(
        workflow_name=graph_definition["workflow_name"],
        intent=state.detected_intent or "proactive_delay_alert",
        response_text=state.response_text or "No proactive response generated.",
        state_snapshot={
            "state": state.model_dump(),
            "graph_nodes": graph_definition["nodes"],
            "trace_id": trace_id,
            "case_id": case.id,
            "alert_id": alert.id,
            "stale_update": stale_update,
            "risk_score": risk_score,
        },
    )
