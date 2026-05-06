from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents.state import GraphState
from app.agents.tools.tracking import (
    build_memory_summary,
    build_shipment_summaries,
    build_tracking_response,
    detect_tracking_intent,
)
from app.repositories.tracking import get_tracking_context


def _add_tool_call(state: GraphState, node: str, tool: str, result: dict | None = None) -> None:
    if "tool_calls" not in state:
        state["tool_calls"] = []
    log = {"node": node, "tool": tool}
    if result:
        log.update(result)
    state["tool_calls"].append(log)


def router_node(state: GraphState) -> GraphState:
    """Determine the initial intent of the user."""
    raw_message = state.get("raw_message", "")
    intent = detect_tracking_intent(raw_message)
    state["detected_intent"] = intent
    _add_tool_call(state, "router_node", "detect_tracking_intent", {"intent": intent})
    return state


def context_resolution_node(db: Session, state: GraphState) -> GraphState:
    """Fetch the full business context for the tracking workflow."""
    customer_id = state.get("customer_id")
    conversation_id = state.get("conversation_id")

    if not customer_id or not conversation_id:
        raise ValueError("customer_id and conversation_id must be in state")

    context = get_tracking_context(db=db, customer_id=customer_id, conversation_id=conversation_id)
    if context is None:
        raise HTTPException(status_code=404, detail="Customer or conversation not found.")

    state["customer"] = context.customer.to_dict()
    state["active_orders"] = [order.to_dict(include_relationships=True) for order in context.active_orders]
    state["active_shipments"] = [shipment.to_dict(include_relationships=True) for shipment in context.active_shipments]
    state["active_order_ids"] = [order.id for order in context.active_orders]
    state["active_shipment_ids"] = [shipment.id for shipment in context.active_shipments]
    
    _add_tool_call(state, "context_resolution_node", "get_tracking_context")
    return state


def memory_retrieval_node(state: GraphState) -> GraphState:
    """Build a summary of the conversation memory."""
    # This node now depends on the context being resolved first.
    customer = state.get("customer", {})
    orders = state.get("active_orders", [])
    
    # Create a mock context object for the tool
    class MockContext:
        def __init__(self, customer, orders):
            self.customer = type("MockCustomer", (), customer)()
            self.active_orders = [type("MockOrder", (), o)() for o in orders]

    if customer and orders:
        mock_context = MockContext(customer, orders)
        memory_summary = build_memory_summary(mock_context)
        state["memory_summary"] = memory_summary
        _add_tool_call(state, "memory_retrieval_node", "build_memory_summary")

    return state


def planner_node(state: GraphState) -> GraphState:
    """Select the appropriate workflow based on the current state."""
    state["selected_workflow"] = "workflow_01_track_shipment"
    _add_tool_call(state, "planner_node", "select_workflow")
    return state


def shipping_node(state: GraphState) -> GraphState:
    """Summarize shipment information."""
    # This node requires the full context to be loaded in state
    shipments = state.get("active_shipments", [])
    
    # The tool expects ORM objects, but we now have dicts.
    # We need to re-hydrate them or adapt the tool. Let's re-hydrate for now.
    class MockShipment:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            # Handle nested objects
            self.events = [type("MockEvent", (), e)() for e in kwargs.get("events", [])]
            self.items = [type("MockItem", (), i)() for i in kwargs.get("items", [])]

    if shipments:
        mock_shipments = [MockShipment(**s) for s in shipments]
        
        # The tool needs a mock context object
        class MockContext:
            def __init__(self, shipments):
                self.active_shipments = shipments
        
        shipment_summaries = build_shipment_summaries(MockContext(mock_shipments))
        state["shipments"] = [s.model_dump() for s in shipment_summaries] # The tool returns Pydantic models
    
    _add_tool_call(state, "shipping_node", "build_shipment_summaries")
    return state


def support_response_node(state: GraphState) -> GraphState:
    """Generate the final response for the user."""
    shipment_summaries = state.get("shipments", [])
    
    # The tool expects Pydantic models, which `shipping_node` now provides.
    class ShipmentSummary:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    if shipment_summaries:
        hydrated_summaries = [ShipmentSummary(**s) for s in shipment_summaries]
        response_text = build_tracking_response(hydrated_summaries)
        state["customer_response"] = response_text
    else:
        # Fallback if no shipments were found
        state["customer_response"] = "ขออภัยค่ะ ไม่พบข้อมูลการจัดส่งสำหรับออเดอร์ของคุณในขณะนี้"

    _add_tool_call(state, "support_response_node", "build_tracking_response")
    return state


def fallback_node(state: GraphState) -> GraphState:
    """Provide a fallback response when the workflow cannot proceed."""
    state["fallback_reason"] = state.get("fallback_reason", "Unknown reason")
    state["customer_response"] = "ขออภัยค่ะ ตอนนี้ฉันยังระบุพัสดุที่ต้องการติดตามไม่ได้ ช่วยส่งเลขออเดอร์ให้ฉันได้ไหมคะ?"
    _add_tool_call(state, "fallback_node", "fallback_response")
    return state
