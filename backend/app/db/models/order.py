from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import (
    Mapped,
    RelationshipProperty,
    class_mapper,
    mapped_column,
    object_mapper,
    relationship,
)

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.customer import Customer, Seller


def _serialize_related(entity: object, exclude: list[str]) -> dict:
    to_dict = getattr(entity, "to_dict", None)
    if callable(to_dict):
        try:
            return to_dict(exclude=exclude, include_relationships=False)
        except TypeError:
            return to_dict(exclude=exclude)

    mapper = class_mapper(entity.__class__)
    columns = [column.key for column in mapper.columns if column.key not in exclude]
    return {column: getattr(entity, column) for column in columns}


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(36), ForeignKey("customers.id"), nullable=False)
    seller_id: Mapped[str] = mapped_column(String(36), ForeignKey("sellers.id"), nullable=False)
    order_status: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_status: Mapped[str | None] = mapped_column(String(50))
    total_amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str] = mapped_column(String(10), default="THB", nullable=False)
    promised_delivery_date: Mapped[date | None] = mapped_column(Date)
    shopify_order_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    shopify_order_id: Mapped[str | None] = mapped_column(String(100), unique=True)

    customer: Mapped["Customer"] = relationship(back_populates="orders")
    seller: Mapped["Seller"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="order")

    def to_dict(self, exclude: list[str] | None = None, include_relationships: bool = False) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)

        # Get columns
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        data = {c: getattr(self, c) for c in columns}

        if include_relationships:
            for prop in object_mapper(self).iterate_properties:
                if isinstance(prop, RelationshipProperty) and prop.key not in exclude:
                    related_obj = getattr(self, prop.key)
                    if related_obj is None:
                        data[prop.key] = None
                    elif isinstance(related_obj, list):
                        data[prop.key] = [
                            _serialize_related(item, exclude) for item in related_obj
                        ]
                    else:
                        data[prop.key] = _serialize_related(related_obj, exclude)
        return data


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"), nullable=False)
    product_name: Mapped[str | None] = mapped_column(String(255))
    sku: Mapped[str | None] = mapped_column(String(100))
    quantity: Mapped[int | None] = mapped_column(Integer)
    unit_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    order: Mapped["Order"] = relationship(back_populates="items")
    shipment_items: Mapped[list["ShipmentItem"]] = relationship(back_populates="order_item")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class Shipment(TimestampMixin, Base):
    __tablename__ = "shipments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(50), ForeignKey("orders.id"), nullable=False)
    carrier: Mapped[str | None] = mapped_column(String(100))
    tracking_no: Mapped[str | None] = mapped_column(String(100), unique=True)
    shipment_status: Mapped[str | None] = mapped_column(String(50))
    eta: Mapped[date | None] = mapped_column(Date)
    last_update: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    delay_risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    shopify_fulfillment_id: Mapped[str | None] = mapped_column(String(100), unique=True)
    shopify_fulfillment_id: Mapped[str | None] = mapped_column(String(100), unique=True)

    order: Mapped["Order"] = relationship(back_populates="shipments")
    shipment_items: Mapped[list["ShipmentItem"]] = relationship(back_populates="shipment")
    events: Mapped[list["ShipmentEvent"]] = relationship(back_populates="shipment")

    def to_dict(self, exclude: list[str] | None = None, include_relationships: bool = False) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)

        # Get columns
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        data = {c: getattr(self, c) for c in columns}

        if include_relationships:
            for prop in object_mapper(self).iterate_properties:
                if isinstance(prop, RelationshipProperty) and prop.key not in exclude:
                    related_obj = getattr(self, prop.key)
                    if related_obj is None:
                        data[prop.key] = None
                    elif isinstance(related_obj, list):
                        data[prop.key] = [
                            _serialize_related(item, exclude) for item in related_obj
                        ]
                    else:
                        data[prop.key] = _serialize_related(related_obj, exclude)
        return data


class ShipmentItem(Base):
    __tablename__ = "shipment_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("shipments.id"), nullable=False)
    order_item_id: Mapped[str] = mapped_column(String(36), ForeignKey("order_items.id"), nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    shipment: Mapped["Shipment"] = relationship(back_populates="shipment_items")
    order_item: Mapped["OrderItem"] = relationship(back_populates="shipment_items")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class ShipmentEvent(Base):
    __tablename__ = "shipment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    shipment_id: Mapped[str] = mapped_column(String(36), ForeignKey("shipments.id"), nullable=False)
    event_type: Mapped[str | None] = mapped_column(String(100))
    event_message: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    event_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    shipment: Mapped["Shipment"] = relationship(back_populates="events")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}
