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
from tavio.services.school_logo_service import (
    ProcessedLogoInfo,
    SchoolLogoError,
    SchoolLogoService,
)

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

        If an existing logo is present on disk, a backup must succeed before replacement begins.
        If updating the database fails after saving the new logo file, the previous logo file
        (if any) is restored so the database and disk stay consistent; if restoring also fails,
        the failure is logged and reported while preserving the backup for manual recovery.
        """
        destination = self._paths.school_logo_path
        backup_path: Path | None = None

        if destination.exists():
            backup_path = self._backup_existing_logo(destination)

        try:
            info = self._logo_service.process_and_save_logo(source_path, destination)
        except Exception:
            if backup_path is not None:
                try:
                    backup_path.unlink(missing_ok=True)
                except OSError as cleanup_exc:
                    logger.warning(
                        "Failed to clean up temporary logo backup '%s' after upload failure: %s",
                        backup_path,
                        cleanup_exc,
                    )
            raise

        try:
            updated_profile = self._repository.update_logo_path(SCHOOL_LOGO_RELATIVE_PATH)
        except Exception as db_exc:
            self._restore_or_cleanup_logo(destination, backup_path, db_exc)
            raise

        if backup_path is not None:
            try:
                backup_path.unlink(missing_ok=True)
            except OSError as cleanup_exc:
                logger.warning(
                    "School logo updated, but failed to delete temporary backup '%s': %s",
                    backup_path,
                    cleanup_exc,
                )

        return updated_profile, info, SCHOOL_LOGO_RELATIVE_PATH

    def remove_logo(self) -> SchoolProfile | None:
        """Stage any existing ``school_logo.png``, clear DB ``logo_path``, then delete staged file."""
        logo_path = self._paths.school_logo_path
        staging_path: Path | None = None

        if logo_path.exists():
            if logo_path.is_dir():
                raise SchoolLogoError(f"Expected logo file, found directory: {logo_path}")
            candidate_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=logo_path.parent,
                    prefix=".school_logo_remove_",
                    suffix=".tmp",
                    delete=False,
                ) as tmp_file:
                    candidate_path = Path(tmp_file.name)
                os.replace(logo_path, candidate_path)
                staging_path = candidate_path
            except OSError as exc:
                if candidate_path is not None and logo_path.exists():
                    with suppress(OSError):
                        candidate_path.unlink(missing_ok=True)
                logger.exception("Failed to stage school logo '%s' before removal", logo_path)
                raise SchoolLogoError(
                    f"Failed to stage school logo for removal: {exc}"
                ) from exc

        try:
            updated_profile = self._repository.update_logo_path(None)
        except Exception as db_exc:
            if staging_path is not None:
                try:
                    os.replace(staging_path, logo_path)
                except OSError as restore_exc:
                    logger.exception(
                        "Database update failed (%s) and restoring staged school logo "
                        "from '%s' to '%s' also failed; staged file preserved for manual recovery",
                        db_exc,
                        staging_path,
                        logo_path,
                    )
                    raise SchoolLogoError(
                        f"Database update failed ({db_exc}) and restoring the school logo "
                        f"failed ({restore_exc}). Staged file preserved at: {staging_path}"
                    ) from db_exc
            raise

        if staging_path is not None:
            try:
                staging_path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning(
                    "School profile logo_path was cleared, but failed to delete staged logo "
                    "file '%s': %s",
                    staging_path,
                    exc,
                )

        logger.info("Removed school logo and cleared school_profile.logo_path.")
        return updated_profile

    def _backup_existing_logo(self, destination: Path) -> Path:
        if destination.is_dir():
            raise SchoolLogoError(
                f"Cannot back up existing school logo because '{destination}' is a directory."
            )
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
        except OSError as exc:
            if tmp_backup is not None:
                with suppress(OSError):
                    tmp_backup.unlink(missing_ok=True)
            logger.exception("Failed to create backup of existing school logo '%s'", destination)
            raise SchoolLogoError(
                f"Unable to back up existing school logo before replacement: {exc}"
            ) from exc

    def _restore_or_cleanup_logo(
        self,
        destination: Path,
        backup_path: Path | None,
        db_exc: Exception,
    ) -> None:
        if backup_path is not None:
            try:
                os.replace(backup_path, destination)
            except OSError as restore_exc:
                logger.exception(
                    "Database update failed (%s) and restoring previous school logo "
                    "from backup '%s' to '%s' also failed; backup preserved for manual recovery",
                    db_exc,
                    backup_path,
                    destination,
                )
                raise SchoolLogoError(
                    f"Database update failed ({db_exc}) and restoring the previous school logo "
                    f"failed ({restore_exc}). Backup preserved at: {backup_path}"
                ) from db_exc
            return

        try:
            destination.unlink(missing_ok=True)
        except OSError as cleanup_exc:
            logger.exception(
                "Database update failed (%s) and cleaning up newly saved logo '%s' also failed",
                db_exc,
                destination,
            )
            raise SchoolLogoError(
                f"Database update failed ({db_exc}) and removing the newly saved school logo "
                f"failed ({cleanup_exc})."
            ) from db_exc
