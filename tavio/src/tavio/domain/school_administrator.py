"""Domain models for TAVIO School Administrators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SchoolAdministrator:
    """Persisted administrator record from ``school_administrators``."""

    id: int
    position_title: str
    administrator_name: str
    sort_order: int
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True, slots=True)
class SchoolAdministratorInput:
    """Validated administrator input values to create or update a record."""

    position_title: str
    administrator_name: str
