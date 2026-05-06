from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.init_db import create_all_tables
from app.db.models import Approval, Case, Policy, PolicyChunk, ProactiveAlert, ShipmentEvent
from app.db.session import SessionLocal
from app.db.seeds.workflow_03_proactive_seed import get_workflow_03_seed_data


DELETE_PLAN = [
    (Approval, "approvals"),
    (ProactiveAlert, "proactive_alerts"),
    (ShipmentEvent, "shipment_events"),
    (Case, "cases"),
    (PolicyChunk, "policy_chunks"),
    (Policy, "policies"),
]

INSERTION_PLAN = [
    (Policy, "policies"),
    (PolicyChunk, "policy_chunks"),
    (Case, "cases"),
    (ShipmentEvent, "shipment_events"),
    (ProactiveAlert, "proactive_alerts"),
    (Approval, "approvals"),
]


def reset_workflow_03_data(db: Session, payload: dict[str, list[dict]]) -> None:
    for model, key in DELETE_PLAN:
        ids = [record["id"] for record in payload.get(key, [])]
        if ids:
            db.execute(delete(model).where(model.id.in_(ids)))


def seed_workflow_03(db: Session) -> None:
    payload = get_workflow_03_seed_data()
    for model, key in INSERTION_PLAN:
        for record in payload.get(key, []):
            db.add(model(**record))


def main() -> None:
    create_all_tables()
    payload = get_workflow_03_seed_data()
    with SessionLocal() as db:
        reset_workflow_03_data(db, payload)
        seed_workflow_03(db)
        db.commit()
        print("Workflow 3 seed complete")


if __name__ == "__main__":
    main()
