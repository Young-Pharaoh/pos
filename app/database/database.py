"""Engine creation, SQLite pragmas, and transactional wiring.

Two things make SQLite behave correctly under SQLAlchemy here:

1. ``PRAGMA foreign_keys=ON`` -- off by default in SQLite, required for the
   ``ON DELETE RESTRICT`` / ``CASCADE`` behaviour the models rely on.
2. The pysqlite "BEGIN IMMEDIATE" recipe -- pysqlite's default transaction
   handling does not give SQLAlchemy real control over when a transaction
   starts, which breaks the atomicity guarantees this application depends
   on for add-stock and complete-sale. Disabling pysqlite's own
   ``isolation_level`` and issuing ``BEGIN IMMEDIATE`` ourselves on
   ``session.begin()`` restores that control.

Callers should not reach for the process-wide singleton
(:func:`get_engine` / :func:`get_session_factory`) inside tests. Use
:func:`create_db_engine` with an explicit temp-file path and
:func:`build_session_factory` instead, so tests never share state with a
developer's real ``store.db``.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, event, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.models import Base, Setting
from app.errors import DatabaseUnavailableError
from app.logging_setup import get_logger
from app.utils.paths import ensure_app_dirs, get_db_path

logger = get_logger("database")

DEFAULT_SETTINGS = {
    "low_stock_threshold": "5",
    "default_sell_price": "1.00",
    "currency_symbol": "$",
    "language": "es",
    "schema_version": "1",
}


def _configure_sqlite(engine: Engine) -> None:
    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, connection_record):
        # Let SQLAlchemy fully own transaction boundaries instead of pysqlite.
        dbapi_connection.isolation_level = None
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()

    @event.listens_for(engine, "begin")
    def _on_begin(conn):
        conn.exec_driver_sql("BEGIN IMMEDIATE")


def create_db_engine(db_path: str | Path | None = None, *, echo: bool = False) -> Engine:
    """Create a configured engine pointed at ``db_path`` (or the default)."""
    path = Path(db_path) if db_path is not None else get_db_path()
    ensure_app_dirs()
    try:
        engine = create_engine(f"sqlite:///{path}", echo=echo, future=True)
        _configure_sqlite(engine)
    except Exception as exc:  # pragma: no cover - defensive
        raise DatabaseUnavailableError(str(exc)) from exc
    return engine


def init_db(engine: Engine) -> None:
    """Create tables if missing and seed default settings. Idempotent."""
    Base.metadata.create_all(engine)
    _seed_default_settings(engine)


def _seed_default_settings(engine: Engine) -> None:
    with Session(engine) as session:
        with session.begin():
            existing = {row.key for row in session.scalars(select(Setting))}
            for key, value in DEFAULT_SETTINGS.items():
                if key not in existing:
                    session.add(Setting(key=key, value=value))


def build_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Build a session factory bound to ``engine``.

    ``expire_on_commit=False`` so plain attribute reads immediately after a
    successful transaction (e.g. to build a return DTO) don't trigger a new
    implicit transaction against a session whose ``with`` block already
    exited.
    """
    return sessionmaker(bind=engine, expire_on_commit=False)


def bootstrap_database(db_path: str | Path | None = None) -> sessionmaker[Session]:
    """Create the engine, initialize the schema, and return a session factory.

    This is the single entry point ``main.py`` and test fixtures use to get
    a ready-to-use database.
    """
    engine = create_db_engine(db_path)
    init_db(engine)
    logger.info("Database ready at %s", db_path or get_db_path())
    return build_session_factory(engine)


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Process-wide engine singleton, used by the running application."""
    global _engine
    if _engine is None:
        _engine = create_db_engine()
        init_db(_engine)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = build_session_factory(get_engine())
    return _session_factory
