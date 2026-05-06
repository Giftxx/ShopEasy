from sqlalchemy.orm import Session

from app.agents.nodes.refund_nodes import (
    approval_node,
    ensure_case_node,
    evidence_node,
    policy_rag_node,
    refund_context_resolution_node,
    refund_logging_node,
    refund_memory_retrieval_node,
    refund_memory_write_node,
    refund_node,
    refund_order_node,
    refund_planner_node,
    refund_router_node,
    refund_support_response_node,
    risk_node,
    supervisor_node,
)
from app.agents.state import TrackingWorkflowState
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.observability import persist_workflow_observability


def handle_refund_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    graph_definition = {
        "workflow_name": "workflow_02_refund_return",
        "nodes": [
            "router_node",
            "memory_retrieval_node",
            "context_resolution_node",
            "planner_node",
            "order_node",
            "policy_rag_node",
            "refund_node",
            "evidence_node",
            "risk_node",
            "supervisor_node",
            "approval_node",
            "support_response_node",
            "memory_write_node",
            "logging_node",
        ],
    }

    state = TrackingWorkflowState(
        conversation_id=payload.conversation_id,
        customer_id=payload.customer_id,
        raw_message=payload.message,
        target_order_id=payload.target_order_id,
    )

    state = refund_router_node(state)
    state, context = refund_context_resolution_node(db, state)
    state = refund_memory_retrieval_node(state, context)
    state = refund_planner_node(state)
    state = refund_order_node(state, context)
    state = policy_rag_node(state, context)
    state, refund_request = refund_node(db, state, context)
    state, evidence_result = evidence_node(state, context)
    state = risk_node(db, state, context, refund_request, evidence_result)
    state = supervisor_node(state, refund_request)
    state, case = ensure_case_node(db, state, context, refund_request)
    state = approval_node(db, state, case, refund_request)
    state = refund_support_response_node(state, context, case, evidence_result)
    state = refund_memory_write_node(state, case)
    state = refund_logging_node(state)
    workflow_name = state.selected_workflow or graph_definition["workflow_name"]
    trace_id = persist_workflow_observability(db, state, workflow_name, case_id=case.id)
    db.commit()

    return ChatResponse(
        workflow_name=workflow_name,
        intent=state.detected_intent or "refund_request",
        response_text=state.response_text or "No response generated.",
        active_shipments=[],
        state_snapshot={
            "state": state.model_dump(),
            "graph_nodes": graph_definition["nodes"],
            "case_id": case.id,
            "refund_request_id": refund_request.id,
            "trace_id": trace_id,
        },
    )
