from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Conversation, Customer, Order, Shipment
from app.db.models.order import ShipmentItem, OrderItem


ACTIVE_SHIPMENT_STATUSES = {"pending", "packing", "shipped", "in_transit", "out_for_delivery"}


@dataclass
class TrackingContext:
    customer: Customer
    conversation: Conversation
    active_orders: list[Order]
    active_shipments: list[Shipment]


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
            if shipment.shipment_status in ACTIVE_SHIPMENT_STATUSES
        ]
        if order_active_shipments:
            active_orders.append(order)
            active_shipments.extend(order_active_shipments)

    return TrackingContext(
        customer=customer,
        conversation=conversation,
        active_orders=active_orders,
        active_shipments=active_shipments,
    )
