"""Tests for TAVIO application configuration and LocalAppData path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from tavio.config import (
    APP_NAME,
    DB_FILENAME,
    ENV_DATA_DIR_OVERRIDE,
    build_app_paths,
    ensure_app_directories,
    resolve_base_data_dir,
)


def test_resolve_base_data_dir_uses_windows_localappdata(tmp_path: Path) -> None:
    fake_local_appdata = tmp_path / "Users" / "Admin" / "AppData" / "Local"
    resolved = resolve_base_data_dir(
        env={"LOCALAPPDATA": str(fake_local_appdata)},
        platform="win32",
    )
    assert resolved == fake_local_appdata.resolve() / "TAVIO"


def test_resolve_base_data_dir_respects_explicit_override(tmp_path: Path) -> None:
    override = tmp_path / "CustomTavio"
    resolved = resolve_base_data_dir(
        env={
            ENV_DATA_DIR_OVERRIDE: str(override),
            "LOCALAPPDATA": str(tmp_path / "IgnoredLocalAppData"),
        },
        platform="win32",
    )
    assert resolved == override.resolve()


def test_resolve_base_data_dir_windows_fallback_uses_userprofile(tmp_path: Path) -> None:
    user_profile = tmp_path / "Users" / "Teacher"
    resolved = resolve_base_data_dir(
        env={"USERPROFILE": str(user_profile)},
        platform="win32",
    )
    assert resolved == user_profile.resolve() / "AppData" / "Local" / "TAVIO"


def test_build_and_ensure_app_directories(isolated_tavio_dir: Path) -> None:
    paths = ensure_app_directories(build_app_paths())

    assert paths.base_dir == isolated_tavio_dir.resolve()
    assert paths.data_dir == isolated_tavio_dir.resolve() / "data"
    assert paths.db_path == isolated_tavio_dir.resolve() / "data" / DB_FILENAME
    assert paths.db_path.name == "tavio.db"
    assert paths.backups_dir.is_dir()
    assert paths.logs_dir.is_dir()
    assert paths.data_dir.is_dir()
    assert paths.lock_file_path == isolated_tavio_dir.resolve() / "tavio.lock"
    assert APP_NAME == "TAVIO"


def test_project_identity_constants() -> None:
    paths = build_app_paths()
    assert paths.base_dir.name == "TAVIO"
    assert DB_FILENAME == "tavio.db"


@pytest.mark.parametrize("bad_env", [{"LOCALAPPDATA": "   "}])
def test_whitespace_localappdata_falls_back_cleanly(
    bad_env: dict[str, str],
    tmp_path: Path,
) -> None:
    env = {**bad_env, "USERPROFILE": str(tmp_path)}
    resolved = resolve_base_data_dir(env=env, platform="win32")
    assert resolved == tmp_path.resolve() / "AppData" / "Local" / "TAVIO"
