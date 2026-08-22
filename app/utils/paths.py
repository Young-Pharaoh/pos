"""Resolves where the application's writable data lives.

Golden rule: nothing mutable is ever read from or written to the
PyInstaller bundle directory (``sys._MEIPASS``). All writable state --
``store.db``, ``images/``, ``logs/``, ``backups/`` -- lives in a single
"base directory" next to the executable:

* Frozen (PyInstaller) build: the directory containing the ``.exe``.
* Normal ``python main.py`` run: the project root.
* Tests: overridable via the ``INVENTORY_APP_DATA_DIR`` environment
  variable, so tests never touch a developer's real ``store.db``.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

DB_FILENAME = "store.db"
IMAGES_DIRNAME = "images"
ITEMS_SUBDIR = "items"
LOGS_DIRNAME = "logs"
BACKUPS_DIRNAME = "backups"

_ENV_OVERRIDE = "INVENTORY_APP_DATA_DIR"


def get_base_dir() -> Path:
    override = os.environ.get(_ENV_OVERRIDE)
    if override:
        return Path(override).resolve()

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    # app/utils/paths.py -> app/utils -> app -> project root
    return Path(__file__).resolve().parent.parent.parent


def get_db_path() -> Path:
    return get_base_dir() / DB_FILENAME


def get_images_dir() -> Path:
    return get_base_dir() / IMAGES_DIRNAME


def get_item_images_dir() -> Path:
    return get_images_dir() / ITEMS_SUBDIR


def get_logs_dir() -> Path:
    return get_base_dir() / LOGS_DIRNAME


def get_backups_dir() -> Path:
    return get_base_dir() / BACKUPS_DIRNAME


def ensure_app_dirs() -> None:
    """Create all writable directories needed by the app, if missing."""
    for directory in (
        get_base_dir(),
        get_item_images_dir(),
        get_logs_dir(),
        get_backups_dir(),
    ):
        directory.mkdir(parents=True, exist_ok=True)


def item_image_relative_path(item_id: int, extension: str = "jpg") -> str:
    """Relative path stored in ``items.image_path``, e.g. ``images/items/15.jpg``."""
    return f"{IMAGES_DIRNAME}/{ITEMS_SUBDIR}/{item_id}.{extension}"


def resolve_image_path(relative_path: str | None) -> Path | None:
    """Resolve a stored relative image path against the base directory."""
    if not relative_path:
        return None
    return get_base_dir() / relative_path
