"""Tests for QLockFile long-lived single-instance protection and safe shutdown release."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QLockFile

from tavio.main import (
    LOCK_TRY_TIMEOUT_MS,
    STALE_LOCK_TIMEOUT_MS,
    acquire_single_instance_lock,
    release_single_instance_lock,
)


def test_long_lived_single_instance_lock_blocks_second_instance_and_releases_cleanly(
    tmp_path: Path,
) -> None:
    lock_path = tmp_path / "tavio.lock"

    assert STALE_LOCK_TIMEOUT_MS == 0
    assert LOCK_TRY_TIMEOUT_MS > 0

    first_lock, first_acquired = acquire_single_instance_lock(lock_path)
    try:
        assert first_acquired is True
        assert first_lock.isLocked() is True
        assert first_lock.staleLockTime() == 0

        second_lock, second_acquired = acquire_single_instance_lock(lock_path)
        assert second_acquired is False
        assert second_lock.isLocked() is False
        assert second_lock.error() == QLockFile.LockError.LockFailedError

        pid, hostname, _appname = second_lock.getLockInfo()
        assert pid == os.getpid()
        assert hostname != ""
    finally:
        release_single_instance_lock(first_lock)

    assert first_lock.isLocked() is False

    # Re-acquiring after clean shutdown release must succeed.
    third_lock, third_acquired = acquire_single_instance_lock(lock_path)
    try:
        assert third_acquired is True
        assert third_lock.isLocked() is True
    finally:
        release_single_instance_lock(third_lock)


def test_release_single_instance_lock_is_idempotent(tmp_path: Path) -> None:
    lock_path = tmp_path / "tavio.lock"
    lock_file, acquired = acquire_single_instance_lock(lock_path)
    assert acquired is True

    release_single_instance_lock(lock_file)
    release_single_instance_lock(lock_file)
    assert lock_file.isLocked() is False


def test_negative_stale_lock_timeout_is_rejected(tmp_path: Path) -> None:
    lock_path = tmp_path / "tavio.lock"
    with pytest.raises(ValueError, match="stale_lock_timeout_ms must be >= 0"):
        acquire_single_instance_lock(lock_path, stale_lock_timeout_ms=-1)
