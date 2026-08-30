"""SQLAlchemy ORM models for the four core tables plus a settings table.

Money columns use :class:`app.database.types.Money` and are handled as
``Decimal`` everywhere above the database layer. Foreign keys to ``items``
use ``ON DELETE RESTRICT`` so the database itself refuses to orphan
historical purchase/sale records if an item row is ever removed outside
the service layer's own (stricter) delete-if-no-history check.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.database.types import Money


class Base(DeclarativeBase):
    pass


class Item(Base):
    """Current state of a product: names, prices, and live stock level."""

    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("length(trim(name_ar)) > 0", name="ck_items_name_ar_not_blank"),
        CheckConstraint("length(trim(name_es)) > 0", name="ck_items_name_es_not_blank"),
        CheckConstraint("purchase_price >= 0", name="ck_items_purchase_price_nonneg"),
        CheckConstraint("sell_price >= 0", name="ck_items_sell_price_nonneg"),
        CheckConstraint("stock >= 0", name="ck_items_stock_nonneg"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_ar: Mapped[str] = mapped_column(nullable=False)
    name_es: Mapped[str] = mapped_column(nullable=False)
    purchase_price: Mapped[Decimal] = mapped_column(
        Money, nullable=False, default=Decimal("0")
    )
    sell_price: Mapped[Decimal] = mapped_column(Money, nullable=False)
    stock: Mapped[int] = mapped_column(nullable=False, default=0)
    image_path: Mapped[str | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, default=datetime.now, onupdate=datetime.now
    )

    stock_purchases: Mapped[list["StockPurchase"]] = relationship(
        back_populates="item"
    )
    sale_items: Mapped[list["SaleItem"]] = relationship(back_populates="item")


class StockPurchase(Base):
    """Historical record of every stock addition.

    Rows are normally append-only. A direct purchase-price correction on the
    product may update rows whose ``unit_price`` matched the old average.
    """

    __tablename__ = "stock_purchases"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stock_purchases_qty_positive"),
        CheckConstraint("unit_price >= 0", name="ck_stock_purchases_unit_price_nonneg"),
        CheckConstraint(
            "total_price >= 0", name="ck_stock_purchases_total_price_nonneg"
        ),
        Index("ix_stock_purchases_item_id", "item_id"),
        Index("ix_stock_purchases_purchase_date", "purchase_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Money, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Money, nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)

    item: Mapped["Item"] = relationship(back_populates="stock_purchases")


class Sale(Base):
    """One completed customer transaction, possibly with several products."""

    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("total >= 0", name="ck_sales_total_nonneg"),
        Index("ix_sales_sale_date", "sale_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_date: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    total: Mapped[Decimal] = mapped_column(Money, nullable=False)

    sale_items: Mapped[list["SaleItem"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan"
    )


class SaleItem(Base):
    """One product line within a sale, snapshotting cost at sale time.

    ``unit_cost`` / ``total_cost`` are frozen at the moment of sale and must
    never be recalculated from the item's later ``purchase_price``. The
    unique constraint on ``(sale_id, item_id)`` enforces the "merge
    duplicate entries" rule at the schema level, not just in the UI.
    """

    __tablename__ = "sale_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_sale_items_qty_positive"),
        CheckConstraint(
            "unit_sell_price >= 0", name="ck_sale_items_unit_sell_price_nonneg"
        ),
        CheckConstraint("unit_cost >= 0", name="ck_sale_items_unit_cost_nonneg"),
        CheckConstraint(
            "total_sell_price >= 0", name="ck_sale_items_total_sell_price_nonneg"
        ),
        CheckConstraint("total_cost >= 0", name="ck_sale_items_total_cost_nonneg"),
        UniqueConstraint("sale_id", "item_id", name="uq_sale_items_sale_item"),
        Index("ix_sale_items_item_id", "item_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="RESTRICT"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_sell_price: Mapped[Decimal] = mapped_column(Money, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Money, nullable=False)
    total_sell_price: Mapped[Decimal] = mapped_column(Money, nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Money, nullable=False)

    sale: Mapped["Sale"] = relationship(back_populates="sale_items")
    item: Mapped["Item"] = relationship(back_populates="sale_items")


class Setting(Base):
    """Simple key/value store for the low-stock threshold, currency, etc."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str] = mapped_column(nullable=False)
