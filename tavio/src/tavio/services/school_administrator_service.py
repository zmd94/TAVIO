"""Application service for School Administrators validation, ordering, status, and safe deletion."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from tavio.database.school_administrator_repository import SchoolAdministratorRepository
from tavio.domain.school_administrator import (
    SchoolAdministrator,
    SchoolAdministratorInput,
)

logger = logging.getLogger(__name__)


class SchoolAdministratorValidationError(ValueError):
    """Raised when school administrator input fails validation."""


class SchoolAdministratorService:
    """Coordinates ``school_administrators`` validation, persistence, ordering, and deletion."""

    def __init__(self, repository: SchoolAdministratorRepository) -> None:
        self._repository = repository

    def validate_input(self, raw: SchoolAdministratorInput) -> SchoolAdministratorInput:
        """Trim and validate required administrator fields."""
        position_title = raw.position_title.strip()
        if not position_title:
            raise SchoolAdministratorValidationError("Position Title is required.")

        administrator_name = raw.administrator_name.strip()
        if not administrator_name:
            raise SchoolAdministratorValidationError("Administrator Name is required.")

        return SchoolAdministratorInput(
            position_title=position_title,
            administrator_name=administrator_name,
        )

    def list_administrators(self, *, active_only: bool | None = True) -> list[SchoolAdministrator]:
        """List administrators filtered by status and ordered by ``sort_order ASC, id ASC``."""
        return self._repository.list_administrators(active_only=active_only)

    def list_signatory_candidates(self) -> list[SchoolAdministrator]:
        """Return only active administrators eligible for new signatory selection."""
        return self._repository.list_signatory_candidates()

    def get_administrator(self, admin_id: int) -> SchoolAdministrator | None:
        """Return a single administrator by ID, or ``None`` if absent."""
        return self._repository.get_by_id(admin_id)

    def add_administrator(self, raw: SchoolAdministratorInput) -> SchoolAdministrator:
        """Validate and create a new active administrator appended to the end of the list."""
        validated = self.validate_input(raw)
        created = self._repository.create_administrator(validated)
        logger.info(
            "Added school administrator id=%d (%s - %s).",
            created.id,
            created.position_title,
            created.administrator_name,
        )
        return created

    def edit_administrator(
        self,
        admin_id: int,
        raw: SchoolAdministratorInput,
    ) -> SchoolAdministrator:
        """Validate and update an existing administrator's position title and name."""
        validated = self.validate_input(raw)
        updated = self._repository.update_administrator(admin_id, validated)
        logger.info(
            "Updated school administrator id=%d (%s - %s).",
            updated.id,
            updated.position_title,
            updated.administrator_name,
        )
        return updated

    def activate_administrator(self, admin_id: int) -> SchoolAdministrator:
        """Mark an administrator as active (``is_active = 1``)."""
        updated = self._repository.set_active(admin_id, is_active=True)
        logger.info("Activated school administrator id=%d.", updated.id)
        return updated

    def deactivate_administrator(self, admin_id: int) -> SchoolAdministrator:
        """Mark an administrator as inactive (``is_active = 0``) without altering foreign keys."""
        updated = self._repository.set_active(admin_id, is_active=False)
        logger.info("Deactivated school administrator id=%d.", updated.id)
        return updated

    def reorder_administrators(self, ordered_ids: Sequence[int]) -> list[SchoolAdministrator]:
        """Persist an explicit administrator display order."""
        updated = self._repository.reorder_administrators(ordered_ids)
        logger.info("Reordered %d school administrator record(s).", len(ordered_ids))
        return updated

    def move_administrator_up(
        self,
        admin_id: int,
        *,
        active_only: bool | None = None,
    ) -> list[SchoolAdministrator]:
        """Move ``admin_id`` one position earlier in the selected filter view."""
        return self._move_by_offset(admin_id, offset=-1, active_only=active_only)

    def move_administrator_down(
        self,
        admin_id: int,
        *,
        active_only: bool | None = None,
    ) -> list[SchoolAdministrator]:
        """Move ``admin_id`` one position later in the selected filter view."""
        return self._move_by_offset(admin_id, offset=1, active_only=active_only)

    def _move_by_offset(
        self,
        admin_id: int,
        *,
        offset: int,
        active_only: bool | None,
    ) -> list[SchoolAdministrator]:
        visible = self._repository.list_administrators(active_only=active_only)
        ordered_ids = [admin.id for admin in visible]
        if admin_id not in ordered_ids:
            return visible

        current_index = ordered_ids.index(admin_id)
        target_index = current_index + offset
        if target_index < 0 or target_index >= len(ordered_ids):
            return visible

        ordered_ids[current_index], ordered_ids[target_index] = (
            ordered_ids[target_index],
            ordered_ids[current_index],
        )
        self._repository.reorder_administrators(ordered_ids)
        return self._repository.list_administrators(active_only=active_only)

    def delete_administrator(self, admin_id: int) -> None:
        """Delete an unused administrator, enforcing ``ON DELETE RESTRICT`` foreign keys."""
        self._repository.delete_administrator(admin_id)
        logger.info("Deleted school administrator id=%d.", admin_id)
