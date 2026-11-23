"""Tests for TAVIO application configuration and LocalAppData path resolution."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest

from tavio.config import (
    APP_NAME,
    DB_FILENAME,
    ENV_DATA_DIR_OVERRIDE,
    ConfigurationError,
    build_app_paths,
    ensure_app_directories,
    get_asset_path,
    get_resource_path,
    get_resource_root,
    resolve_base_data_dir,
)
from tavio.logging_setup import configure_logging


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


def test_ensure_app_directories_raises_on_unwritable_path(tmp_path: Path) -> None:
    blocking_file = tmp_path / "not_a_directory"
    blocking_file.write_text("occupied", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Failed to create TAVIO directory"):
        ensure_app_directories(build_app_paths(blocking_file))


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


def test_get_resource_path_resolves_stylesheet_in_source_tree() -> None:
    qss_path = get_resource_path("styles", "main.qss")
    assert qss_path.is_file()


def test_get_asset_path_resolves_all_branding_assets_from_source_tree() -> None:
    for filename in ("TAVIO.ico", "TAVIO_icon.png", "TAVIO_icon_vertical.png"):
        asset_path = get_asset_path(filename)
        assert asset_path.is_file(), f"Missing branding asset: {filename}"


def test_get_resource_root_prefers_meipass_resources_when_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    meipass_dir = tmp_path / "_internal"
    (meipass_dir / "resources").mkdir(parents=True)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass_dir), raising=False)

    assert get_resource_root() == meipass_dir / "resources"


def test_configure_logging_writes_log_file(isolated_tavio_dir: Path) -> None:
    paths = ensure_app_directories(build_app_paths())
    logger = configure_logging(paths.log_file_path)
    logger.info("Phase 0 logging check")

    for handler in list(logging.getLogger().handlers):
        handler.flush()

    content = paths.log_file_path.read_text(encoding="utf-8")
    assert "Logging initialized" in content
    assert "Phase 0 logging check" in content

    for handler in list(logging.getLogger().handlers):
        logging.getLogger().removeHandler(handler)
        handler.close()
