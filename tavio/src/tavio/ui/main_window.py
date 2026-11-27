"""Minimal Phase 0 PySide6 main window for TAVIO."""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tavio import __version__
from tavio.config import APP_FULL_NAME, APP_NAME, AppPaths, get_asset_path
from tavio.database import (
    DatabaseManager,
    ScheduleSignatoryRepository,
    SchoolAdministratorRepository,
    SchoolProfileRepository,
)
from tavio.services.schedule_signatory_service import ScheduleSignatoryService
from tavio.services.school_administrator_service import SchoolAdministratorService
from tavio.services.school_logo_service import SchoolLogoService
from tavio.services.school_profile_service import SchoolProfileService
from tavio.services.startup_service import StartupDiagnosticReport, StartupService
from tavio.ui.schedule_signatories_page import ScheduleSignatoriesPage
from tavio.ui.school_administrators_page import SchoolAdministratorsPage
from tavio.ui.school_profile_page import SchoolProfilePage

logger = logging.getLogger(__name__)

FUTURE_NAVIGATION_MODULES: tuple[tuple[str, str], ...] = (
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
        database_manager: DatabaseManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._paths = paths
        self._report = report
        self._startup_service = startup_service
        self._database_manager = database_manager
        self._school_profile_service = SchoolProfileService(
            repository=SchoolProfileRepository(database_manager),
            logo_service=SchoolLogoService(),
            paths=paths,
        )
        admin_repository = SchoolAdministratorRepository(database_manager)
        self._school_administrator_service = SchoolAdministratorService(
            repository=admin_repository,
        )
        self._schedule_signatory_service = ScheduleSignatoryService(
            signatory_repository=ScheduleSignatoryRepository(database_manager),
            administrator_repository=admin_repository,
        )

        self.setWindowTitle(f"{APP_NAME} — {APP_FULL_NAME}")
        self.setMinimumSize(1020, 660)

        icon_path = get_asset_path("TAVIO_icon.png")
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))
        else:
            logger.warning("Window icon not found at %s.", icon_path)

        self._nav_list = QTreeWidget()
        self._sidebar: QFrame | None = None
        self._sidebar_layout: QVBoxLayout | None = None
        self._brand_row: QHBoxLayout | None = None
        self._brand_icon_label: QLabel | None = None
        self._brand_icon_pixmap: QPixmap | None = None
        self._brand_text_widget: QWidget | None = None
        self._sidebar_toggle_button: QPushButton | None = None
        self._sidebar_collapsed = False
        self._page_indexes: dict[str, int] = {}
        self._stack = QStackedWidget()
        self._solver_summary_label = QLabel()
        self._dep_table = QTableWidget(0, 4)
        self._school_profile_page = SchoolProfilePage(
            self._school_profile_service,
            auto_load=False,
        )
        self._school_administrators_page = SchoolAdministratorsPage(
            self._school_administrator_service,
            auto_load=False,
        )
        self._schedule_signatories_page = ScheduleSignatoriesPage(
            self._schedule_signatory_service,
            auto_load=False,
        )

        self._build_ui()
        self._populate_diagnostics(report)
        self.statusBar().showMessage(
            f"{APP_NAME} v{__version__} — Phase 1 School Profile, Administrators & Signatories Ready"
        )

    @property
    def database_manager(self) -> DatabaseManager:
        """Return the initialized DatabaseManager instance."""
        return self._database_manager

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar navigation placeholder
        sidebar = QFrame()
        self._sidebar = sidebar
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(250)
        sidebar_layout = QVBoxLayout(sidebar)
        self._sidebar_layout = sidebar_layout
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
        sidebar_layout.setSpacing(12)

        brand_row = QHBoxLayout()
        self._brand_row = brand_row
        brand_row.setSpacing(10)

        brand_icon = QLabel()
        self._brand_icon_label = brand_icon
        brand_icon_path = get_asset_path("TAVIO_icon.png")
        if brand_icon_path.is_file():
            pixmap = QPixmap(str(brand_icon_path))
            self._brand_icon_pixmap = pixmap
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

        brand_text_widget = QWidget()
        self._brand_text_widget = brand_text_widget
        brand_text = QVBoxLayout(brand_text_widget)
        brand_text.setContentsMargins(0, 0, 0, 0)
        brand_text.setSpacing(2)
        brand_label = QLabel(APP_NAME)
        brand_label.setObjectName("BrandTitle")
        subtitle_label = QLabel("Timetable & Relief System")
        subtitle_label.setObjectName("BrandSubtitle")
        brand_text.addWidget(brand_label)
        brand_text.addWidget(subtitle_label)

        brand_row.addWidget(brand_icon, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_row.addWidget(brand_text_widget, 1)
        toggle_button = QPushButton("‹")
        self._sidebar_toggle_button = toggle_button
        toggle_button.setObjectName("SidebarToggle")
        toggle_button.setFixedSize(28, 28)
        toggle_button.setToolTip("Minimize sidebar")
        toggle_button.setAccessibleName("Minimize sidebar")
        toggle_button.clicked.connect(self._toggle_sidebar)
        brand_row.addWidget(toggle_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self._nav_list.setObjectName("NavigationTree")
        self._nav_list.setIconSize(QSize(20, 20))
        self._nav_list.setHeaderHidden(True)
        self._nav_list.setRootIsDecorated(True)
        self._nav_list.setItemsExpandable(True)
        self._nav_list.setExpandsOnDoubleClick(False)
        self._nav_list.setIndentation(18)

        overview_item = QTreeWidgetItem(["System Overview (Phase 0)"])
        self._set_navigation_item_icon(overview_item, QStyle.StandardPixmap.SP_ComputerIcon)
        overview_item.setToolTip(0, "System Overview (Phase 0)")
        overview_item.setData(0, Qt.ItemDataRole.UserRole, "overview")
        self._nav_list.addTopLevelItem(overview_item)

        school_setup_item = QTreeWidgetItem(["School Setup"])
        self._set_navigation_item_icon(school_setup_item, QStyle.StandardPixmap.SP_DirIcon)
        school_setup_item.setToolTip(0, "School Setup")
        school_setup_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self._nav_list.addTopLevelItem(school_setup_item)
        for label, route, icon_name in (
            ("School Profile", "school_profile", QStyle.StandardPixmap.SP_FileIcon),
            ("School Administrators", "school_administrators", QStyle.StandardPixmap.SP_DirOpenIcon),
            ("Schedule Signatories", "schedule_signatories", QStyle.StandardPixmap.SP_FileDialogInfoView),
        ):
            child = QTreeWidgetItem([label])
            self._set_navigation_item_icon(child, icon_name)
            child.setToolTip(0, label)
            child.setData(0, Qt.ItemDataRole.UserRole, route)
            school_setup_item.addChild(child)

        self._nav_list.currentItemChanged.connect(self._on_navigation_changed)
        self._nav_list.itemClicked.connect(self._on_navigation_item_clicked)

        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addWidget(self._nav_list, 1)

        # Main content stack. Route keys keep navigation independent of tree row order.
        self._page_indexes["overview"] = self._stack.addWidget(self._build_overview_page())
        self._page_indexes["school_profile"] = self._stack.addWidget(
            self._school_profile_page
        )
        self._page_indexes["school_administrators"] = self._stack.addWidget(
            self._school_administrators_page
        )
        self._page_indexes["schedule_signatories"] = self._stack.addWidget(
            self._schedule_signatories_page
        )
        for index, (title, description) in enumerate(FUTURE_NAVIGATION_MODULES):
            route = f"future:{index}"
            item = QTreeWidgetItem([title])
            self._set_navigation_item_icon(item, QStyle.StandardPixmap.SP_FileDialogContentsView)
            item.setToolTip(0, f"{title}\n{description}")
            item.setData(0, Qt.ItemDataRole.UserRole, route)
            self._nav_list.addTopLevelItem(item)
            self._page_indexes[route] = self._stack.addWidget(
                self._build_future_phase_page(title, description)
            )

        self._nav_list.expandItem(school_setup_item)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, 1)
        self.setCentralWidget(root)

        self._nav_list.setCurrentItem(overview_item)

    def _set_navigation_item_icon(
        self,
        item: QTreeWidgetItem,
        icon_name: QStyle.StandardPixmap,
    ) -> None:
        """Apply a platform-native icon to a navigation item."""
        item.setIcon(0, self.style().standardIcon(icon_name))

    def _toggle_sidebar(self) -> None:
        """Toggle between the full navigation sidebar and its icon-only state."""
        self._set_sidebar_collapsed(not self._sidebar_collapsed)

    def _set_sidebar_collapsed(self, collapsed: bool) -> None:
        """Update sidebar width and navigation presentation without changing routes."""
        if (
            self._sidebar is None
            or self._sidebar_layout is None
            or self._brand_row is None
            or self._brand_text_widget is None
        ):
            return

        self._sidebar_collapsed = collapsed
        self._sidebar.setFixedWidth(84 if collapsed else 250)
        self._sidebar_layout.setContentsMargins(
            6 if collapsed else 14,
            8 if collapsed else 18,
            6 if collapsed else 14,
            8 if collapsed else 18,
        )
        self._brand_row.setSpacing(4 if collapsed else 10)
        self._brand_text_widget.setVisible(not collapsed)
        self._nav_list.setIndentation(0 if collapsed else 18)
        self._nav_list.setRootIsDecorated(not collapsed)
        self._nav_list.setStyleSheet("color: transparent;" if collapsed else "")

        if self._brand_icon_label is not None:
            icon_size = 34 if collapsed else 46
            self._brand_icon_label.setFixedSize(icon_size, icon_size)
            if self._brand_icon_pixmap is not None:
                pixmap_size = icon_size - 4
                self._brand_icon_label.setPixmap(
                    self._brand_icon_pixmap.scaled(
                        pixmap_size,
                        pixmap_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

        if self._sidebar_toggle_button is not None:
            self._sidebar_toggle_button.setText("›" if collapsed else "‹")
            tooltip = "Expand sidebar" if collapsed else "Minimize sidebar"
            self._sidebar_toggle_button.setToolTip(tooltip)
            self._sidebar_toggle_button.setAccessibleName(tooltip)

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

    def _on_navigation_changed(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            return

        route = current.data(0, Qt.ItemDataRole.UserRole)
        page_index = self._page_indexes.get(route)
        if page_index is None:
            return

        self._stack.setCurrentIndex(page_index)
        if route == "school_profile":
            self._school_profile_page.reload()
        elif route == "school_administrators":
            self._school_administrators_page.reload()
        elif route == "schedule_signatories":
            self._schedule_signatories_page.reload()

    def _on_navigation_item_clicked(
        self,
        item: QTreeWidgetItem,
        _column: int,
    ) -> None:
        """Expand or collapse a navigation group when its parent is clicked."""
        route = item.data(0, Qt.ItemDataRole.UserRole)
        if route is None and item.childCount() > 0:
            self._nav_list.setExpanded(item, not self._nav_list.isExpanded(item))

    def _on_rerun_solver(self) -> None:
        try:
            report = self._startup_service.run_diagnostics()
            self._populate_diagnostics(report)
            self.statusBar().showMessage("CP-SAT verification completed successfully.", 5000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("CP-SAT re-verification failed")
            self._solver_summary_label.setText(f"Verification failed: {exc}")
            self.statusBar().showMessage("CP-SAT verification failed.", 5000)
