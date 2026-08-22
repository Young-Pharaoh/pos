"""Weighted-average inventory costing.

This is the single source of truth for the weighted-average cost formula.
Both the add-stock preview (shown to the user before they confirm) and the
actual commit path call this same function, so the preview and the
persisted result can never disagree.

    new_average_cost = (old_stock * old_avg_cost + added_qty * new_unit_price)
                        / (old_stock + added_qty)

When ``old_stock`` is zero (the product sold out completely before this
purchase), the formula naturally collapses to ``new_unit_price`` -- this is
the correct "reset" behaviour, not a special case that needs its own branch.

Repeated re-averaging is lossy by a fraction of a cent because each result
is quantized to 4 decimal places before being used as an input to the next
purchase. This is an accepted, well-understood property of weighted-average
costing and is not treated as a bug.
"""

from __future__ import annotations

from decimal import Decimal

from app.utils.money import quantize_money, to_decimal


def weighted_average_cost(
    old_stock: int, old_avg_cost, added_qty: int, new_unit_price
) -> Decimal:
    if old_stock < 0:
        raise ValueError("old_stock cannot be negative")
    if added_qty <= 0:
        raise ValueError("added_qty must be a positive integer")

    old_avg_cost = to_decimal(old_avg_cost)
    new_unit_price = to_decimal(new_unit_price)

    total_value = (Decimal(old_stock) * old_avg_cost) + (
        Decimal(added_qty) * new_unit_price
    )
    total_quantity = Decimal(old_stock + added_qty)
    return quantize_money(total_value / total_quantity)
