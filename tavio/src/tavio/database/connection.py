"""SQLite connection creation and PRAGMA configuration for TAVIO."""

from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from tavio.database.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)

VALID_JOURNAL_MODES = frozenset({"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"})
VALID_SYNCHRONOUS_MODES = frozenset({"OFF", "NORMAL", "FULL", "EXTRA"})


@dataclass(frozen=True, slots=True)
class ConnectionConfig:
    """Configuration applied to every SQLite connection opened by TAVIO."""

    timeout_seconds: float = 10.0
    busy_timeout_ms: int = 5000
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    foreign_keys: bool = True
    row_factory: bool = True

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0.")
        if self.busy_timeout_ms < 0:
            raise ValueError("busy_timeout_ms must be >= 0.")

        normalized_journal = self.journal_mode.strip().upper()
        if normalized_journal not in VALID_JOURNAL_MODES:
            raise ValueError(f"Unsupported SQLite journal_mode: {self.journal_mode!r}")
        object.__setattr__(self, "journal_mode", normalized_journal)

        normalized_sync = self.synchronous.strip().upper()
        if normalized_sync not in VALID_SYNCHRONOUS_MODES:
            raise ValueError(f"Unsupported SQLite synchronous mode: {self.synchronous!r}")
        object.__setattr__(self, "synchronous", normalized_sync)


def normalize_db_path(db_path: Path | str) -> Path:
    raw = str(db_path).strip()
    if not raw:
        raise DatabaseConnectionError("Database path cannot be empty.")
    if raw == ":memory:" or raw.startswith("file:"):
        raise DatabaseConnectionError(
            "File-backed database path is required for TAVIO persistence."
        )
    path = Path(db_path).expanduser().resolve()
    if path.exists() and path.is_dir():
        raise DatabaseConnectionError(f"Database path points to a directory: '{path}'")
    return path


def _configure_connection(conn: sqlite3.Connection, config: ConnectionConfig) -> None:
    fk_value = "ON" if config.foreign_keys else "OFF"
    conn.execute(f"PRAGMA foreign_keys = {fk_value}")
    conn.execute(f"PRAGMA busy_timeout = {config.busy_timeout_ms}")

    journal_row = conn.execute(f"PRAGMA journal_mode = {config.journal_mode}").fetchone()
    actual_journal = str(journal_row[0]).upper() if journal_row is not None else ""
    if actual_journal != config.journal_mode:
        raise DatabaseConnectionError(
            f"SQLite journal_mode '{config.journal_mode}' requested, got '{actual_journal}'."
        )

    conn.execute(f"PRAGMA synchronous = {config.synchronous}")
    if config.row_factory:
        conn.row_factory = sqlite3.Row


def create_connection(
    db_path: Path | str,
    config: ConnectionConfig | None = None,
) -> sqlite3.Connection:
    """Open and configure a new SQLite connection with explicit transaction control.

    Parent directories are created automatically if missing. Every connection uses
    ``isolation_level=None`` so transactions are explicitly controlled with SQL
    ``BEGIN`` / ``COMMIT`` / ``ROLLBACK`` consistently across Python 3.11 and 3.12.
    """
    cfg = ConnectionConfig() if config is None else config
    resolved_path = normalize_db_path(db_path)

    try:
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DatabaseConnectionError(
            f"Failed to create database directory '{resolved_path.parent}': {exc}"
        ) from exc

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(
            str(resolved_path),
            timeout=cfg.timeout_seconds,
            isolation_level=None,
        )
        _configure_connection(conn, cfg)
        logger.debug("Opened SQLite connection to %s (journal_mode=%s)", resolved_path, cfg.journal_mode)
        return conn
    except DatabaseConnectionError:
        if conn is not None:
            conn.close()
        raise
    except (sqlite3.Error, OSError) as exc:
        if conn is not None:
            conn.close()
        raise DatabaseConnectionError(
            f"Failed to open or configure SQLite database '{resolved_path}': {exc}"
        ) from exc


def get_connection_pragmas(conn: sqlite3.Connection) -> dict[str, int | str]:
    """Read key connection PRAGMA values for inspection and diagnostics."""
    fk_row = conn.execute("PRAGMA foreign_keys").fetchone()
    busy_row = conn.execute("PRAGMA busy_timeout").fetchone()
    journal_row = conn.execute("PRAGMA journal_mode").fetchone()
    sync_row = conn.execute("PRAGMA synchronous").fetchone()
    version_row = conn.execute("PRAGMA user_version").fetchone()

    return {
        "foreign_keys": int(fk_row[0]) if fk_row is not None else -1,
        "busy_timeout": int(busy_row[0]) if busy_row is not None else -1,
        "journal_mode": str(journal_row[0]).lower() if journal_row is not None else "",
        "synchronous": int(sync_row[0]) if sync_row is not None else -1,
        "user_version": int(version_row[0]) if version_row is not None else -1,
    }
