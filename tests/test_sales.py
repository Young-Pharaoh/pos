from decimal import Decimal

import pytest

from app.errors import InsufficientStockError, ItemInactiveError, ItemNotFoundError, ValidationError
from app.services.sale_draft import SaleDraft


def make_product(inventory_service, **overrides):
    defaults = dict(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        initial_stock=10,
    )
    defaults.update(overrides)
    return inventory_service.create_item(**defaults)


def build_draft(sales_service, *pairs):
    """pairs: sequence of (query, quantity)."""
    draft = SaleDraft()
    for query, qty in pairs:
        snapshot = sales_service.resolve_item(str(query))
        draft.add(snapshot, qty)
    return draft


def test_resolve_item_by_id(inventory_service, sales_service):
    item = make_product(inventory_service)
    snapshot = sales_service.resolve_item(str(item.id))
    assert snapshot.id == item.id
    assert snapshot.available_stock == 10


def test_resolve_item_by_partial_name(inventory_service, sales_service):
    make_product(inventory_service, name_es="Champu")
    snapshot = sales_service.resolve_item("champ")
    assert snapshot.name_es == "Champu"


def test_resolve_item_not_found_raises(sales_service):
    with pytest.raises(ItemNotFoundError):
        sales_service.resolve_item("nonexistent-product-xyz")


def test_resolve_item_excludes_archived(inventory_service, sales_service):
    item = make_product(inventory_service)
    inventory_service.archive_item(item.id)
    with pytest.raises(ItemNotFoundError):
        sales_service.resolve_item(str(item.id))


def test_complete_sale_creates_sale_and_sale_items(inventory_service, sales_service):
    item = make_product(inventory_service, initial_stock=10)
    draft = build_draft(sales_service, (item.id, 3))

    receipt = sales_service.complete_sale(draft)

    assert receipt.id is not None
    assert receipt.total == Decimal("3.0000")
    assert len(receipt.lines) == 1
    assert receipt.lines[0].quantity == 3


def test_complete_sale_with_multiple_products(inventory_service, sales_service):
    shampoo = make_product(inventory_service, name_es="Shampoo", initial_stock=10)
    soap = make_product(inventory_service, name_es="Soap", initial_stock=10)
    draft = build_draft(sales_service, (shampoo.id, 2), (soap.id, 3))

    receipt = sales_service.complete_sale(draft)

    assert receipt.total == Decimal("5.0000")
    assert {line.item_id for line in receipt.lines} == {shampoo.id, soap.id}


def test_complete_sale_decreases_inventory(inventory_service, sales_service):
    item = make_product(inventory_service, initial_stock=10)
    draft = build_draft(sales_service, (item.id, 4))

    sales_service.complete_sale(draft)

    updated = inventory_service.get_item(item.id)
    assert updated.stock == 6


def test_complete_sale_stores_cost_at_time_of_sale(inventory_service, sales_service):
    item = make_product(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    inventory_service.add_stock(item.id, 50, Decimal("0.80"))  # avg becomes 0.7333

    draft = build_draft(sales_service, (item.id, 10))
    receipt = sales_service.complete_sale(draft)

    line = receipt.lines[0]
    assert line.unit_cost == Decimal("0.7333")
    assert line.unit_sell_price == Decimal("1.0000")
    assert line.total_sell_price == Decimal("10.0000")
    assert line.total_cost == Decimal("7.3330")


def test_historical_sale_cost_is_not_changed_by_later_purchase_price_changes(
    inventory_service, sales_service, session_factory
):
    from app.database.models import SaleItem

    item = make_product(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    draft = build_draft(sales_service, (item.id, 10))
    receipt = sales_service.complete_sale(draft)
    original_cost = receipt.lines[0].unit_cost
    assert original_cost == Decimal("0.7000")

    # Purchase price changes drastically after the sale.
    inventory_service.add_stock(item.id, 50, Decimal("5.00"))

    with session_factory() as session:
        stored = session.query(SaleItem).filter_by(sale_id=receipt.id).one()
    assert stored.unit_cost == Decimal("0.7000")
    assert stored.unit_cost == original_cost


def test_complete_sale_merges_duplicate_products_via_draft(inventory_service, sales_service):
    item = make_product(inventory_service, initial_stock=10)
    draft = SaleDraft()
    snapshot = sales_service.resolve_item(str(item.id))
    draft.add(snapshot, 2)
    draft.add(snapshot, 3)

    receipt = sales_service.complete_sale(draft)

    assert len(receipt.lines) == 1
    assert receipt.lines[0].quantity == 5


def test_cannot_sell_more_than_available_stock(inventory_service, sales_service):
    item = make_product(inventory_service, initial_stock=5)
    with pytest.raises(InsufficientStockError):
        build_draft(sales_service, (item.id, 6))


def test_complete_sale_rejects_stock_that_shrank_after_draft_was_built(
    inventory_service, sales_service
):
    """Stock is re-validated at completion time, not just when added to the draft."""
    item = make_product(inventory_service, initial_stock=10)
    draft = build_draft(sales_service, (item.id, 8))

    # Someone else (or another line) sells stock out from under the draft.
    other_draft = build_draft(sales_service, (item.id, 5))
    sales_service.complete_sale(other_draft)  # stock now 5

    with pytest.raises(InsufficientStockError):
        sales_service.complete_sale(draft)


def test_failed_sale_rolls_back_entirely(inventory_service, sales_service, session_factory):
    """A multi-line sale where the second line oversells must leave no trace:
    no sales row, no sale_items rows, and unchanged stock -- the real
    rollback requirement, not just an exception being raised."""
    from app.database.models import Sale, SaleItem

    shampoo = make_product(inventory_service, name_es="Shampoo", initial_stock=10)
    soap = make_product(inventory_service, name_es="Soap", initial_stock=2)

    draft = SaleDraft()
    draft.add(sales_service.resolve_item(str(shampoo.id)), 5)
    # Bypass SaleDraft's own stock check to simulate stock shrinking between
    # adding to the draft and completing the sale.
    draft.add(sales_service.resolve_item(str(soap.id)), 2)

    # Force an oversell on the second line by selling out soap first via a
    # separate, already-completed sale.
    separate = SaleDraft()
    separate.add(sales_service.resolve_item(str(soap.id)), 2)
    sales_service.complete_sale(separate)

    with pytest.raises(InsufficientStockError):
        sales_service.complete_sale(draft)

    with session_factory() as session:
        # Only the "separate" sale should exist; the failed draft's shampoo
        # line must not have been committed either.
        assert session.query(Sale).count() == 1
        assert session.query(SaleItem).count() == 1

    shampoo_after = inventory_service.get_item(shampoo.id)
    assert shampoo_after.stock == 10  # untouched by the rolled-back sale


def test_complete_sale_rejects_empty_draft(sales_service):
    with pytest.raises(ValidationError):
        sales_service.complete_sale(SaleDraft())


def test_complete_sale_rejects_archived_item_snuck_into_draft(
    inventory_service, sales_service
):
    item = make_product(inventory_service, initial_stock=10)
    snapshot = sales_service.resolve_item(str(item.id))
    draft = SaleDraft()
    draft.add(snapshot, 1)

    inventory_service.archive_item(item.id)

    with pytest.raises(ItemInactiveError):
        sales_service.complete_sale(draft)
