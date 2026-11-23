"""Desktop application entry point for TAVIO."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile
from PySide6.QtWidgets import QApplication, QMessageBox

from tavio import __version__
from tavio.config import (
    APP_FULL_NAME,
    APP_NAME,
    ConfigurationError,
    build_app_paths,
    ensure_app_directories,
    get_resource_path,
)
from tavio.logging_setup import configure_logging
from tavio.services.startup_service import StartupService
from tavio.ui.main_window import MainWindow

logger = logging.getLogger(__name__)

STALE_LOCK_TIMEOUT_MS = 30_000
LOCK_TRY_TIMEOUT_MS = 100


def acquire_single_instance_lock(
    lock_file_path: Path,
    *,
    stale_lock_timeout_ms: int = STALE_LOCK_TIMEOUT_MS,
    try_timeout_ms: int = LOCK_TRY_TIMEOUT_MS,
) -> tuple[QLockFile, bool]:
    """Create and attempt to acquire a QLockFile for single-instance protection.

    Uses a positive ``stale_lock_timeout_ms`` so Qt can safely recover locks left behind
    by a terminated/crashed process without manual unsafe file deletion, while still
    blocking a second concurrent instance while a live process holds the lock.
    """
    if stale_lock_timeout_ms <= 0:
        raise ValueError("stale_lock_timeout_ms must be > 0 so stale locks can recover safely.")

    lock_file = QLockFile(str(lock_file_path))
    lock_file.setStaleLockTime(stale_lock_timeout_ms)
    acquired = lock_file.tryLock(try_timeout_ms)
    return lock_file, acquired


def release_single_instance_lock(lock_file: QLockFile) -> None:
    """Release the application QLockFile safely if currently held."""
    if lock_file.isLocked():
        lock_file.unlock()


def _load_stylesheet(app: QApplication) -> None:
    qss_path = get_resource_path("styles", "main.qss")
    if not qss_path.is_file():
        logger.warning("Stylesheet not found at %s; using default Qt style.", qss_path)
        return
    try:
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))
    except OSError as exc:
        logger.warning("Unable to read stylesheet %s: %s", qss_path, exc)


def main() -> int:
    """Initialize TAVIO paths, logging, single-instance lock, diagnostics, and GUI."""
    try:
        paths = ensure_app_directories(build_app_paths())
    except ConfigurationError as exc:
        print(f"{APP_NAME} startup error: {exc}", file=sys.stderr)
        return 1

    configure_logging(paths.log_file_path)
    logger.info("Starting %s v%s (base_dir=%s)", APP_NAME, __version__, paths.base_dir)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setOrganizationName(APP_NAME)

    lock_file, acquired = acquire_single_instance_lock(paths.lock_file_path)
    if not acquired:
        info_ok, pid, hostname, appname = lock_file.getLockInfo()
        logger.warning(
            "Single-instance lock held at %s (error=%s, info_ok=%s, pid=%s, host=%s, app=%s); exiting.",
            paths.lock_file_path,
            lock_file.error(),
            info_ok,
            pid,
            hostname,
            appname,
        )
        QMessageBox.warning(
            None,
            f"{APP_NAME} Already Running",
            f"{APP_NAME} ({APP_FULL_NAME}) is already open.\n\n"
            "Only one running instance is allowed to protect local data.",
        )
        return 1

    app.aboutToQuit.connect(lambda: release_single_instance_lock(lock_file))

    try:
        startup_service = StartupService()
        try:
            report = startup_service.run_diagnostics()
        except Exception as exc:  # noqa: BLE001 - fail loudly on missing deps/solver error
            logger.critical("Phase 0 startup verification failed: %s", exc, exc_info=True)
            QMessageBox.critical(
                None,
                f"{APP_NAME} Startup Verification Error",
                f"{APP_NAME} failed required startup checks:\n\n{exc}\n\n"
                f"Check log file: {paths.log_file_path}",
            )
            return 1

        _load_stylesheet(app)
        window = MainWindow(paths=paths, report=report, startup_service=startup_service)
        window.show()
        return app.exec()
    finally:
        release_single_instance_lock(lock_file)
        logger.info("%s exited cleanly; lock released.", APP_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
