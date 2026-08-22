"""Wires services together and holds cached settings for the UI layer.

One instance is created in ``main.py`` and threaded down to every page and
dialog, so widgets never construct their own services or reach for a
process-wide singleton -- everything they need arrives through this one
object, which keeps widgets easy to test in isolation if needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.sales_service import SalesService
from app.services.settings_service import AppSettings, SettingsService
from app.utils.money import format_money


@dataclass
class AppContext:
    session_factory: sessionmaker[Session]
    inventory_service: InventoryService
    sales_service: SalesService
    report_service: ReportService
    settings_service: SettingsService
    settings: AppSettings

    @classmethod
    def build(cls, session_factory: sessionmaker[Session]) -> "AppContext":
        settings_service = SettingsService(session_factory)
        return cls(
            session_factory=session_factory,
            inventory_service=InventoryService(session_factory),
            sales_service=SalesService(session_factory),
            report_service=ReportService(session_factory),
            settings_service=settings_service,
            settings=settings_service.get_all(),
        )

    def refresh_settings(self) -> None:
        self.settings = self.settings_service.get_all()

    def format_money(self, value) -> str:
        return format_money(value, symbol=self.settings.currency_symbol)
