"""The application shell: header, four-way navigation, and menus.

Matches the spec's suggested layout (section 3): a title bar, a row of
nav buttons over a ``QStackedWidget``, and a status bar. ``Ctrl+1..4``
jump directly between pages for keyboard-first use.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.i18n import LANGUAGES, is_rtl, language_display_name, set_language, t, text_scale_display_name
from app.services.backup_service import backup_database
from app.services.settings_service import LANGUAGE_KEY, TEXT_SCALE_KEY
from app.ui.app_context import AppContext
from app.ui.dashboard.dashboard_page import DashboardPage
from app.ui.products.products_page import ProductsPage
from app.ui.reports.reports_page import ReportsPage
from app.ui.sales.sales_page import SalesPage
from app.ui.settings_dialog import SettingsDialog
from app.text_scale import (
    TEXT_SCALE_PRESETS,
    app_title_stylesheet,
    apply_to_application,
    nav_button_min_height,
    normalize_text_scale,
    window_size_for_preset,
)
from app.ui.widgets.common import guarded, show_error, show_info
from app.utils.paths import get_db_path


class MainWindow(QMainWindow):
    def __init__(self, context: AppContext):
        super().__init__()
        self.context = context
        self.resize(1150, 740)

        self.dashboard_page = DashboardPage(self.context)
        self.products_page = ProductsPage(self.context)
        self.sales_page = SalesPage(self.context)
        self.reports_page = ReportsPage(self.context)

        self._build_ui()
        self._apply_language(self.context.settings.language)
        self._apply_text_scale(self.context.settings.text_scale)

    def _build_ui(self) -> None:
        central = QWidget()
        root_layout = QVBoxLayout(central)

        header_layout = QHBoxLayout()
        self.title_label = QLabel()
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        self.text_scale_label = QLabel()
        header_layout.addWidget(self.text_scale_label)
        self.text_scale_combo = QComboBox()
        for preset in TEXT_SCALE_PRESETS:
            self.text_scale_combo.addItem(text_scale_display_name(preset), preset)
        self.text_scale_combo.currentIndexChanged.connect(self._on_text_scale_changed)
        header_layout.addWidget(self.text_scale_combo)
        self.language_combo = QComboBox()
        for lang in LANGUAGES:
            self.language_combo.addItem(language_display_name(lang), lang)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        header_layout.addWidget(self.language_combo)
        root_layout.addLayout(header_layout)

        nav_layout = QHBoxLayout()
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.stack = QStackedWidget()
        self.nav_buttons: dict[str, QPushButton] = {}

        pages = [
            ("dashboard", self.dashboard_page, "Ctrl+1"),
            ("products", self.products_page, "Ctrl+2"),
            ("new_sale", self.sales_page, "Ctrl+3"),
            ("reports", self.reports_page, "Ctrl+4"),
        ]
        for key, page, shortcut in pages:
            index = self.stack.addWidget(page)
            button = QPushButton()
            button.setCheckable(True)
            button.setMinimumHeight(48)
            button.setShortcut(QKeySequence(shortcut))
            button.clicked.connect(lambda _checked=False, i=index: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(button)
            nav_layout.addWidget(button)
            self.nav_buttons[key] = button
        self.nav_buttons["dashboard"].setChecked(True)

        root_layout.addLayout(nav_layout)
        root_layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self.stack.currentChanged.connect(self._on_page_changed)

        self._build_menu()

        self.db_status_label = QLabel()
        self.statusBar().addWidget(self.db_status_label)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()

        self.file_menu = menu_bar.addMenu("")
        self.backup_action = QAction(self)
        self.backup_action.triggered.connect(self._on_backup)
        self.settings_action = QAction(self)
        self.settings_action.triggered.connect(self._on_settings)
        self.exit_action = QAction(self)
        self.exit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.backup_action)
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.help_menu = menu_bar.addMenu("")
        self.about_action = QAction(self)
        self.about_action.triggered.connect(self._on_about)
        self.help_menu.addAction(self.about_action)

    def _on_text_scale_changed(self) -> None:
        preset = self.text_scale_combo.currentData()
        if preset is None:
            return
        self._apply_text_scale(preset)
        with guarded(self):
            self.context.settings_service.set(TEXT_SCALE_KEY, preset)
            self.context.refresh_settings()

    def _apply_text_scale(self, preset: str) -> None:
        preset = normalize_text_scale(preset)
        app = QApplication.instance()
        if app is not None:
            apply_to_application(app, preset)

        self.title_label.setStyleSheet(app_title_stylesheet(preset))
        for button in self.nav_buttons.values():
            button.setMinimumHeight(nav_button_min_height(preset))

        target_width, target_height = window_size_for_preset(preset)
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            target_width = min(target_width, available.width())
            target_height = min(target_height, available.height())
        if self.width() < target_width or self.height() < target_height:
            self.resize(
                max(self.width(), target_width),
                max(self.height(), target_height),
            )

        self.dashboard_page.apply_text_scale(preset)
        self.products_page.apply_text_scale(preset)
        self.sales_page.apply_text_scale(preset)
        self.reports_page.apply_text_scale(preset)

        index = self.text_scale_combo.findData(preset)
        if index >= 0:
            self.text_scale_combo.blockSignals(True)
            self.text_scale_combo.setCurrentIndex(index)
            self.text_scale_combo.blockSignals(False)

    def _populate_text_scale_combo(self) -> None:
        current = self.text_scale_combo.currentData()
        self.text_scale_combo.blockSignals(True)
        self.text_scale_combo.clear()
        for preset in TEXT_SCALE_PRESETS:
            self.text_scale_combo.addItem(text_scale_display_name(preset), preset)
        if current is not None:
            index = self.text_scale_combo.findData(current)
            if index >= 0:
                self.text_scale_combo.setCurrentIndex(index)
        self.text_scale_combo.blockSignals(False)

    def _on_language_changed(self) -> None:
        lang = self.language_combo.currentData()
        if lang is None:
            return
        self._apply_language(lang)
        with guarded(self):
            self.context.settings_service.set(LANGUAGE_KEY, lang)
            self.context.refresh_settings()

    def _apply_language(self, lang: str) -> None:
        set_language(lang)
        app = QApplication.instance()
        if app is not None:
            app.setLayoutDirection(
                Qt.LayoutDirection.RightToLeft if is_rtl(lang) else Qt.LayoutDirection.LeftToRight
            )
        index = self.language_combo.findData(lang)
        if index >= 0:
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(index)
            self.language_combo.blockSignals(False)
        self.retranslate()

    def retranslate(self) -> None:
        self.setWindowTitle(t("app.title"))
        self.title_label.setText(t("app.title"))
        self.nav_buttons["dashboard"].setText(t("nav.dashboard"))
        self.nav_buttons["products"].setText(t("nav.products"))
        self.nav_buttons["new_sale"].setText(t("nav.new_sale"))
        self.nav_buttons["reports"].setText(t("nav.reports"))

        self.file_menu.setTitle(t("menu.file"))
        self.backup_action.setText(t("menu.backup"))
        self.settings_action.setText(t("menu.settings"))
        self.exit_action.setText(t("menu.exit"))
        self.help_menu.setTitle(t("menu.help"))
        self.about_action.setText(t("menu.about"))
        self.text_scale_label.setText(t("menu.text_scale"))
        self._populate_text_scale_combo()

        self.db_status_label.setText(t("status.db_path", path=str(get_db_path())))

        self.dashboard_page.retranslate()
        self.products_page.retranslate()
        self.sales_page.retranslate()
        self.reports_page.retranslate()

    def _on_page_changed(self, index: int) -> None:
        widget = self.stack.widget(index)
        if widget is self.dashboard_page:
            self.dashboard_page.refresh()
        elif widget is self.products_page:
            self.products_page.refresh()
        elif widget is self.sales_page:
            self.sales_page.focus_entry()
        elif widget is self.reports_page:
            self.reports_page.refresh()

    def _on_backup(self) -> None:
        try:
            backup_path = backup_database()
        except Exception as exc:  # pragma: no cover - defensive
            show_error(self, t("menu.backup_failed", detail=str(exc)))
            return
        show_info(self, t("menu.backup_done", path=str(backup_path)))

    def _on_settings(self) -> None:
        dialog = SettingsDialog(self.context, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            show_info(self, t("settings.saved"))
            self.dashboard_page.refresh()

    def _on_about(self) -> None:
        QMessageBox.information(
            self, t("menu.about"), t("menu.about_text", db_path=str(get_db_path()))
        )
