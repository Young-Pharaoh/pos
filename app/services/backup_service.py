"""Simple SQLite + images backup mechanism (spec section 34).

Uses SQLite's online backup API (``sqlite3.Connection.backup``) rather than
a plain file copy, since the app may hold a WAL-mode connection open at the
same time; the backup API produces a consistent snapshot regardless. No
remote/cloud backup target is offered -- copies land in a local
``backups/`` folder next to ``store.db``, which the shop owner can move to
a USB drive or cloud-synced folder themselves.
"""

from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from app.logging_setup import get_logger
from app.utils.paths import get_backups_dir, get_db_path, get_images_dir

logger = get_logger("backup")


def backup_database(db_path: Path | None = None, backups_dir: Path | None = None) -> Path:
    """Create a timestamped snapshot of the database (and zip of images/).

    Returns the path to the created ``.db`` backup file.
    """
    source_path = db_path or get_db_path()
    destination_dir = backups_dir or get_backups_dir()
    destination_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    destination_db = destination_dir / f"store-{timestamp}.db"

    source_conn = sqlite3.connect(str(source_path))
    try:
        dest_conn = sqlite3.connect(str(destination_db))
        try:
            source_conn.backup(dest_conn)
        finally:
            dest_conn.close()
    finally:
        source_conn.close()

    images_dir = get_images_dir()
    if images_dir.exists() and any(images_dir.rglob("*")):
        archive_base = destination_dir / f"images-{timestamp}"
        shutil.make_archive(str(archive_base), "zip", root_dir=str(images_dir))

    logger.info("Backup created at %s", destination_db)
    return destination_db
