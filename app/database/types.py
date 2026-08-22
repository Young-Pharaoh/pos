"""Custom SQLAlchemy column types."""

from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.types import TypeDecorator

from app.utils.money import from_scaled_int, to_scaled_int


class Money(TypeDecorator):
    """Persists a :class:`decimal.Decimal` as an integer scaled by 10,000.

    SQLite has no native decimal type, and SQLAlchemy's ``Numeric`` falls
    back to Python floats on SQLite, which is exactly the floating-point
    money bug the application must avoid. Storing a scaled integer instead
    keeps ``SUM()`` exact and lets Python-side code work with ``Decimal``
    everywhere via :mod:`app.utils.money`.
    """

    impl = Integer
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return to_scaled_int(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return from_scaled_int(value)
