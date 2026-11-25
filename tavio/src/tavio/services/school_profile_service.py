"""Application service coordinating School Profile validation, persistence, and logo files."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from tavio.config import (
    SCHOOL_LOGO_RELATIVE_PATH,
    AppPaths,
    ConfigurationError,
    resolve_relative_asset_path,
)
from tavio.database.school_profile_repository import SchoolProfileRepository
from tavio.domain.school_profile import (
    VALID_SCHOOL_WEEK_GROUPS,
    SchoolProfile,
    SchoolProfileInput,
)
from tavio.services.school_logo_service import ProcessedLogoInfo, SchoolLogoService

logger = logging.getLogger(__name__)

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SchoolProfileValidationError(ValueError):
    """Raised when school profile form input fails validation."""


@dataclass(frozen=True, slots=True)
class SchoolProfileView:
    """Loaded school profile paired with resolved local logo status."""

    profile: SchoolProfile | None
    logo_file_path: Path | None
    logo_exists: bool
    logo_missing_on_disk: bool


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


class SchoolProfileService:
    """Coordinates ``school_profile`` persistence and safe logo file operations."""

    def __init__(
        self,
        repository: SchoolProfileRepository,
        logo_service: SchoolLogoService,
        paths: AppPaths,
    ) -> None:
        self._repository = repository
        self._logo_service = logo_service
        self._paths = paths

    def load_profile(self) -> SchoolProfileView:
        """Load the saved school profile and inspect its logo file status on disk."""
        profile = self._repository.get_profile()
        if profile is None or profile.logo_path is None:
            return SchoolProfileView(
                profile=profile,
                logo_file_path=None,
                logo_exists=False,
                logo_missing_on_disk=False,
            )

        try:
            resolved = resolve_relative_asset_path(self._paths, profile.logo_path)
        except ConfigurationError:
            return SchoolProfileView(
                profile=profile,
                logo_file_path=None,
                logo_exists=False,
                logo_missing_on_disk=True,
            )

        exists = resolved.is_file()
        return SchoolProfileView(
            profile=profile,
            logo_file_path=resolved if exists else None,
            logo_exists=exists,
            logo_missing_on_disk=not exists,
        )

    def validate_profile_input(self, raw: SchoolProfileInput) -> SchoolProfileInput:
        """Validate and normalize school profile input fields."""
        school_name = raw.school_name.strip()
        if not school_name:
            raise SchoolProfileValidationError("School Name is required.")

        school_code = raw.school_code.strip()
        if not school_code:
            raise SchoolProfileValidationError("School Code is required.")

        week_group = raw.school_week_group.strip().upper()
        if week_group not in VALID_SCHOOL_WEEK_GROUPS:
            raise SchoolProfileValidationError("School Week Group must be 'A' or 'B'.")

        address = _clean_optional_text(raw.address)
        phone = _clean_optional_text(raw.phone)
        email = _clean_optional_text(raw.email)
        if email is not None and not _EMAIL_PATTERN.match(email):
            raise SchoolProfileValidationError("Please enter a valid school email address.")

        logo_path = _clean_optional_text(raw.logo_path)
        if logo_path is not None:
            logo_path = logo_path.replace("\\", "/")
            try:
                resolve_relative_asset_path(self._paths, logo_path)
            except ConfigurationError as exc:
                raise SchoolProfileValidationError(str(exc)) from exc

        return SchoolProfileInput(
            school_name=school_name,
            school_code=school_code,
            school_week_group=week_group,
            address=address,
            phone=phone,
            email=email,
            logo_path=logo_path,
        )

    def save_profile(self, raw: SchoolProfileInput) -> SchoolProfile:
        """Validate and persist the singleton school profile record."""
        validated = self.validate_profile_input(raw)
        saved = self._repository.upsert_profile(validated)
        logger.info("Saved school profile (%s - %s).", saved.school_code, saved.school_name)
        return saved

    def upload_logo(self, source_path: Path) -> tuple[SchoolProfile | None, ProcessedLogoInfo, str]:
        """Validate, process, save ``school_logo.png``, and update DB ``logo_path`` if profile exists.

        If updating the database fails after saving the new logo file, the previous logo file
        (if any) is restored so the database and disk stay consistent.
        """
        destination = self._paths.school_logo_path
        backup_path: Path | None = None

        if destination.is_file():
            backup_path = self._backup_existing_logo(destination)

        try:
            info = self._logo_service.process_and_save_logo(source_path, destination)
        except Exception:
            if backup_path is not None:
                with suppress(OSError):
                    backup_path.unlink(missing_ok=True)
            raise

        try:
            updated_profile = self._repository.update_logo_path(SCHOOL_LOGO_RELATIVE_PATH)
        except Exception:
            self._restore_or_cleanup_logo(destination, backup_path)
            raise

        if backup_path is not None:
            with suppress(OSError):
                backup_path.unlink(missing_ok=True)

        return updated_profile, info, SCHOOL_LOGO_RELATIVE_PATH

    def remove_logo(self) -> SchoolProfile | None:
        """Clear ``school_profile.logo_path`` (if saved) and delete ``school_logo.png``."""
        updated_profile = self._repository.update_logo_path(None)
        self._logo_service.remove_logo_file(self._paths.school_logo_path)
        logger.info("Removed school logo and cleared school_profile.logo_path.")
        return updated_profile

    def _backup_existing_logo(self, destination: Path) -> Path | None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        tmp_backup: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".school_logo_bak_",
                suffix=".tmp",
                delete=False,
            ) as tmp_file:
                tmp_backup = Path(tmp_file.name)
                tmp_file.write(destination.read_bytes())
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            return tmp_backup
        except OSError:
            if tmp_backup is not None:
                with suppress(OSError):
                    tmp_backup.unlink(missing_ok=True)
            return None

    def _restore_or_cleanup_logo(self, destination: Path, backup_path: Path | None) -> None:
        if backup_path is not None and backup_path.is_file():
            with suppress(OSError):
                os.replace(backup_path, destination)
        else:
            with suppress(OSError):
                destination.unlink(missing_ok=True)
