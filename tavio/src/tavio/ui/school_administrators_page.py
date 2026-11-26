"""School Administrators management UI page (Phase 1, Task 2)."""

from __future__ import annotations

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from tavio.database.exceptions import (
    AdministratorInUseError,
    AdministratorNotFoundError,
    DatabaseError,
)
from tavio.domain.school_administrator import (
    SchoolAdministrator,
    SchoolAdministratorInput,
)
from tavio.services.school_administrator_service import (
    SchoolAdministratorService,
    SchoolAdministratorValidationError,
)

logger = logging.getLogger(__name__)


class SchoolAdministratorsPage(QWidget):
    """CRUD, ordering, status toggle, and deletion manager for ``school_administrators``."""

    def __init__(
        self,
        administrator_service: SchoolAdministratorService,
        parent: QWidget | None = None,
        *,
        auto_load: bool = True,
    ) -> None:
        super().__init__(parent)
        self._service = administrator_service
        self._editing_admin_id: int | None = None
        self._visible_admins: list[SchoolAdministrator] = []

        self._form_title_label = QLabel("Add Administrator")
        self._position_input = QLineEdit()
        self._name_input = QLineEdit()
        self._form_status_label = QLabel()
        self._save_button = QPushButton("Add Administrator")
        self._cancel_edit_button = QPushButton("Cancel")

        self._filter_combo = QComboBox()
        self._move_up_button = QPushButton("Move Up")
        self._move_down_button = QPushButton("Move Down")
        self._list_status_label = QLabel()
        self._table = QTableWidget(0, 5)

        self._build_ui()
        if auto_load:
            self.reload()

    def _build_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setObjectName("ProfileScrollArea")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("School Administrators")
        header.setObjectName("PageTitle")
        subtitle = QLabel(
            "Manage school administrators, display order, and active status for report signatories."
        )
        subtitle.setObjectName("HintLabel")
        subtitle.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(self._build_form_card())
        layout.addWidget(self._build_list_card(), 1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_form_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        self._form_title_label.setObjectName("SectionTitle")
        card_layout.addWidget(self._form_title_label)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self._position_input.setPlaceholderText("e.g. Guru Besar, PK Pentadbiran, PK HEM")
        self._name_input.setPlaceholderText("e.g. Puan Aminah binti Ahmad")

        for text, widget in (
            ("Position Title *", self._position_input),
            ("Administrator Name *", self._name_input),
        ):
            lbl = QLabel(text)
            lbl.setObjectName("FieldLabel")
            form.addRow(lbl, widget)

        card_layout.addLayout(form)

        required_hint = QLabel("* Required fields")
        required_hint.setObjectName("HintLabel")
        card_layout.addWidget(required_hint)

        self._form_status_label.setWordWrap(True)
        self._form_status_label.setVisible(False)
        card_layout.addWidget(self._form_status_label)

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        self._cancel_edit_button.setObjectName("SecondaryButton")
        self._cancel_edit_button.setVisible(False)
        self._cancel_edit_button.clicked.connect(self._on_cancel_edit_clicked)

        self._save_button.setMinimumWidth(160)
        self._save_button.clicked.connect(self._on_save_clicked)

        button_row.addWidget(self._cancel_edit_button)
        button_row.addWidget(self._save_button)
        card_layout.addLayout(button_row)
        return card

    def _build_list_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        section_title = QLabel("Administrators List")
        section_title.setObjectName("SectionTitle")
        toolbar.addWidget(section_title)
        toolbar.addStretch(1)

        filter_label = QLabel("Show:")
        filter_label.setObjectName("FieldLabel")
        toolbar.addWidget(filter_label)

        self._filter_combo.addItem("Active Only", True)
        self._filter_combo.addItem("Inactive Only", False)
        self._filter_combo.addItem("All Administrators", None)
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
        toolbar.addWidget(self._filter_combo)

        self._move_up_button.setObjectName("SecondaryButton")
        self._move_up_button.setEnabled(False)
        self._move_up_button.clicked.connect(self._on_move_up_clicked)

        self._move_down_button.setObjectName("SecondaryButton")
        self._move_down_button.setEnabled(False)
        self._move_down_button.clicked.connect(self._on_move_down_clicked)

        toolbar.addWidget(self._move_up_button)
        toolbar.addWidget(self._move_down_button)
        card_layout.addLayout(toolbar)

        self._list_status_label.setWordWrap(True)
        self._list_status_label.setVisible(False)
        card_layout.addWidget(self._list_status_label)

        self._table.setHorizontalHeaderLabels(
            ["Order", "Position Title", "Administrator Name", "Status", "Actions"]
        )
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(44)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setMinimumHeight(280)

        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self._table.itemSelectionChanged.connect(self._update_move_buttons)
        card_layout.addWidget(self._table, 1)
        return card

    def current_filter(self) -> bool | None:
        """Return ``True`` (active), ``False`` (inactive), or ``None`` (all)."""
        data = self._filter_combo.currentData()
        return data if isinstance(data, bool) else None

    def set_filter(self, active_only: bool | None) -> None:
        """Select a list filter mode and refresh the table."""
        idx = self._filter_combo.findData(active_only)
        if idx >= 0:
            self._filter_combo.setCurrentIndex(idx)

    def reload(self, *, selected_admin_id: int | None = None) -> None:
        """Load administrator records matching the active filter from the service."""
        active_filter = self.current_filter()
        try:
            admins = self._service.list_administrators(active_only=active_filter)
        except DatabaseError as exc:
            logger.exception("Failed to load school administrators")
            self._set_banner(
                self._list_status_label,
                f"Unable to load school administrators: {exc}",
                is_error=True,
            )
            return

        self._visible_admins = admins
        self._populate_table(admins, selected_admin_id=selected_admin_id)
        self._update_move_buttons()

    def _populate_table(
        self,
        admins: list[SchoolAdministrator],
        *,
        selected_admin_id: int | None,
    ) -> None:
        self._table.setRowCount(len(admins))
        row_to_select: int | None = None

        for row_idx, admin in enumerate(admins):
            if selected_admin_id is not None and admin.id == selected_admin_id:
                row_to_select = row_idx

            order_item = QTableWidgetItem(str(admin.sort_order))
            order_item.setData(Qt.ItemDataRole.UserRole, admin.id)
            order_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            position_item = QTableWidgetItem(admin.position_title)
            name_item = QTableWidgetItem(admin.administrator_name)

            status_item = QTableWidgetItem("Active" if admin.is_active else "Inactive")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self._table.setItem(row_idx, 0, order_item)
            self._table.setItem(row_idx, 1, position_item)
            self._table.setItem(row_idx, 2, name_item)
            self._table.setItem(row_idx, 3, status_item)
            self._table.setCellWidget(row_idx, 4, self._build_row_actions(admin))

        if row_to_select is not None:
            self._table.selectRow(row_to_select)
        else:
            self._table.clearSelection()

    def _build_row_actions(self, admin: SchoolAdministrator) -> QWidget:
        container = QWidget()
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(6, 4, 6, 4)
        row_layout.setSpacing(6)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("SecondaryButton")
        edit_btn.clicked.connect(lambda _checked=False, aid=admin.id: self._start_edit(aid))

        toggle_label = "Deactivate" if admin.is_active else "Activate"
        toggle_btn = QPushButton(toggle_label)
        toggle_btn.setObjectName("SecondaryButton")
        toggle_btn.clicked.connect(
            lambda _checked=False, aid=admin.id, active=admin.is_active: self._on_toggle_active(
                aid, currently_active=active
            )
        )

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("DangerButton")
        delete_btn.clicked.connect(lambda _checked=False, aid=admin.id: self._on_delete_clicked(aid))

        row_layout.addWidget(edit_btn)
        row_layout.addWidget(toggle_btn)
        row_layout.addWidget(delete_btn)
        return container

    def _selected_admin_id(self) -> int | None:
        current_row = self._table.currentRow()
        if current_row < 0:
            return None
        item = self._table.item(current_row, 0)
        if item is None:
            return None
        admin_id = item.data(Qt.ItemDataRole.UserRole)
        return int(admin_id) if admin_id is not None else None

    def _update_move_buttons(self) -> None:
        current_row = self._table.currentRow()
        row_count = self._table.rowCount()
        has_selection = 0 <= current_row < row_count
        self._move_up_button.setEnabled(has_selection and current_row > 0)
        self._move_down_button.setEnabled(has_selection and current_row < row_count - 1)

    def _set_banner(self, label: QLabel, message: str, *, is_error: bool) -> None:
        label.setObjectName("StatusBannerError" if is_error else "StatusBannerSuccess")
        label.style().unpolish(label)
        label.style().polish(label)
        label.setText(message)
        label.setVisible(True)

    def _clear_form_to_add_mode(self) -> None:
        self._editing_admin_id = None
        self._form_title_label.setText("Add Administrator")
        self._save_button.setText("Add Administrator")
        self._cancel_edit_button.setVisible(False)
        self._position_input.clear()
        self._name_input.clear()

    def _start_edit(self, admin_id: int) -> None:
        target = next((item for item in self._visible_admins if item.id == admin_id), None)
        if target is None:
            target = self._service.get_administrator(admin_id)
        if target is None:
            self._set_banner(
                self._list_status_label,
                "Selected administrator could not be found.",
                is_error=True,
            )
            self.reload()
            return

        self._editing_admin_id = target.id
        self._form_title_label.setText("Edit Administrator")
        self._save_button.setText("Save Changes")
        self._cancel_edit_button.setVisible(True)
        self._position_input.setText(target.position_title)
        self._name_input.setText(target.administrator_name)
        self._form_status_label.setVisible(False)
        self._position_input.setFocus()

    def _on_cancel_edit_clicked(self) -> None:
        self._clear_form_to_add_mode()
        self._form_status_label.setVisible(False)

    def _on_save_clicked(self) -> None:
        raw_input = SchoolAdministratorInput(
            position_title=self._position_input.text(),
            administrator_name=self._name_input.text(),
        )
        try:
            if self._editing_admin_id is None:
                saved = self._service.add_administrator(raw_input)
                message = f"Added administrator '{saved.administrator_name}'."
                if self.current_filter() is False:
                    self._filter_combo.blockSignals(True)
                    self.set_filter(True)
                    self._filter_combo.blockSignals(False)
            else:
                saved = self._service.edit_administrator(self._editing_admin_id, raw_input)
                message = f"Updated administrator '{saved.administrator_name}'."
        except SchoolAdministratorValidationError as exc:
            self._set_banner(self._form_status_label, str(exc), is_error=True)
            return
        except AdministratorNotFoundError as exc:
            self._clear_form_to_add_mode()
            self._set_banner(self._form_status_label, str(exc), is_error=True)
            self.reload()
            return
        except DatabaseError as exc:
            logger.exception("Failed to save school administrator")
            self._set_banner(
                self._form_status_label,
                f"Failed to save administrator: {exc}",
                is_error=True,
            )
            QMessageBox.critical(self, "Save Error", f"Failed to save administrator:\n\n{exc}")
            return

        self._clear_form_to_add_mode()
        self._set_banner(self._form_status_label, message, is_error=False)
        self._list_status_label.setVisible(False)
        self.reload(selected_admin_id=saved.id)

    def _on_filter_changed(self, _index: int) -> None:
        self._list_status_label.setVisible(False)
        self.reload()

    def _on_move_up_clicked(self) -> None:
        admin_id = self._selected_admin_id()
        if admin_id is None:
            return
        try:
            self._service.move_administrator_up(admin_id, active_only=self.current_filter())
        except DatabaseError as exc:
            logger.exception("Failed to move administrator up")
            self._set_banner(
                self._list_status_label,
                f"Failed to reorder administrators: {exc}",
                is_error=True,
            )
            return
        self._set_banner(self._list_status_label, "Display order updated.", is_error=False)
        self.reload(selected_admin_id=admin_id)

    def _on_move_down_clicked(self) -> None:
        admin_id = self._selected_admin_id()
        if admin_id is None:
            return
        try:
            self._service.move_administrator_down(admin_id, active_only=self.current_filter())
        except DatabaseError as exc:
            logger.exception("Failed to move administrator down")
            self._set_banner(
                self._list_status_label,
                f"Failed to reorder administrators: {exc}",
                is_error=True,
            )
            return
        self._set_banner(self._list_status_label, "Display order updated.", is_error=False)
        self.reload(selected_admin_id=admin_id)

    def _on_toggle_active(self, admin_id: int, *, currently_active: bool) -> None:
        try:
            if currently_active:
                updated = self._service.deactivate_administrator(admin_id)
                msg = f"Deactivated administrator '{updated.administrator_name}'."
            else:
                updated = self._service.activate_administrator(admin_id)
                msg = f"Activated administrator '{updated.administrator_name}'."
        except DatabaseError as exc:
            logger.exception("Failed to change administrator active status")
            self._set_banner(
                self._list_status_label,
                f"Failed to update administrator status: {exc}",
                is_error=True,
            )
            QMessageBox.critical(
                self,
                "Status Update Error",
                f"Failed to update administrator status:\n\n{exc}",
            )
            return

        self._set_banner(self._list_status_label, msg, is_error=False)
        self.reload(selected_admin_id=updated.id)

    def _on_delete_clicked(self, admin_id: int) -> None:
        target = next((item for item in self._visible_admins if item.id == admin_id), None)
        label = (
            f"'{target.administrator_name}' ({target.position_title})"
            if target is not None
            else f"administrator #{admin_id}"
        )
        reply = QMessageBox.question(
            self,
            "Delete Administrator",
            f"Delete {label}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.delete_administrator(admin_id)
        except AdministratorInUseError as exc:
            logger.warning("Blocked deletion of in-use administrator id=%d: %s", admin_id, exc)
            self._set_banner(self._list_status_label, str(exc), is_error=True)
            QMessageBox.warning(self, "Administrator In Use", str(exc))
            return
        except DatabaseError as exc:
            logger.exception("Failed to delete school administrator")
            self._set_banner(
                self._list_status_label,
                f"Failed to delete administrator: {exc}",
                is_error=True,
            )
            QMessageBox.critical(self, "Delete Error", f"Failed to delete administrator:\n\n{exc}")
            return

        if self._editing_admin_id == admin_id:
            self._clear_form_to_add_mode()
        self._set_banner(self._list_status_label, "Administrator deleted.", is_error=False)
        self.reload()
