"""Minimal Phase 0 PySide6 main window for TAVIO."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tavio import __version__
from tavio.config import APP_FULL_NAME, APP_NAME, AppPaths, get_asset_path
from tavio.services.startup_service import StartupDiagnosticReport, StartupService

logger = logging.getLogger(__name__)

FUTURE_NAVIGATION_MODULES: tuple[tuple[str, str], ...] = (
    ("School & Sessions (Phase 1)", "School profile, operating days, sessions, and bell schedules."),
    ("Master Data (Phase 2)", "Teachers, classes, education levels, subjects, rooms, and assignments."),
    ("Timetable Engine (Phase 3)", "OR-Tools CP-SAT cross-session timetable generation."),
    ("Manual Editor (Phase 4)", "Interactive Class/Teacher/Room timetable editor and version activation."),
    ("Absences & Relief (Phase 5)", "Teacher absences, automated relief batches, and audit logs."),
    ("Reports & Backup (Phase 6)", "ReportLab PDFs, Slip Guru Ganti, OpenPyXL exports, and backups."),
)


class MainWindow(QMainWindow):
    """Primary desktop window shell for TAVIO Phase 0."""

    def __init__(
        self,
        paths: AppPaths,
        report: StartupDiagnosticReport,
        startup_service: StartupService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._paths = paths
        self._report = report
        self._startup_service = startup_service

        self.setWindowTitle(f"{APP_NAME} — {APP_FULL_NAME}")
        self.setMinimumSize(1020, 660)

        icon_path = get_asset_path("TAVIO_icon.png")
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            logger.warning("Window icon not found at %s.", icon_path)

        self._nav_list = QListWidget()
        self._stack = QStackedWidget()
        self._solver_summary_label = QLabel()
        self._dep_table = QTableWidget(0, 4)

        self._build_ui()
        self._populate_diagnostics(report)
        self.statusBar().showMessage(f"{APP_NAME} v{__version__} — Phase 0 Skeleton Ready")

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar navigation placeholder
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
        sidebar_layout.setSpacing(12)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)

        brand_icon = QLabel()
        brand_icon_path = get_asset_path("TAVIO_icon.png")
        if brand_icon_path.is_file():
            pixmap = QPixmap(str(brand_icon_path))
            brand_icon.setPixmap(
                pixmap.scaled(
                    42,
                    42,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            brand_icon.setFixedSize(46, 46)
        else:
            logger.warning("Sidebar brand icon not found at %s.", brand_icon_path)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        brand_label = QLabel(APP_NAME)
        brand_label.setObjectName("BrandTitle")
        subtitle_label = QLabel("Timetable & Relief System")
        subtitle_label.setObjectName("BrandSubtitle")
        brand_text.addWidget(brand_label)
        brand_text.addWidget(subtitle_label)

        brand_row.addWidget(brand_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addLayout(brand_text, 1)

        self._nav_list.setObjectName("NavigationList")
        self._nav_list.addItem(QListWidgetItem("System Overview (Phase 0)"))
        for title, _desc in FUTURE_NAVIGATION_MODULES:
            self._nav_list.addItem(QListWidgetItem(title))

        self._nav_list.currentRowChanged.connect(self._stack.setCurrentIndex)

        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addWidget(self._nav_list, 1)

        # Main content stack
        self._stack.addWidget(self._build_overview_page())
        for title, description in FUTURE_NAVIGATION_MODULES:
            self._stack.addWidget(self._build_future_phase_page(title, description))

        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, 1)
        self.setCentralWidget(root)

        self._nav_list.setCurrentRow(0)

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel(f"{APP_NAME} — Phase 0 Environment & Packaging Verification")
        header.setObjectName("PageTitle")
        layout.addWidget(header)

        # Paths card
        paths_card = QFrame()
        paths_card.setObjectName("Card")
        paths_grid = QGridLayout(paths_card)
        paths_grid.setColumnStretch(1, 1)

        path_rows = (
            ("LocalAppData Base:", str(self._paths.base_dir)),
            ("Database Directory (reserved):", str(self._paths.db_path)),
            ("Backups Directory:", str(self._paths.backups_dir)),
            ("Log File:", str(self._paths.log_file_path)),
        )
        for row_idx, (label_text, value_text) in enumerate(path_rows):
            lbl = QLabel(label_text)
            lbl.setObjectName("FieldLabel")
            val = QLabel(value_text)
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            paths_grid.addWidget(lbl, row_idx, 0)
            paths_grid.addWidget(val, row_idx, 1)

        layout.addWidget(paths_card)

        # Dependencies table
        dep_title = QLabel("Verified Runtime Dependencies")
        dep_title.setObjectName("SectionTitle")
        layout.addWidget(dep_title)

        self._dep_table.setHorizontalHeaderLabels(["Package", "Import", "Version", "Status"])
        self._dep_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._dep_table.verticalHeader().setVisible(False)
        self._dep_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._dep_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._dep_table.setFixedHeight(170)
        layout.addWidget(self._dep_table)

        # Solver smoke test card
        solver_card = QFrame()
        solver_card.setObjectName("Card")
        solver_layout = QVBoxLayout(solver_card)
        solver_header = QLabel("OR-Tools CP-SAT Smoke Test")
        solver_header.setObjectName("SectionTitle")

        self._solver_summary_label.setWordWrap(True)
        self._solver_summary_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        rerun_btn = QPushButton("Re-run CP-SAT Verification")
        rerun_btn.setFixedWidth(210)
        rerun_btn.clicked.connect(self._on_rerun_solver)

        solver_layout.addWidget(solver_header)
        solver_layout.addWidget(self._solver_summary_label)
        solver_layout.addWidget(rerun_btn)
        layout.addWidget(solver_card)

        layout.addStretch(1)
        return page

    def _build_future_phase_page(self, title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("PageTitle")

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        notice = QLabel(
            "Not yet implemented in Phase 0.\n\n"
            f"Planned scope: {description}"
        )
        notice.setWordWrap(True)
        card_layout.addWidget(notice)

        layout.addWidget(heading)
        layout.addWidget(card)
        layout.addStretch(1)
        return page

    def _populate_diagnostics(self, report: StartupDiagnosticReport) -> None:
        self._dep_table.setRowCount(len(report.dependencies))
        for row_idx, dep in enumerate(report.dependencies):
            status_text = "OK" if dep.available else f"FAILED: {dep.error}"
            values = (dep.display_name, dep.import_name, dep.version, status_text)
            for col_idx, val in enumerate(values):
                item = QTableWidgetItem(val)
                self._dep_table.setItem(row_idx, col_idx, item)

        self._solver_summary_label.setText(report.solver_result.format_summary())

    def _on_rerun_solver(self) -> None:
        try:
            report = self._startup_service.run_diagnostics()
            self._populate_diagnostics(report)
            self.statusBar().showMessage("CP-SAT verification completed successfully.", 5000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("CP-SAT re-verification failed")
            self._solver_summary_label.setText(f"Verification failed: {exc}")
            self.statusBar().showMessage("CP-SAT verification failed.", 5000)
