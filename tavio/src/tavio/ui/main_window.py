"""Minimal Phase 0 PySide6 main window for TAVIO."""

from __future__ import annotations

import logging

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
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

NAVIGATION_GROUPS: tuple[tuple[str, str, str, tuple[tuple[str, str, str], ...]], ...] = (
    ("Workspace", "Phase 0", "Workspace file lifecycle.", (("New", "workspace_new", "Create a new school workspace."), ("Open", "workspace_open", "Open an existing school workspace."), ("Save", "workspace_save", "Save changes to the active workspace."), ("Save As", "workspace_save_as", "Save the active workspace to another file."), ("Exit", "workspace_exit", "Close TAVIO safely."))),
    ("School Setup", "Phase 1", "School identity and authorized schedule signatories.", (("School Profile", "school_profile", ""), ("School Administrators", "school_administrators", ""), ("Schedule Signatories", "schedule_signatories", ""))),
    ("Master Data", "Phase 2", "Manage teachers, classes, class teachers, subjects, special rooms, and teaching distribution.", (("Teachers", "master_teachers", "Manage teacher records."), ("Classes", "master_classes", "Manage class records."), ("Class Teacher", "master_class_teacher", "Assign class teachers to classes."), ("Subjects", "master_subjects", "Manage subject records."), ("Special Rooms", "master_special_rooms", "Manage special teaching rooms."), ("Teaching Distribution", "master_teaching_distribution", "Configure teaching distribution."))),
    ("Timetable", "Phase 3", "Generate, version, and view school timetables.", (("Generate Timetable", "timetable_generate", "Generate a timetable using configured constraints."), ("Timetable Versions", "timetable_versions", "Review and manage timetable versions."), ("View Timetable", "timetable_view", "View the selected timetable."))),
    ("Manual Editor", "Phase 4", "Edit timetable assignments and validate changes before activation.", (("Edit Timetable", "manual_edit", "Edit timetable assignments."), ("Validate Changes", "manual_validate", "Validate timetable changes."))),
    ("Absences & Relief", "Phase 5", "Record teacher absences and manage relief assignments and timetables.", (("Teacher Absences", "relief_absences", "Record and review teacher absences."), ("Relief Management", "relief_management", "Manage relief teacher assignments."), ("Relief Timetable", "relief_timetable", "View the relief timetable."))),
    ("Reports", "Phase 6", "Preview, generate, and configure PDF reports.", (("PDF Preview", "reports_preview", "Preview PDF reports."), ("Generate PDF", "reports_generate", "Generate PDF reports."), ("Report Settings", "reports_settings", "Configure report settings."))),
    ("Settings", "Phase 0", "General preferences, appearance, and application information.", (("General", "settings_general", "Configure general application settings."), ("Appearance", "settings_appearance", "Configure application appearance."), ("About TAVIO", "about_tavio", ""))),
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
        sidebar.setMinimumWidth(286)
        sidebar.setMaximumWidth(340)
        sidebar.resize(300, self.height())
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
        toggle_button = QPushButton()
        self._sidebar_toggle_button = toggle_button
        toggle_button.setObjectName("SidebarToggle")
        toggle_button.setFixedSize(30, 30)
        toggle_button.setIconSize(QSize(16, 16))
        toggle_button.setIcon(self._create_sidebar_arrow_icon(collapsed=False))
        toggle_button.setToolTip("Minimize sidebar")
        toggle_button.setAccessibleName("Minimize sidebar")
        toggle_button.clicked.connect(self._toggle_sidebar)
        brand_row.addWidget(toggle_button, 0, Qt.AlignmentFlag.AlignVCenter)

        self._nav_list.setObjectName("NavigationTree")
        self._nav_list.setIconSize(QSize(20, 20))
        self._nav_list.setHeaderHidden(True)
        # Avoid the extra branch-indicator gutter before top-level navigation labels.
        # Parent groups remain expandable when clicked.
        self._nav_list.setRootIsDecorated(False)
        self._nav_list.setItemsExpandable(True)
        self._nav_list.setExpandsOnDoubleClick(False)
        self._nav_list.setIndentation(16)
        self._nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        dashboard_item = QTreeWidgetItem(["Dashboard"])
        self._set_navigation_item_icon(
            dashboard_item,
            QStyle.StandardPixmap.SP_ComputerIcon,
        )
        dashboard_item.setToolTip(0, "Dashboard")
        dashboard_item.setData(0, Qt.ItemDataRole.UserRole, "dashboard")
        self._nav_list.addTopLevelItem(dashboard_item)
        self._page_indexes["dashboard"] = self._stack.addWidget(
            self._build_placeholder_page(
                "Phase 1",
                "School workspace dashboard, academic year and session context, summary cards, "
                "workspace readiness, timetable status, and quick actions.",
            )
        )

        self._nav_list.currentItemChanged.connect(self._on_navigation_changed)
        self._nav_list.itemClicked.connect(self._on_navigation_item_clicked)
        sidebar_layout.addLayout(brand_row)
        sidebar_layout.addWidget(self._nav_list, 1)

        for group_title, phase, _group_scope, children in NAVIGATION_GROUPS:
            group_item = QTreeWidgetItem([group_title])
            self._set_navigation_item_icon(
                group_item,
                self._navigation_group_icon(group_title),
            )
            group_item.setToolTip(0, group_title)
            group_item.setData(0, Qt.ItemDataRole.UserRole, None)
            self._nav_list.addTopLevelItem(group_item)

            for child_title, route, scope in children:
                child = QTreeWidgetItem([child_title])
                self._set_navigation_item_icon(
                    child,
                    self._navigation_route_icon(route),
                )
                child.setToolTip(0, child_title)
                child.setData(0, Qt.ItemDataRole.UserRole, route)
                group_item.addChild(child)

                if route == "school_profile":
                    page = self._school_profile_page
                elif route == "school_administrators":
                    page = self._school_administrators_page
                elif route == "schedule_signatories":
                    page = self._schedule_signatories_page
                elif route == "about_tavio":
                    page = self._build_overview_page()
                else:
                    child_phase = "Phase 0" if route.startswith(("workspace_", "settings_")) else phase
                    page = self._build_placeholder_page(child_phase, scope)
                self._page_indexes[route] = self._stack.addWidget(page)

        self._nav_list.topLevelItem(2).setExpanded(True)
        root_layout.addWidget(sidebar)
        root_layout.addWidget(self._stack, 1)
        self.setCentralWidget(root)
        self._nav_list.setCurrentItem(dashboard_item)

    def _navigation_group_icon(self, title: str) -> QStyle.StandardPixmap:
        """Return a distinct semantic icon for each primary navigation group."""
        icons = {
            "Workspace": QStyle.StandardPixmap.SP_DirOpenIcon,
            "School Setup": QStyle.StandardPixmap.SP_DirHomeIcon,
            "Master Data": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "Timetable": QStyle.StandardPixmap.SP_FileDialogListView,
            "Manual Editor": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "Absences & Relief": QStyle.StandardPixmap.SP_MessageBoxWarning,
            "Reports": QStyle.StandardPixmap.SP_FileDialogInfoView,
            "Settings": QStyle.StandardPixmap.SP_ComputerIcon,
        }
        return icons.get(title, QStyle.StandardPixmap.SP_DirIcon)

    def _navigation_route_icon(self, route: str) -> QStyle.StandardPixmap:
        """Return a meaningful icon for each navigation destination."""
        icons = {
            "workspace_new": QStyle.StandardPixmap.SP_FileDialogNewFolder,
            "workspace_open": QStyle.StandardPixmap.SP_DialogOpenButton,
            "workspace_save": QStyle.StandardPixmap.SP_DialogSaveButton,
            "workspace_save_as": QStyle.StandardPixmap.SP_DialogSaveAllButton,
            "workspace_exit": QStyle.StandardPixmap.SP_DialogCloseButton,
            "school_profile": QStyle.StandardPixmap.SP_FileDialogInfoView,
            "school_administrators": QStyle.StandardPixmap.SP_DirHomeIcon,
            "schedule_signatories": QStyle.StandardPixmap.SP_DialogApplyButton,
            "master_teachers": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "master_classes": QStyle.StandardPixmap.SP_FileDialogListView,
            "master_class_teacher": QStyle.StandardPixmap.SP_DirHomeIcon,
            "master_subjects": QStyle.StandardPixmap.SP_FileIcon,
            "master_special_rooms": QStyle.StandardPixmap.SP_DirIcon,
            "master_teaching_distribution": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "timetable_generate": QStyle.StandardPixmap.SP_BrowserReload,
            "timetable_versions": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "timetable_view": QStyle.StandardPixmap.SP_FileDialogListView,
            "manual_edit": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "manual_validate": QStyle.StandardPixmap.SP_DialogApplyButton,
            "relief_absences": QStyle.StandardPixmap.SP_MessageBoxWarning,
            "relief_management": QStyle.StandardPixmap.SP_DirHomeIcon,
            "relief_timetable": QStyle.StandardPixmap.SP_FileDialogListView,
            "reports_preview": QStyle.StandardPixmap.SP_FileDialogInfoView,
            "reports_generate": QStyle.StandardPixmap.SP_DialogSaveButton,
            "reports_settings": QStyle.StandardPixmap.SP_FileDialogDetailedView,
            "settings_general": QStyle.StandardPixmap.SP_ComputerIcon,
            "settings_appearance": QStyle.StandardPixmap.SP_DesktopIcon,
            "about_tavio": QStyle.StandardPixmap.SP_MessageBoxInformation,
        }
        return icons.get(route, QStyle.StandardPixmap.SP_FileIcon)

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

    def _create_sidebar_arrow_icon(self, *, collapsed: bool) -> QIcon:
        """Create a restrained chevron icon independent of platform icon themes."""
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(
            QPen(
                QColor("#dbe6f5"),
                2.2,
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
        if collapsed:
            painter.drawLine(6, 3, 12, 9)
            painter.drawLine(12, 9, 6, 15)
        else:
            painter.drawLine(12, 3, 6, 9)
            painter.drawLine(6, 9, 12, 15)
        painter.end()
        return QIcon(pixmap)

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
        if collapsed:
            for index in range(self._nav_list.topLevelItemCount()):
                item = self._nav_list.topLevelItem(index)
                if item.childCount() > 0:
                    item.setExpanded(False)
            self._sidebar.setFixedWidth(76)
        else:
            self._sidebar.setMinimumWidth(286)
            self._sidebar.setMaximumWidth(340)
            self._sidebar.resize(300, self._sidebar.height())
        self._sidebar_layout.setContentsMargins(
            6 if collapsed else 14,
            8 if collapsed else 18,
            6 if collapsed else 14,
            8 if collapsed else 18,
        )
        self._brand_row.setSpacing(0 if collapsed else 10)
        self._brand_text_widget.setVisible(not collapsed)
        if self._brand_icon_label is not None:
            self._brand_icon_label.setVisible(not collapsed)
        self._nav_list.setIndentation(0 if collapsed else 16)
        self._nav_list.clearSelection()
        self._nav_list.setCurrentItem(None)
        self._nav_list.clearFocus()
        self._nav_list.setRootIsDecorated(False)
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
            self._sidebar_toggle_button.setIcon(
                self._create_sidebar_arrow_icon(collapsed=collapsed)
            )
            tooltip = "Expand sidebar" if collapsed else "Minimize sidebar"
            self._sidebar_toggle_button.setToolTip(tooltip)
            self._sidebar_toggle_button.setAccessibleName(tooltip)

    def _build_overview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel(f"About {APP_NAME} — Environment & Packaging Verification")
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

    def _build_placeholder_page(self, phase: str, planned_scope: str) -> QWidget:
        """Build the agreed two-line placeholder for an unimplemented destination."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        status = QLabel(f"Not yet implement ({phase})")
        status.setObjectName("SectionTitle")
        scope = QLabel(f"Planned scope: {planned_scope}")
        scope.setWordWrap(True)
        layout.addWidget(status)
        layout.addWidget(scope)
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
        if self._sidebar_collapsed:
            self._set_sidebar_collapsed(False)
            if route is None and item.childCount() > 0:
                item.setExpanded(True)
            return

        if route is None and item.childCount() > 0:
            item.setExpanded(not item.isExpanded())

    def _on_rerun_solver(self) -> None:
        try:
            report = self._startup_service.run_diagnostics()
            self._populate_diagnostics(report)
            self.statusBar().showMessage("CP-SAT verification completed successfully.", 5000)
        except Exception as exc:  # noqa: BLE001
            logger.exception("CP-SAT re-verification failed")
            self._solver_summary_label.setText(f"Verification failed: {exc}")
            self.statusBar().showMessage("CP-SAT verification failed.", 5000)
