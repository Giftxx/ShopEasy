from typing import Any, TypedDict

from pydantic import BaseModel, Field


class SessionState(TypedDict, total=False):
    """
    Represents the session-specific information.
    """

    trace_id: str
    conversation_id: str
    customer_id: str
    message_id: str
    workflow_name: str


class InputState(TypedDict, total=False):
    """
    Represents the input from the user or an event.
    """

    raw_message: str
    detected_intent: str
    event_payload: dict


class ContextState(TypedDict, total=False):
    """
    Represents the resolved business context for the workflow.
    """

    customer: dict
    active_orders: list[dict]
    active_shipments: list[dict]
    active_order_ids: list[str]
    active_shipment_ids: list[str]
    case_id: str
    refund_request_id: str


class RetrievalState(TypedDict, total=False):
    """
    Represents the data retrieved from various sources.
    """

    memory_summary: str
    orders: list[dict]
    shipments: list[dict]
    shipment_items: list[dict]
    policies: list[str]
    attachments: list[dict]


class DecisionState(TypedDict, total=False):
    """
    Represents the decisions made by the agent during the workflow.
    """

    selected_workflow: str
    eligibility_result: dict
    risk_score: float
    requires_human_approval: bool
    fallback_reason: str


class OutputState(TypedDict, total=False):
    """
    Represents the output to be sent to the user or other systems.
    """

    customer_response: str
    internal_note: str


class ObservabilityState(TypedDict, total=False):
    """
    Represents the data for monitoring and tracing.
    """

    tool_calls: list[dict]
    node_results: list[dict]
    warnings: list[str]


class GraphState(
    SessionState,
    InputState,
    ContextState,
    RetrievalState,
    DecisionState,
    OutputState,
    ObservabilityState,
):
    """
    Represents the complete state of the graph.
    All fields are optional and added dynamically.
    """

    pass


class TrackingWorkflowState(BaseModel):
    trace_id: str | None = None
    conversation_id: str
    customer_id: str
    raw_message: str
    target_order_id: str | None = None
    detected_intent: str | None = None
    selected_workflow: str | None = None
    active_order_ids: list[str] = Field(default_factory=list)
    active_shipment_ids: list[str] = Field(default_factory=list)
    customer_name: str | None = None
    memory_summary: str | None = None
    fallback_reason: str | None = None
    response_text: str | None = None
    active_shipments: list[dict[str, Any]] = Field(default_factory=list)
    tool_logs: list[dict[str, Any]] = Field(default_factory=list)
    # RAG results from policy_rag_node
    policy_chunks: list[str] = Field(default_factory=list)
    policy_titles: list[str] = Field(default_factory=list)
