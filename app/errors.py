"""Application error hierarchy.

Services never let raw database exceptions (``sqlalchemy.exc.*``,
``sqlite3.*``) escape to the UI. Instead they raise one of these
``AppError`` subclasses, carrying a translatable ``message_key`` plus the
parameters needed to fill it in, so the UI layer can render a friendly,
localized message via :mod:`app.i18n` without string-matching exception
text.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all errors intended to be shown to the user."""

    def __init__(self, message_key: str, **params):
        self.message_key = message_key
        self.params = params
        super().__init__(f"{message_key} {params}")


class ValidationError(AppError):
    """Raised when user-supplied input fails a business validation rule."""


class ItemNotFoundError(AppError):
    """Raised when an item id/lookup does not resolve to an active record."""

    def __init__(self, item_id):
        super().__init__("error.item_not_found", item_id=item_id)
        self.item_id = item_id


class ItemInactiveError(AppError):
    """Raised when a sale references an archived (inactive) item."""

    def __init__(self, item_id):
        super().__init__("error.item_inactive", item_id=item_id)
        self.item_id = item_id


class InsufficientStockError(AppError):
    """Raised when a requested quantity exceeds the available stock."""

    def __init__(self, item_id, requested, available):
        super().__init__(
            "error.insufficient_stock",
            item_id=item_id,
            requested=requested,
            available=available,
        )
        self.item_id = item_id
        self.requested = requested
        self.available = available


class DeletionNotAllowedError(AppError):
    """Raised when deleting an item would corrupt historical records."""

    def __init__(self, item_id):
        super().__init__("error.deletion_not_allowed", item_id=item_id)
        self.item_id = item_id


class DatabaseUnavailableError(AppError):
    """Raised when the database file cannot be opened or written."""

    def __init__(self, detail: str = ""):
        super().__init__("error.database_unavailable", detail=detail)
