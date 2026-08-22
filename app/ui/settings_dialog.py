"""Settings dialog: the few values the spec asks not to hard-code
(low-stock threshold, default sell price, currency symbol).

Interface language is switched from the header toggle in
:class:`app.ui.main_window.MainWindow`, not duplicated here.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QVBoxLayout,
)

from app.i18n import t
from app.ui.app_context import AppContext
from app.ui.widgets.common import guarded


class SettingsDialog(QDialog):
    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self._build_ui()
        self.retranslate()
        self._load_current()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(0, 1_000_000)

        self.default_sell_price_spin = QDoubleSpinBox()
        self.default_sell_price_spin.setRange(0, 1_000_000)
        self.default_sell_price_spin.setDecimals(2)

        self.currency_edit = QLineEdit()
        self.currency_edit.setMaxLength(5)

        self.threshold_label = QLabel()
        self.default_sell_price_label = QLabel()
        self.currency_label = QLabel()

        form.addRow(self.threshold_label, self.threshold_spin)
        form.addRow(self.default_sell_price_label, self.default_sell_price_spin)
        form.addRow(self.currency_label, self.currency_edit)
        layout.addLayout(form)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def retranslate(self) -> None:
        self.setWindowTitle(t("settings.title"))
        self.threshold_label.setText(t("settings.low_stock_threshold"))
        self.default_sell_price_label.setText(t("settings.default_sell_price"))
        self.currency_label.setText(t("settings.currency_symbol"))
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(t("common.save"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))

    def _load_current(self) -> None:
        settings = self.context.settings
        self.threshold_spin.setValue(settings.low_stock_threshold)
        self.default_sell_price_spin.setValue(float(settings.default_sell_price))
        self.currency_edit.setText(settings.currency_symbol)

    def _on_save(self) -> None:
        with guarded(self):
            self.context.settings_service.update_many(
                {
                    "low_stock_threshold": str(self.threshold_spin.value()),
                    "default_sell_price": str(Decimal(str(self.default_sell_price_spin.value()))),
                    "currency_symbol": self.currency_edit.text().strip() or "$",
                }
            )
            self.context.refresh_settings()
            self.accept()
