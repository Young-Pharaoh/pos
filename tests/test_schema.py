"""Smoke tests for the database wiring itself: constraints, cascades,
foreign-key enforcement, and transaction rollback -- independent of any
service layer built on top.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.database.database import bootstrap_database
from app.database.models import Item, Sale, SaleItem, StockPurchase


def _make_item(**overrides):
    defaults = dict(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        stock=10,
    )
    defaults.update(overrides)
    return Item(**defaults)


def test_create_all_and_default_settings(tmp_path):
    from app.database.models import Setting

    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session:
        keys = {row.key for row in session.query(Setting).all()}
    assert "low_stock_threshold" in keys
    assert "default_sell_price" in keys


def test_foreign_keys_are_enforced(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with pytest.raises(IntegrityError):
        with session_factory() as session, session.begin():
            session.add(
                StockPurchase(
                    item_id=999,
                    quantity=1,
                    unit_price=Decimal("1"),
                    total_price=Decimal("1"),
                    purchase_date=datetime.now(),
                )
            )


def test_check_constraint_rejects_negative_stock(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with pytest.raises(IntegrityError):
        with session_factory() as session, session.begin():
            session.add(_make_item(stock=-1))


def test_money_columns_round_trip_as_decimal(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session, session.begin():
        item = _make_item(purchase_price=Decimal("0.7333"))
        session.add(item)
        session.flush()
        item_id = item.id

    with session_factory() as session:
        fetched = session.get(Item, item_id)
        assert fetched.purchase_price == Decimal("0.7333")
        assert isinstance(fetched.purchase_price, Decimal)


def test_failed_transaction_rolls_back_completely(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session, session.begin():
        item = _make_item()
        session.add(item)
        session.flush()
        item_id = item.id

    with pytest.raises(IntegrityError):
        with session_factory() as session, session.begin():
            session.add(
                StockPurchase(
                    item_id=item_id,
                    quantity=5,
                    unit_price=Decimal("1"),
                    total_price=Decimal("5"),
                    purchase_date=datetime.now(),
                )
            )
            # Second insert violates the quantity>0 check, so the whole
            # transaction -- including the valid insert above -- must roll
            # back; there should be zero stock_purchases rows afterwards.
            session.add(
                StockPurchase(
                    item_id=item_id,
                    quantity=-1,
                    unit_price=Decimal("1"),
                    total_price=Decimal("-1"),
                    purchase_date=datetime.now(),
                )
            )

    with session_factory() as session:
        assert session.query(StockPurchase).count() == 0


def test_sale_item_duplicate_item_in_same_sale_is_rejected(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session, session.begin():
        item = _make_item()
        session.add(item)
        session.flush()
        item_id = item.id

    with pytest.raises(IntegrityError):
        with session_factory() as session, session.begin():
            sale = Sale(sale_date=datetime.now(), total=Decimal("2"))
            session.add(sale)
            session.flush()
            session.add(
                SaleItem(
                    sale_id=sale.id,
                    item_id=item_id,
                    quantity=1,
                    unit_sell_price=Decimal("1"),
                    unit_cost=Decimal("0.7"),
                    total_sell_price=Decimal("1"),
                    total_cost=Decimal("0.7"),
                )
            )
            session.add(
                SaleItem(
                    sale_id=sale.id,
                    item_id=item_id,
                    quantity=1,
                    unit_sell_price=Decimal("1"),
                    unit_cost=Decimal("0.7"),
                    total_sell_price=Decimal("1"),
                    total_cost=Decimal("0.7"),
                )
            )


def test_deleting_sale_cascades_to_sale_items(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session, session.begin():
        item = _make_item()
        session.add(item)
        session.flush()
        sale = Sale(sale_date=datetime.now(), total=Decimal("1"))
        session.add(sale)
        session.flush()
        session.add(
            SaleItem(
                sale_id=sale.id,
                item_id=item.id,
                quantity=1,
                unit_sell_price=Decimal("1"),
                unit_cost=Decimal("0.7"),
                total_sell_price=Decimal("1"),
                total_cost=Decimal("0.7"),
            )
        )
        sale_id = sale.id

    with session_factory() as session, session.begin():
        sale = session.get(Sale, sale_id)
        session.delete(sale)

    with session_factory() as session:
        assert session.query(SaleItem).count() == 0


def test_restrict_prevents_deleting_item_with_purchase_history(tmp_path):
    session_factory = bootstrap_database(tmp_path / "store.db")
    with session_factory() as session, session.begin():
        item = _make_item()
        session.add(item)
        session.flush()
        session.add(
            StockPurchase(
                item_id=item.id,
                quantity=5,
                unit_price=Decimal("1"),
                total_price=Decimal("5"),
                purchase_date=datetime.now(),
            )
        )
        item_id = item.id

    with pytest.raises(IntegrityError):
        with session_factory() as session, session.begin():
            item = session.get(Item, item_id)
            session.delete(item)
