"""Reporting calculations (spec sections 15-21).

The definitions here are deliberately literal translations of the spec:

* ``current_stock`` always comes from ``items.stock`` (live), never from
  period purchases minus period sales.
* ``profit`` is realized profit on units actually sold in the period
  (``sell_total - cogs``), never "sales minus all purchases".
* ``inventory_value`` is a separate figure from profit: money still tied
  up in unsold stock, not money the shop has made.
* ``purchase_unit_price`` is the *period* average price paid (blank when
  nothing was purchased in the period); ``current_avg_cost`` is the
  *live* weighted-average cost used for inventory valuation. These are two
  different numbers and are exposed as two different fields so the UI can
  label them distinctly instead of overloading one "Purchase Price" column.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy.orm import Session, sessionmaker

from app.database.repositories.item_repository import ItemRepository
from app.database.repositories.report_repository import ReportRepository
from app.utils.dates import DateRange, this_month, today
from app.utils.money import quantize_money


@dataclass(frozen=True)
class ProductReportRow:
    item_id: int
    name_ar: str
    name_es: str
    qty_purchased: int
    qty_sold: int
    current_stock: int
    purchase_unit_price: Decimal | None
    purchase_total: Decimal
    current_avg_cost: Decimal
    sell_unit_price: Decimal
    sell_total: Decimal
    cogs: Decimal
    profit: Decimal
    inventory_value: Decimal


@dataclass(frozen=True)
class ProductReportTotals:
    purchase_total: Decimal
    sell_total: Decimal
    profit: Decimal
    inventory_value: Decimal


@dataclass(frozen=True)
class ProductReport:
    date_range: DateRange
    rows: list[ProductReportRow] = field(default_factory=list)
    totals: ProductReportTotals = None


@dataclass(frozen=True)
class BestSellerRow:
    item_id: int
    name_ar: str
    name_es: str
    qty_sold: int


@dataclass(frozen=True)
class ProfitRow:
    item_id: int
    name_ar: str
    name_es: str
    profit: Decimal


@dataclass(frozen=True)
class SlowSellerRow:
    item_id: int
    name_ar: str
    name_es: str
    qty_sold: int
    current_stock: int
    sell_through_rate: Decimal  # qty_sold / (qty_sold + current_stock), 0..1


@dataclass(frozen=True)
class LowStockRow:
    item_id: int
    name_ar: str
    name_es: str
    stock: int


@dataclass(frozen=True)
class DashboardSummary:
    today_sales_total: Decimal
    month_sales_total: Decimal
    month_profit: Decimal
    inventory_value: Decimal
    low_stock: list[LowStockRow]
    best_sellers: list[BestSellerRow]


_ZERO = Decimal("0")


class ReportService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def product_report(self, date_range: DateRange) -> ProductReport:
        with self._session_factory() as session:
            items_repo = ItemRepository(session)
            report_repo = ReportRepository(session)

            purchases = report_repo.purchases_by_item(date_range)
            sales = report_repo.sales_by_item(date_range)
            relevant_ids = set(purchases) | set(sales)

            rows: list[ProductReportRow] = []
            for item in items_repo.list_all(include_archived=True):
                if not item.is_active and item.id not in relevant_ids:
                    continue

                qty_purchased, purchase_total = purchases.get(item.id, (0, _ZERO))
                qty_sold, sell_total, cogs = sales.get(item.id, (0, _ZERO, _ZERO))
                qty_purchased = qty_purchased or 0
                qty_sold = qty_sold or 0

                purchase_unit_price = (
                    quantize_money(purchase_total / qty_purchased)
                    if qty_purchased
                    else None
                )
                profit = quantize_money(sell_total - cogs)
                inventory_value = quantize_money(item.purchase_price * item.stock)

                rows.append(
                    ProductReportRow(
                        item_id=item.id,
                        name_ar=item.name_ar,
                        name_es=item.name_es,
                        qty_purchased=qty_purchased,
                        qty_sold=qty_sold,
                        current_stock=item.stock,
                        purchase_unit_price=purchase_unit_price,
                        purchase_total=quantize_money(purchase_total),
                        current_avg_cost=item.purchase_price,
                        sell_unit_price=item.sell_price,
                        sell_total=quantize_money(sell_total),
                        cogs=quantize_money(cogs),
                        profit=profit,
                        inventory_value=inventory_value,
                    )
                )

            totals = ProductReportTotals(
                purchase_total=quantize_money(sum((r.purchase_total for r in rows), _ZERO)),
                sell_total=quantize_money(sum((r.sell_total for r in rows), _ZERO)),
                profit=quantize_money(sum((r.profit for r in rows), _ZERO)),
                inventory_value=quantize_money(sum((r.inventory_value for r in rows), _ZERO)),
            )
            return ProductReport(date_range=date_range, rows=rows, totals=totals)

    def best_sellers(self, date_range: DateRange, limit: int = 10) -> list[BestSellerRow]:
        with self._session_factory() as session:
            items_by_id = {i.id: i for i in ItemRepository(session).list_all(include_archived=True)}
            sales = ReportRepository(session).sales_by_item(date_range)

            rows = []
            for item_id, (qty_sold, _sell_total, _cogs) in sales.items():
                item = items_by_id.get(item_id)
                if item is None or not qty_sold:
                    continue
                rows.append(
                    BestSellerRow(
                        item_id=item_id, name_ar=item.name_ar, name_es=item.name_es, qty_sold=qty_sold
                    )
                )
            rows.sort(key=lambda r: r.qty_sold, reverse=True)
            return rows[:limit]

    def most_profitable(self, date_range: DateRange, limit: int = 10) -> list[ProfitRow]:
        with self._session_factory() as session:
            items_by_id = {i.id: i for i in ItemRepository(session).list_all(include_archived=True)}
            sales = ReportRepository(session).sales_by_item(date_range)

            rows = []
            for item_id, (_qty_sold, sell_total, cogs) in sales.items():
                item = items_by_id.get(item_id)
                if item is None:
                    continue
                rows.append(
                    ProfitRow(
                        item_id=item_id,
                        name_ar=item.name_ar,
                        name_es=item.name_es,
                        profit=quantize_money(sell_total - cogs),
                    )
                )
            rows.sort(key=lambda r: r.profit, reverse=True)
            return rows[:limit]

    def slow_sellers(self, date_range: DateRange, limit: int = 10) -> list[SlowSellerRow]:
        """Sell-through rate = qty_sold / (qty_sold + current_stock).

        Restricted to items currently in stock (a sold-out item isn't
        "slow", it's gone). Ascending order: lowest sell-through first.
        """
        with self._session_factory() as session:
            active_items = ItemRepository(session).list_all(include_archived=False)
            sales = ReportRepository(session).sales_by_item(date_range)

            rows = []
            for item in active_items:
                if item.stock <= 0:
                    continue
                qty_sold, _sell_total, _cogs = sales.get(item.id, (0, _ZERO, _ZERO))
                qty_sold = qty_sold or 0
                denominator = qty_sold + item.stock
                rate = (
                    (Decimal(qty_sold) / Decimal(denominator)) if denominator else _ZERO
                )
                rows.append(
                    SlowSellerRow(
                        item_id=item.id,
                        name_ar=item.name_ar,
                        name_es=item.name_es,
                        qty_sold=qty_sold,
                        current_stock=item.stock,
                        sell_through_rate=rate,
                    )
                )
            rows.sort(key=lambda r: r.sell_through_rate)
            return rows[:limit]

    def low_stock(self, threshold: int) -> list[LowStockRow]:
        with self._session_factory() as session:
            items = ItemRepository(session).list_low_stock(threshold)
            return [
                LowStockRow(item_id=i.id, name_ar=i.name_ar, name_es=i.name_es, stock=i.stock)
                for i in items
            ]

    def dashboard_summary(
        self, low_stock_threshold: int, best_sellers_limit: int = 5
    ) -> DashboardSummary:
        today_range = today()
        month_range = this_month()

        with self._session_factory() as session:
            items_repo = ItemRepository(session)
            report_repo = ReportRepository(session)

            today_sell_total, _today_cost = report_repo.totals_for_range(today_range)
            month_sell_total, month_cost_total = report_repo.totals_for_range(month_range)
            month_profit = quantize_money(month_sell_total - month_cost_total)

            active_items = items_repo.list_all(include_archived=False)
            inventory_value = quantize_money(
                sum(
                    (quantize_money(item.purchase_price * item.stock) for item in active_items),
                    _ZERO,
                )
            )

            low_stock_items = items_repo.list_low_stock(low_stock_threshold)
            low_stock_rows = [
                LowStockRow(item_id=i.id, name_ar=i.name_ar, name_es=i.name_es, stock=i.stock)
                for i in low_stock_items
            ]

            items_by_id = {i.id: i for i in active_items}
            month_sales = report_repo.sales_by_item(month_range)
            best_rows = []
            for item_id, (qty_sold, _sell_total, _cogs) in month_sales.items():
                item = items_by_id.get(item_id)
                if item is None or not qty_sold:
                    continue
                best_rows.append(
                    BestSellerRow(
                        item_id=item_id, name_ar=item.name_ar, name_es=item.name_es, qty_sold=qty_sold
                    )
                )
            best_rows.sort(key=lambda r: r.qty_sold, reverse=True)
            best_rows = best_rows[:best_sellers_limit]

        return DashboardSummary(
            today_sales_total=quantize_money(today_sell_total),
            month_sales_total=quantize_money(month_sell_total),
            month_profit=month_profit,
            inventory_value=inventory_value,
            low_stock=low_stock_rows,
            best_sellers=best_rows,
        )
