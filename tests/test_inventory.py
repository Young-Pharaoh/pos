from decimal import Decimal

import pytest

from app.errors import (
    DeletionNotAllowedError,
    ItemNotFoundError,
    ValidationError,
)


def create_shampoo(inventory_service, **overrides):
    defaults = dict(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        initial_stock=0,
    )
    defaults.update(overrides)
    return inventory_service.create_item(**defaults)


def test_create_product(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=0)
    assert item.id is not None
    assert item.name_ar == "\u0634\u0627\u0645\u0628\u0648"
    assert item.name_es == "Champu"
    assert item.purchase_price == Decimal("0.7000")
    assert item.sell_price == Decimal("1.0000")
    assert item.stock == 0
    assert item.is_active is True


def test_create_product_with_initial_stock_records_a_purchase(
    inventory_service, session_factory
):
    from app.database.models import StockPurchase

    item = create_shampoo(inventory_service, initial_stock=50)
    assert item.stock == 50

    with session_factory() as session:
        purchases = session.query(StockPurchase).filter_by(item_id=item.id).all()
    assert len(purchases) == 1
    assert purchases[0].quantity == 50
    assert purchases[0].unit_price == Decimal("0.7000")


def test_create_product_with_zero_initial_stock_records_no_purchase(
    inventory_service, session_factory
):
    from app.database.models import StockPurchase

    item = create_shampoo(inventory_service, initial_stock=0)
    with session_factory() as session:
        purchases = session.query(StockPurchase).filter_by(item_id=item.id).all()
    assert purchases == []


@pytest.mark.parametrize(
    "field,value,error_key",
    [
        ("name_ar", "", "error.name_ar_required"),
        ("name_ar", "   ", "error.name_ar_required"),
        ("name_es", "", "error.name_es_required"),
        ("purchase_price", Decimal("-1"), "error.negative_purchase_price"),
        ("sell_price", Decimal("-1"), "error.negative_sell_price"),
        ("initial_stock", -5, "error.negative_initial_stock"),
    ],
)
def test_create_product_validation(inventory_service, field, value, error_key):
    with pytest.raises(ValidationError) as exc_info:
        create_shampoo(inventory_service, **{field: value})
    assert exc_info.value.message_key == error_key


def test_add_stock_increases_stock(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=100)
    updated = inventory_service.add_stock(item.id, 50, Decimal("0.70"))
    assert updated.stock == 150


def test_add_stock_at_same_price_keeps_average_unchanged(inventory_service):
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    updated = inventory_service.add_stock(item.id, 50, Decimal("0.70"))
    assert updated.purchase_price == Decimal("0.7000")


def test_add_stock_at_different_price_recalculates_weighted_average(inventory_service):
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    updated = inventory_service.add_stock(item.id, 50, Decimal("0.80"))
    # (100 * 0.70 + 50 * 0.80) / 150 = 0.7333
    assert updated.purchase_price == Decimal("0.7333")
    assert updated.stock == 150


def test_add_stock_records_historical_purchase_row(inventory_service, session_factory):
    from app.database.models import StockPurchase

    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    inventory_service.add_stock(item.id, 50, Decimal("0.80"))

    with session_factory() as session:
        purchases = (
            session.query(StockPurchase)
            .filter_by(item_id=item.id)
            .order_by(StockPurchase.id)
            .all()
        )
    assert len(purchases) == 2
    assert purchases[1].quantity == 50
    assert purchases[1].unit_price == Decimal("0.8000")
    assert purchases[1].total_price == Decimal("40.0000")


def test_add_stock_rejects_invalid_quantity(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=10)
    with pytest.raises(ValidationError):
        inventory_service.add_stock(item.id, 0, Decimal("0.7"))
    with pytest.raises(ValidationError):
        inventory_service.add_stock(item.id, -5, Decimal("0.7"))


def test_add_stock_rejects_negative_price(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=10)
    with pytest.raises(ValidationError):
        inventory_service.add_stock(item.id, 5, Decimal("-1"))


def test_add_stock_unknown_item_raises_not_found(inventory_service):
    with pytest.raises(ItemNotFoundError):
        inventory_service.add_stock(999, 5, Decimal("1"))


def test_add_stock_failure_does_not_partially_update(inventory_service, monkeypatch):
    """If the purchase insert fails, stock and average cost must be untouched."""
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)

    from app.database.repositories import purchase_repository as purchase_repo_module

    def boom(self, purchase):
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(purchase_repo_module.PurchaseRepository, "add", boom)

    with pytest.raises(RuntimeError):
        inventory_service.add_stock(item.id, 50, Decimal("0.80"))

    reloaded = inventory_service.get_item(item.id)
    assert reloaded.stock == 100
    assert reloaded.purchase_price == Decimal("0.7000")


def test_preview_add_stock_does_not_write_anything(inventory_service):
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    preview = inventory_service.preview_add_stock(item.id, 50, Decimal("0.80"))

    assert preview.current_stock == 100
    assert preview.current_price == Decimal("0.7000")
    assert preview.new_stock == 150
    assert preview.new_average_price == Decimal("0.7333")
    assert preview.price_changed is True

    unchanged = inventory_service.get_item(item.id)
    assert unchanged.stock == 100
    assert unchanged.purchase_price == Decimal("0.7000")


