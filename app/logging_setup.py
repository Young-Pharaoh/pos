"""Simple, single-file rotating log setup.

Deliberately minimal: one rotating log file plus a console handler when not
frozen. No structured logging, no external log shipping -- this is a local
desktop app for a single small shop.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from app.utils.paths import ensure_app_dirs, get_logs_dir

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_MAX_BYTES = 1_000_000
_BACKUP_COUNT = 3

_configured = False


def configure_logging() -> logging.Logger:
    """Configure application-wide logging. Safe to call more than once."""
    global _configured
    root = logging.getLogger("inventory_system")
    if _configured:
        return root

    ensure_app_dirs()
    root.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(
        get_logs_dir() / "app.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(file_handler)

    if not getattr(sys, "frozen", False):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(_LOG_FORMAT))
        root.addHandler(console_handler)

    def _log_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        root.critical(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = _log_unhandled_exception

    _configured = True
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"inventory_system.{name}")
