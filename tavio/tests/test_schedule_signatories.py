"""Comprehensive tests for Phase 1 Task 3: Schedule Signatories configuration."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from tavio.config import AppPaths, build_app_paths, ensure_app_directories
from tavio.database import (
    DatabaseError,
    DatabaseManager,
    InvalidSignatoryAdministratorError,
    ScheduleSignatoryRepository,
    SchoolAdministratorRepository,
)
from tavio.domain import (
    DEFAULT_SIGNATORY_LABEL_LANGUAGE,
    SCHEDULE_TYPE_CLASS,
    SCHEDULE_TYPE_SPECIAL_ROOM,
    SCHEDULE_TYPE_TEACHER,
    SCHEDULE_TYPES,
    SIGNATORY_LANGUAGE_ENGLISH,
    SIGNATORY_LANGUAGE_MALAY,
    ScheduleSignatoryInput,
    SchoolAdministratorInput,
)
from tavio.services.schedule_signatory_service import (
    ScheduleSignatoryService,
    ScheduleSignatoryValidationError,
)
from tavio.services.school_administrator_service import SchoolAdministratorService
from tavio.services.startup_service import StartupDiagnosticReport
from tavio.solver.smoke_test import SolverSmokeResult
from tavio.ui import MainWindow, ScheduleSignatoriesPage


def _setup_env(
    isolated_tavio_dir: Path,
) -> tuple[
    AppPaths,
    DatabaseManager,
    ScheduleSignatoryRepository,
    SchoolAdministratorService,
    ScheduleSignatoryService,
]:
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()
    signatory_repo = ScheduleSignatoryRepository(db_manager)
    admin_repo = SchoolAdministratorRepository(db_manager)
    admin_service = SchoolAdministratorService(admin_repo)
    signatory_service = ScheduleSignatoryService(signatory_repo, admin_repo)
    return paths, db_manager, signatory_repo, admin_service, signatory_service


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


def test_load_overview_returns_three_schedule_types_and_active_candidates(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)

    active_1 = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "SURAIDA BINTI MOHD JANI")
    )
    active_2 = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "AHMAD BIN ALI")
    )
    inactive = admin_service.add_administrator(
        SchoolAdministratorInput("PK HEM", "SALMAH BINTI HASSAN")
    )
    admin_service.deactivate_administrator(inactive.id)

    overview = signatory_service.load_overview()
    assert list(overview.details.keys()) == list(SCHEDULE_TYPES)
    assert [admin.id for admin in overview.active_candidates] == [active_1.id, active_2.id]
    assert overview.label_language == DEFAULT_SIGNATORY_LABEL_LANGUAGE
    for schedule_type in SCHEDULE_TYPES:
        detail = overview.details[schedule_type]
        assert detail.setting.prepared_by_administrator_id is None
        assert detail.setting.verified_by_administrator_id is None


def test_save_signatories_and_allow_same_admin_across_different_schedule_types(
    isolated_tavio_dir: Path,
) -> None:
    _paths, db_manager, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)

    admin_a = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "ENCIK RAZAK")
    )
    admin_b = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN SURAIDA")
    )

    saved_teacher = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_TEACHER,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    saved_class = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_CLASS,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    saved_room = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_SPECIAL_ROOM,
            prepared_by_administrator_id=admin_b.id,
            verified_by_administrator_id=admin_a.id,
        )
    )

    assert saved_teacher.prepared_by_administrator_id == admin_a.id
    assert saved_teacher.verified_by_administrator_id == admin_b.id
    assert saved_class.prepared_by_administrator_id == admin_a.id
    assert saved_class.verified_by_administrator_id == admin_b.id
    assert saved_room.prepared_by_administrator_id == admin_b.id
    assert saved_room.verified_by_administrator_id == admin_a.id

    with db_manager.connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM schedule_signatory_settings").fetchone()[0]
    assert count == 3


def test_rejects_same_administrator_for_both_roles_in_same_schedule_type(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    admin = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN SURAIDA")
    )

    with pytest.raises(
        ScheduleSignatoryValidationError,
        match="two different administrators",
    ):
        signatory_service.save_signatory_setting(
            ScheduleSignatoryInput(
                schedule_type=SCHEDULE_TYPE_TEACHER,
                prepared_by_administrator_id=admin.id,
                verified_by_administrator_id=admin.id,
            )
        )

    overview = signatory_service.load_overview()
    assert overview.details[SCHEDULE_TYPE_TEACHER].setting.prepared_by_administrator_id is None
    assert overview.details[SCHEDULE_TYPE_TEACHER].setting.verified_by_administrator_id is None


def test_rejects_inactive_administrator_for_new_assignments(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    active_admin = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "ENCIK AKTIF")
    )
    inactive_admin = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN TIDAK AKTIF")
    )
    admin_service.deactivate_administrator(inactive_admin.id)

    with pytest.raises(ScheduleSignatoryValidationError, match="Inactive administrators"):
        signatory_service.save_signatory_setting(
            ScheduleSignatoryInput(
                schedule_type=SCHEDULE_TYPE_CLASS,
                prepared_by_administrator_id=inactive_admin.id,
                verified_by_administrator_id=active_admin.id,
            )
        )

    with pytest.raises(ScheduleSignatoryValidationError, match="Inactive administrators"):
        signatory_service.save_signatory_setting(
            ScheduleSignatoryInput(
                schedule_type=SCHEDULE_TYPE_CLASS,
                prepared_by_administrator_id=active_admin.id,
                verified_by_administrator_id=inactive_admin.id,
            )
        )


def test_clearing_assignments_to_null_persists(isolated_tavio_dir: Path) -> None:
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    admin_a = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "ENCIK A")
    )
    admin_b = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN B")
    )

    signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_TEACHER,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    cleared_one = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_TEACHER,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=None,
        )
    )
    assert cleared_one.prepared_by_administrator_id == admin_a.id
    assert cleared_one.verified_by_administrator_id is None

    cleared_both = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_TEACHER,
            prepared_by_administrator_id=None,
            verified_by_administrator_id=None,
        )
    )
    assert cleared_both.prepared_by_administrator_id is None
    assert cleared_both.verified_by_administrator_id is None


def test_preserves_existing_assignment_when_administrator_becomes_inactive(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    admin_a = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "ENCIK A")
    )
    admin_b = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN B")
    )
    replacement = admin_service.add_administrator(
        SchoolAdministratorInput("PK HEM", "PUAN PENGGANTI")
    )

    signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_SPECIAL_ROOM,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    admin_service.deactivate_administrator(admin_a.id)

    overview = signatory_service.load_overview()
    detail = overview.details[SCHEDULE_TYPE_SPECIAL_ROOM]
    assert detail.setting.prepared_by_administrator_id == admin_a.id
    assert detail.prepared_by_is_inactive is True
    assert detail.verified_by_is_inactive is False
    assert [a.id for a in overview.active_candidates] == [admin_b.id, replacement.id]

    # User can replace inactive assignment with an active administrator.
    replaced = signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_SPECIAL_ROOM,
            prepared_by_administrator_id=replacement.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    assert replaced.prepared_by_administrator_id == replacement.id


def test_rejects_invalid_administrator_ids_in_service_and_repository_fk(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    valid_admin = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN SURAIDA")
    )

    with pytest.raises(ScheduleSignatoryValidationError, match="does not exist"):
        signatory_service.save_signatory_setting(
            ScheduleSignatoryInput(
                schedule_type=SCHEDULE_TYPE_TEACHER,
                prepared_by_administrator_id=9999,
                verified_by_administrator_id=valid_admin.id,
            )
        )

    with pytest.raises(InvalidSignatoryAdministratorError):
        repo.update_setting(
            ScheduleSignatoryInput(
                schedule_type=SCHEDULE_TYPE_TEACHER,
                prepared_by_administrator_id=valid_admin.id,
                verified_by_administrator_id=9999,
            )
        )


def test_persistence_across_restart_and_transaction_rollback_on_failure(
    isolated_tavio_dir: Path,
) -> None:
    paths, db_manager, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)
    admin_a = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "ENCIK A")
    )
    admin_b = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "PUAN B")
    )

    signatory_service.save_signatory_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_TEACHER,
            prepared_by_administrator_id=admin_a.id,
            verified_by_administrator_id=admin_b.id,
        )
    )
    signatory_service.set_label_language(SIGNATORY_LANGUAGE_MALAY)

    # Simulate transaction failure midway through repository update; prior state must remain.
    with patch.object(db_manager, "transaction") as mock_tx:
        class _BrokenConn:
            def execute(self, *_args: object, **_kwargs: object) -> None:
                raise sqlite3.OperationalError("Simulated disk I/O error")

        mock_tx.return_value.__enter__.return_value = _BrokenConn()
        mock_tx.return_value.__exit__.return_value = False
        with pytest.raises(DatabaseError, match="Simulated disk I/O error"):
            signatory_service.save_signatory_setting(
                ScheduleSignatoryInput(
                    schedule_type=SCHEDULE_TYPE_TEACHER,
                    prepared_by_administrator_id=None,
                    verified_by_administrator_id=None,
                )
            )

    # Simulate application restart / reinitialization.
    restarted_db = DatabaseManager.from_app_paths(paths)
    restarted_db.initialize()
    restarted_service = ScheduleSignatoryService(
        ScheduleSignatoryRepository(restarted_db),
        SchoolAdministratorRepository(restarted_db),
    )

    reloaded = restarted_service.load_overview()
    teacher_setting = reloaded.details[SCHEDULE_TYPE_TEACHER].setting
    assert teacher_setting.prepared_by_administrator_id == admin_a.id
    assert teacher_setting.verified_by_administrator_id == admin_b.id
    assert reloaded.label_language == SIGNATORY_LANGUAGE_MALAY


def test_signatory_label_language_validation_and_persistence(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db, _repo, _admin_service, signatory_service = _setup_env(isolated_tavio_dir)

    assert signatory_service.get_label_language() == SIGNATORY_LANGUAGE_ENGLISH
    assert signatory_service.set_label_language("ms") == SIGNATORY_LANGUAGE_MALAY
    assert signatory_service.get_label_language() == SIGNATORY_LANGUAGE_MALAY
    assert signatory_service.set_label_language("EN") == SIGNATORY_LANGUAGE_ENGLISH

    with pytest.raises(ScheduleSignatoryValidationError, match="Unsupported signatory label language"):
        signatory_service.set_label_language("FR")


def test_schedule_signatories_page_ui_mutual_exclusion_language_inactive_and_save(
    isolated_tavio_dir: Path,
) -> None:
    _app = QApplication.instance() or QApplication([])
    _paths, _db, _repo, admin_service, signatory_service = _setup_env(isolated_tavio_dir)

    admin_1 = admin_service.add_administrator(
        SchoolAdministratorInput("GURU BESAR", "SURAIDA BINTI MOHD JANI")
    )
    admin_2 = admin_service.add_administrator(
        SchoolAdministratorInput("PK PENTADBIRAN", "AHMAD BIN ALI")
    )
    admin_3 = admin_service.add_administrator(
        SchoolAdministratorInput("PK HEM", "SALMAH BINTI HASSAN")
    )

    page = ScheduleSignatoriesPage(signatory_service, auto_load=True)
    try:
        teacher_card = page._cards[SCHEDULE_TYPE_TEACHER]
        class_card = page._cards[SCHEDULE_TYPE_CLASS]
        room_card = page._cards[SCHEDULE_TYPE_SPECIAL_ROOM]

        # Formatting & unassigned option present.
        assert teacher_card.prepared_combo.itemText(0) == "(Unassigned)"
        assert teacher_card.prepared_combo.itemData(0) is None
        assert (
            teacher_card.prepared_combo.itemText(1)
            == "GURU BESAR \u2014 SURAIDA BINTI MOHD JANI"
        )

        # Mutual exclusion: selecting admin_1 in Prepared By removes admin_1 from Verified By.
        idx_1 = teacher_card.prepared_combo.findData(admin_1.id)
        assert idx_1 > 0
        teacher_card.prepared_combo.setCurrentIndex(idx_1)
        assert teacher_card.verified_combo.findData(admin_1.id) == -1
        assert teacher_card.verified_combo.findData(admin_2.id) > 0

        # Select admin_2 in Verified By -> admin_2 removed from Prepared By.
        idx_2 = teacher_card.verified_combo.findData(admin_2.id)
        teacher_card.verified_combo.setCurrentIndex(idx_2)
        assert teacher_card.prepared_combo.findData(admin_2.id) == -1

        # Save Teacher Schedule signatories.
        page._on_save_card_clicked(SCHEDULE_TYPE_TEACHER)
        assert teacher_card.status_label.isHidden() is False
        assert "saved successfully" in teacher_card.status_label.text()

        # Language switch updates labels across all three cards without altering saved data.
        ms_idx = page._language_combo.findData(SIGNATORY_LANGUAGE_MALAY)
        page._language_combo.setCurrentIndex(ms_idx)
        for card in (teacher_card, class_card, room_card):
            assert card.prepared_label.text() == "DISEDIAKAN OLEH"
            assert card.verified_label.text() == "DISAHKAN OLEH"

        en_idx = page._language_combo.findData(SIGNATORY_LANGUAGE_ENGLISH)
        page._language_combo.setCurrentIndex(en_idx)
        for card in (teacher_card, class_card, room_card):
            assert card.prepared_label.text() == "PREPARED BY"
            assert card.verified_label.text() == "VERIFIED BY"

        # Deactivating assigned admin_1 preserves existing assignment and shows UI warning.
        admin_service.deactivate_administrator(admin_1.id)
        page.reload()
        assert teacher_card.inactive_warning_label.isHidden() is False
        assert teacher_card.prepared_combo.currentData() == admin_1.id
        assert "[Inactive]" in teacher_card.prepared_combo.currentText()
        assert teacher_card.prepared_combo.findData(admin_3.id) > 0

        # Replace inactive admin_1 with active admin_3 and save.
        teacher_card.prepared_combo.setCurrentIndex(teacher_card.prepared_combo.findData(admin_3.id))
        page._on_save_card_clicked(SCHEDULE_TYPE_TEACHER)
        assert teacher_card.inactive_warning_label.isHidden() is True
        assert signatory_service.load_overview().details[
            SCHEDULE_TYPE_TEACHER
        ].setting.prepared_by_administrator_id == admin_3.id
    finally:
        page.close()


def test_main_window_navigates_to_schedule_signatories_and_reloads(
    isolated_tavio_dir: Path,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()

    admin_repo = SchoolAdministratorRepository(db_manager)
    admin = admin_repo.create_administrator(
        SchoolAdministratorInput("GURU BESAR", "SURAIDA BINTI MOHD JANI")
    )
    signatory_repo = ScheduleSignatoryRepository(db_manager)
    signatory_repo.update_setting(
        ScheduleSignatoryInput(
            schedule_type=SCHEDULE_TYPE_CLASS,
            prepared_by_administrator_id=admin.id,
            verified_by_administrator_id=None,
        )
    )
    signatory_repo.set_label_language(SIGNATORY_LANGUAGE_MALAY)

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
        school_setup_item = window._nav_list.topLevelItem(1)
        assert school_setup_item.text(0) == "School Setup"
        signatories_item = school_setup_item.child(2)
        assert signatories_item.text(0) == "Schedule Signatories"
        assert (
            signatories_item.data(0, Qt.ItemDataRole.UserRole) == "schedule_signatories"
        )
        window._nav_list.setCurrentItem(signatories_item)
        assert window._stack.currentWidget() is window._schedule_signatories_page
        assert window._schedule_signatories_page.current_label_language() == SIGNATORY_LANGUAGE_MALAY
        class_card = window._schedule_signatories_page._cards[SCHEDULE_TYPE_CLASS]
        assert class_card.prepared_label.text() == "DISEDIAKAN OLEH"
        assert class_card.prepared_combo.currentData() == admin.id
    finally:
        window.close()
