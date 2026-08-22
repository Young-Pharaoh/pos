"""Data access for the ``sales`` / ``sale_items`` write path.

The conditional stock decrement (``UPDATE ... WHERE stock >= :qty``) plus
checking that exactly one row was affected is what makes "sale recorded but
stock unchanged" and "stock decreased but sale missing" structurally
impossible: either both happen inside the same transaction, or an
exception aborts the whole transaction before either is committed.
"""

from __future__ import annotations

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.database.models import Item, Sale, SaleItem


class SaleRepository:
    def __init__(self, session: Session):
        self._session = session

    def add_sale(self, sale: Sale) -> Sale:
        self._session.add(sale)
        self._session.flush()
        return sale

    def add_sale_item(self, sale_item: SaleItem) -> SaleItem:
        self._session.add(sale_item)
        self._session.flush()
        return sale_item

    def decrement_stock(self, item_id: int, quantity: int) -> bool:
        """Atomically decrement stock; returns False if insufficient stock.

        The ``stock >= :quantity`` guard in the WHERE clause means this is
        safe even under concurrent writers: if the row doesn't satisfy the
        condition, zero rows are affected and no partial decrement happens.
        """
        stmt = (
            update(Item)
            .where(Item.id == item_id, Item.stock >= quantity)
            .values(stock=Item.stock - quantity)
        )
        result = self._session.execute(stmt)
        return result.rowcount == 1
