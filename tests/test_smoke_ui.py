"""End-to-end offscreen smoke test: build the real MainWindow against a
real (temp-file) database and drive it through the Definition-of-Done
workflow (spec section 39) using its actual widgets, not mocks.

QMessageBox popups are patched to auto-accept, since a real modal dialog
would otherwise block the test waiting for a user click that never comes.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QDialog, QDialogButtonBox, QMessageBox

from app.i18n import get_language
from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow
from app.ui.products.add_stock_dialog import AddStockDialog
from app.ui.products.product_dialog import ProductDialog
from app.ui.sales.sales_page import SalesPage


@pytest.fixture(autouse=True)
def _auto_accept_message_boxes(monkeypatch):
    monkeypatch.setattr(
        QMessageBox, "information", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
    )
    monkeypatch.setattr(
        QMessageBox, "critical", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Ok)
    )
    monkeypatch.setattr(
        QMessageBox, "question", staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
    )


def test_main_window_constructs_and_navigates_every_page(qtbot, session_factory):
    context = AppContext.build(session_factory)
    window = MainWindow(context)
    qtbot.addWidget(window)

    for index in range(4):
        window.stack.setCurrentIndex(index)
        assert window.stack.currentIndex() == index


def test_language_toggle_switches_layout_direction(qtbot, session_factory):
    context = AppContext.build(session_factory)
    window = MainWindow(context)
    qtbot.addWidget(window)

    ar_index = window.language_combo.findData("ar")
    window.language_combo.setCurrentIndex(ar_index)
    assert get_language() == "ar"
    assert QApplication.instance().layoutDirection() == Qt.LayoutDirection.RightToLeft

    es_index = window.language_combo.findData("es")
    window.language_combo.setCurrentIndex(es_index)
    assert get_language() == "es"
    assert QApplication.instance().layoutDirection() == Qt.LayoutDirection.LeftToRight


def test_text_scale_combo_persists_and_increases_font(qtbot, session_factory):
    from app.services.settings_service import TEXT_SCALE_KEY
    from app.text_scale import TEXT_SCALE_EXTRA_LARGE, TEXT_SCALE_NORMAL

    context = AppContext.build(session_factory)
    window = MainWindow(context)
    qtbot.addWidget(window)

    normal_font = QApplication.instance().font().pointSizeF()
    assert window.text_scale_combo.currentData() == TEXT_SCALE_NORMAL

    extra_large_index = window.text_scale_combo.findData(TEXT_SCALE_EXTRA_LARGE)
    window.text_scale_combo.setCurrentIndex(extra_large_index)

    assert QApplication.instance().font().pointSizeF() > normal_font
    assert context.settings_service.get(TEXT_SCALE_KEY) == TEXT_SCALE_EXTRA_LARGE

    normal_index = window.text_scale_combo.findData(TEXT_SCALE_NORMAL)
    window.text_scale_combo.setCurrentIndex(normal_index)
    assert QApplication.instance().font().pointSizeF() == normal_font
    assert context.settings_service.get(TEXT_SCALE_KEY) == TEXT_SCALE_NORMAL


def test_create_product_via_dialog_and_see_it_in_products_table(qtbot, session_factory):
    context = AppContext.build(session_factory)
    window = MainWindow(context)
    qtbot.addWidget(window)
    window.stack.setCurrentWidget(window.products_page)

    # Constructing the dialog directly (rather than calling
    # products_page._on_new(), which calls the blocking QDialog.exec())
    # avoids a nested event loop inside the test.
    dialog = ProductDialog(context, item=None, parent=window.products_page)
    qtbot.addWidget(dialog)
    dialog.name_ar_edit.setText("\u0634\u0627\u0645\u0628\u0648")
    dialog.name_es_edit.setText("Champu")
    dialog.purchase_price_spin.setValue(0.70)
    dialog.sell_price_spin.setValue(1.00)
    dialog.initial_stock_spin.setValue(10)

    save_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Save)
    qtbot.mouseClick(save_button, Qt.MouseButton.LeftButton)

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.result_item is not None
    assert dialog.result_item.stock == 10

    window.products_page.refresh()
    assert window.products_page.table.rowCount() == 1
    assert window.products_page.table.item(0, 2).text() == "Champu"


def test_add_stock_dialog_price_change_flow(qtbot, session_factory):
    context = AppContext.build(session_factory)
    item = context.inventory_service.create_item(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        initial_stock=100,
    )

    dialog = AddStockDialog(context, item=item)
    qtbot.addWidget(dialog)
    dialog.quantity_spin.setValue(50)
    dialog.unit_price_spin.setValue(0.80)

    ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
    qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)

    assert dialog.result() == QDialog.DialogCode.Accepted
    assert dialog.result_item.stock == 150
    assert dialog.result_item.purchase_price == Decimal("0.7333")


def test_sales_page_full_keyboard_flow_completes_a_sale(qtbot, session_factory):
    context = AppContext.build(session_factory)
    item = context.inventory_service.create_item(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        initial_stock=10,
    )

    page = SalesPage(context)
    qtbot.addWidget(page)

    page.item_edit.setText(str(item.id))
    qtbot.keyClick(page.item_edit, Qt.Key.Key_Return)
    assert page._pending_snapshot is not None
    assert page._pending_snapshot.id == item.id

    page.quantity_spin.setValue(3)
    qtbot.keyClick(page.quantity_spin.lineEdit(), Qt.Key.Key_Return)

    assert len(page.draft.lines) == 1
    assert page.draft.lines[0].quantity == 3
    assert page.table.rowCount() == 1

    qtbot.mouseClick(page.complete_button, Qt.MouseButton.LeftButton)

    assert page.draft.is_empty
    assert page.table.rowCount() == 0

    updated = context.inventory_service.get_item(item.id)
    assert updated.stock == 7


def test_sales_page_merges_duplicate_entries_in_the_table(qtbot, session_factory):
    context = AppContext.build(session_factory)
    item = context.inventory_service.create_item(
        name_ar="\u0635\u0627\u0628\u0648\u0646",
        name_es="Jabon",
        purchase_price=Decimal("0.50"),
        sell_price=Decimal("1.00"),
        initial_stock=10,
    )
    page = SalesPage(context)
    qtbot.addWidget(page)

    for _ in range(2):
        page.item_edit.setText(str(item.id))
        qtbot.keyClick(page.item_edit, Qt.Key.Key_Return)
        page.quantity_spin.setValue(2)
        qtbot.keyClick(page.quantity_spin.lineEdit(), Qt.Key.Key_Return)

    assert len(page.draft.lines) == 1
    assert page.draft.lines[0].quantity == 4
    assert page.table.rowCount() == 1


def test_reports_page_generates_without_error(qtbot, session_factory):
    context = AppContext.build(session_factory)
    context.inventory_service.create_item(
        name_ar="\u0634\u0627\u0645\u0628\u0648",
        name_es="Champu",
        purchase_price=Decimal("0.70"),
        sell_price=Decimal("1.00"),
        initial_stock=10,
    )

    window = MainWindow(context)
    qtbot.addWidget(window)
    window.stack.setCurrentWidget(window.reports_page)
    window.reports_page._on_generate()

    assert window.reports_page.products_table.rowCount() >= 1


def test_full_definition_of_done_workflow_end_to_end(qtbot, session_factory):
    """Create -> add stock -> sell -> report, exactly as spec section 39
    describes, driven through the real widgets against a real database."""
    context = AppContext.build(session_factory)
    window = MainWindow(context)
    qtbot.addWidget(window)

    # Create product with initial stock.
    product_dialog = ProductDialog(context, item=None, parent=window)
    qtbot.addWidget(product_dialog)
    product_dialog.name_ar_edit.setText("\u0634\u0627\u0645\u0628\u0648")
    product_dialog.name_es_edit.setText("Champu")
    product_dialog.purchase_price_spin.setValue(0.70)
    product_dialog.sell_price_spin.setValue(1.00)
    product_dialog.initial_stock_spin.setValue(100)
    qtbot.mouseClick(
        product_dialog.button_box.button(QDialogButtonBox.StandardButton.Save),
        Qt.MouseButton.LeftButton,
    )
    item = product_dialog.result_item
    assert item.stock == 100

    # Add more stock at a different price -> weighted average recalculated.
    add_stock_dialog = AddStockDialog(context, item=item, parent=window)
    qtbot.addWidget(add_stock_dialog)
    add_stock_dialog.quantity_spin.setValue(50)
    add_stock_dialog.unit_price_spin.setValue(0.80)
    qtbot.mouseClick(
        add_stock_dialog.button_box.button(QDialogButtonBox.StandardButton.Ok),
        Qt.MouseButton.LeftButton,
    )
    restocked = add_stock_dialog.result_item
    assert restocked.stock == 150
    assert restocked.purchase_price == Decimal("0.7333")

    # Sell some units.
    window.stack.setCurrentWidget(window.sales_page)
    sales_page = window.sales_page
    sales_page.item_edit.setText(str(item.id))
    qtbot.keyClick(sales_page.item_edit, Qt.Key.Key_Return)
    sales_page.quantity_spin.setValue(40)
    qtbot.keyClick(sales_page.quantity_spin.lineEdit(), Qt.Key.Key_Return)
    qtbot.mouseClick(sales_page.complete_button, Qt.MouseButton.LeftButton)

    after_sale = context.inventory_service.get_item(item.id)
    assert after_sale.stock == 110  # 150 - 40

    # Report reflects it correctly.
    window.stack.setCurrentWidget(window.reports_page)
    window.reports_page._on_generate()
    report = window.reports_page._current_report
    row = next(r for r in report.rows if r.item_id == item.id)
    assert row.current_stock == 110
    assert row.qty_sold == 40
    assert row.profit == Decimal("10.6680")  # 40*(1.00 - 0.7333)
