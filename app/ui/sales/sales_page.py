"""New Sale screen (spec sections 10-14): a keyboard-first checkout loop.

Nothing here touches the database until "Complete Sale" is pressed --
adding, editing, and removing lines only mutates the in-memory
``SaleDraft``. The two-step keyboard flow is: type an id/name and press
Enter (resolves and shows the product, moves focus to quantity), then
press Enter again in the quantity field (adds the line and returns focus
to the id field for the next scan).
"""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.i18n import t
from app.services.sale_draft import ItemSnapshot, SaleDraft
from app.ui.app_context import AppContext
from app.ui.widgets.common import combined_name, guarded, show_error, show_info

_QUANTITY_COLUMN = 2


class SalesPage(QWidget):
    def __init__(self, context: AppContext, parent=None):
        super().__init__(parent)
        self.context = context
        self.draft = SaleDraft()
        self._pending_snapshot: ItemSnapshot | None = None
        self._pending_query: str | None = None

        self._build_ui()
        self.retranslate()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(self.title_label)

        entry_layout = QHBoxLayout()
        self.item_label = QLabel()
        self.item_edit = QLineEdit()
        self.item_edit.returnPressed.connect(self._on_item_return_pressed)
        self.quantity_label = QLabel()
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 1_000_000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.lineEdit().returnPressed.connect(self._add_current_line)
        self.add_button = QPushButton()
        self.add_button.clicked.connect(self._add_current_line)
        entry_layout.addWidget(self.item_label)
        entry_layout.addWidget(self.item_edit, 2)
        entry_layout.addWidget(self.quantity_label)
        entry_layout.addWidget(self.quantity_spin)
        entry_layout.addWidget(self.add_button)
        layout.addLayout(entry_layout)

        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: #555555;")
        layout.addWidget(self.info_label)

        self.table = QTableWidget(0, 5)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.installEventFilter(self)
        layout.addWidget(self.table, 1)

        bottom_layout = QHBoxLayout()
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        bottom_layout.addWidget(self.total_label)
        bottom_layout.addStretch()
        self.complete_button = QPushButton()
        self.complete_button.setMinimumHeight(44)
        self.complete_button.setShortcut(QKeySequence("F12"))
        self.complete_button.clicked.connect(self._on_complete_sale)
        bottom_layout.addWidget(self.complete_button)
        layout.addLayout(bottom_layout)

    def retranslate(self) -> None:
        self.title_label.setText(t("sales.title"))
        self.item_label.setText(t("sales.item_field_label"))
        self.quantity_label.setText(t("sales.quantity_label"))
        self.add_button.setText(t("sales.button_add"))
        self.table.setHorizontalHeaderLabels(
            [
                t("sales.column_id"),
                t("sales.column_product"),
                t("sales.column_quantity"),
                t("sales.column_price"),
                t("sales.column_total"),
            ]
        )
        self.complete_button.setText(t("sales.button_complete_sale"))
        self._refresh_table()

    def focus_entry(self) -> None:
        self.item_edit.setFocus()
        self.item_edit.selectAll()

    def eventFilter(self, obj, event):  # noqa: N802 - Qt override signature
        if obj is self.table and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
                self._remove_selected_line()
                return True
        return super().eventFilter(obj, event)

    def _on_item_return_pressed(self) -> None:
        query = self.item_edit.text().strip()
        if not query:
            return
        with guarded(self):
            snapshot = self.context.sales_service.resolve_item(query)
            self._pending_snapshot = snapshot
            self._pending_query = query
            name = combined_name(snapshot.name_ar, snapshot.name_es)
            self.info_label.setText(
                t("sales.item_found_info", name=name, stock=snapshot.available_stock)
            )
            self.quantity_spin.setFocus()
            self.quantity_spin.selectAll()
            return
        self._pending_snapshot = None
        self._pending_query = None
        self.info_label.setText("")

    def _add_current_line(self) -> None:
        query = self.item_edit.text().strip()
        if not query:
            return
        added = False
        with guarded(self):
            if self._pending_snapshot is not None and self._pending_query == query:
                snapshot = self._pending_snapshot
            else:
                snapshot = self.context.sales_service.resolve_item(query)
            self.draft.add(snapshot, self.quantity_spin.value())
            added = True
        if added:
            self._refresh_table()
        self._reset_entry_fields()

    def _reset_entry_fields(self) -> None:
        self.item_edit.clear()
        self.quantity_spin.setValue(1)
        self._pending_snapshot = None
        self._pending_query = None
        self.info_label.setText("")
        self.item_edit.setFocus()

    def _on_cell_double_clicked(self, row: int, column: int) -> None:
        lines = self.draft.lines
        if not (0 <= row < len(lines)) or column != _QUANTITY_COLUMN:
            return
        line = lines[row]
        new_quantity, accepted = QInputDialog.getInt(
            self,
            t("sales.quantity_label"),
            t("sales.quantity_label"),
            line.quantity,
            1,
            line.item.available_stock,
            1,
        )
        if not accepted:
            return
        with guarded(self):
            self.draft.set_quantity(line.item.id, new_quantity)
        self._refresh_table()

    def _remove_selected_line(self) -> None:
        selection_model = self.table.selectionModel()
        if selection_model is None:
            return
        rows = selection_model.selectedRows()
        if not rows:
            return
        index = rows[0].row()
        lines = self.draft.lines
        if 0 <= index < len(lines):
            self.draft.remove(lines[index].item.id)
            self._refresh_table()

    def _refresh_table(self) -> None:
        lines = self.draft.lines
        self.table.setRowCount(len(lines))
        for row, line in enumerate(lines):
            values = [
                str(line.item.id),
                combined_name(line.item.name_ar, line.item.name_es),
                str(line.quantity),
                self.context.format_money(line.unit_sell_price),
                self.context.format_money(line.total_sell_price),
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, cell)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.total_label.setText(t("sales.total_label", total=self.context.format_money(self.draft.total)))

    def _on_complete_sale(self) -> None:
        if self.draft.is_empty:
            show_error(self, t("sales.empty_sale_message"))
            return
        with guarded(self):
            receipt = self.context.sales_service.complete_sale(self.draft)
            show_info(
                self,
                t("sales.sale_completed_message", sale_id=receipt.id, total=self.context.format_money(receipt.total)),
                title=t("sales.sale_completed_title"),
            )
            self.draft.clear()
            self._refresh_table()
            self._reset_entry_fields()
