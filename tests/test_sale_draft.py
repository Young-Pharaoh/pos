"""Tests for the pure, database-free SaleDraft (spec sections 11-12)."""

from decimal import Decimal

import pytest

from app.errors import InsufficientStockError, ValidationError
from app.services.sale_draft import ItemSnapshot, SaleDraft


def make_item(id=1, stock=10, sell_price="1.00", cost="0.70"):
    return ItemSnapshot(
        id=id,
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        sell_price=Decimal(sell_price),
        cost=Decimal(cost),
        available_stock=stock,
    )


def test_add_single_line():
    draft = SaleDraft()
    item = make_item(stock=10)
    draft.add(item, 2)
    assert len(draft) == 1
    assert draft.lines[0].quantity == 2
    assert draft.total == Decimal("2.0000")


def test_adding_same_item_twice_merges_quantities():
    draft = SaleDraft()
    item = make_item(stock=10)
    draft.add(item, 2)
    draft.add(item, 3)
    assert len(draft) == 1
    assert draft.lines[0].quantity == 5


def test_merge_does_not_create_duplicate_rows():
    draft = SaleDraft()
    item = make_item(stock=10)
    draft.add(item, 1)
    draft.add(item, 1)
    draft.add(item, 1)
    assert len(draft.lines) == 1
    assert draft.lines[0].quantity == 3


def test_add_multiple_different_products():
    draft = SaleDraft()
    shampoo = make_item(id=15, stock=10, sell_price="1.00")
    soap = make_item(id=22, stock=10, sell_price="1.00")
    draft.add(shampoo, 2)
    draft.add(soap, 3)
    assert draft.total == Decimal("5.0000")


def test_add_rejects_quantity_exceeding_stock():
    draft = SaleDraft()
    item = make_item(stock=5)
    with pytest.raises(InsufficientStockError):
        draft.add(item, 6)
    assert draft.is_empty


def test_merge_rejects_when_combined_quantity_exceeds_stock():
    draft = SaleDraft()
    item = make_item(stock=5)
    draft.add(item, 3)
    with pytest.raises(InsufficientStockError):
        draft.add(item, 3)
    # Original line must be untouched after the rejected merge.
    assert draft.lines[0].quantity == 3


def test_add_rejects_non_positive_quantity():
    draft = SaleDraft()
    item = make_item(stock=5)
    with pytest.raises(ValidationError):
        draft.add(item, 0)
    with pytest.raises(ValidationError):
        draft.add(item, -1)


def test_set_quantity_updates_existing_line():
    draft = SaleDraft()
    item = make_item(stock=10)
    draft.add(item, 2)
    draft.set_quantity(item.id, 7)
    assert draft.lines[0].quantity == 7


def test_set_quantity_revalidates_stock():
    draft = SaleDraft()
    item = make_item(stock=5)
    draft.add(item, 2)
    with pytest.raises(InsufficientStockError):
        draft.set_quantity(item.id, 6)


def test_set_quantity_unknown_item_raises_key_error():
    draft = SaleDraft()
    with pytest.raises(KeyError):
        draft.set_quantity(999, 1)


def test_remove_line():
    draft = SaleDraft()
    item = make_item()
    draft.add(item, 1)
    draft.remove(item.id)
    assert draft.is_empty


def test_remove_unknown_item_is_a_no_op():
    draft = SaleDraft()
    draft.remove(999)
    assert draft.is_empty


def test_total_reflects_unit_cost_and_sell_price_snapshot():
    draft = SaleDraft()
    item = make_item(stock=20, sell_price="1.00", cost="0.7333")
    draft.add(item, 10)
    line = draft.lines[0]
    assert line.total_sell_price == Decimal("10.0000")
    assert line.total_cost == Decimal("7.3330")


def test_empty_draft_total_is_zero():
    draft = SaleDraft()
    assert draft.total == Decimal("0.0000")


def test_line_order_preserved_by_first_insertion():
    draft = SaleDraft()
    shampoo = make_item(id=15)
    soap = make_item(id=22)
    draft.add(soap, 1)
    draft.add(shampoo, 1)
    draft.add(soap, 1)  # merge; must not move to the end
    ids = [line.item.id for line in draft.lines]
    assert ids == [22, 15]
