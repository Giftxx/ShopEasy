from app.db.base import Base
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
from app.db.session import engine


def create_all_tables() -> None:
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_all_tables()
