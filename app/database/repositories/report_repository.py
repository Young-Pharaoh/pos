"""Read-only aggregate queries backing the reporting screens.

Each method returns raw, per-item aggregates for a date range; the
business meaning of those numbers (what "profit" means, what "current
stock" means, etc.) is defined in :mod:`app.services.report_service`, not
here. Keeping this repository "dumb" about business semantics makes it
easy to verify each query in isolation.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.models import Sale, SaleItem, StockPurchase
from app.utils.dates import DateRange


class ReportRepository:
    def __init__(self, session: Session):
        self._session = session

    def purchases_by_item(self, date_range: DateRange) -> dict[int, tuple[int, Decimal]]:
        """``{item_id: (quantity_purchased, total_spent)}`` within the range."""
        stmt = (
            select(
                StockPurchase.item_id,
                func.sum(StockPurchase.quantity),
                func.sum(StockPurchase.total_price),
            )
            .where(
                StockPurchase.purchase_date >= date_range.start,
                StockPurchase.purchase_date < date_range.end_exclusive,
            )
            .group_by(StockPurchase.item_id)
        )
        return {
            item_id: (qty, total) for item_id, qty, total in self._session.execute(stmt)
        }

    def sales_by_item(
        self, date_range: DateRange
    ) -> dict[int, tuple[int, Decimal, Decimal]]:
        """``{item_id: (quantity_sold, sell_total, cost_total)}`` within the range."""
        stmt = (
            select(
                SaleItem.item_id,
                func.sum(SaleItem.quantity),
                func.sum(SaleItem.total_sell_price),
                func.sum(SaleItem.total_cost),
            )
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(
                Sale.sale_date >= date_range.start,
                Sale.sale_date < date_range.end_exclusive,
            )
            .group_by(SaleItem.item_id)
        )
        return {
            item_id: (qty, sell_total, cost_total)
            for item_id, qty, sell_total, cost_total in self._session.execute(stmt)
        }

    def totals_for_range(self, date_range: DateRange) -> tuple[Decimal, Decimal]:
        """``(sell_total, cost_total)`` summed across every product -- for the dashboard."""
        stmt = (
            select(
                func.coalesce(func.sum(SaleItem.total_sell_price), 0),
                func.coalesce(func.sum(SaleItem.total_cost), 0),
            )
            .join(Sale, Sale.id == SaleItem.sale_id)
            .where(
                Sale.sale_date >= date_range.start,
                Sale.sale_date < date_range.end_exclusive,
            )
        )
        sell_total, cost_total = self._session.execute(stmt).one()
        return sell_total, cost_total
