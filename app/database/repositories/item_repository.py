"""Data access for the ``items`` table.

Repositories are internal to the service layer: they take a live
``Session`` (owned and committed by the calling service) and return ORM
objects. They contain no business rules and no transaction management --
that responsibility belongs to the services in :mod:`app.services`.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Item, SaleItem, StockPurchase


class ItemRepository:
    def __init__(self, session: Session):
        self._session = session

    def get(self, item_id: int) -> Item | None:
        return self._session.get(Item, item_id)

    def list_all(self, *, include_archived: bool = True) -> list[Item]:
        stmt = select(Item).order_by(Item.id)
        if not include_archived:
            stmt = stmt.where(Item.is_active.is_(True))
        return list(self._session.scalars(stmt))

    def search(self, query: str, *, include_archived: bool = False) -> list[Item]:
        """Unified search by id substring, Arabic name, or Spanish name.

        Matching is done in Python (not SQL ``LIKE``) so Unicode
        case-folding works correctly for accented Spanish letters, which
        SQLite's default ``LIKE`` only case-folds for ASCII. The shop's
        catalog is small enough that a full scan is negligible.
        """
        items = self.list_all(include_archived=include_archived)
        q = query.strip()
        if not q:
            return items
        q_fold = q.casefold()
        return [
            item
            for item in items
            if q in str(item.id)
            or q_fold in item.name_ar.casefold()
            or q_fold in item.name_es.casefold()
        ]

    def add(self, item: Item) -> Item:
        self._session.add(item)
        self._session.flush()
        return item

    def delete(self, item: Item) -> None:
        self._session.delete(item)

    def has_purchase_history(self, item_id: int) -> bool:
        stmt = select(func.count()).select_from(StockPurchase).where(
            StockPurchase.item_id == item_id
        )
        return bool(self._session.scalar(stmt))

    def has_sale_history(self, item_id: int) -> bool:
        stmt = select(func.count()).select_from(SaleItem).where(
            SaleItem.item_id == item_id
        )
        return bool(self._session.scalar(stmt))

    def has_history(self, item_id: int) -> bool:
        return self.has_purchase_history(item_id) or self.has_sale_history(item_id)

    def list_low_stock(self, threshold: int) -> list[Item]:
        stmt = (
            select(Item)
            .where(Item.is_active.is_(True), Item.stock < threshold)
            .order_by(Item.stock)
        )
        return list(self._session.scalars(stmt))
