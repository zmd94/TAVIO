"""Comprehensive tests for Phase 1 Task 2: School Administrators management."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMessageBox

from tavio.config import AppPaths, build_app_paths, ensure_app_directories
from tavio.database import (
    AdministratorInUseError,
    AdministratorNotFoundError,
    DatabaseManager,
    SchoolAdministratorRepository,
)
from tavio.domain import SchoolAdministratorInput
from tavio.services.school_administrator_service import (
    SchoolAdministratorService,
    SchoolAdministratorValidationError,
)
from tavio.services.startup_service import StartupDiagnosticReport
from tavio.solver.smoke_test import SolverSmokeResult
from tavio.ui import MainWindow, SchoolAdministratorsPage


def _setup_env(
    isolated_tavio_dir: Path,
) -> tuple[AppPaths, DatabaseManager, SchoolAdministratorRepository, SchoolAdministratorService]:
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()
    repo = SchoolAdministratorRepository(db_manager)
    service = SchoolAdministratorService(repo)
    return paths, db_manager, repo, service


def _make_dummy_report() -> StartupDiagnosticReport:
    return StartupDiagnosticReport(
        dependencies=(),
        solver_result=SolverSmokeResult(
            status_name="OPTIMAL",
            objective_value=15,
            assignments={"T1": 2, "T2": 1, "T3": 3},
            wall_time_ms=1.25,
        ),
    )


def test_add_administrator_and_list_ordering(isolated_tavio_dir: Path) -> None:
    _paths, db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    assert service.list_administrators(active_only=None) == []

    first = service.add_administrator(
        SchoolAdministratorInput(
            position_title="Guru Besar",
            administrator_name="Puan Aminah binti Ahmad",
        )
    )
    second = service.add_administrator(
        SchoolAdministratorInput(
            position_title="PK Pentadbiran",
            administrator_name="Encik Razak bin Hassan",
        )
    )
    third = service.add_administrator(
        SchoolAdministratorInput(
            position_title="Penyelaras Khas",
            administrator_name="Puan Mei Ling",
        )
    )

    assert first.is_active is True
    assert second.is_active is True
    assert third.is_active is True
    assert (first.sort_order, second.sort_order, third.sort_order) == (1, 2, 3)

    listed = service.list_administrators(active_only=True)
    assert [admin.id for admin in listed] == [first.id, second.id, third.id]

    # When sort_order ties exist, secondary sort by id ASC must be deterministic.
    with db_manager.transaction() as conn:
        conn.execute("UPDATE school_administrators SET sort_order = 1")

    tied = service.list_administrators(active_only=True)
    assert [admin.id for admin in tied] == [first.id, second.id, third.id]


@pytest.mark.parametrize("blank_position", ["", "   ", "\t\n"])
def test_rejects_empty_or_whitespace_position_title(
    isolated_tavio_dir: Path,
    blank_position: str,
) -> None:
    _paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    with pytest.raises(SchoolAdministratorValidationError, match="Position Title"):
        service.add_administrator(
            SchoolAdministratorInput(
                position_title=blank_position,
                administrator_name="Encik Ali",
            )
        )
    assert service.list_administrators(active_only=None) == []


@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_rejects_empty_or_whitespace_administrator_name(
    isolated_tavio_dir: Path,
    blank_name: str,
) -> None:
    _paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    with pytest.raises(SchoolAdministratorValidationError, match="Administrator Name"):
        service.add_administrator(
            SchoolAdministratorInput(
                position_title="Guru Besar",
                administrator_name=blank_name,
            )
        )
    assert service.list_administrators(active_only=None) == []


def test_trims_whitespace_on_add_and_edit(isolated_tavio_dir: Path) -> None:
    _paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    created = service.add_administrator(
        SchoolAdministratorInput(
            position_title="  Guru Besar  ",
            administrator_name="  Puan Aminah  ",
        )
    )
    assert created.position_title == "Guru Besar"
    assert created.administrator_name == "Puan Aminah"

    edited = service.edit_administrator(
        created.id,
        SchoolAdministratorInput(
            position_title="  Pengetua  ",
            administrator_name="  Puan Aminah binti Ahmad  ",
        ),
    )
    assert edited.id == created.id
    assert edited.position_title == "Pengetua"
    assert edited.administrator_name == "Puan Aminah binti Ahmad"
    assert edited.sort_order == created.sort_order
    assert edited.is_active is True
    assert edited.created_at == created.created_at


def test_edit_preserves_other_records_and_rejects_invalid_input(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    admin_a = service.add_administrator(
        SchoolAdministratorInput(position_title="Guru Besar", administrator_name="Puan A")
    )
    admin_b = service.add_administrator(
        SchoolAdministratorInput(position_title="PK HEM", administrator_name="Encik B")
    )

    with pytest.raises(SchoolAdministratorValidationError):
        service.edit_administrator(
            admin_a.id,
            SchoolAdministratorInput(position_title="   ", administrator_name="Puan A"),
        )

    assert service.get_administrator(admin_a.id) == admin_a
    assert service.get_administrator(admin_b.id) == admin_b

    updated_a = service.edit_administrator(
        admin_a.id,
        SchoolAdministratorInput(position_title="Pengetua", administrator_name="Puan A Baru"),
    )
    assert updated_a.position_title == "Pengetua"
    assert updated_a.administrator_name == "Puan A Baru"
    assert service.get_administrator(admin_b.id) == admin_b


def test_reorder_administrators_persists_across_app_restart(
    isolated_tavio_dir: Path,
) -> None:
    paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    a = service.add_administrator(
        SchoolAdministratorInput(position_title="Guru Besar", administrator_name="Satu")
    )
    b = service.add_administrator(
        SchoolAdministratorInput(position_title="PK 1", administrator_name="Dua")
    )
    c = service.add_administrator(
        SchoolAdministratorInput(position_title="PK HEM", administrator_name="Tiga")
    )

    service.move_administrator_up(c.id, active_only=True)
    assert [x.id for x in service.list_administrators(active_only=True)] == [a.id, c.id, b.id]

    service.move_administrator_down(a.id, active_only=True)
    assert [x.id for x in service.list_administrators(active_only=True)] == [c.id, a.id, b.id]

    # Simulate application restart with fresh DatabaseManager, repository, and service.
    restarted_db = DatabaseManager.from_app_paths(paths)
    restarted_db.initialize()
    restarted_service = SchoolAdministratorService(SchoolAdministratorRepository(restarted_db))

    reloaded = restarted_service.list_administrators(active_only=None)
    assert [x.id for x in reloaded] == [c.id, a.id, b.id]
    assert [x.sort_order for x in reloaded] == [1, 2, 3]
    assert [(x.position_title, x.administrator_name) for x in reloaded] == [
        ("PK HEM", "Tiga"),
        ("Guru Besar", "Satu"),
        ("PK 1", "Dua"),
    ]


def test_activate_deactivate_reactivate_and_signatory_candidate_filtering(
    isolated_tavio_dir: Path,
) -> None:
    _paths, db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    active_a = service.add_administrator(
        SchoolAdministratorInput(position_title="Guru Besar", administrator_name="Puan A")
    )
    target = service.add_administrator(
        SchoolAdministratorInput(position_title="PK Pentadbiran", administrator_name="Encik B")
    )

    # Link target in schedule_signatory_settings to verify deactivation preserves FK links.
    with db_manager.transaction() as conn:
        conn.execute(
            "UPDATE schedule_signatory_settings SET prepared_by_administrator_id = ? "
            "WHERE schedule_type = 'TEACHER'",
            (target.id,),
        )

    deactivated = service.deactivate_administrator(target.id)
    assert deactivated.is_active is False

    # Inactive administrator excluded from default active list and signatory candidates.
    assert [x.id for x in service.list_administrators(active_only=True)] == [active_a.id]
    assert [x.id for x in service.list_signatory_candidates()] == [active_a.id]
    assert [x.id for x in service.list_administrators(active_only=False)] == [target.id]
    assert [x.id for x in service.list_administrators(active_only=None)] == [
        active_a.id,
        target.id,
    ]

    # Existing signatory reference and other records remain untouched.
    with db_manager.connection() as conn:
        signatory_ref = conn.execute(
            "SELECT prepared_by_administrator_id FROM schedule_signatory_settings "
            "WHERE schedule_type = 'TEACHER'"
        ).fetchone()
        assert signatory_ref is not None
        assert int(signatory_ref["prepared_by_administrator_id"]) == target.id

    reactivated = service.activate_administrator(target.id)
    assert reactivated.is_active is True
    assert [x.id for x in service.list_administrators(active_only=True)] == [
        active_a.id,
        target.id,
    ]
    assert [x.id for x in service.list_signatory_candidates()] == [active_a.id, target.id]


def test_delete_unused_administrator_keeps_other_records_intact(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    kept = service.add_administrator(
        SchoolAdministratorInput(position_title="Guru Besar", administrator_name="Puan Kekal")
    )
    removable = service.add_administrator(
        SchoolAdministratorInput(position_title="PK Kokurikulum", administrator_name="Encik Padam")
    )

    service.delete_administrator(removable.id)

    assert service.get_administrator(removable.id) is None
    assert service.list_administrators(active_only=None) == [kept]

    with pytest.raises(AdministratorNotFoundError):
        service.delete_administrator(removable.id)


def test_delete_blocked_when_referenced_as_prepared_by_or_verified_by(
    isolated_tavio_dir: Path,
) -> None:
    _paths, db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    prepared_admin = service.add_administrator(
        SchoolAdministratorInput(position_title="PK Pentadbiran", administrator_name="Penyedia")
    )
    verified_admin = service.add_administrator(
        SchoolAdministratorInput(position_title="Guru Besar", administrator_name="Pengesah")
    )
    unused_admin = service.add_administrator(
        SchoolAdministratorInput(position_title="PK HEM", administrator_name="Tidak Digunakan")
    )

    with db_manager.transaction() as conn:
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET prepared_by_administrator_id = ? WHERE schedule_type = 'TEACHER'",
            (prepared_admin.id,),
        )
        conn.execute(
            "UPDATE schedule_signatory_settings "
            "SET verified_by_administrator_id = ? WHERE schedule_type = 'CLASS'",
            (verified_admin.id,),
        )

    with pytest.raises(AdministratorInUseError, match="Schedule Signatory Settings"):
        service.delete_administrator(prepared_admin.id)

    with pytest.raises(AdministratorInUseError, match="Schedule Signatory Settings"):
        service.delete_administrator(verified_admin.id)

    # Both referenced records and unrelated unused record remain intact; FK check passes.
    assert service.get_administrator(prepared_admin.id) is not None
    assert service.get_administrator(verified_admin.id) is not None
    assert service.get_administrator(unused_admin.id) is not None
    with db_manager.connection() as conn:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []


def test_school_administrators_page_ui_crud_filter_reorder_status_and_delete(
    isolated_tavio_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths, db_manager, _repo, service = _setup_env(isolated_tavio_dir)

    page = SchoolAdministratorsPage(service, auto_load=True)
    try:
        assert page._table.rowCount() == 0
        assert page.current_filter() is True

        # Empty validation error shown without inserting row.
        page._position_input.setText("   ")
        page._name_input.setText("Encik Uji")
        page._on_save_clicked()
        assert "Position Title is required" in page._form_status_label.text()
        assert page._table.rowCount() == 0

        # Add two administrators via form.
        page._position_input.setText("  Guru Besar  ")
        page._name_input.setText("  Puan Aminah  ")
        page._on_save_clicked()
        assert page._table.rowCount() == 1
        assert page._table.item(0, 1).text() == "Guru Besar"
        assert page._table.item(0, 2).text() == "Puan Aminah"

        page._position_input.setText("PK Pentadbiran")
        page._name_input.setText("Encik Razak")
        page._on_save_clicked()
        assert page._table.rowCount() == 2

        first_id = int(page._table.item(0, 0).data(Qt.ItemDataRole.UserRole))
        second_id = int(page._table.item(1, 0).data(Qt.ItemDataRole.UserRole))

        # Reorder: move second row up.
        page._table.selectRow(1)
        page._on_move_up_clicked()
        assert int(page._table.item(0, 0).data(Qt.ItemDataRole.UserRole)) == second_id
        assert int(page._table.item(1, 0).data(Qt.ItemDataRole.UserRole)) == first_id

        # Edit first row.
        page._start_edit(second_id)
        assert page._cancel_edit_button.isVisible() is True
        page._position_input.setText("PK Akademik")
        page._name_input.setText("Encik Razak Hassan")
        page._on_save_clicked()
        assert page._table.item(0, 1).text() == "PK Akademik"
        assert page._table.item(0, 2).text() == "Encik Razak Hassan"
        assert page._cancel_edit_button.isVisible() is False

        # Deactivate second_id -> hidden in Active Only, visible in Inactive Only.
        page._on_toggle_active(second_id, currently_active=True)
        assert page._table.rowCount() == 1
        assert int(page._table.item(0, 0).data(Qt.ItemDataRole.UserRole)) == first_id

        page.set_filter(False)
        assert page._table.rowCount() == 1
        assert int(page._table.item(0, 0).data(Qt.ItemDataRole.UserRole)) == second_id
        assert page._table.item(0, 3).text() == "Inactive"

        # Reactivate second_id -> visible again in Active Only.
        page._on_toggle_active(second_id, currently_active=False)
        page.set_filter(True)
        assert page._table.rowCount() == 2

        # Block deleting an administrator referenced in schedule_signatory_settings.
        with db_manager.transaction() as conn:
            conn.execute(
                "UPDATE schedule_signatory_settings "
                "SET prepared_by_administrator_id = ? WHERE schedule_type = 'TEACHER'",
                (first_id,),
            )

        warnings_shown: list[str] = []
        monkeypatch.setattr(
            "tavio.ui.school_administrators_page.QMessageBox.question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
        )
        monkeypatch.setattr(
            "tavio.ui.school_administrators_page.QMessageBox.warning",
            lambda _parent, _title, text, *_args: warnings_shown.append(text),
        )
        page._on_delete_clicked(first_id)
        assert len(warnings_shown) == 1
        assert "deactivate" in warnings_shown[0].lower()
        assert service.get_administrator(first_id) is not None

        # Delete unused administrator with confirmation Yes.
        page._on_delete_clicked(second_id)
        assert service.get_administrator(second_id) is None
        assert page._table.rowCount() == 1

        # Verify persisted data remains when opening a new page on a restarted DB manager.
        restarted_service = SchoolAdministratorService(
            SchoolAdministratorRepository(DatabaseManager.from_app_paths(paths))
        )
        reopened_page = SchoolAdministratorsPage(restarted_service, auto_load=True)
        try:
            assert reopened_page._table.rowCount() == 1
            assert int(reopened_page._table.item(0, 0).data(Qt.ItemDataRole.UserRole)) == first_id
        finally:
            reopened_page.close()
    finally:
        page.close()


def test_main_window_navigates_to_school_administrators_and_reloads(
    isolated_tavio_dir: Path,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()

    repo = SchoolAdministratorRepository(db_manager)
    repo.create_administrator(
        SchoolAdministratorInput(
            position_title="Guru Besar",
            administrator_name="Puan Aminah",
        )
    )

    class _MockStartupService:
        def run_diagnostics(self) -> StartupDiagnosticReport:
            return _make_dummy_report()

    window = MainWindow(
        paths=paths,
        report=_make_dummy_report(),
        startup_service=_MockStartupService(),  # type: ignore[arg-type]
        database_manager=db_manager,
    )
    try:
        assert window._nav_list.item(2).text() == "School Administrators (Phase 1)"
        window._nav_list.setCurrentRow(2)
        assert window._stack.currentWidget() is window._school_administrators_page
        assert window._school_administrators_page._table.rowCount() == 1
        assert window._school_administrators_page._table.item(0, 1).text() == "Guru Besar"
        assert window._school_administrators_page._table.item(0, 2).text() == "Puan Aminah"
    finally:
        window.close()
