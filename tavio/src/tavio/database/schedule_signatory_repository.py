"""SQLite repository for ``schedule_signatory_settings`` and signatory label language preference."""

from __future__ import annotations

import sqlite3

from tavio.database.exceptions import (
    DatabaseError,
    InvalidSignatoryAdministratorError,
)
from tavio.database.manager import DatabaseManager
from tavio.domain.schedule_signatory import (
    DEFAULT_SIGNATORY_LABEL_LANGUAGE,
    SIGNATORY_LABEL_LANGUAGES,
    ScheduleSignatoryInput,
    ScheduleSignatorySetting,
)

SIGNATORY_LANGUAGE_SETTING_KEY = "signatory_label_language"

_SELECT_SETTINGS_SQL = """
    SELECT
        schedule_type,
        prepared_by_administrator_id,
        verified_by_administrator_id,
        created_at,
        updated_at
    FROM schedule_signatory_settings
"""


def _row_to_setting(row: sqlite3.Row) -> ScheduleSignatorySetting:
    return ScheduleSignatorySetting(
        schedule_type=str(row["schedule_type"]),
        prepared_by_administrator_id=(
            None
            if row["prepared_by_administrator_id"] is None
            else int(row["prepared_by_administrator_id"])
        ),
        verified_by_administrator_id=(
            None
            if row["verified_by_administrator_id"] is None
            else int(row["verified_by_administrator_id"])
        ),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class ScheduleSignatoryRepository:
    """Data access repository for ``schedule_signatory_settings`` and label language setting."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def list_settings(self) -> list[ScheduleSignatorySetting]:
        """Return all three signatory setting rows in canonical display order."""
        sql = (
            f"{_SELECT_SETTINGS_SQL} "
            "ORDER BY CASE schedule_type "
            "WHEN 'TEACHER' THEN 1 "
            "WHEN 'CLASS' THEN 2 "
            "WHEN 'SPECIAL_ROOM' THEN 3 "
            "ELSE 4 END"
        )
        try:
            with self._database_manager.connection() as conn:
                rows = conn.execute(sql).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to load schedule signatory settings: {exc}") from exc

        return [_row_to_setting(row) for row in rows]

    def get_setting(self, schedule_type: str) -> ScheduleSignatorySetting | None:
        """Return the signatory setting for ``schedule_type``, or ``None`` if missing."""
        try:
            with self._database_manager.connection() as conn:
                row = conn.execute(
                    f"{_SELECT_SETTINGS_SQL} WHERE schedule_type = ?",
                    (schedule_type,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Failed to load signatory setting for '{schedule_type}': {exc}"
            ) from exc

        return None if row is None else _row_to_setting(row)

    def update_setting(self, data: ScheduleSignatoryInput) -> ScheduleSignatorySetting:
        """Update Prepared By and Verified By IDs for ``data.schedule_type`` atomically."""
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                cursor = conn.execute(
                    """
                    UPDATE schedule_signatory_settings
                    SET prepared_by_administrator_id = ?,
                        verified_by_administrator_id = ?,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    WHERE schedule_type = ?
                    """,
                    (
                        data.prepared_by_administrator_id,
                        data.verified_by_administrator_id,
                        data.schedule_type,
                    ),
                )
                if cursor.rowcount == 0:
                    raise DatabaseError(
                        f"Signatory configuration row for '{data.schedule_type}' was not found."
                    )
                row = conn.execute(
                    f"{_SELECT_SETTINGS_SQL} WHERE schedule_type = ?",
                    (data.schedule_type,),
                ).fetchone()
        except DatabaseError:
            raise
        except sqlite3.IntegrityError as exc:
            if "FOREIGN KEY" in str(exc).upper():
                raise InvalidSignatoryAdministratorError(
                    "Selected administrator does not exist in school_administrators."
                ) from exc
            raise DatabaseError(
                f"Failed to update signatory setting for '{data.schedule_type}': {exc}"
            ) from exc
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Failed to update signatory setting for '{data.schedule_type}': {exc}"
            ) from exc

        if row is None:
            raise DatabaseError(
                f"Updated signatory setting for '{data.schedule_type}' could not be reloaded."
            )
        return _row_to_setting(row)

    def get_label_language(self) -> str:
        """Read persisted signatory display-label language from ``app_settings``."""
        try:
            with self._database_manager.connection() as conn:
                row = conn.execute(
                    "SELECT setting_value FROM app_settings WHERE setting_key = ?",
                    (SIGNATORY_LANGUAGE_SETTING_KEY,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to read signatory label language setting: {exc}") from exc

        if row is None:
            return DEFAULT_SIGNATORY_LABEL_LANGUAGE
        value = str(row["setting_value"]).strip().upper()
        return value if value in SIGNATORY_LABEL_LANGUAGES else DEFAULT_SIGNATORY_LABEL_LANGUAGE

    def set_label_language(self, language_code: str) -> str:
        """Persist signatory display-label language in ``app_settings``."""
        normalized = language_code.strip().upper()
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                conn.execute(
                    """
                    INSERT INTO app_settings (
                        setting_key,
                        setting_value,
                        value_type,
                        description
                    ) VALUES (?, ?, 'STRING', ?)
                    ON CONFLICT(setting_key) DO UPDATE SET
                        setting_value = excluded.setting_value,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    """,
                    (
                        SIGNATORY_LANGUAGE_SETTING_KEY,
                        normalized,
                        "Display language for schedule signatory role labels (EN or MS).",
                    ),
                )
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to save signatory label language setting: {exc}") from exc

        return normalized
