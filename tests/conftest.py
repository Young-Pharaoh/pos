"""Shared pytest fixtures.

Every test gets its own temp-file SQLite database (never an in-memory
``:memory:`` database, since that would hide file-locking / WAL behaviour
that matters for this app) and a matching set of repositories/services
wired against it. No mocks: this follows the project's TDD skill, which
favours exercising real collaborators over stubbing internals.
"""

from __future__ import annotations

import os

# Must be set before any PySide6.QtWidgets.QApplication is constructed.
# Only applied if the environment hasn't already picked a platform (e.g. a
# developer running tests with a real display attached).
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from app.database.database import bootstrap_database
from app.services.inventory_service import InventoryService
from app.services.report_service import ReportService
from app.services.sales_service import SalesService
from app.services.settings_service import SettingsService


@pytest.fixture()
def session_factory(tmp_path):
    db_path = tmp_path / "store.db"
    os.environ["INVENTORY_APP_DATA_DIR"] = str(tmp_path)
    try:
        yield bootstrap_database(db_path)
    finally:
        os.environ.pop("INVENTORY_APP_DATA_DIR", None)


@pytest.fixture()
def settings_service(session_factory):
    return SettingsService(session_factory)


@pytest.fixture()
def inventory_service(session_factory):
    return InventoryService(session_factory)


@pytest.fixture()
def sales_service(session_factory):
    return SalesService(session_factory)


@pytest.fixture()
def report_service(session_factory):
    return ReportService(session_factory)
