"""Domain models and constants for TAVIO School Profile."""

from __future__ import annotations

from dataclasses import dataclass

VALID_SCHOOL_WEEK_GROUPS: tuple[str, ...] = ("A", "B")
DEFAULT_SCHOOL_WEEK_GROUP = "B"


@dataclass(frozen=True, slots=True)
class SchoolProfile:
    """Persisted school profile record from ``school_profile`` (id = 1)."""

    id: int
    school_name: str
    school_code: str
    school_week_group: str
    address: str | None
    phone: str | None
    email: str | None
    principal_name: str | None
    logo_path: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SchoolProfileInput:
    """Validated school profile values to create or update ``school_profile``."""

    school_name: str
    school_code: str
    school_week_group: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    logo_path: str | None = None
