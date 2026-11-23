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
ENV_DATA_DIR_OVERRIDE = "TAVIO_DATA_DIR"


class ConfigurationError(RuntimeError):
    """Raised when TAVIO cannot resolve or initialize local application paths."""


@dataclass(frozen=True, slots=True)
class AppPaths:
    """Resolved filesystem paths for TAVIO local storage."""

    base_dir: Path
    data_dir: Path
    db_path: Path
    backups_dir: Path
    logs_dir: Path
    log_file_path: Path
    lock_file_path: Path


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
    backups_dir = resolved_base / "backups"
    logs_dir = resolved_base / "logs"

    return AppPaths(
        base_dir=resolved_base,
        data_dir=data_dir,
        db_path=data_dir / DB_FILENAME,
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


def get_resource_root() -> Path:
    """Return the root directory for bundled static resources (dev and PyInstaller)."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / "resources"
    return Path(__file__).resolve().parents[2] / "resources"


def get_resource_path(*parts: str) -> Path:
    """Resolve a path inside the TAVIO resources directory."""
    return get_resource_root().joinpath(*parts)
