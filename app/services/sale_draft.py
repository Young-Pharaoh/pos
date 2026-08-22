"""In-memory representation of a sale being built at the register.

``SaleDraft`` has no Qt and no database access: it is plain Python holding
a snapshot of each item's sell price, cost, and available stock at the
moment it was added to the sale. This is what makes the New Sale screen's
behaviour (merge duplicate entries, block overselling, live total) testable
without spinning up a database or a Qt event loop, and what the Qt table
model in the UI layer wraps as a thin adapter.

Nothing here touches the database: stock is only actually decremented, and
sale rows only actually written, when the service layer commits the draft
via ``SalesService.complete_sale``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.errors import InsufficientStockError, ValidationError
from app.utils.money import quantize_money


@dataclass(frozen=True)
class ItemSnapshot:
    """Item data as known at the moment it was added to the draft."""

    id: int
    name_ar: str
    name_es: str
    sell_price: Decimal
    cost: Decimal
    available_stock: int


@dataclass
class SaleDraftLine:
    item: ItemSnapshot
    quantity: int

    @property
    def unit_sell_price(self) -> Decimal:
        return self.item.sell_price

    @property
    def unit_cost(self) -> Decimal:
        return self.item.cost

    @property
    def total_sell_price(self) -> Decimal:
        return quantize_money(self.unit_sell_price * self.quantity)

    @property
    def total_cost(self) -> Decimal:
        return quantize_money(self.unit_cost * self.quantity)


class SaleDraft:
    """A sale being built. Ordered by first-added item, duplicates merged."""

    def __init__(self) -> None:
        self._lines: dict[int, SaleDraftLine] = {}

    def add(self, item: ItemSnapshot, quantity: int) -> SaleDraftLine:
        """Add ``quantity`` of ``item``, merging into an existing line if present."""
        if quantity <= 0:
            raise ValidationError("error.invalid_quantity")

        existing = self._lines.get(item.id)
        merged_quantity = quantity + (existing.quantity if existing else 0)
        if merged_quantity > item.available_stock:
            raise InsufficientStockError(item.id, merged_quantity, item.available_stock)

        line = SaleDraftLine(item=item, quantity=merged_quantity)
        self._lines[item.id] = line
        return line

    def set_quantity(self, item_id: int, quantity: int) -> SaleDraftLine:
        """Change the quantity of an existing line, revalidating stock."""
        if item_id not in self._lines:
            raise KeyError(item_id)
        if quantity <= 0:
            raise ValidationError("error.invalid_quantity")

        line = self._lines[item_id]
        if quantity > line.item.available_stock:
            raise InsufficientStockError(item_id, quantity, line.item.available_stock)

        line.quantity = quantity
        return line

    def remove(self, item_id: int) -> None:
        self._lines.pop(item_id, None)

    def clear(self) -> None:
        self._lines.clear()

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._lines

    def __len__(self) -> int:
        return len(self._lines)

    @property
    def is_empty(self) -> bool:
        return not self._lines

    @property
    def lines(self) -> list[SaleDraftLine]:
        return list(self._lines.values())

    @property
    def total(self) -> Decimal:
        if not self._lines:
            return Decimal("0.0000")
        return quantize_money(sum((line.total_sell_price for line in self.lines), Decimal("0")))
