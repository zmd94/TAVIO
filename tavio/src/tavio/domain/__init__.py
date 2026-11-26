"""Domain layer package for TAVIO."""

from __future__ import annotations

from tavio.domain.schedule_signatory import (
    DEFAULT_SIGNATORY_LABEL_LANGUAGE,
    SCHEDULE_TYPE_CLASS,
    SCHEDULE_TYPE_SPECIAL_ROOM,
    SCHEDULE_TYPE_TEACHER,
    SCHEDULE_TYPE_TITLES,
    SCHEDULE_TYPES,
    SIGNATORY_LABEL_LANGUAGES,
    SIGNATORY_LANGUAGE_ENGLISH,
    SIGNATORY_LANGUAGE_MALAY,
    SIGNATORY_ROLE_LABELS,
    ScheduleSignatoryDetail,
    ScheduleSignatoryInput,
    ScheduleSignatorySetting,
)
from tavio.domain.school_administrator import (
    SchoolAdministrator,
    SchoolAdministratorInput,
)
from tavio.domain.school_profile import (
    DEFAULT_SCHOOL_WEEK_GROUP,
    VALID_SCHOOL_WEEK_GROUPS,
    SchoolProfile,
    SchoolProfileInput,
)

__all__ = [
    "DEFAULT_SCHOOL_WEEK_GROUP",
    "DEFAULT_SIGNATORY_LABEL_LANGUAGE",
    "SCHEDULE_TYPES",
    "SCHEDULE_TYPE_CLASS",
    "SCHEDULE_TYPE_SPECIAL_ROOM",
    "SCHEDULE_TYPE_TEACHER",
    "SCHEDULE_TYPE_TITLES",
    "SIGNATORY_LABEL_LANGUAGES",
    "SIGNATORY_LANGUAGE_ENGLISH",
    "SIGNATORY_LANGUAGE_MALAY",
    "SIGNATORY_ROLE_LABELS",
    "ScheduleSignatoryDetail",
    "ScheduleSignatoryInput",
    "ScheduleSignatorySetting",
    "SchoolAdministrator",
    "SchoolAdministratorInput",
    "SchoolProfile",
    "SchoolProfileInput",
    "VALID_SCHOOL_WEEK_GROUPS",
]
