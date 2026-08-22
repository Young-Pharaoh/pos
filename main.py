"""Inventory System entry point.

Run with: python main.py

Creates/opens ``store.db`` next to this script (or next to the frozen
executable when packaged), builds the service layer, and shows the main
window. See README.md for setup, testing, and packaging instructions.
"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from app.database.database import bootstrap_database
from app.i18n import set_language, t
from app.logging_setup import configure_logging
from app.ui.app_context import AppContext
from app.ui.main_window import MainWindow


def _install_qt_excepthook(logger) -> None:
    """Log unhandled exceptions and show a friendly dialog instead of
    letting the app crash silently or dump a traceback at the user."""

    def _handle(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        try:
            QMessageBox.critical(
                None, t("common.error"), t("error.unexpected", detail=str(exc_value))
            )
        except Exception:  # pragma: no cover - last-resort guard
            pass

    sys.excepthook = _handle


def main() -> int:
    logger = configure_logging()
    logger.info("Starting Inventory System")

    app = QApplication(sys.argv)
    app.setApplicationName("Inventory System")

    _install_qt_excepthook(logger)

    try:
        session_factory = bootstrap_database()
    except Exception:
        logger.exception("Failed to initialize database")
        QMessageBox.critical(
            None,
            "Error",
            "No se pudo inicializar la base de datos. Revise los registros (logs) para mas detalles.",
        )
        return 1

    context = AppContext.build(session_factory)
    set_language(context.settings.language)

    window = MainWindow(context)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
