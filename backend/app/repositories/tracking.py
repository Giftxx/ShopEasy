from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Conversation, Customer, Order, Shipment
from app.db.models.order import ShipmentItem, OrderItem
from app.db.models.refund import ProactiveAlert, RefundRequest


# Statuses that appear in the 'active' (in-progress) view — used as the
# default filter when the user asks a general question with no specific status.
ACTIVE_SHIPMENT_STATUSES = {"pending", "packing", "packed", "shipped", "in_transit", "out_for_delivery"}

# All statuses the repository should fetch so status-specific queries
# ("สำเร็จ", "ยกเลิก") can work correctly.
ALL_SHIPMENT_STATUSES = ACTIVE_SHIPMENT_STATUSES | {"delivered", "completed", "cancelled", "canceled", "failed", "delayed"}


@dataclass
class TrackingContext:
    customer: Customer
    conversation: Conversation
    active_orders: list[Order]
    active_shipments: list[Shipment]
    refund_requests: list[RefundRequest] = field(default_factory=list)
    proactive_alerts: list[ProactiveAlert] = field(default_factory=list)


def get_tracking_context(db: Session, customer_id: str, conversation_id: str) -> TrackingContext | None:
    customer = db.get(Customer, customer_id)
    if customer is None:
        return None

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.customer_id == customer_id,
        )
    )
    if conversation is None:
        return None

    orders = list(
        db.scalars(
            select(Order)
            .options(
                joinedload(Order.seller),
                joinedload(Order.items),
                joinedload(Order.shipments)
                    .joinedload(Shipment.shipment_items)
                    .joinedload(ShipmentItem.order_item),
            )
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.asc(), Order.id.asc())
        )
        .unique()
    )

    active_orders: list[Order] = []
    active_shipments: list[Shipment] = []

    for order in orders:
        order_active_shipments = [
            shipment
            for shipment in order.shipments
            if (shipment.shipment_status or "").lower() in ALL_SHIPMENT_STATUSES
        ]
        if order_active_shipments:
            active_orders.append(order)
            active_shipments.extend(order_active_shipments)

    # Fetch refund requests for this customer
    refund_requests = list(
        db.scalars(
            select(RefundRequest)
            .where(RefundRequest.customer_id == customer_id)
            .order_by(RefundRequest.created_at.desc())
            .limit(10)
        )
    )

    # Fetch proactive alerts for this customer's orders
    order_ids = [o.id for o in orders]
    proactive_alerts: list[ProactiveAlert] = []
    if order_ids:
        proactive_alerts = list(
            db.scalars(
                select(ProactiveAlert)
                .where(ProactiveAlert.order_id.in_(order_ids))
                .order_by(ProactiveAlert.created_at.desc())
                .limit(10)
            )
        )

    return TrackingContext(
        customer=customer,
        conversation=conversation,
        active_orders=active_orders,
        active_shipments=active_shipments,
        refund_requests=refund_requests,
        proactive_alerts=proactive_alerts,
    )
