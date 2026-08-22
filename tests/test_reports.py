from datetime import datetime
from decimal import Decimal

from app.database.models import Item, Sale, SaleItem, StockPurchase
from app.utils.dates import custom, day, month


def seed_item(session_factory, **overrides) -> int:
    defaults = dict(
        name_ar="\u0645\u0646\u062a\u062c",
        name_es="Producto",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        stock=0,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    defaults.update(overrides)
    with session_factory() as session, session.begin():
        item = Item(**defaults)
        session.add(item)
        session.flush()
        item_id = item.id
    return item_id


def seed_purchase(session_factory, item_id, quantity, unit_price, when):
    with session_factory() as session, session.begin():
        session.add(
            StockPurchase(
                item_id=item_id,
                quantity=quantity,
                unit_price=Decimal(unit_price),
                total_price=Decimal(unit_price) * quantity,
                purchase_date=when,
            )
        )


def seed_sale(session_factory, item_id, quantity, unit_sell_price, unit_cost, when):
    with session_factory() as session, session.begin():
        sale = Sale(sale_date=when, total=Decimal(unit_sell_price) * quantity)
        session.add(sale)
        session.flush()
        session.add(
            SaleItem(
                sale_id=sale.id,
                item_id=item_id,
                quantity=quantity,
                unit_sell_price=Decimal(unit_sell_price),
                unit_cost=Decimal(unit_cost),
                total_sell_price=Decimal(unit_sell_price) * quantity,
                total_cost=Decimal(unit_cost) * quantity,
            )
        )
        return sale.id


def test_spec_worked_example_shampoo(session_factory, report_service):
    # Section 18 example: 100 purchased @ 0.70, 40 sold @ 1.00 (cost 0.70),
    # current stock 60, purchase total 70.00, sell total 40.00, profit 12.00.
    item_id = seed_item(session_factory, purchase_price=Decimal("0.70"), stock=60)
    when = datetime(2026, 3, 15)
    seed_purchase(session_factory, item_id, 100, "0.70", when)
    seed_sale(session_factory, item_id, 40, "1.00", "0.70", when)

    report = report_service.product_report(month(2026, 3))
    row = next(r for r in report.rows if r.item_id == item_id)

    assert row.qty_purchased == 100
    assert row.qty_sold == 40
    assert row.current_stock == 60
    assert row.purchase_unit_price == Decimal("0.7000")
    assert row.purchase_total == Decimal("70.0000")
    assert row.sell_unit_price == Decimal("1.0000")
    assert row.sell_total == Decimal("40.0000")
    assert row.profit == Decimal("12.0000")


def test_current_stock_is_live_not_derived_from_period(session_factory, report_service):
    """Purchase in January, sell in February; a February report's current
    stock must reflect both months' activity, not just February's."""
    item_id = seed_item(session_factory, stock=60)
    seed_purchase(session_factory, item_id, 100, "0.70", datetime(2026, 1, 10))
    seed_sale(session_factory, item_id, 40, "1.00", "0.70", datetime(2026, 2, 5))

    february_report = report_service.product_report(month(2026, 2))
    row = next(r for r in february_report.rows if r.item_id == item_id)

    assert row.qty_purchased == 0  # nothing purchased in February
    assert row.qty_sold == 40
    assert row.current_stock == 60  # NOT "period purchases - period sales" (which would be -40)


def test_purchase_total_is_inventory_spend_not_cogs(session_factory, report_service):
    item_id = seed_item(session_factory, stock=200)
    when = datetime(2026, 4, 1)
    seed_purchase(session_factory, item_id, 100, "0.70", when)
    seed_purchase(session_factory, item_id, 50, "0.80", when)
    # No sales at all this period.

    report = report_service.product_report(month(2026, 4))
    row = next(r for r in report.rows if r.item_id == item_id)
    assert row.purchase_total == Decimal("110.0000")  # 100*0.70 + 50*0.80
    assert row.sell_total == Decimal("0.0000")
    assert row.profit == Decimal("0.0000")


def test_profit_is_realized_not_sales_minus_all_purchases(session_factory, report_service):
    """Buying a lot of unsold inventory must not look like a loss."""
    item_id = seed_item(session_factory, purchase_price=Decimal("0.70"), stock=200)
    when = datetime(2026, 5, 1)
    seed_purchase(session_factory, item_id, 200, "0.70", when)  # spent $140
    seed_sale(session_factory, item_id, 10, "1.00", "0.70", when)  # sold only 10

    report = report_service.product_report(month(2026, 5))
    row = next(r for r in report.rows if r.item_id == item_id)

    # profit = sell_total - cogs = 10.00 - 7.00 = 3.00, NOT 10.00 - 140.00.
    assert row.profit == Decimal("3.0000")


def test_inventory_value_uses_current_avg_cost_times_current_stock(session_factory, report_service):
    item_id = seed_item(session_factory, purchase_price=Decimal("0.70"), stock=60)
    report = report_service.product_report(month(2026, 6))
    row = next(r for r in report.rows if r.item_id == item_id)
    assert row.inventory_value == Decimal("42.0000")  # 60 * 0.70


def test_zero_activity_item_reports_zeros_not_none_or_errors(session_factory, report_service):
    item_id = seed_item(session_factory, stock=0)
    report = report_service.product_report(month(2026, 7))
    row = next(r for r in report.rows if r.item_id == item_id)

    assert row.qty_purchased == 0
    assert row.qty_sold == 0
    assert row.purchase_total == Decimal("0.0000")
    assert row.sell_total == Decimal("0.0000")
    assert row.profit == Decimal("0.0000")
    assert row.purchase_unit_price is None  # nothing purchased -> undefined, not zero


def test_report_totals_sum_all_rows(session_factory, report_service):
    a = seed_item(session_factory, name_es="A", stock=10)
    b = seed_item(session_factory, name_es="B", stock=20)
    when = datetime(2026, 8, 1)
    seed_purchase(session_factory, a, 10, "0.70", when)
    seed_purchase(session_factory, b, 20, "0.50", when)
    seed_sale(session_factory, a, 5, "1.00", "0.70", when)
    seed_sale(session_factory, b, 5, "1.00", "0.50", when)

    report = report_service.product_report(month(2026, 8))
    assert report.totals.purchase_total == Decimal("17.0000")  # 7 + 10
    assert report.totals.sell_total == Decimal("10.0000")
    assert report.totals.profit == Decimal("4.0000")  # (5-3.5)+(5-2.5)


def test_day_boundary_is_inclusive_start_exclusive_end(session_factory, report_service):
    item_id = seed_item(session_factory, stock=100)
    last_second_of_day = datetime(2026, 3, 15, 23, 59, 59)
    first_second_of_next_day = datetime(2026, 3, 16, 0, 0, 0)
    seed_sale(session_factory, item_id, 3, "1.00", "0.70", last_second_of_day)
    seed_sale(session_factory, item_id, 7, "1.00", "0.70", first_second_of_next_day)

    day_report = report_service.product_report(day(datetime(2026, 3, 15).date()))
    row = next(r for r in day_report.rows if r.item_id == item_id)
    assert row.qty_sold == 3  # only the 23:59:59 sale, not the midnight-next-day one


def test_custom_range_is_inclusive_of_both_end_dates(session_factory, report_service):
    item_id = seed_item(session_factory, stock=100)
    seed_sale(session_factory, item_id, 1, "1.00", "0.70", datetime(2026, 3, 10, 0, 0, 0))
    seed_sale(session_factory, item_id, 2, "1.00", "0.70", datetime(2026, 3, 12, 23, 59, 59))
    seed_sale(session_factory, item_id, 4, "1.00", "0.70", datetime(2026, 3, 13, 0, 0, 0))

    from datetime import date

    report = report_service.product_report(custom(date(2026, 3, 10), date(2026, 3, 12)))
    row = next(r for r in report.rows if r.item_id == item_id)
    assert row.qty_sold == 3  # the 10th and 12th sales, not the 13th


def test_best_sellers_ranked_by_quantity(session_factory, report_service):
    shampoo = seed_item(session_factory, name_es="Shampoo", stock=50)
    toothpaste = seed_item(session_factory, name_es="Toothpaste", stock=50)
    soap = seed_item(session_factory, name_es="Soap", stock=50)
    when = datetime(2026, 9, 1)
    seed_sale(session_factory, shampoo, 82, "1.00", "0.70", when)
    seed_sale(session_factory, toothpaste, 48, "1.00", "0.70", when)
    seed_sale(session_factory, soap, 31, "1.00", "0.70", when)

    rows = report_service.best_sellers(month(2026, 9))
    assert [r.name_es for r in rows[:3]] == ["Shampoo", "Toothpaste", "Soap"]
    assert rows[0].qty_sold == 82


def test_most_profitable_ranked_by_realized_profit(session_factory, report_service):
    a = seed_item(session_factory, name_es="A", stock=50)
    b = seed_item(session_factory, name_es="B", stock=50)
    when = datetime(2026, 9, 1)
    seed_sale(session_factory, a, 10, "1.00", "0.20", when)  # profit 8.00
    seed_sale(session_factory, b, 10, "1.00", "0.70", when)  # profit 3.00

    rows = report_service.most_profitable(month(2026, 9))
    assert rows[0].name_es == "A"
    assert rows[0].profit == Decimal("8.0000")


def test_slow_sellers_matches_spec_worked_example(session_factory, report_service):
    cookies = seed_item(session_factory, name_es="Cookies", stock=47)
    candy = seed_item(session_factory, name_es="Candy", stock=52)
    soap = seed_item(session_factory, name_es="Soap", stock=81)
    when = datetime(2026, 10, 1)
    seed_sale(session_factory, cookies, 3, "1.00", "0.70", when)
    seed_sale(session_factory, candy, 4, "1.00", "0.70", when)
    seed_sale(session_factory, soap, 12, "1.00", "0.70", when)

    rows = report_service.slow_sellers(month(2026, 10))
    assert [r.name_es for r in rows[:3]] == ["Cookies", "Candy", "Soap"]


def test_slow_sellers_excludes_sold_out_items(session_factory, report_service):
    sold_out = seed_item(session_factory, name_es="SoldOut", stock=0)
    in_stock = seed_item(session_factory, name_es="InStock", stock=10)
    when = datetime(2026, 10, 1)
    seed_sale(session_factory, in_stock, 1, "1.00", "0.70", when)

    rows = report_service.slow_sellers(month(2026, 10))
    assert sold_out not in [r.item_id for r in rows]


def test_low_stock_uses_configurable_threshold(session_factory, report_service):
    seed_item(session_factory, name_es="Low", stock=3)
    seed_item(session_factory, name_es="High", stock=30)

    rows = report_service.low_stock(threshold=5)
    assert [r.name_es for r in rows] == ["Low"]


def test_dashboard_summary_aggregates_today_month_and_low_stock(session_factory, report_service):
    item_id = seed_item(session_factory, purchase_price=Decimal("0.70"), stock=3)
    now = datetime.now()
    seed_sale(session_factory, item_id, 2, "1.00", "0.70", now)

    summary = report_service.dashboard_summary(low_stock_threshold=5)

    assert summary.today_sales_total == Decimal("2.0000")
    assert summary.month_sales_total == Decimal("2.0000")
    assert summary.month_profit == Decimal("0.6000")  # (2*1.00) - (2*0.70)
    assert any(row.item_id == item_id for row in summary.low_stock)
    assert any(row.item_id == item_id for row in summary.best_sellers)
