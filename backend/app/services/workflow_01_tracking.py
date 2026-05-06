from sqlalchemy.orm import Session

from app.agents.graph import create_tracking_workflow
from app.agents.state import TrackingWorkflowState
from app.schemas.chat import ChatRequest, ChatResponse, ShipmentSummary
from app.services.observability import persist_workflow_observability


def handle_tracking_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    """
    Handles chat requests for the tracking workflow using a compiled LangGraph.
    """
    graph = create_tracking_workflow(db)

    initial_state = {
        "conversation_id": payload.conversation_id,
        "customer_id": payload.customer_id,
        "raw_message": payload.message,
        "tool_calls": [],  # Initialize tool calls list
    }

    # Invoke the graph to run the workflow
    final_state = graph.invoke(initial_state)

    # Extract data from the final state for the response
    shipments = [ShipmentSummary(**shipment) for shipment in final_state.get("shipments", [])]
    workflow_name = final_state.get("selected_workflow", "workflow_01_track_shipment")
    detected_intent = final_state.get("detected_intent", "unknown")
    response_text = final_state.get("customer_response", "No response generated.")

    workflow_state = TrackingWorkflowState(
        trace_id=final_state.get("trace_id"),
        conversation_id=payload.conversation_id,
        customer_id=payload.customer_id,
        raw_message=payload.message,
        detected_intent=detected_intent,
        selected_workflow=workflow_name,
        active_order_ids=[order.get("id") for order in final_state.get("active_orders", []) if order.get("id")],
        active_shipment_ids=[
            shipment.get("id") for shipment in final_state.get("active_shipments", []) if shipment.get("id")
        ],
        customer_name=(final_state.get("customer") or {}).get("name"),
        memory_summary=final_state.get("memory_summary"),
        fallback_reason=final_state.get("fallback_reason"),
        response_text=response_text,
        active_shipments=final_state.get("shipments", []),
        tool_logs=final_state.get("tool_calls", []),
    )

    # Persist observability data
    trace_id = persist_workflow_observability(db, workflow_state, workflow_name)
    db.commit()

    return ChatResponse(
        workflow_name=workflow_name,
        intent=detected_intent,
        response_text=response_text,
        active_shipments=shipments,
        state_snapshot={
            "state": final_state,
            "trace_id": trace_id,
        },
    )
