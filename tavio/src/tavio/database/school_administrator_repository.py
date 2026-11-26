"""SQLite repository for ``school_administrators`` management."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence

from tavio.database.exceptions import (
    AdministratorInUseError,
    AdministratorNotFoundError,
    DatabaseError,
)
from tavio.database.manager import DatabaseManager
from tavio.domain.school_administrator import (
    SchoolAdministrator,
    SchoolAdministratorInput,
)

_SELECT_COLUMNS = """
    SELECT
        id,
        position_title,
        administrator_name,
        sort_order,
        is_active,
        created_at,
        updated_at
    FROM school_administrators
"""


def _row_to_administrator(row: sqlite3.Row) -> SchoolAdministrator:
    return SchoolAdministrator(
        id=int(row["id"]),
        position_title=str(row["position_title"]),
        administrator_name=str(row["administrator_name"]),
        sort_order=int(row["sort_order"]),
        is_active=bool(int(row["is_active"])),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


class SchoolAdministratorRepository:
    """Data access repository for ``school_administrators``."""

    def __init__(self, database_manager: DatabaseManager) -> None:
        self._database_manager = database_manager

    def list_administrators(self, *, active_only: bool | None = None) -> list[SchoolAdministrator]:
        """Return administrators ordered by ``sort_order ASC, id ASC``."""
        where_clause = ""
        params: tuple[int, ...] = ()
        if active_only is True:
            where_clause = "WHERE is_active = ?"
            params = (1,)
        elif active_only is False:
            where_clause = "WHERE is_active = ?"
            params = (0,)

        sql = f"{_SELECT_COLUMNS} {where_clause} ORDER BY sort_order ASC, id ASC"
        try:
            with self._database_manager.connection() as conn:
                rows = conn.execute(sql, params).fetchall()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to list school administrators: {exc}") from exc

        return [_row_to_administrator(row) for row in rows]

    def list_signatory_candidates(self) -> list[SchoolAdministrator]:
        """Return only active administrators eligible for new signatory assignments."""
        return self.list_administrators(active_only=True)

    def get_by_id(self, admin_id: int) -> SchoolAdministrator | None:
        """Return a single administrator by ID, or ``None`` if not found."""
        try:
            with self._database_manager.connection() as conn:
                row = conn.execute(
                    f"{_SELECT_COLUMNS} WHERE id = ?",
                    (admin_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to load school administrator {admin_id}: {exc}") from exc

        return None if row is None else _row_to_administrator(row)

    def create_administrator(self, data: SchoolAdministratorInput) -> SchoolAdministrator:
        """Create a new active administrator appended to the end of the display order."""
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                next_order_row = conn.execute(
                    "SELECT COALESCE(MAX(sort_order), 0) + 1 AS next_order FROM school_administrators"
                ).fetchone()
                next_order = int(next_order_row["next_order"]) if next_order_row is not None else 1

                cursor = conn.execute(
                    """
                    INSERT INTO school_administrators (
                        position_title,
                        administrator_name,
                        sort_order,
                        is_active
                    ) VALUES (?, ?, ?, 1)
                    """,
                    (data.position_title, data.administrator_name, next_order),
                )
                new_id = cursor.lastrowid
                row = conn.execute(
                    f"{_SELECT_COLUMNS} WHERE id = ?",
                    (new_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to create school administrator: {exc}") from exc

        if row is None:
            raise DatabaseError("Created school administrator could not be reloaded.")
        return _row_to_administrator(row)

    def update_administrator(
        self,
        admin_id: int,
        data: SchoolAdministratorInput,
    ) -> SchoolAdministrator:
        """Update position title and name while preserving ``id``, ``sort_order``, ``is_active``, and ``created_at``."""
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                cursor = conn.execute(
                    """
                    UPDATE school_administrators
                    SET position_title = ?,
                        administrator_name = ?,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    WHERE id = ?
                    """,
                    (data.position_title, data.administrator_name, admin_id),
                )
                if cursor.rowcount == 0:
                    raise AdministratorNotFoundError(
                        f"School administrator with id={admin_id} was not found."
                    )
                row = conn.execute(
                    f"{_SELECT_COLUMNS} WHERE id = ?",
                    (admin_id,),
                ).fetchone()
        except AdministratorNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to update school administrator {admin_id}: {exc}") from exc

        if row is None:
            raise DatabaseError(f"Updated school administrator {admin_id} could not be reloaded.")
        return _row_to_administrator(row)

    def set_active(self, admin_id: int, *, is_active: bool) -> SchoolAdministrator:
        """Activate or deactivate an administrator without removing records or foreign keys."""
        active_flag = 1 if is_active else 0
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                cursor = conn.execute(
                    """
                    UPDATE school_administrators
                    SET is_active = ?,
                        updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                    WHERE id = ?
                    """,
                    (active_flag, admin_id),
                )
                if cursor.rowcount == 0:
                    raise AdministratorNotFoundError(
                        f"School administrator with id={admin_id} was not found."
                    )
                row = conn.execute(
                    f"{_SELECT_COLUMNS} WHERE id = ?",
                    (admin_id,),
                ).fetchone()
        except AdministratorNotFoundError:
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Failed to update active status for school administrator {admin_id}: {exc}"
            ) from exc

        if row is None:
            raise DatabaseError(f"School administrator {admin_id} could not be reloaded.")
        return _row_to_administrator(row)

    def reorder_administrators(self, ordered_ids: Sequence[int]) -> list[SchoolAdministrator]:
        """Persist a new display ordering for ``ordered_ids`` atomically inside a transaction.

        If ``ordered_ids`` represents a filtered subset (e.g., active administrators only),
        their relative slots in the full ordered table are updated while preserving the
        positions of non-included records, and ``sort_order`` is normalized sequentially
        across all records starting at 1.
        """
        requested_ids = list(ordered_ids)
        if len(set(requested_ids)) != len(requested_ids):
            raise DatabaseError("Duplicate administrator IDs provided for reordering.")

        try:
            with self._database_manager.transaction(immediate=True) as conn:
                rows = conn.execute(
                    f"{_SELECT_COLUMNS} ORDER BY sort_order ASC, id ASC"
                ).fetchall()
                existing_by_id = {int(row["id"]): row for row in rows}
                missing = [admin_id for admin_id in requested_ids if admin_id not in existing_by_id]
                if missing:
                    raise AdministratorNotFoundError(
                        f"School administrator ID(s) not found for reordering: {missing}"
                    )

                if not requested_ids:
                    return [_row_to_administrator(row) for row in rows]

                requested_set = set(requested_ids)
                canonical_ids = [int(row["id"]) for row in rows]
                target_slots = [
                    idx for idx, admin_id in enumerate(canonical_ids) if admin_id in requested_set
                ]
                reordered_ids = list(canonical_ids)
                for slot_idx, admin_id in zip(target_slots, requested_ids, strict=True):
                    reordered_ids[slot_idx] = admin_id

                for new_order, admin_id in enumerate(reordered_ids, start=1):
                    if int(existing_by_id[admin_id]["sort_order"]) != new_order:
                        conn.execute(
                            """
                            UPDATE school_administrators
                            SET sort_order = ?,
                                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                            WHERE id = ?
                            """,
                            (new_order, admin_id),
                        )

                updated_rows = conn.execute(
                    f"{_SELECT_COLUMNS} ORDER BY sort_order ASC, id ASC"
                ).fetchall()
        except (AdministratorNotFoundError, DatabaseError):
            raise
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to reorder school administrators: {exc}") from exc

        return [_row_to_administrator(row) for row in updated_rows]

    def delete_administrator(self, admin_id: int) -> None:
        """Delete an administrator if not referenced by ``schedule_signatory_settings``.

        Relies on SQLite's ``ON DELETE RESTRICT`` foreign key constraint and translates
        foreign key violations into ``AdministratorInUseError``.
        """
        try:
            with self._database_manager.transaction(immediate=True) as conn:
                existing = conn.execute(
                    "SELECT id FROM school_administrators WHERE id = ?",
                    (admin_id,),
                ).fetchone()
                if existing is None:
                    raise AdministratorNotFoundError(
                        f"School administrator with id={admin_id} was not found."
                    )
                conn.execute("DELETE FROM school_administrators WHERE id = ?", (admin_id,))
        except AdministratorNotFoundError:
            raise
        except sqlite3.IntegrityError as exc:
            if "FOREIGN KEY" in str(exc).upper():
                raise AdministratorInUseError(
                    "This administrator cannot be deleted because they are currently assigned in "
                    "Schedule Signatory Settings. Please deactivate this administrator instead."
                ) from exc
            raise DatabaseError(f"Failed to delete school administrator {admin_id}: {exc}") from exc
        except sqlite3.Error as exc:
            raise DatabaseError(f"Failed to delete school administrator {admin_id}: {exc}") from exc
