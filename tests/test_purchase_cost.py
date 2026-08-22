from decimal import Decimal

import pytest

from app.services.costing import weighted_average_cost


def test_spec_worked_example_100_at_070_plus_50_at_080():
    # (100 * 0.70 + 50 * 0.80) / 150 = 0.733333... -> 0.7333
    result = weighted_average_cost(100, Decimal("0.70"), 50, Decimal("0.80"))
    assert result == Decimal("0.7333")


def test_adding_stock_at_same_price_keeps_average_unchanged():
    result = weighted_average_cost(100, Decimal("0.70"), 50, Decimal("0.70"))
    assert result == Decimal("0.7000")


def test_adding_stock_when_sold_out_resets_to_new_price():
    result = weighted_average_cost(0, Decimal("0.70"), 20, Decimal("0.95"))
    assert result == Decimal("0.9500")


def test_repeated_averaging_is_order_dependent_but_stable():
    first = weighted_average_cost(100, Decimal("0.70"), 50, Decimal("0.80"))
    second = weighted_average_cost(150, first, 25, Decimal("1.00"))
    # (150 * 0.7333 + 25 * 1.00) / 175 = 0.7714 (rounded half up)
    assert second == Decimal("0.7714")


def test_rejects_zero_or_negative_added_quantity():
    with pytest.raises(ValueError):
        weighted_average_cost(10, Decimal("0.5"), 0, Decimal("0.6"))
    with pytest.raises(ValueError):
        weighted_average_cost(10, Decimal("0.5"), -3, Decimal("0.6"))


def test_rejects_negative_old_stock():
    with pytest.raises(ValueError):
        weighted_average_cost(-1, Decimal("0.5"), 5, Decimal("0.6"))


def test_accepts_string_and_float_inputs_via_money_conversion():
    result = weighted_average_cost(100, "0.70", 50, "0.80")
    assert result == Decimal("0.7333")
