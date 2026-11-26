"""Application service for Schedule Signatories validation, loading, and language preferences."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from tavio.database.schedule_signatory_repository import ScheduleSignatoryRepository
from tavio.database.school_administrator_repository import SchoolAdministratorRepository
from tavio.domain.schedule_signatory import (
    SCHEDULE_TYPES,
    SIGNATORY_LABEL_LANGUAGES,
    SIGNATORY_ROLE_LABELS,
    ScheduleSignatoryDetail,
    ScheduleSignatoryInput,
    ScheduleSignatorySetting,
)
from tavio.domain.school_administrator import SchoolAdministrator

logger = logging.getLogger(__name__)


class ScheduleSignatoryValidationError(ValueError):
    """Raised when a schedule signatory assignment or language selection fails validation."""


@dataclass(frozen=True, slots=True)
class ScheduleSignatoriesOverview:
    """Loaded signatory configurations paired with active candidates and label language."""

    details: dict[str, ScheduleSignatoryDetail]
    active_candidates: list[SchoolAdministrator]
    label_language: str

    @property
    def role_labels(self) -> tuple[str, str]:
        """Return ``(prepared_by_label, verified_by_label)`` for the current language."""
        return SIGNATORY_ROLE_LABELS[self.label_language]


class ScheduleSignatoryService:
    """Coordinates ``schedule_signatory_settings`` validation and persistence."""

    def __init__(
        self,
        signatory_repository: ScheduleSignatoryRepository,
        administrator_repository: SchoolAdministratorRepository,
    ) -> None:
        self._signatory_repo = signatory_repository
        self._admin_repo = administrator_repository

    def load_overview(self) -> ScheduleSignatoriesOverview:
        """Load all three schedule signatory settings, active candidates, and label language."""
        settings = self._signatory_repo.list_settings()
        all_admins = self._admin_repo.list_administrators(active_only=None)
        admins_by_id = {admin.id: admin for admin in all_admins}
        active_candidates = self._admin_repo.list_signatory_candidates()
        label_language = self._signatory_repo.get_label_language()

        details: dict[str, ScheduleSignatoryDetail] = {}
        for setting in settings:
            prepared_admin = (
                admins_by_id.get(setting.prepared_by_administrator_id)
                if setting.prepared_by_administrator_id is not None
                else None
            )
            verified_admin = (
                admins_by_id.get(setting.verified_by_administrator_id)
                if setting.verified_by_administrator_id is not None
                else None
            )
            details[setting.schedule_type] = ScheduleSignatoryDetail(
                setting=setting,
                prepared_by_admin=prepared_admin,
                verified_by_admin=verified_admin,
            )

        return ScheduleSignatoriesOverview(
            details=details,
            active_candidates=active_candidates,
            label_language=label_language,
        )

    def save_signatory_setting(self, raw: ScheduleSignatoryInput) -> ScheduleSignatorySetting:
        """Validate business rules and persist Prepared By / Verified By for one schedule type."""
        schedule_type = raw.schedule_type.strip().upper()
        if schedule_type not in SCHEDULE_TYPES:
            raise ScheduleSignatoryValidationError(
                f"Unsupported schedule type '{raw.schedule_type}'."
            )

        prepared_id = raw.prepared_by_administrator_id
        verified_id = raw.verified_by_administrator_id

        if prepared_id is not None and verified_id is not None and prepared_id == verified_id:
            raise ScheduleSignatoryValidationError(
                "Prepared By and Verified By must be two different administrators "
                "for the same schedule type."
            )

        existing = self._signatory_repo.get_setting(schedule_type)

        if prepared_id is not None:
            prepared_admin = self._admin_repo.get_by_id(prepared_id)
            if prepared_admin is None:
                raise ScheduleSignatoryValidationError(
                    f"Selected Prepared By administrator (id={prepared_id}) does not exist."
                )
            is_existing_prepared = (
                existing is not None and existing.prepared_by_administrator_id == prepared_id
            )
            if not prepared_admin.is_active and not is_existing_prepared:
                raise ScheduleSignatoryValidationError(
                    "Inactive administrators cannot be selected for new Prepared By assignments."
                )

        if verified_id is not None:
            verified_admin = self._admin_repo.get_by_id(verified_id)
            if verified_admin is None:
                raise ScheduleSignatoryValidationError(
                    f"Selected Verified By administrator (id={verified_id}) does not exist."
                )
            is_existing_verified = (
                existing is not None and existing.verified_by_administrator_id == verified_id
            )
            if not verified_admin.is_active and not is_existing_verified:
                raise ScheduleSignatoryValidationError(
                    "Inactive administrators cannot be selected for new Verified By assignments."
                )

        saved = self._signatory_repo.update_setting(
            ScheduleSignatoryInput(
                schedule_type=schedule_type,
                prepared_by_administrator_id=prepared_id,
                verified_by_administrator_id=verified_id,
            )
        )
        logger.info(
            "Saved signatory setting for %s (prepared_by=%s, verified_by=%s).",
            saved.schedule_type,
            saved.prepared_by_administrator_id,
            saved.verified_by_administrator_id,
        )
        return saved

    def get_label_language(self) -> str:
        """Return the persisted signatory label language (``'EN'`` or ``'MS'``)."""
        return self._signatory_repo.get_label_language()

    def set_label_language(self, language_code: str) -> str:
        """Validate and persist the signatory label language preference."""
        normalized = language_code.strip().upper()
        if normalized not in SIGNATORY_LABEL_LANGUAGES:
            raise ScheduleSignatoryValidationError(
                f"Unsupported signatory label language '{language_code}'. Use 'EN' or 'MS'."
            )
        saved = self._signatory_repo.set_label_language(normalized)
        logger.info("Updated signatory label language preference to '%s'.", saved)
        return saved
