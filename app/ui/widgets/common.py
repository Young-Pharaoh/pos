"""Shared dialog helpers so pages don't hand-roll QMessageBox calls.

``guarded`` is the standard way a button handler calls into a service: it
converts an ``AppError`` into the translated, friendly message the spec
requires (section 26/29), and never lets a raw exception or traceback
reach the user.
"""

from __future__ import annotations

from contextlib import contextmanager

from PySide6.QtWidgets import QMessageBox, QWidget

from app.errors import AppError
from app.i18n import get_language, t
from app.logging_setup import get_logger

logger = get_logger("ui")


def display_name(name_ar: str, name_es: str) -> str:
    """The name in the current interface language, used where space is tight."""
    return name_ar if get_language() == "ar" else name_es


def combined_name(name_ar: str, name_es: str) -> str:
    """Both names together, for lists where showing only one would hide data
    the shop owner may need (spec: product/sales screens must show both)."""
    return f"{name_es} / {name_ar}"


def show_error(parent: QWidget, message: str, title: str | None = None) -> None:
    QMessageBox.critical(parent, title or t("common.error"), message)


def show_info(parent: QWidget, message: str, title: str | None = None) -> None:
    QMessageBox.information(parent, title or t("common.success"), message)


def confirm(parent: QWidget, message: str, title: str | None = None) -> bool:
    result = QMessageBox.question(
        parent,
        title or t("common.confirm"),
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes


@contextmanager
def guarded(parent: QWidget, *, on_error=None):
    """Run a UI action, turning AppError/unexpected errors into a dialog.

    Never lets a raw database exception or traceback reach the user. If
    ``on_error`` is given, it is called (instead of nothing) after the
    dialog is dismissed, so callers can e.g. abort a wizard step.
    """
    try:
        yield
    except AppError as exc:
        logger.info("Business rule blocked action: %s %s", exc.message_key, exc.params)
        show_error(parent, t(exc.message_key, **exc.params))
        if on_error:
            on_error()
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.exception("Unexpected error in UI action")
        show_error(parent, t("error.unexpected", detail=str(exc)))
        if on_error:
            on_error()
