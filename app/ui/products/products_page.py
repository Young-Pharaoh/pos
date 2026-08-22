"""Products screen: catalog table, unified search, and product actions."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.i18n import t
from app.services.inventory_service import ItemView
from app.ui.app_context import AppContext
from app.ui.products.add_stock_dialog import AddStockDialog
from app.ui.products.product_dialog import ProductDialog
from app.ui.widgets.common import combined_name, confirm, guarded, show_error, show_info
from app.ui.widgets.image_view import ImageView

_COLUMN_COUNT = 8


class ProductsPage(QWidget):
    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self._items: list[ItemView] = []
        self._build_ui()
        self.retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.title_label)

        search_layout = QHBoxLayout()
        self.search_label = QLabel()
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(lambda _: self.refresh())
        self.show_archived_checkbox = QCheckBox()
        self.show_archived_checkbox.stateChanged.connect(lambda _: self.refresh())
        search_layout.addWidget(self.search_label)
        search_layout.addWidget(self.search_edit, 1)
        search_layout.addWidget(self.show_archived_checkbox)
        layout.addLayout(search_layout)

        content_layout = QHBoxLayout()
        self.table = QTableWidget(0, _COLUMN_COUNT)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        content_layout.addWidget(self.table, 3)

        detail_layout = QVBoxLayout()
        self.detail_image = ImageView(size=160)
        detail_layout.addWidget(self.detail_image, alignment=Qt.AlignmentFlag.AlignHCenter)
        detail_layout.addStretch()
        content_layout.addLayout(detail_layout, 1)
        layout.addLayout(content_layout, 1)

        buttons_layout = QHBoxLayout()
        self.new_button = QPushButton()
        self.edit_button = QPushButton()
        self.add_stock_button = QPushButton()
        self.archive_button = QPushButton()
        self.delete_button = QPushButton()
        for btn in (
            self.new_button,
            self.edit_button,
            self.add_stock_button,
            self.archive_button,
            self.delete_button,
        ):
            btn.setMinimumHeight(36)
            buttons_layout.addWidget(btn)
        layout.addLayout(buttons_layout)

        self.new_button.clicked.connect(self._on_new)
        self.edit_button.clicked.connect(self._on_edit)
        self.add_stock_button.clicked.connect(self._on_add_stock)
        self.archive_button.clicked.connect(self._on_archive_or_restore)
        self.delete_button.clicked.connect(self._on_delete)

    def retranslate(self) -> None:
        self.title_label.setText(t("products.title"))
        self.search_label.setText(t("common.search"))
        self.search_edit.setPlaceholderText(t("products.search_placeholder"))
        self.show_archived_checkbox.setText(t("common.archived"))
        self.table.setHorizontalHeaderLabels(
            [
                t("products.column_id"),
                t("products.column_name_ar"),
                t("products.column_name_es"),
                t("products.column_stock"),
                t("products.column_avg_cost"),
                t("products.column_sell_price"),
                t("products.column_inventory_value"),
                t("products.column_status"),
            ]
        )
        self.new_button.setText(t("products.button_new"))
        self.edit_button.setText(t("products.button_edit"))
        self.add_stock_button.setText(t("products.button_add_stock"))
        self.delete_button.setText(t("products.button_delete"))
        self.refresh()

    def refresh(self) -> None:
        query = self.search_edit.text()
        include_archived = self.show_archived_checkbox.isChecked()
        if query.strip():
            self._items = self.context.inventory_service.search_items(
                query, include_archived=include_archived
            )
        else:
            self._items = self.context.inventory_service.list_items(
                include_archived=include_archived
            )
        self._populate_table()
        self._update_action_buttons()

    def _populate_table(self) -> None:
        self.table.setRowCount(len(self._items))
        for row, item in enumerate(self._items):
            values = [
                str(item.id),
                item.name_ar,
                item.name_es,
                str(item.stock),
                self.context.format_money(item.purchase_price),
                self.context.format_money(item.sell_price),
                self.context.format_money(item.inventory_value),
                t("products.status_active") if item.is_active else t("products.status_archived"),
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 1:
                    cell.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _selected_item(self) -> ItemView | None:
        selection_model = self.table.selectionModel()
        if selection_model is None:
            return None
        rows = selection_model.selectedRows()
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def _on_selection_changed(self) -> None:
        self._update_action_buttons()

    def _update_action_buttons(self) -> None:
        item = self._selected_item()
        self.detail_image.set_image(item.image_path if item else None)

        has_selection = item is not None
        self.edit_button.setEnabled(has_selection)
        self.add_stock_button.setEnabled(has_selection and item.is_active)
        self.delete_button.setEnabled(has_selection)

        if item is None:
            self.archive_button.setEnabled(False)
            self.archive_button.setText(t("products.button_archive"))
            return

        self.archive_button.setEnabled(True)
        self.archive_button.setText(
            t("products.button_restore") if not item.is_active else t("products.button_archive")
        )

    def _on_new(self) -> None:
        dialog = ProductDialog(self.context, item=None, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_edit(self) -> None:
        item = self._selected_item()
        if item is None:
            show_error(self, t("products.no_selection"))
            return
        dialog = ProductDialog(self.context, item=item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _on_add_stock(self) -> None:
        item = self._selected_item()
        if item is None:
            show_error(self, t("products.no_selection"))
            return
        dialog = AddStockDialog(self.context, item=item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_info(self, t("add_stock_dialog.success"))
            self.refresh()

    def _on_archive_or_restore(self) -> None:
        item = self._selected_item()
        if item is None:
            return
        with guarded(self):
            if item.is_active:
                self.context.inventory_service.archive_item(item.id)
                show_info(self, t("products.archived_message"))
            else:
                self.context.inventory_service.restore_item(item.id)
                show_info(self, t("products.restored_message"))
            self.refresh()

    def _on_delete(self) -> None:
        item = self._selected_item()
        if item is None:
            show_error(self, t("products.no_selection"))
            return

        name = combined_name(item.name_ar, item.name_es)
        if not self.context.inventory_service.can_delete(item.id):
            if confirm(
                self,
                t("products.confirm_archive_message", name=name),
                title=t("products.confirm_archive_title"),
            ):
                with guarded(self):
                    self.context.inventory_service.archive_item(item.id)
                    show_info(self, t("products.archived_message"))
                    self.refresh()
            return

        if confirm(
            self,
            t("products.confirm_delete_message", name=name),
            title=t("products.confirm_delete_title"),
        ):
            with guarded(self):
                self.context.inventory_service.delete_item(item.id)
                show_info(self, t("products.deleted_message"))
                self.refresh()
