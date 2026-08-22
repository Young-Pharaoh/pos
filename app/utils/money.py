"""Money handling policy for the whole application.

All monetary values are handled as :class:`decimal.Decimal` in Python and
persisted in SQLite as integers scaled by :data:`STORAGE_SCALE` (four
decimal places). This keeps ``SUM()`` exact in SQLite (which has no native
decimal type) while still holding sub-cent weighted-average costs such as
``$0.7333``.

Precision policy:

* Storage precision: 4 decimal places (``STORAGE_EXPONENT``).
* Display precision: 2 decimal places (``DISPLAY_EXPONENT``).
* Rounding mode: ``ROUND_HALF_UP`` everywhere, so behaviour matches what a
  shop owner expects from a cash register rather than banker's rounding.

Never divide or average money columns inside SQL: a ``SUM`` of the scaled
integer column decodes correctly back to ``Decimal``, but a SQL-side
division would not go through :class:`~app.database.types.Money` and would
silently degrade to floating point. Fetch the summed quantity and summed
money separately and divide in Python using this module.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

STORAGE_EXPONENT = Decimal("0.0001")
DISPLAY_EXPONENT = Decimal("0.01")
STORAGE_SCALE = 10_000


def to_decimal(value) -> Decimal:
    """Coerce ``int``, ``float``, ``str``, or ``Decimal`` into a ``Decimal``.

    Floats are converted via ``str()`` first to avoid inheriting binary
    floating-point noise (e.g. ``Decimal(0.1)`` vs ``Decimal("0.1")``).
    """
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        value = repr(value)
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Cannot convert {value!r} to a monetary Decimal") from exc


def quantize_money(value) -> Decimal:
    """Round to the 4-decimal-place storage precision."""
    return to_decimal(value).quantize(STORAGE_EXPONENT, rounding=ROUND_HALF_UP)


def quantize_display(value) -> Decimal:
    """Round to the 2-decimal-place display precision."""
    return to_decimal(value).quantize(DISPLAY_EXPONENT, rounding=ROUND_HALF_UP)


def to_scaled_int(value) -> int:
    """Convert a monetary Decimal into the scaled integer used for storage."""
    return int(quantize_money(value) * STORAGE_SCALE)


def from_scaled_int(value: int) -> Decimal:
    """Convert a stored scaled integer back into a Decimal."""
    return (Decimal(value) / STORAGE_SCALE).quantize(
        STORAGE_EXPONENT, rounding=ROUND_HALF_UP
    )


def format_money(value, symbol: str = "$") -> str:
    """Format a monetary value for display, e.g. ``$1.00`` or ``$0.70``."""
    amount = quantize_display(value)
    return f"{symbol}{amount:,.2f}"


def is_negative(value) -> bool:
    return to_decimal(value) < 0
