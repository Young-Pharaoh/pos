"""Add Stock dialog (spec sections 7 and 9).

The preview (current stock/price, resulting stock/average) is recomputed
live from ``InventoryService.preview_add_stock``, which performs no
writes. If the entered price differs from the registered one, confirming
raises the price-change dialog; cancelling that dialog -- or this one --
leaves the database untouched, since ``add_stock`` (the only method that
writes) is only called after the user explicitly confirms.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from app.errors import AppError
from app.i18n import t
from app.services.inventory_service import AddStockPreview, ItemView
from app.ui.app_context import AppContext
from app.ui.widgets.common import combined_name, confirm, guarded


class AddStockDialog(QDialog):
    def __init__(self, context: AppContext, item: ItemView, parent=None):
        super().__init__(parent)
        self.context = context
        self.item = item
        self.result_item: ItemView | None = None
        self._preview: AddStockPreview | None = None

        self._build_ui()
        self.retranslate()
        self._update_preview()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.current_stock_label = QLabel()
        self.current_price_label = QLabel()
        layout.addWidget(self.current_stock_label)
        layout.addWidget(self.current_price_label)

        form = QFormLayout()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1_000_000)
        self.quantity_spin.valueChanged.connect(self._update_preview)

        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setRange(0, 1_000_000)
        self.unit_price_spin.setDecimals(2)
        self.unit_price_spin.setValue(float(self.item.purchase_price))
        self.unit_price_spin.valueChanged.connect(self._update_preview)

        self.quantity_label = QLabel()
        self.unit_price_label = QLabel()
        form.addRow(self.quantity_label, self.quantity_spin)
        form.addRow(self.unit_price_label, self.unit_price_spin)
        layout.addLayout(form)

        self.preview_stock_label = QLabel()
        self.preview_average_label = QLabel()
        self.preview_stock_label.setStyleSheet("font-weight: 600;")
        self.preview_average_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.preview_stock_label)
        layout.addWidget(self.preview_average_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_confirm)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def retranslate(self) -> None:
        name = combined_name(self.item.name_ar, self.item.name_es)
        self.setWindowTitle(t("add_stock_dialog.title", name=name))
        self.current_stock_label.setText(t("add_stock_dialog.current_stock", stock=self.item.stock))
        self.current_price_label.setText(
            t("add_stock_dialog.current_price", price=self.context.format_money(self.item.purchase_price))
        )
        self.quantity_label.setText(t("add_stock_dialog.quantity"))
        self.unit_price_label.setText(t("add_stock_dialog.unit_price"))
        self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(t("common.continue"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))
        self._update_preview()

    def _update_preview(self) -> None:
        try:
            self._preview = self.context.inventory_service.preview_add_stock(
                self.item.id,
                self.quantity_spin.value(),
                Decimal(str(self.unit_price_spin.value())),
            )
        except AppError:
            self._preview = None
            self.preview_stock_label.setText("")
            self.preview_average_label.setText("")
            return

        self.preview_stock_label.setText(
            t("add_stock_dialog.preview_new_stock", stock=self._preview.new_stock)
        )
        self.preview_average_label.setText(
            t(
                "add_stock_dialog.preview_new_average",
                price=self.context.format_money(self._preview.new_average_price),
            )
        )

    def _on_confirm(self) -> None:
        preview = self._preview
        if preview is None:
            return

        if preview.price_changed:
            message = t(
                "add_stock_dialog.confirm_price_change_message",
                old_price=self.context.format_money(preview.current_price),
                new_price=self.context.format_money(preview.new_unit_price),
                new_average=self.context.format_money(preview.new_average_price),
            )
            if not confirm(
                self, message, title=t("add_stock_dialog.confirm_price_change_title")
            ):
                return  # Cancelled: no stock/database changes happen.

        with guarded(self):
            self.result_item = self.context.inventory_service.add_stock(
                self.item.id,
                self.quantity_spin.value(),
                Decimal(str(self.unit_price_spin.value())),
            )
            self.accept()
