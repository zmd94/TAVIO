"""Shared pytest fixtures for TAVIO Phase 0 tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tavio.config import ENV_DATA_DIR_OVERRIDE


@pytest.fixture
def isolated_tavio_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate TAVIO_DATA_DIR to a temporary directory for each test."""
    target = tmp_path / "TAVIO"
    monkeypatch.setenv(ENV_DATA_DIR_OVERRIDE, str(target))
    return target
