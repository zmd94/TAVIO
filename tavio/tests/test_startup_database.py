"""Tests for Task 2 database initialization integration during application startup."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from tavio import main as tavio_main
from tavio.config import AppPaths, build_app_paths
from tavio.database import DatabaseConnectionError, DatabaseManager
from tavio.services.startup_service import (
    DependencyStatus,
    StartupDiagnosticReport,
    StartupService,
)
from tavio.solver.smoke_test import SolverSmokeResult
from tavio.ui.main_window import FUTURE_NAVIGATION_MODULES, MainWindow


def _make_dummy_report(*, objective_value: int = 15) -> StartupDiagnosticReport:
    return StartupDiagnosticReport(
        dependencies=(
            DependencyStatus(
                display_name="PySide6",
                import_name="PySide6",
                distribution_name="PySide6",
                available=True,
                version="6.8.0",
            ),
            DependencyStatus(
                display_name="OR-Tools",
                import_name="ortools.sat.python.cp_model",
                distribution_name="ortools",
                available=True,
                version="9.11.0",
            ),
        ),
        solver_result=SolverSmokeResult(
            status_name="OPTIMAL",
            objective_value=objective_value,
            assignments={"T1": 2, "T2": 1, "T3": 3},
            wall_time_ms=1.25,
        ),
    )


def _cleanup_root_logging_handlers() -> None:
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
        handler.close()


class _FakeSignal:
    def __init__(self) -> None:
        self.callbacks: list[object] = []

    def connect(self, callback: object) -> None:
        self.callbacks.append(callback)


class _FakeQApplication:
    def __init__(self, argv: list[str], *, exec_return: int = 0) -> None:
        self.argv = argv
        self.exec_return = exec_return
        self.aboutToQuit = _FakeSignal()
        self.stylesheet: str = ""
        self.exec_calls = 0

    def setApplicationName(self, _name: str) -> None:
        pass

    def setApplicationDisplayName(self, _name: str) -> None:
        pass

    def setOrganizationName(self, _name: str) -> None:
        pass

    def setWindowIcon(self, _icon: object) -> None:
        pass

    def setStyleSheet(self, stylesheet: str) -> None:
        self.stylesheet = stylesheet

    def exec(self) -> int:
        self.exec_calls += 1
        return self.exec_return


def test_startup_initializes_database_once_from_app_paths_and_passes_to_main_window(
    isolated_tavio_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []
    captured: dict[str, object] = {}
    dummy_report = _make_dummy_report()
    fake_app = _FakeQApplication(["tavio"], exec_return=0)

    class _FakeDbManager:
        def __init__(self, paths: AppPaths) -> None:
            self.paths = paths
            self.initialize_calls = 0

        def initialize(self) -> SimpleNamespace:
            self.initialize_calls += 1
            events.append("db_initialize")
            return SimpleNamespace(initial_version=0, final_version=1, applied_versions=(1,))

    def fake_from_app_paths(paths: AppPaths) -> _FakeDbManager:
        events.append("db_from_app_paths")
        captured["db_paths_arg"] = paths
        manager = _FakeDbManager(paths)
        captured["db_manager"] = manager
        return manager

    class _FakeStartupService:
        def __init__(self) -> None:
            self.calls = 0

        def run_diagnostics(self) -> StartupDiagnosticReport:
            self.calls += 1
            events.append("run_diagnostics")
            captured["startup_service"] = self
            return dummy_report

    class _FakeMainWindow:
        def __init__(
            self,
            *,
            paths: AppPaths,
            report: StartupDiagnosticReport,
            startup_service: object,
            database_manager: object,
        ) -> None:
            events.append("main_window_init")
            captured["window_kwargs"] = {
                "paths": paths,
                "report": report,
                "startup_service": startup_service,
                "database_manager": database_manager,
            }

        def show(self) -> None:
            events.append("main_window_show")

    real_acquire = tavio_main.acquire_single_instance_lock
    real_release = tavio_main.release_single_instance_lock

    def spy_acquire(lock_file_path: Path):
        events.append("acquire_lock")
        lock_file, acquired = real_acquire(lock_file_path)
        captured["lock_file"] = lock_file
        return lock_file, acquired

    def spy_release(lock_file) -> None:
        events.append("release_lock")
        real_release(lock_file)

    monkeypatch.setattr(tavio_main, "QApplication", lambda argv: fake_app)
    monkeypatch.setattr(tavio_main, "QIcon", lambda path: ("QIcon", path))
    monkeypatch.setattr(tavio_main, "acquire_single_instance_lock", spy_acquire)
    monkeypatch.setattr(tavio_main, "release_single_instance_lock", spy_release)
    monkeypatch.setattr(tavio_main.DatabaseManager, "from_app_paths", staticmethod(fake_from_app_paths))
    monkeypatch.setattr(tavio_main, "StartupService", _FakeStartupService)
    monkeypatch.setattr(tavio_main, "MainWindow", _FakeMainWindow)

    try:
        exit_code = tavio_main.main()
    finally:
        _cleanup_root_logging_handlers()

    assert exit_code == 0
    assert fake_app.exec_calls == 1

    db_paths_arg = captured["db_paths_arg"]
    assert isinstance(db_paths_arg, AppPaths)
    assert db_paths_arg.db_path == isolated_tavio_dir.resolve() / "data" / "tavio.db"
    assert not db_paths_arg.db_path.exists()

    db_manager = captured["db_manager"]
    assert isinstance(db_manager, _FakeDbManager)
    assert db_manager.initialize_calls == 1

    window_kwargs = captured["window_kwargs"]
    assert isinstance(window_kwargs, dict)
    assert window_kwargs["paths"] == db_paths_arg
    assert window_kwargs["report"] is dummy_report
    assert window_kwargs["startup_service"] is captured["startup_service"]
    assert window_kwargs["database_manager"] is db_manager

    assert events.index("acquire_lock") < events.index("db_from_app_paths")
    assert events.index("db_from_app_paths") < events.index("db_initialize")
    assert events.index("db_initialize") < events.index("main_window_init")
    assert events.index("main_window_init") < events.index("main_window_show")
    assert "release_lock" in events
    assert captured["lock_file"].isLocked() is False


def test_startup_handles_database_init_failure_logs_shows_critical_and_releases_lock(
    isolated_tavio_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    fake_app = _FakeQApplication(["tavio"])
    critical_dialogs: list[tuple[object, str, str]] = []
    window_constructions: list[object] = []
    diagnostics_calls: list[int] = []
    lock_events: list[str] = []
    captured: dict[str, object] = {}

    class _FailingDbManager:
        def __init__(self) -> None:
            self.initialize_calls = 0

        def initialize(self) -> None:
            self.initialize_calls += 1
            raise DatabaseConnectionError("Simulated SQLite open failure")

    failing_db_manager = _FailingDbManager()

    class _SpyStartupService:
        def run_diagnostics(self) -> StartupDiagnosticReport:
            diagnostics_calls.append(1)
            return _make_dummy_report()

    def fake_critical(parent: object, title: str, text: str) -> None:
        critical_dialogs.append((parent, title, text))

    real_acquire = tavio_main.acquire_single_instance_lock
    real_release = tavio_main.release_single_instance_lock

    def spy_acquire(lock_file_path: Path):
        lock_file, acquired = real_acquire(lock_file_path)
        captured["lock_file"] = lock_file
        return lock_file, acquired

    def spy_release(lock_file) -> None:
        lock_events.append("released")
        real_release(lock_file)

    monkeypatch.setattr(tavio_main, "configure_logging", lambda _path: logging.getLogger("tavio"))
    monkeypatch.setattr(tavio_main, "QApplication", lambda argv: fake_app)
    monkeypatch.setattr(tavio_main, "QIcon", lambda path: ("QIcon", path))
    monkeypatch.setattr(tavio_main.QMessageBox, "critical", staticmethod(fake_critical))
    monkeypatch.setattr(tavio_main, "acquire_single_instance_lock", spy_acquire)
    monkeypatch.setattr(tavio_main, "release_single_instance_lock", spy_release)
    monkeypatch.setattr(
        tavio_main.DatabaseManager,
        "from_app_paths",
        staticmethod(lambda _paths: failing_db_manager),
    )
    monkeypatch.setattr(tavio_main, "StartupService", _SpyStartupService)
    monkeypatch.setattr(
        tavio_main,
        "MainWindow",
        lambda **kwargs: window_constructions.append(kwargs),
    )

    expected_log_path = isolated_tavio_dir.resolve() / "logs" / "tavio.log"
    expected_db_path = isolated_tavio_dir.resolve() / "data" / "tavio.db"

    with caplog.at_level(logging.CRITICAL, logger="tavio.main"):
        exit_code = tavio_main.main()

    assert exit_code == 1
    assert failing_db_manager.initialize_calls == 1
    assert window_constructions == []
    assert diagnostics_calls == []
    assert fake_app.exec_calls == 0

    assert len(critical_dialogs) == 1
    _parent, title, message = critical_dialogs[0]
    assert "Database" in title
    assert "Simulated SQLite open failure" in message
    assert str(expected_log_path) in message

    critical_records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(critical_records) == 1
    assert "Database initialization failed" in critical_records[0].getMessage()
    assert critical_records[0].exc_info is not None

    assert lock_events == ["released"]
    assert captured["lock_file"].isLocked() is False
    assert not expected_db_path.exists()


def test_startup_releases_lock_when_diagnostics_fail_after_db_init(
    isolated_tavio_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_app = _FakeQApplication(["tavio"])
    critical_dialogs: list[tuple[object, str, str]] = []
    window_constructions: list[object] = []
    captured: dict[str, object] = {}

    class _OkDbManager:
        def __init__(self) -> None:
            self.initialize_calls = 0

        def initialize(self) -> SimpleNamespace:
            self.initialize_calls += 1
            return SimpleNamespace(initial_version=1, final_version=1, applied_versions=())

    ok_db_manager = _OkDbManager()

    class _FailingStartupService:
        def run_diagnostics(self) -> StartupDiagnosticReport:
            raise RuntimeError("Simulated OR-Tools failure")

    real_acquire = tavio_main.acquire_single_instance_lock
    real_release = tavio_main.release_single_instance_lock

    def spy_acquire(lock_file_path: Path):
        lock_file, acquired = real_acquire(lock_file_path)
        captured["lock_file"] = lock_file
        return lock_file, acquired

    monkeypatch.setattr(tavio_main, "QApplication", lambda argv: fake_app)
    monkeypatch.setattr(tavio_main, "QIcon", lambda path: ("QIcon", path))
    monkeypatch.setattr(
        tavio_main.QMessageBox,
        "critical",
        staticmethod(lambda parent, title, text: critical_dialogs.append((parent, title, text))),
    )
    monkeypatch.setattr(tavio_main, "acquire_single_instance_lock", spy_acquire)
    monkeypatch.setattr(tavio_main, "release_single_instance_lock", real_release)
    monkeypatch.setattr(
        tavio_main.DatabaseManager,
        "from_app_paths",
        staticmethod(lambda _paths: ok_db_manager),
    )
    monkeypatch.setattr(tavio_main, "StartupService", _FailingStartupService)
    monkeypatch.setattr(
        tavio_main,
        "MainWindow",
        lambda **kwargs: window_constructions.append(kwargs),
    )

    try:
        exit_code = tavio_main.main()
    finally:
        _cleanup_root_logging_handlers()

    assert exit_code == 1
    assert ok_db_manager.initialize_calls == 1
    assert window_constructions == []
    assert len(critical_dialogs) == 1
    assert "Simulated OR-Tools failure" in critical_dialogs[0][2]
    assert captured["lock_file"].isLocked() is False
    assert not (isolated_tavio_dir.resolve() / "data" / "tavio.db").exists()


def test_main_window_receives_database_manager_and_preserves_ui(
    isolated_tavio_dir: Path,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths = build_app_paths(isolated_tavio_dir)
    db_manager = DatabaseManager.from_app_paths(paths)
    initial_report = _make_dummy_report(objective_value=15)
    rerun_report = _make_dummy_report(objective_value=21)

    class _MockStartupService:
        def __init__(self) -> None:
            self.rerun_calls = 0

        def run_diagnostics(self) -> StartupDiagnosticReport:
            self.rerun_calls += 1
            return rerun_report

    mock_service = _MockStartupService()
    window = MainWindow(
        paths=paths,
        report=initial_report,
        startup_service=mock_service,  # type: ignore[arg-type]
        database_manager=db_manager,
    )
    try:
        assert window.database_manager is db_manager
        assert window._database_manager is db_manager
        assert not paths.db_path.exists()

        assert window._nav_list.count() == 3 + len(FUTURE_NAVIGATION_MODULES)
        assert window._dep_table.rowCount() == len(initial_report.dependencies)
        assert window._solver_summary_label.text() == initial_report.solver_result.format_summary()

        window._on_rerun_solver()
        assert mock_service.rerun_calls == 1
        assert window._solver_summary_label.text() == rerun_report.solver_result.format_summary()
        assert not paths.db_path.exists()
    finally:
        window.close()


def test_startup_service_remains_independent_of_database_package() -> None:
    service_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "tavio"
        / "services"
        / "startup_service.py"
    )
    tree = ast.parse(service_path.read_text(encoding="utf-8"), filename=str(service_path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("tavio.database")
                assert alias.name != "sqlite3"
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not node.module.startswith("tavio.database")
            assert node.module != "sqlite3"

    assert hasattr(StartupService, "run_diagnostics")
