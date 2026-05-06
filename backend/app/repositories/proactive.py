from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db.models import Order, Policy, Shipment, ShipmentEvent


@dataclass
class ProactiveContext:
    shipment: Shipment
    latest_event: ShipmentEvent | None
    policies: list[Policy]


def get_proactive_context(db: Session, shipment_id: str) -> ProactiveContext | None:
    shipment = db.scalar(
        select(Shipment)
        .options(
            joinedload(Shipment.order).joinedload(Order.customer),
            joinedload(Shipment.order).joinedload(Order.seller),
        )
        .where(Shipment.id == shipment_id)
    )
    if shipment is None:
        return None

    latest_event = db.scalar(
        select(ShipmentEvent)
        .where(ShipmentEvent.shipment_id == shipment_id)
        .order_by(ShipmentEvent.event_time.desc(), ShipmentEvent.created_at.desc(), ShipmentEvent.id.desc())
    )

    policies = list(
        db.scalars(
            select(Policy)
            .where(Policy.category.in_(["shipping", "compensation"]), Policy.status == "active")
            .order_by(Policy.category.asc(), Policy.title.asc())
        )
    )

    return ProactiveContext(shipment=shipment, latest_event=latest_event, policies=policies)
