"""Domain layer package for TAVIO."""

from __future__ import annotations

from tavio.domain.school_profile import (
    DEFAULT_SCHOOL_WEEK_GROUP,
    VALID_SCHOOL_WEEK_GROUPS,
    SchoolProfile,
    SchoolProfileInput,
)

__all__ = [
    "DEFAULT_SCHOOL_WEEK_GROUP",
    "SchoolProfile",
    "SchoolProfileInput",
    "VALID_SCHOOL_WEEK_GROUPS",
]
