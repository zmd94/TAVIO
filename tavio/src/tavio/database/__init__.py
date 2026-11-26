"""Foundational SQLite database infrastructure for TAVIO."""

from __future__ import annotations

from tavio.database.connection import (
    ConnectionConfig,
    create_connection,
    get_connection_pragmas,
)
from tavio.database.exceptions import (
    AdministratorInUseError,
    AdministratorNotFoundError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseMigrationError,
    DatabaseTransactionError,
    UnsupportedDatabaseVersionError,
)
from tavio.database.manager import DatabaseManager
from tavio.database.migrations import (
    DEFAULT_MIGRATIONS,
    Migration,
    MigrationResult,
    apply_migrations,
    get_schema_version,
    split_sql_statements,
    validate_migrations,
)
from tavio.database.school_administrator_repository import SchoolAdministratorRepository
from tavio.database.school_profile_repository import SchoolProfileRepository

__all__ = [
    "AdministratorInUseError",
    "AdministratorNotFoundError",
    "ConnectionConfig",
    "DEFAULT_MIGRATIONS",
    "DatabaseConnectionError",
    "DatabaseError",
    "DatabaseManager",
    "DatabaseMigrationError",
    "DatabaseTransactionError",
    "Migration",
    "MigrationResult",
    "SchoolAdministratorRepository",
    "SchoolProfileRepository",
    "UnsupportedDatabaseVersionError",
    "apply_migrations",
    "create_connection",
    "get_connection_pragmas",
    "get_schema_version",
    "split_sql_statements",
    "validate_migrations",
]
