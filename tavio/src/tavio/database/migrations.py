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
from tavio.database.schema_v1 import MIGRATION_V1_SQL

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


DEFAULT_MIGRATIONS: tuple[Migration, ...] = (
    Migration(
        version=1,
        description="Create TAVIO v1.3.2 core schema (42 tables, 45 indexes, 64 triggers) and default seeds",
        sql=MIGRATION_V1_SQL,
    ),
)


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


def _scan_quoted_token(sql_script: str, start: int, quote_char: str) -> int:
    """Advance past a single-quoted literal or double-quoted/backticked identifier."""
    length = len(sql_script)
    i = start + 1
    while i < length:
        if sql_script[i] == quote_char:
            if i + 1 < length and sql_script[i + 1] == quote_char:
                i += 2
                continue
            return i + 1
        i += 1
    raise DatabaseMigrationError(
        f"Unterminated SQL token starting with {quote_char!r} in migration script."
    )


def split_sql_statements(sql_script: str) -> tuple[str, ...]:
    """Split a multi-statement SQL script into single statements without implicit commits.

    Lexically tracks comments, string literals, and quoted identifiers so semicolons
    on the same line split cleanly while compound ``CREATE TRIGGER ... BEGIN ... END``
    blocks remain intact via ``sqlite3.complete_statement``.
    """
    statements: list[str] = []
    length = len(sql_script)
    stmt_start = 0
    has_sql_token = False
    i = 0

    while i < length:
        ch = sql_script[i]

        if ch.isspace():
            i += 1
            if not has_sql_token:
                stmt_start = i
            continue

        if ch == "-" and i + 1 < length and sql_script[i + 1] == "-":
            newline_idx = sql_script.find("\n", i + 2)
            i = length if newline_idx == -1 else newline_idx + 1
            if not has_sql_token:
                stmt_start = i
            continue

        if ch == "/" and i + 1 < length and sql_script[i + 1] == "*":
            close_idx = sql_script.find("*/", i + 2)
            if close_idx == -1:
                raise DatabaseMigrationError("Unterminated SQL block comment in migration script.")
            i = close_idx + 2
            if not has_sql_token:
                stmt_start = i
            continue

        if ch in ("'", '"', "`"):
            has_sql_token = True
            i = _scan_quoted_token(sql_script, i, ch)
            continue

        if ch == "[":
            has_sql_token = True
            close_idx = sql_script.find("]", i + 1)
            if close_idx == -1:
                raise DatabaseMigrationError("Unterminated bracketed SQL identifier in migration script.")
            i = close_idx + 1
            continue

        if ch == ";":
            if not has_sql_token:
                stmt_start = i + 1
                i += 1
                continue

            candidate = sql_script[stmt_start : i + 1]
            if sqlite3.complete_statement(candidate):
                cleaned = candidate.strip()
                if cleaned:
                    statements.append(cleaned)
                stmt_start = i + 1
                has_sql_token = False
            i += 1
            continue

        has_sql_token = True
        i += 1

    if has_sql_token:
        trailing = sql_script[stmt_start:].strip()
        if trailing:
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
