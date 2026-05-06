from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.init_db import create_all_tables
from app.db.models import (
    AgentTrace,
    Conversation,
    Customer,
    Message,
    Order,
    OrderItem,
    ProactiveAlert,
    Seller,
    Shipment,
    ShipmentEvent,
    ShipmentItem,
    ToolLog,
    User,
)
from app.db.session import SessionLocal
from app.db.seeds.workflow_01_tracking_seed import get_workflow_01_seed_data


MODEL_ORDER = [
    ToolLog,
    AgentTrace,
    Message,
    Conversation,
    ProactiveAlert,
    ShipmentEvent,  # Delete events before shipments
    ShipmentItem,
    Shipment,
    OrderItem,
    Order,
    Seller,
    Customer,
    User,
]

INSERTION_PLAN = [
    (User, "users"),
    (Customer, "customers"),
    (Seller, "sellers"),
    (Order, "orders"),
    (OrderItem, "order_items"),
    (Shipment, "shipments"),
    (ShipmentItem, "shipment_items"),
    (ShipmentEvent, "shipment_events"),  # Add shipment events to insertion
    (Conversation, "conversations"),
    (Message, "messages"),
    (AgentTrace, "agent_traces"),
    (ToolLog, "tool_logs"),
    (ProactiveAlert, "proactive_alerts"),
]



def reset_workflow_01_data(db: Session) -> None:
    for model in MODEL_ORDER:
        db.execute(delete(model))


def seed_workflow_01(db: Session) -> None:
    payload = get_workflow_01_seed_data()
    for model, key in INSERTION_PLAN:
        records = payload.get(key, [])
        for record in records:
            db.add(model(**record))


def main() -> None:
    create_all_tables()
    with SessionLocal() as db:
        reset_workflow_01_data(db)
        seed_workflow_01(db)
        db.commit()

        customer_count = len(list(db.scalars(select(Customer))))
        order_count = len(list(db.scalars(select(Order))))
        shipment_count = len(list(db.scalars(select(Shipment))))
        print(
            "Workflow 1 seed complete:",
            {
                "customers": customer_count,
                "orders": order_count,
                "shipments": shipment_count,
            },
        )


if __name__ == "__main__":
    main()
