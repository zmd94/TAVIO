"""Versioned SQLite schema migration runner using PRAGMA user_version."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tavio.database.exceptions import (
    DatabaseMigrationError,
    UnsupportedDatabaseVersionError,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Migration:
    """Single atomic forward schema migration identified by an integer version."""

    version: int
    description: str
    sql: str | None = None
    up: Callable[[sqlite3.Connection], None] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.version, bool) or not isinstance(self.version, int) or self.version < 1:
            raise ValueError("Migration version must be an integer >= 1.")
        if not self.description.strip():
            raise ValueError("Migration description cannot be empty.")

        has_sql = self.sql is not None and bool(self.sql.strip())
        has_up = self.up is not None
        if has_sql == has_up:
            raise ValueError("Migration must define exactly one of non-empty 'sql' or 'up'.")
        if self.up is not None and not callable(self.up):
            raise ValueError("Migration 'up' handler must be callable.")


@dataclass(frozen=True, slots=True)
class MigrationResult:
    """Outcome summary returned after applying schema migrations."""

    initial_version: int
    final_version: int
    applied_versions: tuple[int, ...]


# Phase 1 Task 1 establishes the database foundation only; business tables start at version 1+.
DEFAULT_MIGRATIONS: tuple[Migration, ...] = ()


def get_schema_version(conn: sqlite3.Connection) -> int:
    """Return the current SQLite schema version stored in PRAGMA user_version."""
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
    except sqlite3.Error as exc:
        raise DatabaseMigrationError(f"Failed to read PRAGMA user_version: {exc}") from exc

    if row is None:
        raise DatabaseMigrationError("PRAGMA user_version returned no result.")
    return int(row[0])


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    if isinstance(version, bool) or not isinstance(version, int) or version < 0:
        raise DatabaseMigrationError(f"Invalid schema version: {version!r}")
    conn.execute(f"PRAGMA user_version = {version}")


def validate_migrations(migrations: Sequence[Migration]) -> tuple[Migration, ...]:
    """Validate that migration versions are contiguous positive integers (1..N)."""
    ordered = tuple(sorted(migrations, key=lambda item: item.version))
    for expected_version, migration in enumerate(ordered, start=1):
        if migration.version != expected_version:
            raise DatabaseMigrationError(
                f"Expected contiguous migration version {expected_version}, "
                f"found {migration.version} ({migration.description!r})."
            )
    return ordered


def split_sql_statements(sql_script: str) -> tuple[str, ...]:
    """Split a multi-statement SQL script into single statements without implicit commits.

    Uses ``sqlite3.complete_statement`` so comments, string literals, and compound
    ``BEGIN ... END`` trigger blocks remain intact and execute inside our explicit
    migration transaction.
    """
    statements: list[str] = []
    buffer: list[str] = []

    for line in sql_script.splitlines(keepends=True):
        buffer.append(line)
        candidate = "".join(buffer)
        if sqlite3.complete_statement(candidate):
            cleaned = candidate.strip()
            if cleaned:
                statements.append(cleaned)
            buffer.clear()

    trailing = "".join(buffer).strip()
    if trailing:
        # Allow a single statement omitting trailing semicolon or trailing SQL comments.
        if sqlite3.complete_statement(f"{trailing}\n;"):
            statements.append(trailing)
        else:
            raise DatabaseMigrationError(f"Incomplete SQL statement in migration: {trailing!r}")

    return tuple(statements)


def _execute_migration(conn: sqlite3.Connection, migration: Migration) -> None:
    if migration.sql is not None:
        for statement in split_sql_statements(migration.sql):
            conn.execute(statement)
    elif migration.up is not None:
        migration.up(conn)


def apply_migrations(
    conn: sqlite3.Connection,
    migrations: Sequence[Migration] = DEFAULT_MIGRATIONS,
) -> MigrationResult:
    """Apply any pending schema migrations atomically and update PRAGMA user_version.

    Never auto-downgrades: if ``PRAGMA user_version`` exceeds the maximum known
    migration version, raises ``UnsupportedDatabaseVersionError``.
    """
    validated = validate_migrations(migrations)
    max_supported_version = validated[-1].version if validated else 0
    initial_version = get_schema_version(conn)

    if initial_version < 0:
        raise UnsupportedDatabaseVersionError(
            f"Invalid negative database schema version: {initial_version}."
        )

    if initial_version > max_supported_version:
        raise UnsupportedDatabaseVersionError(
            f"Database schema version {initial_version} is newer than supported version "
            f"{max_supported_version}; downgrading is not supported."
        )

    if conn.in_transaction:
        raise DatabaseMigrationError(
            "Cannot apply schema migrations while a transaction is already active."
        )

    pending = [m for m in validated if m.version > initial_version]
    if not pending:
        logger.debug(
            "Database schema is up to date at version %d.",
            initial_version,
        )
        return MigrationResult(
            initial_version=initial_version,
            final_version=initial_version,
            applied_versions=(),
        )

    applied: list[int] = []
    current_version = initial_version

    for migration in pending:
        logger.info(
            "Applying database migration v%d: %s",
            migration.version,
            migration.description,
        )
        try:
            conn.execute("BEGIN IMMEDIATE")
            _execute_migration(conn, migration)
            _set_schema_version(conn, migration.version)
            if conn.in_transaction:
                conn.execute("COMMIT")
            applied.append(migration.version)
            current_version = migration.version
        except Exception as exc:
            if conn.in_transaction:
                try:
                    conn.execute("ROLLBACK")
                except sqlite3.Error as rollback_exc:
                    logger.error(
                        "Failed to roll back failed migration v%d: %s",
                        migration.version,
                        rollback_exc,
                    )
            if isinstance(exc, DatabaseMigrationError):
                raise
            raise DatabaseMigrationError(
                f"Failed to apply migration v{migration.version} ({migration.description}): {exc}"
            ) from exc

    logger.info("Database migrations completed cleanly (v%d -> v%d).", initial_version, current_version)
    return MigrationResult(
        initial_version=initial_version,
        final_version=current_version,
        applied_versions=tuple(applied),
    )
