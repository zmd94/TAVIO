"""Application configuration and Windows local directory resolution for TAVIO."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "TAVIO"
APP_FULL_NAME = "Timetable Administration & Validation Intelligent Organizer"
PACKAGE_NAME = "tavio"
DB_FILENAME = "tavio.db"
LOCK_FILENAME = "tavio.lock"
LOG_FILENAME = "tavio.log"
SCHOOL_LOGO_FILENAME = "school_logo.png"
SCHOOL_LOGO_RELATIVE_PATH = f"assets/{SCHOOL_LOGO_FILENAME}"
ENV_DATA_DIR_OVERRIDE = "TAVIO_DATA_DIR"


class ConfigurationError(RuntimeError):
    """Raised when TAVIO cannot resolve or initialize local application paths."""


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Resolved filesystem paths for TAVIO local storage."""

    base_dir: Path
    data_dir: Path
    db_path: Path
    assets_dir: Path
    backups_dir: Path
    logs_dir: Path
    log_file_path: Path
    lock_file_path: Path

    @property
    def school_logo_path(self) -> Path:
        """Return the canonical local filesystem path for the school logo PNG."""
        return self.assets_dir / SCHOOL_LOGO_FILENAME


def resolve_base_data_dir(
    env: Mapping[str, str] | None = None,
    *,
    platform: str | None = None,
) -> Path:
    """Resolve the root local application data directory for TAVIO.

    Resolution priority:
    1. Explicit ``TAVIO_DATA_DIR`` environment override (for testing/portable mode).
    2. ``%LOCALAPPDATA%\\TAVIO`` on Windows (or whenever ``LOCALAPPDATA`` is set).
    3. Platform-appropriate fallback under the user's home directory.
    """
    environ = os.environ if env is None else env
    target_platform = sys.platform if platform is None else platform

    override = environ.get(ENV_DATA_DIR_OVERRIDE, "").strip()
    if override:
        return Path(override).expanduser().resolve()

    local_app_data = environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        return Path(local_app_data).expanduser().resolve() / APP_NAME

    if target_platform.startswith("win"):
        home_dir = environ.get("USERPROFILE", "").strip()
        base_home = Path(home_dir).expanduser() if home_dir else Path.home()
        return base_home.resolve() / "AppData" / "Local" / APP_NAME

    return (Path.home() / ".local" / "share" / APP_NAME).resolve()


def build_app_paths(base_dir: Path | None = None) -> AppPaths:
    """Construct the complete set of TAVIO local application paths."""
    resolved_base = resolve_base_data_dir() if base_dir is None else base_dir.resolve()
    data_dir = resolved_base / "data"
    assets_dir = resolved_base / "assets"
    backups_dir = resolved_base / "backups"
    logs_dir = resolved_base / "logs"

    return AppPaths(
        base_dir=resolved_base,
        data_dir=data_dir,
        db_path=data_dir / DB_FILENAME,
        assets_dir=assets_dir,
        backups_dir=backups_dir,
        logs_dir=logs_dir,
        log_file_path=logs_dir / LOG_FILENAME,
        lock_file_path=resolved_base / LOCK_FILENAME,
    )


def ensure_app_directories(paths: AppPaths) -> AppPaths:
    """Create all required local TAVIO directories if they do not exist."""
    directories = (
        paths.base_dir,
        paths.data_dir,
        paths.assets_dir,
        paths.backups_dir,
        paths.logs_dir,
    )
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ConfigurationError(
                f"Failed to create TAVIO directory '{directory}': {exc}"
            ) from exc
    return paths


def resolve_relative_asset_path(paths: AppPaths, relative_path: str) -> Path:
    """Resolve a stored relative asset path safely inside ``paths.base_dir``."""
    normalized = relative_path.strip().replace("\\", "/")
    if not normalized:
        raise ConfigurationError("Asset relative path cannot be empty.")
    if Path(normalized).is_absolute() or (len(normalized) >= 2 and normalized[1] == ":"):
        raise ConfigurationError(f"Asset path '{relative_path}' must be relative.")

    candidate = (paths.base_dir / normalized).resolve()
    base_resolved = paths.base_dir.resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ConfigurationError(
            f"Asset path '{relative_path}' escapes TAVIO base directory."
        ) from exc
    return candidate


def get_resource_root() -> Path:
    """Return the root directory for bundled static resources (dev and PyInstaller)."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        meipass_resources = Path(frozen_root) / "resources"
        if meipass_resources.exists():
            return meipass_resources
        return Path(sys.executable).resolve().parent / "resources"
    return Path(__file__).resolve().parents[2] / "resources"


def get_resource_path(*parts: str) -> Path:
    """Resolve a path inside the TAVIO resources directory."""
    return get_resource_root().joinpath(*parts)


def get_asset_path(filename: str) -> Path:
    """Resolve a branded asset in both source and PyInstaller environments.

    PyInstaller bundles packaging/assets into resources/assets. During source
    development, assets remain in packaging/assets in the project directory.
    """
    bundled_path = get_resource_path("assets", filename)
    if bundled_path.is_file():
        return bundled_path

    project_root = Path(__file__).resolve().parents[2]
    source_path = project_root / "packaging" / "assets" / filename
    if source_path.is_file():
        return source_path

    return bundled_path
