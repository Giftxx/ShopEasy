from sqlalchemy.orm import Session

from app.agents.tools.refund import detect_refund_intent
from app.agents.tools.tracking import detect_tracking_intent
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.workflow_01_tracking import handle_tracking_chat
from app.services.workflow_02_refund import handle_refund_chat


def handle_chat(db: Session, payload: ChatRequest) -> ChatResponse:
    refund_intent = detect_refund_intent(payload.message)
    if refund_intent == "refund_request" and any(
        keyword in payload.message.lower()
        for keyword in ["คืนเงิน", "refund", "return", "สินค้าเสียหาย", "ของเสียหาย", "ของพัง"]
    ):
        return handle_refund_chat(db, payload)

    tracking_intent = detect_tracking_intent(payload.message)
    if tracking_intent == "track_shipment":
        return handle_tracking_chat(db, payload)

    return handle_tracking_chat(db, payload)
