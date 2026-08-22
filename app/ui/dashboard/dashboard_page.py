"""Dashboard: the figures a shop owner checks first (spec section 21).

Deliberately simple -- six numbers/lists, no charts. Everything here reads
through :class:`app.services.report_service.ReportService`; the page holds
no business logic of its own.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.i18n import t
from app.ui.app_context import AppContext
from app.text_scale import page_title_stylesheet
from app.ui.widgets.common import combined_name
from app.ui.widgets.stat_card import StatCard


class DashboardPage(QWidget):
    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self._build_ui()
        self.retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        header = QHBoxLayout()
        self.title_label = QLabel()
        header.addWidget(self.title_label)
        header.addStretch()
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refresh)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)

        cards_layout = QHBoxLayout()
        self.today_sales_card = StatCard()
        self.month_sales_card = StatCard()
        self.month_profit_card = StatCard()
        self.inventory_value_card = StatCard()
        for card in (
            self.today_sales_card,
            self.month_sales_card,
            self.month_profit_card,
            self.inventory_value_card,
        ):
            cards_layout.addWidget(card)
        layout.addLayout(cards_layout)

        lists_layout = QHBoxLayout()

        self.low_stock_box = QGroupBox()
        low_stock_layout = QVBoxLayout(self.low_stock_box)
        self.low_stock_list = QListWidget()
        low_stock_layout.addWidget(self.low_stock_list)
        lists_layout.addWidget(self.low_stock_box)

        self.best_sellers_box = QGroupBox()
        best_sellers_layout = QVBoxLayout(self.best_sellers_box)
        self.best_sellers_list = QListWidget()
        best_sellers_layout.addWidget(self.best_sellers_list)
        lists_layout.addWidget(self.best_sellers_box)

        layout.addLayout(lists_layout, stretch=1)

    def retranslate(self) -> None:
        self.title_label.setText(t("dashboard.title"))
        self.refresh_button.setText(t("common.refresh"))
        self.today_sales_card.set_title(t("dashboard.today_sales"))
        self.month_sales_card.set_title(t("dashboard.month_sales"))
        self.month_profit_card.set_title(t("dashboard.month_profit"))
        self.inventory_value_card.set_title(t("dashboard.inventory_value"))
        self.low_stock_box.setTitle(t("dashboard.low_stock"))
        self.best_sellers_box.setTitle(t("dashboard.best_sellers"))
        self.refresh()

    def apply_text_scale(self, preset: str) -> None:
        self.title_label.setStyleSheet(page_title_stylesheet(preset))
        self.today_sales_card.apply_text_scale(preset)
        self.month_sales_card.apply_text_scale(preset)
        self.month_profit_card.apply_text_scale(preset)
        self.inventory_value_card.apply_text_scale(preset)

    def refresh(self) -> None:
        summary = self.context.report_service.dashboard_summary(
            self.context.settings.low_stock_threshold
        )

        self.today_sales_card.set_value(self.context.format_money(summary.today_sales_total))
        self.month_sales_card.set_value(self.context.format_money(summary.month_sales_total))
        self.month_profit_card.set_value(self.context.format_money(summary.month_profit))
        self.inventory_value_card.set_value(self.context.format_money(summary.inventory_value))

        self.low_stock_list.clear()
        if not summary.low_stock:
            self.low_stock_list.addItem(t("dashboard.no_low_stock"))
        else:
            for row in summary.low_stock:
                name = combined_name(row.name_ar, row.name_es)
                text = f"\u26a0 {name} \u2014 {t('dashboard.units_remaining', stock=row.stock)}"
                self.low_stock_list.addItem(text)

        self.best_sellers_list.clear()
        if not summary.best_sellers:
            self.best_sellers_list.addItem(t("dashboard.no_sales_yet"))
        else:
            for rank, row in enumerate(summary.best_sellers, start=1):
                name = combined_name(row.name_ar, row.name_es)
                text = f"{rank}. {name} \u2014 {t('dashboard.units_sold', qty=row.qty_sold)}"
                self.best_sellers_list.addItem(text)
