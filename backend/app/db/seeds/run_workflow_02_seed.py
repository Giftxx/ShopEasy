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

# NOTE: policy_chunks intentionally omitted — we re-chunk via intelligent extractor below
INSERTION_PLAN = [
    (Conversation, "conversations"),
    (Message, "messages"),
    (Case, "cases"),
    (RefundRequest, "refund_requests"),
    (Attachment, "attachments"),
    (Policy, "policies"),
    (Approval, "approvals"),
]


def reset_workflow_02_data(db: Session, payload: dict[str, list[dict]]) -> None:
    for model, key in DELETE_PLAN:
        records = payload.get(key, [])
        if not records:
            continue
        ids = [record["id"] for record in records]
        db.execute(delete(model).where(model.id.in_(ids)))


def _rechunk_policies(db: Session, payload: dict[str, list[dict]]) -> None:
    """Re-chunk all seeded policies through the intelligent extractor (heading + tag detection)."""
    from app.services import policy_rag
    from app.services.pdf_extractor import extract_from_text

    for record in payload.get("policies", []):
        content = record.get("content") or ""
        if not content.strip():
            continue
        sections = extract_from_text(content)
        policy_rag._create_chunks_from_sections(db, policy_id=record["id"], sections=sections)


def seed_workflow_02(db: Session) -> None:
    payload = get_workflow_02_seed_data()
    for model, key in INSERTION_PLAN:
        for record in payload.get(key, []):
            db.add(model(**record))
    db.flush()
    _rechunk_policies(db, payload)


def main() -> None:
    create_all_tables()
    payload = get_workflow_02_seed_data()
    with SessionLocal() as db:
        reset_workflow_02_data(db, payload)
        for model, key in INSERTION_PLAN:
            for record in payload.get(key, []):
                db.add(model(**record))
        db.flush()
        _rechunk_policies(db, payload)
        db.commit()
        print("Workflow 2 seed complete")


if __name__ == "__main__":
    main()

