from typing import Any

from pydantic import BaseModel, Field


class ProactiveEventRequest(BaseModel):
    shipment_id: str = Field(..., examples=["SHP-9002"])
    event_type: str = Field(default="shipment_no_update_48h", examples=["shipment_no_update_48h"])


class ProactiveEventResponse(BaseModel):
    workflow_name: str
    intent: str
    response_text: str
    state_snapshot: dict[str, Any]
