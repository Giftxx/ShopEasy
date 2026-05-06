from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.db.init_db import create_all_tables
from app.db.models import Approval, Attachment, Case, Conversation, Message, Policy, PolicyChunk, RefundRequest
from app.db.session import SessionLocal
from app.db.seeds.workflow_02_refund_seed import get_workflow_02_seed_data


DELETE_PLAN = [
    (Approval, "approvals"),
    (Attachment, "attachments"),
    (RefundRequest, "refund_requests"),
    (Case, "cases"),
    (PolicyChunk, "policy_chunks"),
    (Policy, "policies"),
    (Message, "messages"),
    (Conversation, "conversations"),
]

INSERTION_PLAN = [
    (Conversation, "conversations"),
    (Message, "messages"),
    (Case, "cases"),
    (RefundRequest, "refund_requests"),
    (Attachment, "attachments"),
    (Policy, "policies"),
    (PolicyChunk, "policy_chunks"),
    (Approval, "approvals"),
]


def reset_workflow_02_data(db: Session, payload: dict[str, list[dict]]) -> None:
    for model, key in DELETE_PLAN:
        records = payload.get(key, [])
        if not records:
            continue
        ids = [record["id"] for record in records]
        db.execute(delete(model).where(model.id.in_(ids)))


def seed_workflow_02(db: Session) -> None:
    payload = get_workflow_02_seed_data()
    for model, key in INSERTION_PLAN:
        for record in payload.get(key, []):
            db.add(model(**record))


def main() -> None:
    create_all_tables()
    payload = get_workflow_02_seed_data()
    with SessionLocal() as db:
        reset_workflow_02_data(db, payload)
        for model, key in INSERTION_PLAN:
            for record in payload.get(key, []):
                db.add(model(**record))
        db.commit()
        print("Workflow 2 seed complete")


if __name__ == "__main__":
    main()
