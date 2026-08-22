from decimal import Decimal

from app.utils.money import (
    format_money,
    from_scaled_int,
    quantize_display,
    quantize_money,
    to_decimal,
    to_scaled_int,
)


def test_to_decimal_from_string():
    assert to_decimal("0.7333") == Decimal("0.7333")


def test_to_decimal_from_float_avoids_binary_noise():
    # 0.1 + 0.2 in raw binary floating point is 0.30000000000000004.
    # Going through str() first must avoid that noise.
    assert to_decimal(0.1) + to_decimal(0.2) == Decimal("0.3")


def test_quantize_money_rounds_to_four_places_half_up():
    assert quantize_money("0.73335") == Decimal("0.7334")
    assert quantize_money("0.73334") == Decimal("0.7333")


def test_quantize_display_rounds_to_two_places_half_up():
    assert quantize_display("0.7333") == Decimal("0.73")
    assert quantize_display("0.7350") == Decimal("0.74")


def test_scaled_int_roundtrip():
    value = Decimal("0.7333")
    scaled = to_scaled_int(value)
    assert scaled == 7333
    assert from_scaled_int(scaled) == value


def test_scaled_int_roundtrip_whole_number():
    assert to_scaled_int(Decimal("1.00")) == 10_000
    assert from_scaled_int(10_000) == Decimal("1.0000")


def test_format_money_default_symbol():
    assert format_money(Decimal("1")) == "$1.00"
    assert format_money(Decimal("0.7")) == "$0.70"
    assert format_money(Decimal("12.5")) == "$12.50"


def test_format_money_custom_symbol():
    assert format_money(Decimal("5"), symbol="Bs. ") == "Bs. 5.00"


def test_format_money_thousands_separator():
    assert format_money(Decimal("1234.5")) == "$1,234.50"
