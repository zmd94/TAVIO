"""SQLite repository for the singleton ``school_profile`` record."""

from __future__ import annotations

import sqlite3

from tavio.database.exceptions import DatabaseError
from tavio.database.manager import DatabaseManager
from tavio.domain.school_profile import SchoolProfile, SchoolProfileInput

_SELECT_SCHOOL_PROFILE_SQL = """
    SELECT
        id,
        school_name,
        school_code,
        school_week_group,
        address,
        phone,
        email,
        principal_name,
        logo_path,
        created_at,
        updated_at
    FROM school_profile
    WHERE id = 1
"""


def _row_to_school_profile(row: sqlite3.Row) -> SchoolProfile:
    return SchoolProfile(
        id=int(row["id"]),
        school_name=str(row["school_name"]),
        school_code=str(row["school_code"]),
        school_week_group=str(row["school_week_group"]),
        address=None if row["address"] is None else str(row["address"]),
        phone=None if row["phone"] is None else str(row["phone"]),
        email=None if row["email"] is None else str(row["email"]),
        principal_name=None if row["principal_name"] is None else str(row["principal_name"]),
        logo_path=None if row["logo_path"] is None else str(row["logo_path"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class SchoolProfileRepository:
    """Data access repository for the ``school_profile`` table (singleton ``id = 1``)."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def get_profile(self) -> SchoolProfile | None:
        """Return the saved school profile or ``None`` if not yet configured."""
        try:
            with self._database_manager.connection() as conn:
                row = conn.execute(_SELECT_SCHOOL_PROFILE_SQL).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to load school profile: {exc}") from exc

        return None if row is None else _row_to_school_profile(row)

    def upsert_profile(self, profile: SchoolProfileInput) -> SchoolProfile:
        """Create or update the singleton school profile while preserving ``principal_name``."""
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                conn.execute(
                    """
                    INSERT INTO school_profile (
                        id,
                        school_name,
                        school_code,
                        school_week_group,
                        address,
                        phone,
                        email,
                        logo_path
                    ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        school_name = excluded.school_name,
                        school_code = excluded.school_code,
                        school_week_group = excluded.school_week_group,
                        address = excluded.address,
                        phone = excluded.phone,
                        email = excluded.email,
                        logo_path = excluded.logo_path,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    """,
                    (
                        profile.school_name,
                        profile.school_code,
                        profile.school_week_group,
                        profile.address,
                        profile.phone,
                        profile.email,
                        profile.logo_path,
                    ),
                )
                row = conn.execute(_SELECT_SCHOOL_PROFILE_SQL).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save school profile: {exc}") from exc

        if row is None:
            raise DatabaseError("Saved school profile could not be reloaded.")
        return _row_to_school_profile(row)

    def update_logo_path(self, logo_path: str | None) -> SchoolProfile | None:
        """Update ``school_profile.logo_path`` if a school profile row exists."""
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                cursor = conn.execute(
                    """
                    UPDATE school_profile
                    SET logo_path = ?,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    WHERE id = 1
                    """,
                    (logo_path,),
                )
                if cursor.rowcount == 0:
                    return None
                row = conn.execute(_SELECT_SCHOOL_PROFILE_SQL).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to update school logo path: {exc}") from exc

        return None if row is None else _row_to_school_profile(row)
