"""Schedule Signatories configuration UI page (Phase 1, Task 3)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tavio.database.exceptions import DatabaseError
from tavio.domain.schedule_signatory import (
    DEFAULT_SIGNATORY_LABEL_LANGUAGE,
    SCHEDULE_TYPE_TITLES,
    SCHEDULE_TYPES,
    SIGNATORY_LANGUAGE_ENGLISH,
    SIGNATORY_LANGUAGE_MALAY,
    SIGNATORY_ROLE_LABELS,
    ScheduleSignatoryDetail,
    ScheduleSignatoryInput,
)
from tavio.domain.school_administrator import SchoolAdministrator
from tavio.services.schedule_signatory_service import (
    ScheduleSignatoryService,
    ScheduleSignatoryValidationError,
)

logger = logging.getLogger(__name__)


def _format_admin_label(admin: SchoolAdministrator, *, inactive: bool = False) -> str:
    base = f"{admin.position_title} \u2014 {admin.administrator_name}"
    return f"[Inactive] {base}" if inactive else base


@dataclass(slots=True)
class _SignatoryCardWidgets:
    schedule_type: str
    card: QFrame
    inactive_warning_label: QLabel
    prepared_label: QLabel
    prepared_combo: QComboBox
    verified_label: QLabel
    verified_combo: QComboBox
    status_label: QLabel
    save_button: QPushButton


class ScheduleSignatoriesPage(QWidget):
    """Configuration page for TEACHER, CLASS, and SPECIAL_ROOM schedule signatories."""

    def __init__(
        self,
        signatory_service: ScheduleSignatoryService,
        parent: QWidget | None = None,
        *,
        auto_load: bool = True,
    ) -> None:
        super().__init__(parent)
        self._service = signatory_service
        self._active_candidates: list[SchoolAdministrator] = []
        self._details: dict[str, ScheduleSignatoryDetail] = {}
        self._current_language: str = DEFAULT_SIGNATORY_LABEL_LANGUAGE
        self._cards: dict[str, _SignatoryCardWidgets] = {}

        self._language_combo = QComboBox()
        self._language_status_label = QLabel()

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

        header = QLabel("Schedule Signatories")
        header.setObjectName("PageTitle")
        subtitle = QLabel(
            "Assign active school administrators as Prepared By and Verified By signatories "
            "for Teacher, Class, and Special Room schedules."
        )
        subtitle.setObjectName("HintLabel")
        subtitle.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(subtitle)
        layout.addWidget(self._build_language_card())

        for schedule_type in SCHEDULE_TYPES:
            card_widgets = self._build_schedule_card(schedule_type)
            self._cards[schedule_type] = card_widgets
            layout.addWidget(card_widgets.card)

        layout.addStretch(1)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_language_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        section_title = QLabel("Signatory Label Language")
        section_title.setObjectName("SectionTitle")
        card_layout.addWidget(section_title)

        row = QHBoxLayout()
        row.setSpacing(12)

        lbl = QLabel("Display Language")
        lbl.setObjectName("FieldLabel")
        row.addWidget(lbl)

        self._language_combo.addItem(
            "English (PREPARED BY / VERIFIED BY)",
            SIGNATORY_LANGUAGE_ENGLISH,
        )
        self._language_combo.addItem(
            "Bahasa Melayu (DISEDIAKAN OLEH / DISAHKAN OLEH)",
            SIGNATORY_LANGUAGE_MALAY,
        )
        self._language_combo.currentIndexChanged.connect(self._on_language_changed)
        row.addWidget(self._language_combo, 1)
        card_layout.addLayout(row)

        hint = QLabel(
            "Controls display labels for signatory roles across all schedule types "
            "without altering stored administrator records."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        card_layout.addWidget(hint)

        self._language_status_label.setWordWrap(True)
        self._language_status_label.setVisible(False)
        card_layout.addWidget(self._language_status_label)
        return card

    def _build_schedule_card(self, schedule_type: str) -> _SignatoryCardWidgets:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        section_title = QLabel(SCHEDULE_TYPE_TITLES[schedule_type])
        section_title.setObjectName("SectionTitle")
        card_layout.addWidget(section_title)

        inactive_warning = QLabel()
        inactive_warning.setObjectName("StatusBannerError")
        inactive_warning.setWordWrap(True)
        inactive_warning.setVisible(False)
        card_layout.addWidget(inactive_warning)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        prepared_title, verified_title = SIGNATORY_ROLE_LABELS[self._current_language]
        prepared_label = QLabel(prepared_title)
        prepared_label.setObjectName("FieldLabel")
        prepared_combo = QComboBox()

        verified_label = QLabel(verified_title)
        verified_label.setObjectName("FieldLabel")
        verified_combo = QComboBox()

        form.addRow(prepared_label, prepared_combo)
        form.addRow(verified_label, verified_combo)
        card_layout.addLayout(form)

        status_label = QLabel()
        status_label.setWordWrap(True)
        status_label.setVisible(False)
        card_layout.addWidget(status_label)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        save_button = QPushButton("Save Changes")
        save_button.setMinimumWidth(150)
        save_button.clicked.connect(
            lambda _checked=False, st=schedule_type: self._on_save_card_clicked(st)
        )
        button_row.addWidget(save_button)
        card_layout.addLayout(button_row)

        prepared_combo.currentIndexChanged.connect(
            lambda _idx, st=schedule_type: self._on_role_selection_changed(st)
        )
        verified_combo.currentIndexChanged.connect(
            lambda _idx, st=schedule_type: self._on_role_selection_changed(st)
        )

        return _SignatoryCardWidgets(
            schedule_type=schedule_type,
            card=card,
            inactive_warning_label=inactive_warning,
            prepared_label=prepared_label,
            prepared_combo=prepared_combo,
            verified_label=verified_label,
            verified_combo=verified_combo,
            status_label=status_label,
            save_button=save_button,
        )

    def current_label_language(self) -> str:
        """Return the active display-language code (``'EN'`` or ``'MS'``)."""
        return self._current_language

    def reload(self) -> None:
        """Reload signatory settings, active candidates, and label language from service."""
        try:
            overview = self._service.load_overview()
        except DatabaseError as exc:
            logger.exception("Failed to load schedule signatories")
            self._set_banner(
                self._language_status_label,
                f"Unable to load schedule signatories: {exc}",
                is_error=True,
            )
            return

        self._active_candidates = overview.active_candidates
        self._details = overview.details
        self._current_language = overview.label_language

        self._language_combo.blockSignals(True)
        lang_idx = self._language_combo.findData(self._current_language)
        if lang_idx >= 0:
            self._language_combo.setCurrentIndex(lang_idx)
        self._language_combo.blockSignals(False)

        self._apply_role_labels()

        for schedule_type in SCHEDULE_TYPES:
            self._populate_card(schedule_type)

    def _apply_role_labels(self) -> None:
        prepared_text, verified_text = SIGNATORY_ROLE_LABELS[self._current_language]
        for widgets in self._cards.values():
            widgets.prepared_label.setText(prepared_text)
            widgets.verified_label.setText(verified_text)

    def _populate_card(self, schedule_type: str) -> None:
        widgets = self._cards[schedule_type]
        detail = self._details.get(schedule_type)
        prepared_id = detail.setting.prepared_by_administrator_id if detail else None
        verified_id = detail.setting.verified_by_administrator_id if detail else None

        self._refresh_card_combos(
            schedule_type,
            selected_prepared_id=prepared_id,
            selected_verified_id=verified_id,
        )
        self._update_inactive_warning(widgets, detail)

    def _refresh_card_combos(
        self,
        schedule_type: str,
        *,
        selected_prepared_id: int | None,
        selected_verified_id: int | None,
    ) -> None:
        widgets = self._cards[schedule_type]
        detail = self._details.get(schedule_type)

        inactive_prepared = (
            detail.prepared_by_admin
            if detail is not None and detail.prepared_by_is_inactive
            else None
        )
        inactive_verified = (
            detail.verified_by_admin
            if detail is not None and detail.verified_by_is_inactive
            else None
        )

        self._populate_role_combo(
            widgets.prepared_combo,
            selected_id=selected_prepared_id,
            excluded_id=selected_verified_id,
            inactive_assigned=inactive_prepared,
        )
        self._populate_role_combo(
            widgets.verified_combo,
            selected_id=selected_verified_id,
            excluded_id=selected_prepared_id,
            inactive_assigned=inactive_verified,
        )

    def _populate_role_combo(
        self,
        combo: QComboBox,
        *,
        selected_id: int | None,
        excluded_id: int | None,
        inactive_assigned: SchoolAdministrator | None,
    ) -> None:
        combo.blockSignals(True)
        try:
            combo.clear()
            combo.addItem("(Unassigned)", None)

            if (
                inactive_assigned is not None
                and inactive_assigned.id != excluded_id
                and selected_id == inactive_assigned.id
            ):
                combo.addItem(
                    _format_admin_label(inactive_assigned, inactive=True),
                    inactive_assigned.id,
                )

            for admin in self._active_candidates:
                if excluded_id is not None and admin.id == excluded_id:
                    continue
                combo.addItem(_format_admin_label(admin), admin.id)

            target_idx = combo.findData(selected_id)
            combo.setCurrentIndex(target_idx if target_idx >= 0 else 0)
        finally:
            combo.blockSignals(False)

    def _update_inactive_warning(
        self,
        widgets: _SignatoryCardWidgets,
        detail: ScheduleSignatoryDetail | None,
    ) -> None:
        if detail is None:
            widgets.inactive_warning_label.setVisible(False)
            return

        inactive_roles: list[str] = []
        prepared_title, verified_title = SIGNATORY_ROLE_LABELS[self._current_language]
        if detail.prepared_by_is_inactive and detail.prepared_by_admin is not None:
            inactive_roles.append(
                f"{prepared_title}: {detail.prepared_by_admin.administrator_name}"
            )
        if detail.verified_by_is_inactive and detail.verified_by_admin is not None:
            inactive_roles.append(
                f"{verified_title}: {detail.verified_by_admin.administrator_name}"
            )

        if inactive_roles:
            joined = "; ".join(inactive_roles)
            widgets.inactive_warning_label.setText(
                f"Inactive administrator currently assigned ({joined}). "
                "Please replace with an active administrator or clear the assignment."
            )
            widgets.inactive_warning_label.setVisible(True)
        else:
            widgets.inactive_warning_label.setVisible(False)

    def _on_role_selection_changed(self, schedule_type: str) -> None:
        widgets = self._cards[schedule_type]
        prepared_data = widgets.prepared_combo.currentData()
        verified_data = widgets.verified_combo.currentData()
        prepared_id = int(prepared_data) if prepared_data is not None else None
        verified_id = int(verified_data) if verified_data is not None else None

        self._refresh_card_combos(
            schedule_type,
            selected_prepared_id=prepared_id,
            selected_verified_id=verified_id,
        )
        widgets.status_label.setVisible(False)

    def _on_language_changed(self, _index: int) -> None:
        selected_code = str(
            self._language_combo.currentData() or DEFAULT_SIGNATORY_LABEL_LANGUAGE
        )
        try:
            saved_language = self._service.set_label_language(selected_code)
        except (ScheduleSignatoryValidationError, DatabaseError) as exc:
            logger.exception("Failed to update signatory label language")
            self._set_banner(
                self._language_status_label,
                f"Failed to update signatory label language: {exc}",
                is_error=True,
            )
            return

        self._current_language = saved_language
        self._apply_role_labels()
        for schedule_type, widgets in self._cards.items():
            self._update_inactive_warning(widgets, self._details.get(schedule_type))
        self._set_banner(
            self._language_status_label,
            "Signatory label language updated.",
            is_error=False,
        )

    def _on_save_card_clicked(self, schedule_type: str) -> None:
        widgets = self._cards[schedule_type]
        prepared_data = widgets.prepared_combo.currentData()
        verified_data = widgets.verified_combo.currentData()
        prepared_id = int(prepared_data) if prepared_data is not None else None
        verified_id = int(verified_data) if verified_data is not None else None

        try:
            self._service.save_signatory_setting(
                ScheduleSignatoryInput(
                    schedule_type=schedule_type,
                    prepared_by_administrator_id=prepared_id,
                    verified_by_administrator_id=verified_id,
                )
            )
        except ScheduleSignatoryValidationError as exc:
            self._set_banner(widgets.status_label, str(exc), is_error=True)
            return
        except DatabaseError as exc:
            logger.exception("Failed to save schedule signatory setting for %s", schedule_type)
            self._set_banner(
                widgets.status_label,
                f"Failed to save signatories: {exc}",
                is_error=True,
            )
            QMessageBox.critical(
                self,
                "Save Signatories Error",
                f"Failed to save signatories for {SCHEDULE_TYPE_TITLES[schedule_type]}:\n\n{exc}",
            )
            return

        self.reload()
        self._set_banner(
            self._cards[schedule_type].status_label,
            f"{SCHEDULE_TYPE_TITLES[schedule_type]} signatories saved successfully.",
            is_error=False,
        )

    def _set_banner(self, label: QLabel, message: str, *, is_error: bool) -> None:
        label.setObjectName("StatusBannerError" if is_error else "StatusBannerSuccess")
        label.style().unpolish(label)
        label.style().polish(label)
        label.setText(message)
        label.setVisible(True)
