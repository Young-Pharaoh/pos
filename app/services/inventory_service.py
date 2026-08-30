"""Product catalog and stock-purchase business logic.

This is the only place in the application allowed to change
``items.stock`` or ``items.purchase_price`` outside of a completed sale.
Stock only ever moves through ``add_stock`` (or a sale). Purchase price
can be corrected directly via ``update_item``; matching ``stock_purchases``
rows whose ``unit_price`` equals the old average are updated in the same
transaction so purchase reports stay consistent with data-entry fixes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Item, StockPurchase
from app.database.repositories.item_repository import ItemRepository
from app.database.repositories.purchase_repository import PurchaseRepository
from app.errors import DeletionNotAllowedError, ItemNotFoundError, ValidationError
from app.services.costing import weighted_average_cost
from app.utils.money import quantize_money, to_decimal


@dataclass(frozen=True)
class ItemView:
    """Read-only snapshot of an item, safe to hand to the UI or a test."""

    id: int
    name_ar: str
    name_es: str
    purchase_price: Decimal
    sell_price: Decimal
    stock: int
    image_path: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @property
    def inventory_value(self) -> Decimal:
        return quantize_money(self.purchase_price * self.stock)


@dataclass(frozen=True)
class AddStockPreview:
    """Read-only preview of what ``add_stock`` would do; no database writes."""

    item_id: int
    current_stock: int
    current_price: Decimal
    added_quantity: int
    new_unit_price: Decimal
    new_stock: int
    new_average_price: Decimal
    price_changed: bool


def _to_view(item: Item) -> ItemView:
    return ItemView(
        id=item.id,
        name_ar=item.name_ar,
        name_es=item.name_es,
        purchase_price=item.purchase_price,
        sell_price=item.sell_price,
        stock=item.stock,
        image_path=item.image_path,
        is_active=item.is_active,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _validate_names(name_ar: str, name_es: str) -> None:
    if not name_ar or not name_ar.strip():
        raise ValidationError("error.name_ar_required")
    if not name_es or not name_es.strip():
        raise ValidationError("error.name_es_required")


def _validate_price(value, error_key: str) -> Decimal:
    try:
        decimal_value = to_decimal(value)
    except ValueError as exc:
        raise ValidationError("error.invalid_price") from exc
    if decimal_value < 0:
        raise ValidationError(error_key)
    return decimal_value


def _validate_quantity(value) -> int:
    try:
        quantity = int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError("error.invalid_quantity") from exc
    if quantity <= 0:
        raise ValidationError("error.invalid_quantity")
    return quantity


class InventoryService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    # -- reads -----------------------------------------------------------

    def get_item(self, item_id: int) -> ItemView:
        with self._session_factory() as session:
            item = ItemRepository(session).get(item_id)
            if item is None:
                raise ItemNotFoundError(item_id)
            return _to_view(item)

    def list_items(self, *, include_archived: bool = True) -> list[ItemView]:
        with self._session_factory() as session:
            items = ItemRepository(session).list_all(include_archived=include_archived)
            return [_to_view(item) for item in items]

    def search_items(self, query: str, *, include_archived: bool = False) -> list[ItemView]:
        with self._session_factory() as session:
            items = ItemRepository(session).search(query, include_archived=include_archived)
            return [_to_view(item) for item in items]

    def list_low_stock(self, threshold: int) -> list[ItemView]:
        with self._session_factory() as session:
            items = ItemRepository(session).list_low_stock(threshold)
            return [_to_view(item) for item in items]

    def can_delete(self, item_id: int) -> bool:
        with self._session_factory() as session:
            return not ItemRepository(session).has_history(item_id)

    # -- writes ------------------------------------------------------------

    def create_item(
        self,
        *,
        name_ar: str,
        name_es: str,
        purchase_price,
        sell_price,
        initial_stock: int = 0,
        image_path: str | None = None,
    ) -> ItemView:
        _validate_names(name_ar, name_es)
        purchase_price_dec = _validate_price(purchase_price, "error.negative_purchase_price")
        sell_price_dec = _validate_price(sell_price, "error.negative_sell_price")
        try:
            initial_stock_int = int(initial_stock)
        except (TypeError, ValueError) as exc:
            raise ValidationError("error.negative_initial_stock") from exc
        if initial_stock_int < 0:
            raise ValidationError("error.negative_initial_stock")

        with self._session_factory() as session:
            with session.begin():
                now = datetime.now()
                item = Item(
                    name_ar=name_ar.strip(),
                    name_es=name_es.strip(),
                    purchase_price=purchase_price_dec,
                    sell_price=sell_price_dec,
                    stock=initial_stock_int,
                    image_path=image_path,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                items = ItemRepository(session)
                items.add(item)

                if initial_stock_int > 0:
                    purchases = PurchaseRepository(session)
                    purchases.add(
                        StockPurchase(
                            item_id=item.id,
                            quantity=initial_stock_int,
                            unit_price=purchase_price_dec,
                            total_price=quantize_money(purchase_price_dec * initial_stock_int),
                            purchase_date=now,
                        )
                    )
                view = _to_view(item)
            return view

    def update_item(
        self,
        item_id: int,
        *,
        name_ar: str | None = None,
        name_es: str | None = None,
        purchase_price=None,
        sell_price=None,
        image_path: str | None | object = ...,
    ) -> ItemView:
        """Edit product metadata, including a direct purchase-price correction.

        Stock is intentionally not a parameter here -- it can only change via
        ``add_stock`` (or a sale). When ``purchase_price`` changes, any
        ``stock_purchases`` row whose ``unit_price`` matched the old average
        is updated so purchase reports reflect typo fixes at creation time.
        Past ``sale_items`` costs are never touched. ``image_path`` uses ``...``
        (Ellipsis) as its "not provided" sentinel so callers can still
        explicitly pass ``None`` to clear the image.
        """
        with self._session_factory() as session:
            with session.begin():
                items = ItemRepository(session)
                item = items.get(item_id)
                if item is None:
                    raise ItemNotFoundError(item_id)

                new_name_ar = name_ar if name_ar is not None else item.name_ar
                new_name_es = name_es if name_es is not None else item.name_es
                _validate_names(new_name_ar, new_name_es)
                item.name_ar = new_name_ar.strip()
                item.name_es = new_name_es.strip()

                if purchase_price is not None:
                    new_purchase_price = _validate_price(
                        purchase_price, "error.negative_purchase_price"
                    )
                    old_purchase_price = item.purchase_price
                    if new_purchase_price != old_purchase_price:
                        item.purchase_price = new_purchase_price
                        purchases = PurchaseRepository(session)
                        for purchase in purchases.list_by_item_id(item.id):
                            if purchase.unit_price == old_purchase_price:
                                purchase.unit_price = new_purchase_price
                                purchase.total_price = quantize_money(
                                    new_purchase_price * purchase.quantity
                                )

                if sell_price is not None:
                    item.sell_price = _validate_price(sell_price, "error.negative_sell_price")

                if image_path is not ...:
                    item.image_path = image_path

                item.updated_at = datetime.now()
                view = _to_view(item)
            return view

    def preview_add_stock(self, item_id: int, quantity, unit_price) -> AddStockPreview:
        """Read-only: computes what ``add_stock`` would do without writing anything."""
        quantity_int = _validate_quantity(quantity)
        unit_price_dec = _validate_price(unit_price, "error.negative_purchase_price")

        with self._session_factory() as session:
            item = ItemRepository(session).get(item_id)
            if item is None:
                raise ItemNotFoundError(item_id)

            new_average = weighted_average_cost(
                item.stock, item.purchase_price, quantity_int, unit_price_dec
            )
            return AddStockPreview(
                item_id=item.id,
                current_stock=item.stock,
                current_price=item.purchase_price,
                added_quantity=quantity_int,
                new_unit_price=unit_price_dec,
                new_stock=item.stock + quantity_int,
                new_average_price=new_average,
                price_changed=unit_price_dec != item.purchase_price,
            )

    def add_stock(self, item_id: int, quantity, unit_price) -> ItemView:
        """Atomically record a stock purchase and update stock/average cost.

        1. Compute the new weighted-average cost.
        2. Insert the historical ``stock_purchases`` row.
        3. Increase ``items.stock`` and update ``items.purchase_price``.
        4. Commit everything together; any failure rolls back all of it.
        """
        quantity_int = _validate_quantity(quantity)
        unit_price_dec = _validate_price(unit_price, "error.negative_purchase_price")

        with self._session_factory() as session:
            with session.begin():
                items = ItemRepository(session)
                item = items.get(item_id)
                if item is None:
                    raise ItemNotFoundError(item_id)

                new_average = weighted_average_cost(
                    item.stock, item.purchase_price, quantity_int, unit_price_dec
                )
                now = datetime.now()

                PurchaseRepository(session).add(
                    StockPurchase(
                        item_id=item.id,
                        quantity=quantity_int,
                        unit_price=unit_price_dec,
                        total_price=quantize_money(unit_price_dec * quantity_int),
                        purchase_date=now,
                    )
                )

                item.stock = item.stock + quantity_int
                item.purchase_price = new_average
                item.updated_at = now
                view = _to_view(item)
            return view

    def archive_item(self, item_id: int) -> ItemView:
        return self._set_active(item_id, False)

    def restore_item(self, item_id: int) -> ItemView:
        return self._set_active(item_id, True)

    def _set_active(self, item_id: int, active: bool) -> ItemView:
        with self._session_factory() as session:
            with session.begin():
                items = ItemRepository(session)
                item = items.get(item_id)
                if item is None:
                    raise ItemNotFoundError(item_id)
                item.is_active = active
                item.updated_at = datetime.now()
                view = _to_view(item)
            return view

    def delete_item(self, item_id: int) -> None:
        """Hard-delete only if the item has no purchase or sale history.

        Otherwise raises ``DeletionNotAllowedError`` -- the caller (UI) is
        expected to offer archiving instead, which preserves history.
        """
        with self._session_factory() as session:
            with session.begin():
                items = ItemRepository(session)
                item = items.get(item_id)
                if item is None:
                    raise ItemNotFoundError(item_id)
                if items.has_history(item_id):
                    raise DeletionNotAllowedError(item_id)
                items.delete(item)