def test_preview_add_stock_price_changed_false_when_same_price(inventory_service):
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    preview = inventory_service.preview_add_stock(item.id, 50, Decimal("0.70"))
    assert preview.price_changed is False


def test_update_item_cannot_touch_stock(inventory_service):
    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    updated = inventory_service.update_item(item.id, name_es="Shampoo Nuevo", sell_price=Decimal("1.50"))
    assert updated.name_es == "Shampoo Nuevo"
    assert updated.sell_price == Decimal("1.5000")
    assert updated.stock == 100
    assert updated.purchase_price == Decimal("0.7000")

    import inspect

    from app.services.inventory_service import InventoryService

    params = inspect.signature(InventoryService.update_item).parameters
    assert "stock" not in params


def test_update_item_can_correct_purchase_price(inventory_service):
    item = create_shampoo(
        inventory_service, purchase_price=Decimal("50.00"), initial_stock=10
    )
    updated = inventory_service.update_item(item.id, purchase_price=Decimal("0.50"))
    assert updated.purchase_price == Decimal("0.5000")
    assert updated.stock == 10


def test_update_item_purchase_price_syncs_matching_stock_purchases(
    inventory_service, session_factory
):
    from app.database.models import StockPurchase

    item = create_shampoo(
        inventory_service, purchase_price=Decimal("50.00"), initial_stock=10
    )
    inventory_service.update_item(item.id, purchase_price=Decimal("0.50"))

    with session_factory() as session:
        purchase = session.query(StockPurchase).filter_by(item_id=item.id).one()
    assert purchase.unit_price == Decimal("0.5000")
    assert purchase.total_price == Decimal("5.0000")


def test_update_item_purchase_price_does_not_sync_unrelated_stock_purchases(
    inventory_service, session_factory
):
    from app.database.models import StockPurchase

    item = create_shampoo(inventory_service, purchase_price=Decimal("0.70"), initial_stock=100)
    inventory_service.add_stock(item.id, 50, Decimal("0.80"))

    inventory_service.update_item(item.id, purchase_price=Decimal("0.50"))

    with session_factory() as session:
        purchases = (
            session.query(StockPurchase)
            .filter_by(item_id=item.id)
            .order_by(StockPurchase.id)
            .all()
        )
    assert purchases[0].unit_price == Decimal("0.7000")
    assert purchases[1].unit_price == Decimal("0.8000")
    assert inventory_service.get_item(item.id).purchase_price == Decimal("0.5000")


def test_update_item_rejects_blank_names(inventory_service):
    item = create_shampoo(inventory_service)
    with pytest.raises(ValidationError):
        inventory_service.update_item(item.id, name_ar="   ")


def test_archive_and_restore_item(inventory_service):
    item = create_shampoo(inventory_service)
    archived = inventory_service.archive_item(item.id)
    assert archived.is_active is False

    restored = inventory_service.restore_item(item.id)
    assert restored.is_active is True


def test_archived_items_excluded_from_active_search_by_default(inventory_service):
    item = create_shampoo(inventory_service)
    inventory_service.archive_item(item.id)
    results = inventory_service.search_items("Champu")
    assert results == []
    results_with_archived = inventory_service.search_items("Champu", include_archived=True)
    assert len(results_with_archived) == 1


def test_delete_item_without_history_succeeds(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=0)
    inventory_service.delete_item(item.id)
    with pytest.raises(ItemNotFoundError):
        inventory_service.get_item(item.id)


def test_delete_item_with_purchase_history_is_rejected(inventory_service):
    item = create_shampoo(inventory_service, initial_stock=10)
    with pytest.raises(DeletionNotAllowedError):
        inventory_service.delete_item(item.id)
    # item must still exist afterwards
    assert inventory_service.get_item(item.id) is not None


def test_can_delete_reflects_history(inventory_service):
    no_history = create_shampoo(inventory_service, initial_stock=0)
    with_history = create_shampoo(inventory_service, name_es="Jabon", initial_stock=5)
    assert inventory_service.can_delete(no_history.id) is True
    assert inventory_service.can_delete(with_history.id) is False


def test_search_by_id(inventory_service):
    item = create_shampoo(inventory_service)
    results = inventory_service.search_items(str(item.id))
    assert any(r.id == item.id for r in results)


def test_search_by_partial_name(inventory_service):
    create_shampoo(inventory_service, name_ar="\u0634\u0627\u0645\u0628\u0648", name_es="Champu")
    results = inventory_service.search_items("champ")
    assert len(results) == 1


def test_search_supports_arabic_name(inventory_service):
    create_shampoo(inventory_service, name_ar="\u0635\u0627\u0628\u0648\u0646", name_es="Jabon")
    results = inventory_service.search_items("\u0635\u0627\u0628\u0648\u0646")
    assert len(results) == 1


def test_list_low_stock(inventory_service):
    create_shampoo(inventory_service, name_es="Bajo", initial_stock=2)
    create_shampoo(inventory_service, name_es="Alto", initial_stock=50)
    low = inventory_service.list_low_stock(threshold=5)
    assert [item.name_es for item in low] == ["Bajo"]
