"""Desktop application entry point for TAVIO."""

from __future__ import annotations

import logging
import sys

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

    lock_file = QLockFile(str(paths.lock_file_path))
    lock_file.setStaleLockTime(0)
    if not lock_file.tryLock(100):
        logger.warning(
            "Single-instance lock held at %s (error=%s); exiting.",
            paths.lock_file_path,
            lock_file.error(),
        )
        QMessageBox.warning(
            None,
            f"{APP_NAME} Already Running",
            f"{APP_NAME} ({APP_FULL_NAME}) is already open.\n\n"
            "Only one running instance is allowed to protect local data.",
        )
        return 1

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
        lock_file.unlock()
        logger.info("%s exited cleanly; lock released.", APP_NAME)


if __name__ == "__main__":
    raise SystemExit(main())
