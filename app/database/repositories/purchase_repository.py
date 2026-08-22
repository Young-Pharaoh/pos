"""Data access for the ``stock_purchases`` table.

Read-side aggregate queries used by reports live in
:mod:`app.database.repositories.report_repository` instead, keeping this
repository focused on the write path used by ``InventoryService``.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.database.models import StockPurchase


class PurchaseRepository:
    def __init__(self, session: Session):
        self._session = session

    def add(self, purchase: StockPurchase) -> StockPurchase:
        self._session.add(purchase)
        self._session.flush()
        return purchase
