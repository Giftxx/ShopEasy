from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.proactive import ProactiveEventRequest, ProactiveEventResponse
from app.services.workflow_03_proactive import handle_proactive_event


router = APIRouter()


@router.post("/proactive-delay", response_model=ProactiveEventResponse)
def trigger_proactive_delay(payload: ProactiveEventRequest, db: Session = Depends(get_db)) -> ProactiveEventResponse:
    return handle_proactive_event(db, payload)
