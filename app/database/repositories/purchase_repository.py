"""Data access for the ``stock_purchases`` table.

Read-side aggregate queries used by reports live in
:mod:`app.database.repositories.report_repository` instead, keeping this
repository focused on the write path used by ``InventoryService``.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import StockPurchase


class PurchaseRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, purchase: StockPurchase) -> StockPurchase:
        self._session.add(purchase)
        self._session.flush()
        return purchase

    def list_by_item_id(self, item_id: int) -> list[StockPurchase]:
        stmt = (
            select(StockPurchase)
            .where(StockPurchase.item_id == item_id)
            .order_by(StockPurchase.id)
        )
        return list(self._session.scalars(stmt))
