from functools import partial

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from app.agents.nodes.tracking_nodes import (
    context_resolution_node,
    fallback_node,
    memory_retrieval_node,
    memory_write_node,
    planner_node,
    router_node,
    shipping_node,
    support_response_node,
)
from app.agents.state import GraphState


def should_route_after_memory(state: GraphState) -> str:
    """Route to tracking pipeline or fallback after context+memory are loaded."""
    if state.get("detected_intent") == "track_shipment":
        return "tracking"
    return "fallback"


def create_tracking_workflow(db: Session):
    """Create the tracking workflow graph using the new GraphState."""
    workflow = StateGraph(GraphState)

    # Bind database session to the context resolution node
    context_node_with_db = partial(context_resolution_node, db)
    memory_read_with_db = partial(memory_retrieval_node, db)
    memory_write_with_db = partial(memory_write_node, db)
    planner_with_db = partial(planner_node, db)
    fallback_with_db = partial(fallback_node, db)
    respond_with_db = partial(support_response_node, db)

    # Define the nodes
    workflow.add_node("router", router_node)
    workflow.add_node("get_context", context_node_with_db)
    workflow.add_node("get_memory", memory_read_with_db)
    workflow.add_node("plan", planner_with_db)
    workflow.add_node("get_shipping", shipping_node)
    workflow.add_node("respond", respond_with_db)
    workflow.add_node("write_memory", memory_write_with_db)
    workflow.add_node("fallback", fallback_with_db)

    # Build the graph — ALL paths go through context + memory first
    workflow.set_entry_point("router")
    workflow.add_edge("router", "get_context")
    workflow.add_edge("get_context", "get_memory")

    # After memory is loaded, branch based on intent
    workflow.add_conditional_edges(
        "get_memory",
        should_route_after_memory,
        {
            "tracking": "plan",
            "fallback": "fallback",
        },
    )

    # Tracking path
    workflow.add_edge("plan", "get_shipping")
    workflow.add_edge("get_shipping", "respond")
    workflow.add_edge("respond", "write_memory")

    # Fallback path — also writes memory
    workflow.add_edge("fallback", "write_memory")

    workflow.add_edge("write_memory", END)

    return workflow.compile()


