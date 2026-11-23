"""Custom exceptions for the TAVIO SQLite database foundation."""

from __future__ import annotations


class DatabaseError(RuntimeError):
    """Base exception for all TAVIO database foundation errors."""


class DatabaseConnectionError(DatabaseError):
    """Raised when opening or configuring a SQLite connection fails."""


class DatabaseTransactionError(DatabaseError):
    """Raised when starting, committing, rolling back, or nesting a transaction fails."""


class DatabaseMigrationError(DatabaseError):
    """Raised when schema migration definitions or execution fail."""


class UnsupportedDatabaseVersionError(DatabaseMigrationError):
    """Raised when an existing database schema version is unsupported or newer than known."""
