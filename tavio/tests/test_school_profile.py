"""Comprehensive tests for Phase 1 Task 1: School Profile & School Logo management."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication, QMessageBox

from tavio.config import (
    SCHOOL_LOGO_RELATIVE_PATH,
    AppPaths,
    build_app_paths,
    ensure_app_directories,
)
from tavio.database import DatabaseError, DatabaseManager, SchoolProfileRepository
from tavio.domain import SchoolProfileInput
from tavio.services import (
    MAX_LOGO_DIMENSION,
    MAX_LOGO_FILE_SIZE_BYTES,
    SchoolLogoError,
    SchoolLogoService,
    SchoolProfileService,
    SchoolProfileValidationError,
)
from tavio.services.startup_service import (
    SolverVerificationResult,
    StartupDiagnosticReport,
)
from tavio.ui import MainWindow, SchoolProfilePage


def _setup_env(isolated_tavio_dir: Path) -> tuple[AppPaths, DatabaseManager, SchoolProfileService]:
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()
    service = SchoolProfileService(
        repository=SchoolProfileRepository(db_manager),
        logo_service=SchoolLogoService(),
        paths=paths,
    )
    return paths, db_manager, service


def _create_image_file(
    path: Path,
    *,
    fmt: str,
    size: tuple[int, int],
    mode: str = "RGB",
    color: tuple[int, ...] = (30, 80, 150),
) -> Path:
    img = Image.new(mode, size, color)
    img.save(path, format=fmt)
    return path


def _make_dummy_report() -> StartupDiagnosticReport:
    return StartupDiagnosticReport(
        dependencies=(),
        solver_result=SolverVerificationResult(
            success=True,
            status_name="OPTIMAL",
            objective_value=1,
            assigned_slots={"Ali": "Mon P1"},
        ),
    )


def test_repository_empty_create_update_and_preserve_principal_name(
    isolated_tavio_dir: Path,
) -> None:
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()
    repo = SchoolProfileRepository(db_manager)

    assert repo.get_profile() is None

    created = repo.upsert_profile(
        SchoolProfileInput(
            school_name="SK Seri Melati",
            school_code="BBA1001",
            school_week_group="B",
            address="Jalan Melati 1",
            phone="03-12345678",
            email="bba1001@moe.edu.my",
            logo_path=None,
        )
    )
    assert created.id == 1
    assert created.school_name == "SK Seri Melati"
    assert created.school_code == "BBA1001"
    assert created.school_week_group == "B"
    assert created.principal_name is None
    assert created.logo_path is None

    # Simulate legacy principal_name already populated in school_profile.
    with db_manager.transaction() as conn:
        conn.execute(
            "UPDATE school_profile SET principal_name = ? WHERE id = 1",
            ("Puan Aminah binti Ahmad",),
        )

    updated = repo.upsert_profile(
        SchoolProfileInput(
            school_name="SK Seri Melati Baru",
            school_code="BBA1002",
            school_week_group="A",
            address=None,
            phone="09-8765432",
            email=None,
            logo_path="assets/school_logo.png",
        )
    )
    assert updated.school_name == "SK Seri Melati Baru"
    assert updated.school_code == "BBA1002"
    assert updated.school_week_group == "A"
    assert updated.address is None
    assert updated.phone == "09-8765432"
    assert updated.email is None
    assert updated.logo_path == "assets/school_logo.png"
    assert updated.principal_name == "Puan Aminah binti Ahmad"
    assert updated.created_at == created.created_at


def test_service_validates_required_fields_week_group_and_email(
    isolated_tavio_dir: Path,
) -> None:
    _paths, _db_manager, service = _setup_env(isolated_tavio_dir)

    with pytest.raises(SchoolProfileValidationError, match="School Name"):
        service.save_profile(
            SchoolProfileInput(school_name="   ", school_code="BBA1001", school_week_group="B")
        )

    with pytest.raises(SchoolProfileValidationError, match="School Code"):
        service.save_profile(
            SchoolProfileInput(school_name="SK Uji", school_code="  ", school_week_group="B")
        )

    with pytest.raises(SchoolProfileValidationError, match="School Week Group"):
        service.save_profile(
            SchoolProfileInput(school_name="SK Uji", school_code="BBA1001", school_week_group="C")
        )

    with pytest.raises(SchoolProfileValidationError, match="valid school email"):
        service.save_profile(
            SchoolProfileInput(
                school_name="SK Uji",
                school_code="BBA1001",
                school_week_group="A",
                email="not-an-email",
            )
        )

    with pytest.raises(SchoolProfileValidationError, match="escapes"):
        service.save_profile(
            SchoolProfileInput(
                school_name="SK Uji",
                school_code="BBA1001",
                school_week_group="A",
                logo_path="../outside.png",
            )
        )

    saved = service.save_profile(
        SchoolProfileInput(
            school_name="  SK Taman Ilmu  ",
            school_code="  JBA2001 ",
            school_week_group="a",
            address="   ",
            phone="  07-2223333  ",
            email="  jba2001@moe.edu.my  ",
        )
    )
    assert saved.school_name == "SK Taman Ilmu"
    assert saved.school_code == "JBA2001"
    assert saved.school_week_group == "A"
    assert saved.address is None
    assert saved.phone == "07-2223333"
    assert saved.email == "jba2001@moe.edu.my"


@pytest.mark.parametrize(
    ("filename", "fmt"),
    [
        ("badge.png", "PNG"),
        ("badge.jpg", "JPEG"),
        ("badge.jpeg", "JPEG"),
    ],
)
def test_upload_valid_png_jpg_jpeg_saves_optimized_png_and_relative_db_path(
    isolated_tavio_dir: Path,
    tmp_path: Path,
    filename: str,
    fmt: str,
) -> None:
    paths, db_manager, service = _setup_env(isolated_tavio_dir)
    service.save_profile(
        SchoolProfileInput(
            school_name="SMK Seri Bayu",
            school_code="WEA0001",
            school_week_group="B",
        )
    )
    src = _create_image_file(tmp_path / filename, fmt=fmt, size=(420, 260))

    updated_profile, info, rel_path = service.upload_logo(src)

    assert rel_path == SCHOOL_LOGO_RELATIVE_PATH
    assert updated_profile is not None
    assert updated_profile.logo_path == "assets/school_logo.png"
    assert info.output_path == paths.school_logo_path
    assert paths.school_logo_path.is_file()
    assert not info.was_resized
    assert info.final_size == (420, 260)

    with Image.open(paths.school_logo_path) as saved_img:
        assert saved_img.format == "PNG"
        assert saved_img.size == (420, 260)

    with db_manager.connection() as conn:
        raw_logo_path = conn.execute("SELECT logo_path FROM school_profile WHERE id = 1").fetchone()[0]
    assert raw_logo_path == "assets/school_logo.png"


def test_upload_preserves_png_transparency(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    src = tmp_path / "transparent.png"
    img = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    for x in range(50, 150):
        for y in range(50, 150):
            img.putpixel((x, y), (47, 85, 151, 255))
    img.save(src, format="PNG")

    _profile, info, _rel = service.upload_logo(src)
    assert info.has_transparency is True

    with Image.open(paths.school_logo_path) as saved_img:
        assert saved_img.format == "PNG"
        assert saved_img.mode == "RGBA"
        assert saved_img.getpixel((5, 5))[3] == 0
        assert saved_img.getpixel((100, 100))[3] == 255


def test_upload_palette_png_with_transparency_preserves_alpha(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    src = tmp_path / "palette_alpha.png"
    rgba = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
    for x in range(40, 140):
        for y in range(40, 140):
            rgba.putpixel((x, y), (20, 110, 60, 255))
    palette_img = rgba.convert("P", palette=Image.Palette.ADAPTIVE)
    palette_img.save(src, format="PNG", transparency=palette_img.getpixel((0, 0)))

    _profile, info, _rel = service.upload_logo(src)
    assert info.has_transparency is True
    with Image.open(paths.school_logo_path) as saved_img:
        assert saved_img.mode == "RGBA"
        assert saved_img.getpixel((0, 0))[3] == 0
        assert saved_img.getpixel((90, 90))[3] == 255


@pytest.mark.parametrize(
    ("orig_size", "expected_size"),
    [
        ((4000, 2000), (MAX_LOGO_DIMENSION, 1500)),
        ((1800, 3600), (1500, MAX_LOGO_DIMENSION)),
    ],
)
def test_upload_oversized_image_is_proportionally_resized_without_cropping(
    isolated_tavio_dir: Path,
    tmp_path: Path,
    orig_size: tuple[int, int],
    expected_size: tuple[int, int],
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    src = tmp_path / "large_logo.png"
    # Distinct corner & center colors verify image is resized proportionally, not cropped.
    img = Image.new("RGB", orig_size, (200, 200, 200))
    img.putpixel((0, 0), (255, 0, 0))
    img.putpixel((orig_size[0] - 1, orig_size[1] - 1), (0, 0, 255))
    img.save(src, format="PNG")

    _profile, info, _rel = service.upload_logo(src)
    assert info.was_resized is True
    assert info.original_size == orig_size
    assert info.final_size == expected_size

    with Image.open(paths.school_logo_path) as saved_img:
        assert saved_img.format == "PNG"
        assert saved_img.size == expected_size
        assert max(saved_img.size) == MAX_LOGO_DIMENSION


@pytest.mark.parametrize("small_size", [(127, 200), (200, 127), (64, 64)])
def test_upload_rejects_undersized_image_without_upscaling(
    isolated_tavio_dir: Path,
    tmp_path: Path,
    small_size: tuple[int, int],
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    src = _create_image_file(tmp_path / "too_small.png", fmt="PNG", size=small_size)

    with pytest.raises(SchoolLogoError, match="128x128"):
        service.upload_logo(src)
    assert not paths.school_logo_path.exists()


def test_upload_rejects_file_exceeding_5mb_and_empty_file(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)

    oversized_file = tmp_path / "over_5mb.png"
    oversized_file.write_bytes(b"A" * (MAX_LOGO_FILE_SIZE_BYTES + 1))
    with pytest.raises(SchoolLogoError, match="5 MB"):
        service.upload_logo(oversized_file)

    empty_file = tmp_path / "empty.png"
    empty_file.write_bytes(b"")
    with pytest.raises(SchoolLogoError, match="empty"):
        service.upload_logo(empty_file)

    assert not paths.school_logo_path.exists()


def test_upload_rejects_non_image_unsupported_format_and_corrupted_files(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)

    fake_png = tmp_path / "fake.png"
    fake_png.write_text("not really an image", encoding="utf-8")
    with pytest.raises(SchoolLogoError):
        service.upload_logo(fake_png)

    gif_disguised_as_png = _create_image_file(tmp_path / "disguised.png", fmt="GIF", size=(256, 256))
    with pytest.raises(SchoolLogoError, match="Unsupported image format"):
        service.upload_logo(gif_disguised_as_png)

    valid_png = _create_image_file(tmp_path / "valid_src.png", fmt="PNG", size=(256, 256))
    raw_bytes = valid_png.read_bytes()
    corrupted_png = tmp_path / "corrupted.png"
    corrupted_png.write_bytes(raw_bytes[: len(raw_bytes) // 2])
    with pytest.raises(SchoolLogoError):
        service.upload_logo(corrupted_png)

    assert not paths.school_logo_path.exists()


def test_failed_replacement_preserves_existing_logo_and_db_path(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    service.save_profile(
        SchoolProfileInput(school_name="SK Stabil", school_code="BBA5555", school_week_group="B")
    )
    good_src = _create_image_file(
        tmp_path / "good.png",
        fmt="PNG",
        size=(300, 300),
        color=(10, 90, 170),
    )
    service.upload_logo(good_src)
    original_bytes = paths.school_logo_path.read_bytes()

    bad_src = _create_image_file(tmp_path / "bad_small.jpg", fmt="JPEG", size=(100, 100))
    with pytest.raises(SchoolLogoError):
        service.upload_logo(bad_src)

    assert paths.school_logo_path.read_bytes() == original_bytes
    view = service.load_profile()
    assert view.profile is not None
    assert view.profile.logo_path == "assets/school_logo.png"
    assert view.logo_exists is True


def test_db_failure_after_logo_processing_restores_previous_logo_file(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    service.save_profile(
        SchoolProfileInput(school_name="SK Rollback", school_code="BBA6666", school_week_group="B")
    )
    first_src = _create_image_file(
        tmp_path / "first.png",
        fmt="PNG",
        size=(240, 240),
        color=(15, 45, 95),
    )
    service.upload_logo(first_src)
    first_bytes = paths.school_logo_path.read_bytes()

    second_src = _create_image_file(
        tmp_path / "second.png",
        fmt="PNG",
        size=(260, 260),
        color=(200, 40, 40),
    )
    with (
        patch.object(
            service._repository,
            "update_logo_path",
            side_effect=DatabaseError("Simulated DB lock"),
        ),
        pytest.raises(DatabaseError, match="Simulated DB lock"),
    ):
        service.upload_logo(second_src)

    assert paths.school_logo_path.read_bytes() == first_bytes


def test_remove_logo_clears_db_path_and_deletes_only_school_logo(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    service.save_profile(
        SchoolProfileInput(school_name="SK Padam", school_code="BBA7777", school_week_group="A")
    )
    src = _create_image_file(tmp_path / "logo.jpg", fmt="JPEG", size=(220, 220))
    service.upload_logo(src)

    unrelated_asset = paths.assets_dir / "keep_me.txt"
    unrelated_asset.write_text("keep", encoding="utf-8")

    updated = service.remove_logo()
    assert updated is not None
    assert updated.logo_path is None
    assert not paths.school_logo_path.exists()
    assert unrelated_asset.is_file()


def test_load_profile_handles_missing_logo_file_on_disk_gracefully(
    isolated_tavio_dir: Path,
    tmp_path: Path,
) -> None:
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)
    service.save_profile(
        SchoolProfileInput(school_name="SK Hilang", school_code="BBA8888", school_week_group="B")
    )
    src = _create_image_file(tmp_path / "logo.png", fmt="PNG", size=(200, 200))
    service.upload_logo(src)
    paths.school_logo_path.unlink()

    view = service.load_profile()
    assert view.profile is not None
    assert view.profile.logo_path == "assets/school_logo.png"
    assert view.logo_exists is False
    assert view.logo_missing_on_disk is True
    assert view.logo_file_path is None


def test_school_profile_page_load_save_upload_remove_and_missing_logo_ui(
    isolated_tavio_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths, _db_manager, service = _setup_env(isolated_tavio_dir)

    page = SchoolProfilePage(service, auto_load=True)
    try:
        assert page._remove_logo_button.isEnabled() is False
        assert page._upload_logo_button.text() == "Upload Logo"

        # Validation error shown without persisting invalid record.
        page._school_name_input.setText("   ")
        page._school_code_input.setText("BBA9999")
        page._on_save_clicked()
        assert "School Name is required" in page._form_status_label.text()
        assert service.load_profile().profile is None

        # Valid save updates database.
        page._school_name_input.setText("SK UI Test")
        page._school_code_input.setText("BBA9999")
        page._set_week_group("A")
        page._address_input.setPlainText("1 Jalan Sekolah")
        page._phone_input.setText("03-99998888")
        page._email_input.setText("ui@moe.edu.my")
        page._on_save_clicked()

        loaded = service.load_profile()
        assert loaded.profile is not None
        assert loaded.profile.school_name == "SK UI Test"
        assert loaded.profile.school_week_group == "A"
        assert "saved successfully" in page._form_status_label.text()

        # Upload logo via mocked file dialog.
        logo_src = _create_image_file(tmp_path / "ui_logo.jpg", fmt="JPEG", size=(300, 300))
        monkeypatch.setattr(
            "tavio.ui.school_profile_page.QFileDialog.getOpenFileName",
            lambda *_args, **_kwargs: (str(logo_src), "Image Files (*.png *.jpg *.jpeg)"),
        )
        page._on_upload_logo_clicked()

        assert paths.school_logo_path.is_file()
        assert page._upload_logo_button.text() == "Replace Logo"
        assert page._remove_logo_button.isEnabled() is True
        assert not page._logo_preview_label.pixmap().isNull()

        # Reloading when file is missing on disk shows graceful fallback without crashing.
        paths.school_logo_path.unlink()
        page.reload()
        assert "missing on disk" in page._logo_preview_label.text().lower()
        assert page._remove_logo_button.isEnabled() is True

        # Re-upload then remove logo via mocked confirmation dialog.
        page._on_upload_logo_clicked()
        assert paths.school_logo_path.is_file()
        monkeypatch.setattr(
            "tavio.ui.school_profile_page.QMessageBox.question",
            lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
        )
        page._on_remove_logo_clicked()
        assert not paths.school_logo_path.exists()
        assert page._remove_logo_button.isEnabled() is False
        assert page._upload_logo_button.text() == "Upload Logo"
        assert service.load_profile().profile is not None
        assert service.load_profile().profile.logo_path is None
    finally:
        page.close()


def test_main_window_navigates_to_school_profile_and_reloads(
    isolated_tavio_dir: Path,
) -> None:
    _app = QApplication.instance() or QApplication([])
    paths = ensure_app_directories(build_app_paths(isolated_tavio_dir))
    db_manager = DatabaseManager.from_app_paths(paths)
    db_manager.initialize()

    repo = SchoolProfileRepository(db_manager)
    repo.upsert_profile(
        SchoolProfileInput(
            school_name="SMK Integrasi",
            school_code="BEA1234",
            school_week_group="B",
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
        assert window._nav_list.item(1).text() == "School Profile (Phase 1)"
        window._nav_list.setCurrentRow(1)
        assert window._stack.currentWidget() is window._school_profile_page
        assert window._school_profile_page._school_name_input.text() == "SMK Integrasi"
        assert window._school_profile_page._school_code_input.text() == "BEA1234"
    finally:
        window.close()
