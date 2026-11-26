"""Domain models and display-label constants for TAVIO Schedule Signatories."""

from __future__ import annotations

from dataclasses import dataclass

from tavio.domain.school_administrator import SchoolAdministrator

SCHEDULE_TYPE_TEACHER = "TEACHER"
SCHEDULE_TYPE_CLASS = "CLASS"
SCHEDULE_TYPE_SPECIAL_ROOM = "SPECIAL_ROOM"

SCHEDULE_TYPES: tuple[str, ...] = (
    SCHEDULE_TYPE_TEACHER,
    SCHEDULE_TYPE_CLASS,
    SCHEDULE_TYPE_SPECIAL_ROOM,
)

SCHEDULE_TYPE_TITLES: dict[str, str] = {
    SCHEDULE_TYPE_TEACHER: "Teacher Schedule",
    SCHEDULE_TYPE_CLASS: "Class Schedule",
    SCHEDULE_TYPE_SPECIAL_ROOM: "Special Room Schedule",
}

SIGNATORY_LANGUAGE_ENGLISH = "EN"
SIGNATORY_LANGUAGE_MALAY = "MS"
SIGNATORY_LABEL_LANGUAGES: tuple[str, ...] = (
    SIGNATORY_LANGUAGE_ENGLISH,
    SIGNATORY_LANGUAGE_MALAY,
)
DEFAULT_SIGNATORY_LABEL_LANGUAGE = SIGNATORY_LANGUAGE_ENGLISH

SIGNATORY_ROLE_LABELS: dict[str, tuple[str, str]] = {
    SIGNATORY_LANGUAGE_ENGLISH: ("PREPARED BY", "VERIFIED BY"),
    SIGNATORY_LANGUAGE_MALAY: ("DISEDIAKAN OLEH", "DISAHKAN OLEH"),
}


@dataclass(frozen=True, slots=True)
class ScheduleSignatorySetting:
    """Persisted signatory configuration row from ``schedule_signatory_settings``."""

    schedule_type: str
    prepared_by_administrator_id: int | None
    verified_by_administrator_id: int | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class ScheduleSignatoryInput:
    """Input values to update one ``schedule_signatory_settings`` row."""

    schedule_type: str
    prepared_by_administrator_id: int | None = None
    verified_by_administrator_id: int | None = None


@dataclass(frozen=True, slots=True)
class ScheduleSignatoryDetail:
    """Resolved signatory setting paired with administrator details and active status."""

    setting: ScheduleSignatorySetting
    prepared_by_admin: SchoolAdministrator | None
    verified_by_admin: SchoolAdministrator | None

    @property
    def prepared_by_is_inactive(self) -> bool:
        """Return True if the assigned Prepared By administrator is inactive."""
        return self.prepared_by_admin is not None and not self.prepared_by_admin.is_active

    @property
    def verified_by_is_inactive(self) -> bool:
        """Return True if the assigned Verified By administrator is inactive."""
        return self.verified_by_admin is not None and not self.verified_by_admin.is_active
