"""Reads and writes the ``settings`` key/value table.

Deliberately a flat key/value store rather than typed columns: it lets the
Settings dialog add a new configurable value without a schema migration,
which matters more for a small app maintained occasionally than strict
typing at the database layer. Typed access happens here, in Python.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Setting
from app.utils.money import to_decimal

LOW_STOCK_THRESHOLD_KEY = "low_stock_threshold"
DEFAULT_SELL_PRICE_KEY = "default_sell_price"
CURRENCY_SYMBOL_KEY = "currency_symbol"
LANGUAGE_KEY = "language"


@dataclass(frozen=True)
class AppSettings:
    low_stock_threshold: int
    default_sell_price: Decimal
    currency_symbol: str
    language: str


class SettingsService:
    def __init__(self, session_factory: sessionmaker[Session]):
        self._session_factory = session_factory

    def get_all(self) -> AppSettings:
        with self._session_factory() as session:
            rows = {row.key: row.value for row in session.scalars(select(Setting))}
        return AppSettings(
            low_stock_threshold=int(rows.get(LOW_STOCK_THRESHOLD_KEY, 5)),
            default_sell_price=to_decimal(rows.get(DEFAULT_SELL_PRICE_KEY, "1.00")),
            currency_symbol=rows.get(CURRENCY_SYMBOL_KEY, "$"),
            language=rows.get(LANGUAGE_KEY, "es"),
        )

    def get(self, key: str, default: str | None = None) -> str | None:
        with self._session_factory() as session:
            row = session.get(Setting, key)
        return row.value if row is not None else default

    def set(self, key: str, value: str) -> None:
        with self._session_factory() as session, session.begin():
            row = session.get(Setting, key)
            if row is None:
                session.add(Setting(key=key, value=value))
            else:
                row.value = value

    def update_many(self, values: dict[str, str]) -> None:
        with self._session_factory() as session, session.begin():
            for key, value in values.items():
                row = session.get(Setting, key)
                if row is None:
                    session.add(Setting(key=key, value=str(value)))
                else:
                    row.value = str(value)
