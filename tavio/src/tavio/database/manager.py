"""Database lifecycle, connection, and transaction manager for TAVIO."""

from __future__ import annotations

import logging
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING

from tavio.database.connection import ConnectionConfig, create_connection, normalize_db_path
from tavio.database.exceptions import DatabaseTransactionError
from tavio.database.migrations import (
    DEFAULT_MIGRATIONS,
    Migration,
    MigrationResult,
    apply_migrations,
    get_schema_version,
    validate_migrations,
)

if TYPE_CHECKING:
    from tavio.config import AppPaths

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Coordinates SQLite initialization, per-operation connections, and transactions.

    No global shared SQLite connection is maintained; each ``connection()`` or
    ``transaction()`` context opens a properly configured connection and closes it
    deterministically on exit.
    """

    def __init__(
        self,
        db_path: Path | str,
        *,
        config: ConnectionConfig | None = None,
        migrations: Sequence[Migration] = DEFAULT_MIGRATIONS,
    ) -> None:
        self._db_path_input: Path | str = db_path
        raw = str(db_path).strip()
        self._resolved_db_path: Path | None = (
            None
            if (not raw or raw == ":memory:" or raw.startswith("file:"))
            else Path(db_path).expanduser().resolve()
        )
        self._config = ConnectionConfig() if config is None else config
        self._migrations = validate_migrations(migrations)
        self._tx_state = threading.local()

    @classmethod
    def from_app_paths(
        cls,
        paths: AppPaths,
        *,
        config: ConnectionConfig | None = None,
        migrations: Sequence[Migration] = DEFAULT_MIGRATIONS,
    ) -> DatabaseManager:
        """Create a DatabaseManager bound to ``AppPaths.db_path``."""
        return cls(paths.db_path, config=config, migrations=migrations)

    @property
    def db_path(self) -> Path:
        """Return the resolved SQLite database file path."""
        if self._resolved_db_path is None:
            return normalize_db_path(self._db_path_input)
        return self._resolved_db_path

    @property
    def config(self) -> ConnectionConfig:
        """Return the connection configuration applied to every connection."""
        return self._config

    @property
    def migrations(self) -> tuple[Migration, ...]:
        """Return the validated migration sequence registered with this manager."""
        return self._migrations

    @property
    def supported_version(self) -> int:
        """Return the highest schema version supported by registered migrations."""
        return self._migrations[-1].version if self._migrations else 0

    def _is_thread_in_transaction(self) -> bool:
        return bool(getattr(self._tx_state, "active", False))

    def _set_thread_in_transaction(self, active: bool) -> None:
        self._tx_state.active = active

    def initialize(self) -> MigrationResult:
        """Create/open the database, verify PRAGMAs, and apply pending migrations."""
        with self.connection() as conn:
            result = apply_migrations(conn, self._migrations)
        logger.info(
            "Database initialized at %s (schema v%d)",
            self.db_path,
            result.final_version,
        )
        return result

    def get_schema_version(self) -> int:
        """Open a connection briefly and return the current PRAGMA user_version."""
        with self.connection() as conn:
            return get_schema_version(conn)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a newly configured SQLite connection and close it on exit."""
        conn = create_connection(self._db_path_input, self._config)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except sqlite3.Error as exc:
                logger.warning("Failed to close SQLite connection cleanly: %s", exc)

    @contextmanager
    def transaction(self, *, immediate: bool = False) -> Iterator[sqlite3.Connection]:
        """Execute a unit of work inside an explicit atomic SQLite transaction.

        Commits on normal exit, rolls back on any raised exception, closes the
        connection in ``finally``, and rejects unsafe nested transactions on the
        same thread.
        """
        if self._is_thread_in_transaction():
            raise DatabaseTransactionError(
                "Nested transactions are not supported; complete the active transaction first."
            )

        begin_sql = "BEGIN IMMEDIATE" if immediate else "BEGIN"
        conn = create_connection(self._db_path_input, self._config)
        self._set_thread_in_transaction(True)

        try:
            try:
                conn.execute(begin_sql)
            except sqlite3.Error as exc:
                raise DatabaseTransactionError(
                    f"Failed to begin SQLite transaction ({begin_sql}): {exc}"
                ) from exc

            try:
                yield conn
            except BaseException:
                if conn.in_transaction:
                    try:
                        conn.execute("ROLLBACK")
                    except sqlite3.Error as rollback_exc:
                        logger.error("Failed to roll back SQLite transaction: %s", rollback_exc)
                raise

            if conn.in_transaction:
                try:
                    conn.execute("COMMIT")
                except sqlite3.Error as exc:
                    with suppress(sqlite3.Error):
                        if conn.in_transaction:
                            conn.execute("ROLLBACK")
                    raise DatabaseTransactionError(
                        f"Failed to commit SQLite transaction: {exc}"
                    ) from exc
        finally:
            self._set_thread_in_transaction(False)
            try:
                conn.close()
            except sqlite3.Error as exc:
                logger.warning("Failed to close SQLite connection cleanly: %s", exc)
