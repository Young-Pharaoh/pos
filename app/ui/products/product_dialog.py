"""Create/Edit product dialog.

Purchase price and initial stock are only editable when creating a new
product. In edit mode those two controls are disabled and a note points
the user at "Add Stock" instead -- this is the UI-level enforcement of the
spec's "do not directly manipulate stock/purchase price" rule; the service
layer enforces the same rule structurally by not accepting those
parameters in ``update_item``.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from app.i18n import t
from app.services.inventory_service import ItemView
from app.ui.app_context import AppContext
from app.ui.widgets.common import guarded
from app.ui.widgets.image_view import ImageView
from app.utils.images import delete_item_image, save_item_image


class ProductDialog(QDialog):
    def __init__(self, context: AppContext, item: ItemView | None = None, parent=None):
        super().__init__(parent)
        self.context = context
        self.item = item
        self.result_item: ItemView | None = None
        self._pending_image_source: str | None = None
        self._image_removed = False

        self._build_ui()
        self.retranslate()
        if item is not None:
            self._load_item(item)
        else:
            self._load_defaults()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_ar_edit = QLineEdit()
        self.name_ar_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.name_ar_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.name_es_edit = QLineEdit()

        self.purchase_price_spin = QDoubleSpinBox()
        self.purchase_price_spin.setRange(0, 1_000_000)
        self.purchase_price_spin.setDecimals(2)

        self.sell_price_spin = QDoubleSpinBox()
        self.sell_price_spin.setRange(0, 1_000_000)
        self.sell_price_spin.setDecimals(2)

        self.initial_stock_spin = QSpinBox()
        self.initial_stock_spin.setRange(0, 1_000_000)

        self.name_ar_label = QLabel()
        self.name_es_label = QLabel()
        self.purchase_price_label = QLabel()
        self.sell_price_label = QLabel()
        self.initial_stock_label = QLabel()

        form.addRow(self.name_ar_label, self.name_ar_edit)
        form.addRow(self.name_es_label, self.name_es_edit)
        form.addRow(self.purchase_price_label, self.purchase_price_spin)
        form.addRow(self.sell_price_label, self.sell_price_spin)
        form.addRow(self.initial_stock_label, self.initial_stock_spin)
        layout.addLayout(form)

        image_layout = QHBoxLayout()
        self.image_view = ImageView(size=100)
        image_layout.addWidget(self.image_view)
        image_buttons = QVBoxLayout()
        self.choose_image_button = QPushButton()
        self.choose_image_button.clicked.connect(self._choose_image)
        self.remove_image_button = QPushButton()
        self.remove_image_button.clicked.connect(self._remove_image)
        image_buttons.addWidget(self.choose_image_button)
        image_buttons.addWidget(self.remove_image_button)
        image_buttons.addStretch()
        image_layout.addLayout(image_buttons)
        image_layout.addStretch()
        layout.addLayout(image_layout)

        self.note_label = QLabel()
        self.note_label.setWordWrap(True)
        self.note_label.setStyleSheet("color: #806b00; font-style: italic;")
        layout.addWidget(self.note_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        if self.item is not None:
            self.purchase_price_spin.setEnabled(False)
            self.initial_stock_spin.setEnabled(False)

    def retranslate(self) -> None:
        self.setWindowTitle(
            t("product_dialog.title_edit") if self.item else t("product_dialog.title_new")
        )
        self.name_ar_label.setText(t("product_dialog.name_ar"))
        self.name_es_label.setText(t("product_dialog.name_es"))
        self.purchase_price_label.setText(t("product_dialog.purchase_price"))
        self.sell_price_label.setText(t("product_dialog.sell_price"))
        self.initial_stock_label.setText(t("product_dialog.initial_stock"))
        self.choose_image_button.setText(t("common.choose_image"))
        self.remove_image_button.setText(t("common.remove_image"))
        self.note_label.setText(t("product_dialog.note_locked_fields"))
        self.note_label.setVisible(self.item is not None)
        self.button_box.button(QDialogButtonBox.StandardButton.Save).setText(t("common.save"))
        self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(t("common.cancel"))

    def _load_item(self, item: ItemView) -> None:
        self.name_ar_edit.setText(item.name_ar)
        self.name_es_edit.setText(item.name_es)
        self.purchase_price_spin.setValue(float(item.purchase_price))
        self.sell_price_spin.setValue(float(item.sell_price))
        self.initial_stock_spin.setValue(item.stock)
        self.image_view.set_image(item.image_path)

    def _load_defaults(self) -> None:
        self.purchase_price_spin.setValue(0.0)
        self.sell_price_spin.setValue(float(self.context.settings.default_sell_price))
        self.initial_stock_spin.setValue(0)

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, t("common.choose_image"), "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        self._pending_image_source = path
        self._image_removed = False
        self.image_view.setText("")
        self.image_view.setPixmap(
            pixmap.scaled(
                self.image_view.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _remove_image(self) -> None:
        self._pending_image_source = None
        self._image_removed = True
        self.image_view.set_image(None)

    def _on_save(self) -> None:
        name_ar = self.name_ar_edit.text()
        name_es = self.name_es_edit.text()
        sell_price = Decimal(str(self.sell_price_spin.value()))

        with guarded(self):
            if self.item is None:
                purchase_price = Decimal(str(self.purchase_price_spin.value()))
                initial_stock = self.initial_stock_spin.value()
                created = self.context.inventory_service.create_item(
                    name_ar=name_ar,
                    name_es=name_es,
                    purchase_price=purchase_price,
                    sell_price=sell_price,
                    initial_stock=initial_stock,
                )
                item_id = created.id
                previous_image = None
            else:
                updated = self.context.inventory_service.update_item(
                    self.item.id, name_ar=name_ar, name_es=name_es, sell_price=sell_price
                )
                item_id = updated.id
                previous_image = self.item.image_path

            if self._image_removed:
                delete_item_image(previous_image)
                self.context.inventory_service.update_item(item_id, image_path=None)
            elif self._pending_image_source:
                relative_path = save_item_image(self._pending_image_source, item_id)
                self.context.inventory_service.update_item(item_id, image_path=relative_path)

            self.result_item = self.context.inventory_service.get_item(item_id)
            self.accept()
