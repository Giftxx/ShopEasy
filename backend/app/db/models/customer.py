from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, class_mapper

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.db.models.conversation import Conversation
    from app.db.models.order import Order


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    hashed_password: Mapped[str | None] = mapped_column(String(255))

    customer_profile: Mapped["Customer | None"] = relationship(back_populates="user", uselist=False)

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class Customer(TimestampMixin, Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    tier: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(20), default="th", nullable=False)

    user: Mapped["User | None"] = relationship(back_populates="customer_profile")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}


class Seller(TimestampMixin, Base):
    __tablename__ = "sellers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    sla_level: Mapped[str | None] = mapped_column(String(50))
    rating: Mapped[float | None] = mapped_column(Numeric(3, 2))
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)

    orders: Mapped[list["Order"]] = relationship(back_populates="seller")

    def to_dict(self, exclude: list[str] | None = None) -> dict:
        exclude = exclude or []
        mapper = class_mapper(self.__class__)
        columns = [c.key for c in mapper.columns if c.key not in exclude]
        return {c: getattr(self, c) for c in columns}
