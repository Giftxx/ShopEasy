from sqlalchemy import delete

from app.db.init_db import create_all_tables
from app.db.models import (
    AgentTrace,
    Approval,
    Attachment,
    Case,
    Conversation,
    Customer,
    Message,
    Order,
    OrderItem,
    Policy,
    PolicyChunk,
    ProactiveAlert,
    RefundRequest,
    Seller,
    Shipment,
    ShipmentEvent,
    ShipmentItem,
    ToolLog,
    User,
)
from app.db.seeds.run_workflow_01_seed import seed_workflow_01
from app.db.seeds.run_workflow_02_seed import seed_workflow_02
from app.db.seeds.run_workflow_03_seed import seed_workflow_03
from app.db.session import SessionLocal


DELETE_PLAN = [
    ToolLog,
    AgentTrace,
    Approval,
    Attachment,
    ProactiveAlert,
    RefundRequest,
    ShipmentEvent,
    ShipmentItem,
    Message,
    Case,
    Conversation,
    PolicyChunk,
    Policy,
    Shipment,
    OrderItem,
    Order,
    Seller,
    Customer,
    User,
]


def reset_all_data() -> None:
    with SessionLocal() as db:
        for model in DELETE_PLAN:
            db.execute(delete(model))
        db.commit()


def main() -> None:
    create_all_tables()
    reset_all_data()
    with SessionLocal() as db:
        seed_workflow_01(db)
        seed_workflow_02(db)
        seed_workflow_03(db)
        db.commit()


if __name__ == "__main__":
    main()
