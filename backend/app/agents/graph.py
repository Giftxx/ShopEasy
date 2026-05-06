from functools import partial

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes.tracking_nodes import (
    context_resolution_node,
    fallback_node,
    memory_retrieval_node,
    planner_node,
    router_node,
    shipping_node,
    support_response_node,
)
from app.agents.state import GraphState


def should_route_to_fallback(state: GraphState) -> str:
    """Determine if the workflow should proceed or fallback."""
    if state.get("detected_intent") == "track_shipment":
        return "continue"
    return "fallback"


def create_tracking_workflow(db: Session):
    """Create the tracking workflow graph using the new GraphState."""
    workflow = StateGraph(GraphState)

    # Bind database session to the context resolution node
    context_node_with_db = partial(context_resolution_node, db)

    # Define the nodes
    workflow.add_node("router", router_node)
    workflow.add_node("get_context", context_node_with_db)
    workflow.add_node("get_memory", memory_retrieval_node)
    workflow.add_node("plan", planner_node)
    workflow.add_node("get_shipping", shipping_node)
    workflow.add_node("respond", support_response_node)
    workflow.add_node("fallback", fallback_node)

    # Build the graph
    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        should_route_to_fallback,
        {
            "continue": "get_context",
            "fallback": "fallback",
        },
    )

    workflow.add_edge("get_context", "get_memory")
    workflow.add_edge("get_memory", "plan")
    workflow.add_edge("plan", "get_shipping")
    workflow.add_edge("get_shipping", "respond")
    workflow.add_edge("respond", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()


