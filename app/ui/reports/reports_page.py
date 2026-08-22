"""Reports screen (spec sections 15-19): period selector, the main product
report table with a totals footer, and the three performance views.
"""

from __future__ import annotations

import csv
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.i18n import t
from app.services.report_service import ProductReport
from app.ui.app_context import AppContext
from app.ui.widgets.common import combined_name, guarded, show_info
from app.utils.dates import DateRange, custom, day, month, year

_PRODUCT_COLUMNS = 12
_PURCHASE_UNIT_COL = 5
_AVG_COST_COL = 7


class ReportsPage(QWidget):
    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self._current_report: ProductReport | None = None
        self._build_ui()
        self.retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.title_label)

        period_layout = QHBoxLayout()
        self.period_combo = QComboBox()
        self.period_combo.currentIndexChanged.connect(self._on_period_changed)
        period_layout.addWidget(self.period_combo)

        self.date_edit = QDateEdit(calendarPopup=True)
        self.date_edit.setDate(QDate.currentDate())
        period_layout.addWidget(self.date_edit)

        self.from_label = QLabel()
        self.from_date_edit = QDateEdit(calendarPopup=True)
        self.from_date_edit.setDate(QDate.currentDate())
        self.to_label = QLabel()
        self.to_date_edit = QDateEdit(calendarPopup=True)
        self.to_date_edit.setDate(QDate.currentDate())
        period_layout.addWidget(self.from_label)
        period_layout.addWidget(self.from_date_edit)
        period_layout.addWidget(self.to_label)
        period_layout.addWidget(self.to_date_edit)

        self.generate_button = QPushButton()
        self.generate_button.clicked.connect(self._on_generate)
        period_layout.addWidget(self.generate_button)
        period_layout.addStretch()

        self.export_button = QPushButton()
        self.export_button.clicked.connect(self._on_export_csv)
        period_layout.addWidget(self.export_button)
        layout.addLayout(period_layout)

        self.tabs = QTabWidget()
        self.products_table = QTableWidget(0, _PRODUCT_COLUMNS)
        self.best_sellers_table = QTableWidget(0, 3)
        self.most_profitable_table = QTableWidget(0, 3)
        self.slow_sellers_table = QTableWidget(0, 5)
        for table in (
            self.products_table,
            self.best_sellers_table,
            self.most_profitable_table,
            self.slow_sellers_table,
        ):
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.verticalHeader().setVisible(False)

        self.tabs.addTab(self.products_table, "")
        self.tabs.addTab(self.best_sellers_table, "")
        self.tabs.addTab(self.most_profitable_table, "")
        self.tabs.addTab(self.slow_sellers_table, "")
        layout.addWidget(self.tabs, 1)

        self.slow_sellers_hint_label = QLabel()
        self.slow_sellers_hint_label.setWordWrap(True)
        self.slow_sellers_hint_label.setStyleSheet("color: #777777; font-style: italic;")
        layout.addWidget(self.slow_sellers_hint_label)

    def retranslate(self) -> None:
        self.title_label.setText(t("reports.title"))

        current_key = self.period_combo.currentData() if self.period_combo.count() else "month"
        self.period_combo.blockSignals(True)
        self.period_combo.clear()
        self.period_combo.addItem(t("reports.period_day"), "day")
        self.period_combo.addItem(t("reports.period_month"), "month")
        self.period_combo.addItem(t("reports.period_year"), "year")
        self.period_combo.addItem(t("reports.period_custom"), "custom")
        index = max(0, self.period_combo.findData(current_key))
        self.period_combo.setCurrentIndex(index if index >= 0 else 1)
        self.period_combo.blockSignals(False)

        self.from_label.setText(t("reports.from_label"))
        self.to_label.setText(t("reports.to_label"))
        self.generate_button.setText(t("reports.button_generate"))
        self.export_button.setText(t("common.export_csv"))
        self.tabs.setTabText(0, t("reports.tab_products"))
        self.tabs.setTabText(1, t("reports.tab_best_sellers"))
        self.tabs.setTabText(2, t("reports.tab_most_profitable"))
        self.tabs.setTabText(3, t("reports.tab_slow_sellers"))
        self.slow_sellers_hint_label.setText(t("reports.slow_sellers_hint"))

        self._update_period_controls_visibility()
        self._on_generate()

    def refresh(self) -> None:
        self._on_generate()

    def _update_period_controls_visibility(self) -> None:
        is_custom = self.period_combo.currentData() == "custom"
        self.date_edit.setVisible(not is_custom)
        self.from_label.setVisible(is_custom)
        self.from_date_edit.setVisible(is_custom)
        self.to_label.setVisible(is_custom)
        self.to_date_edit.setVisible(is_custom)

    def _on_period_changed(self, _index: int) -> None:
        self._update_period_controls_visibility()

    def _build_date_range(self) -> DateRange:
        key = self.period_combo.currentData()
        if key == "day":
            return day(self.date_edit.date().toPython())
        if key == "year":
            return year(self.date_edit.date().toPython().year)
        if key == "custom":
            return custom(self.from_date_edit.date().toPython(), self.to_date_edit.date().toPython())
        reference = self.date_edit.date().toPython()
        return month(reference.year, reference.month)

    def _on_generate(self) -> None:
        with guarded(self):
            date_range = self._build_date_range()
            report_service = self.context.report_service
            self._current_report = report_service.product_report(date_range)
            self._populate_products_table(self._current_report)
            self._populate_best_sellers(report_service.best_sellers(date_range))
            self._populate_most_profitable(report_service.most_profitable(date_range))
            self._populate_slow_sellers(report_service.slow_sellers(date_range))

    def _set_row(self, table: QTableWidget, row: int, values: list[str], *, bold: bool = False) -> None:
        for col, value in enumerate(values):
            item = QTableWidgetItem(value)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if bold:
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            table.setItem(row, col, item)

    def _populate_products_table(self, report: ProductReport) -> None:
        table = self.products_table
        table.setHorizontalHeaderLabels(
            [
                t("products.column_id"),
                t("reports.column_item"),
                t("reports.column_purchased"),
                t("reports.column_sold"),
                t("reports.column_current_stock"),
                t("reports.column_purchase_unit"),
                t("reports.column_purchase_total"),
                t("reports.column_current_avg_cost"),
                t("reports.column_sell_unit"),
                t("reports.column_sell_total"),
                t("reports.column_profit"),
                t("reports.column_inventory_value"),
            ]
        )
        purchase_unit_header = table.horizontalHeaderItem(_PURCHASE_UNIT_COL)
        if purchase_unit_header:
            purchase_unit_header.setToolTip(t("reports.column_purchase_unit_tooltip"))
        avg_cost_header = table.horizontalHeaderItem(_AVG_COST_COL)
        if avg_cost_header:
            avg_cost_header.setToolTip(t("reports.column_current_avg_cost_tooltip"))

        rows = report.rows
        table.setRowCount(len(rows) + 1)
        for r, row in enumerate(rows):
            purchase_unit_display = (
                self.context.format_money(row.purchase_unit_price)
                if row.purchase_unit_price is not None
                else "\u2014"
            )
            self._set_row(
                table,
                r,
                [
                    str(row.item_id),
                    combined_name(row.name_ar, row.name_es),
                    str(row.qty_purchased),
                    str(row.qty_sold),
                    str(row.current_stock),
                    purchase_unit_display,
                    self.context.format_money(row.purchase_total),
                    self.context.format_money(row.current_avg_cost),
                    self.context.format_money(row.sell_unit_price),
                    self.context.format_money(row.sell_total),
                    self.context.format_money(row.profit),
                    self.context.format_money(row.inventory_value),
                ],
            )

        totals = report.totals
        self._set_row(
            table,
            len(rows),
            [
                "",
                t("reports.totals_row_label"),
                "",
                "",
                "",
                "",
                self.context.format_money(totals.purchase_total),
                "",
                "",
                self.context.format_money(totals.sell_total),
                self.context.format_money(totals.profit),
                self.context.format_money(totals.inventory_value),
            ],
            bold=True,
        )
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _populate_best_sellers(self, rows) -> None:
        table = self.best_sellers_table
        table.setHorizontalHeaderLabels([t("reports.rank"), t("reports.column_item"), t("reports.qty_sold")])
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._set_row(
                table, r, [str(r + 1), combined_name(row.name_ar, row.name_es), str(row.qty_sold)]
            )
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _populate_most_profitable(self, rows) -> None:
        table = self.most_profitable_table
        table.setHorizontalHeaderLabels([t("reports.rank"), t("reports.column_item"), t("reports.profit")])
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self._set_row(
                table,
                r,
                [str(r + 1), combined_name(row.name_ar, row.name_es), self.context.format_money(row.profit)],
            )
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _populate_slow_sellers(self, rows) -> None:
        table = self.slow_sellers_table
        table.setHorizontalHeaderLabels(
            [
                t("reports.rank"),
                t("reports.column_item"),
                t("reports.qty_sold"),
                t("products.column_stock"),
                t("reports.column_sell_through_pct"),
            ]
        )
        table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            pct = (row.sell_through_rate * 100).quantize(Decimal("0.1"))
            self._set_row(
                table,
                r,
                [
                    str(r + 1),
                    combined_name(row.name_ar, row.name_es),
                    str(row.qty_sold),
                    str(row.current_stock),
                    f"{pct}%",
                ],
            )
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _on_export_csv(self) -> None:
        if self._current_report is None:
            return
        path, _ = QFileDialog.getSaveFileName(self, t("common.export_csv"), "reporte.csv", "CSV (*.csv)")
        if not path:
            return

        with guarded(self):
            with open(path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(
                    [
                        t("products.column_id"),
                        t("reports.column_item"),
                        t("reports.column_purchased"),
                        t("reports.column_sold"),
                        t("reports.column_current_stock"),
                        t("reports.column_purchase_unit"),
                        t("reports.column_purchase_total"),
                        t("reports.column_current_avg_cost"),
                        t("reports.column_sell_unit"),
                        t("reports.column_sell_total"),
                        t("reports.column_profit"),
                        t("reports.column_inventory_value"),
                    ]
                )
                for row in self._current_report.rows:
                    writer.writerow(
                        [
                            row.item_id,
                            combined_name(row.name_ar, row.name_es),
                            row.qty_purchased,
                            row.qty_sold,
                            row.current_stock,
                            self.context.format_money(row.purchase_unit_price)
                            if row.purchase_unit_price is not None
                            else "",
                            self.context.format_money(row.purchase_total),
                            self.context.format_money(row.current_avg_cost),
                            self.context.format_money(row.sell_unit_price),
                            self.context.format_money(row.sell_total),
                            self.context.format_money(row.profit),
                            self.context.format_money(row.inventory_value),
                        ]
                    )
            show_info(self, t("reports.export_success", path=path))
