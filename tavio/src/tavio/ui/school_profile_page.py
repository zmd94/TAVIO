"""School Profile management UI page (Phase 1, Task 1)."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from tavio.database.exceptions import DatabaseError
from tavio.domain.school_profile import DEFAULT_SCHOOL_WEEK_GROUP, SchoolProfileInput
from tavio.services.school_logo_service import SchoolLogoError
from tavio.services.school_profile_service import (
    SchoolProfileService,
    SchoolProfileValidationError,
    SchoolProfileView,
)

logger = logging.getLogger(__name__)

_LOGO_PREVIEW_BOX_SIZE = 220
_LOGO_PIXMAP_PADDING = 16


class SchoolProfilePage(QWidget):
    """Form and logo manager for the singleton TAVIO School Profile."""

    def __init__(
        self,
        profile_service: SchoolProfileService,
        parent: QWidget | None = None,
        *,
        auto_load: bool = True,
    ) -> None:
        super().__init__(parent)
        self._service = profile_service
        self._current_logo_path: str | None = None

        self._school_name_input = QLineEdit()
        self._school_code_input = QLineEdit()
        self._week_group_combo = QComboBox()
        self._address_input = QPlainTextEdit()
        self._phone_input = QLineEdit()
        self._email_input = QLineEdit()

        self._form_status_label = QLabel()
        self._save_button = QPushButton("Save School Profile")

        self._logo_preview_label = QLabel("No school logo uploaded")
        self._logo_path_label = QLabel("Logo status: Not configured")
        self._logo_status_label = QLabel()
        self._upload_logo_button = QPushButton("Upload Logo")
        self._remove_logo_button = QPushButton("Remove Logo")

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

        header = QLabel("School Profile")
        header.setObjectName("PageTitle")
        subtitle = QLabel(
            "Configure school identity, weekly schooling group (A/B), and official school logo."
        )
        subtitle.setObjectName("HintLabel")
        subtitle.setWordWrap(True)

        layout.addWidget(header)
        layout.addWidget(subtitle)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        cards_row.addWidget(self._build_info_card(), 3)
        cards_row.addWidget(self._build_logo_card(), 2)
        layout.addLayout(cards_row)
        layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    def _build_info_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        section_title = QLabel("School Information")
        section_title.setObjectName("SectionTitle")
        card_layout.addWidget(section_title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        form.setVerticalSpacing(10)
        form.setHorizontalSpacing(14)

        self._school_name_input.setPlaceholderText("e.g. Sekolah Kebangsaan Seri Melati")
        self._school_code_input.setPlaceholderText("e.g. BBA1001")

        self._week_group_combo.addItem("Group B — Monday to Friday (Weekend: Sat–Sun)", "B")
        self._week_group_combo.addItem("Group A — Sunday to Thursday (Weekend: Fri–Sat)", "A")

        self._address_input.setPlaceholderText("School street address, postcode, city, state")
        self._address_input.setFixedHeight(84)
        self._phone_input.setPlaceholderText("e.g. 03-12345678")
        self._email_input.setPlaceholderText("e.g. school@moe.edu.my")

        for text, widget in (
            ("School Name *", self._school_name_input),
            ("School Code *", self._school_code_input),
            ("School Week Group *", self._week_group_combo),
            ("Address", self._address_input),
            ("Phone Number", self._phone_input),
            ("Email Address", self._email_input),
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
        self._save_button.setMinimumWidth(160)
        self._save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(self._save_button)
        card_layout.addLayout(button_row)
        card_layout.addStretch(1)
        return card

    def _build_logo_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)

        section_title = QLabel("School Logo")
        section_title.setObjectName("SectionTitle")
        card_layout.addWidget(section_title)

        self._logo_preview_label.setObjectName("LogoPreview")
        self._logo_preview_label.setFixedSize(_LOGO_PREVIEW_BOX_SIZE, _LOGO_PREVIEW_BOX_SIZE)
        self._logo_preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_preview_label.setWordWrap(True)
        card_layout.addWidget(self._logo_preview_label, 0, Qt.AlignmentFlag.AlignHCenter)

        rules_label = QLabel(
            "Accepted formats: PNG, JPG, JPEG\n"
            "Max file size: 5 MB • Min size: 128×128 px\n"
            "Images above 3000×3000 px are resized proportionally."
        )
        rules_label.setObjectName("HintLabel")
        rules_label.setWordWrap(True)
        card_layout.addWidget(rules_label)

        self._logo_path_label.setObjectName("HintLabel")
        self._logo_path_label.setWordWrap(True)
        card_layout.addWidget(self._logo_path_label)

        self._logo_status_label.setWordWrap(True)
        self._logo_status_label.setVisible(False)
        card_layout.addWidget(self._logo_status_label)

        actions_row = QHBoxLayout()
        actions_row.setSpacing(10)
        self._upload_logo_button.clicked.connect(self._on_upload_logo_clicked)
        self._remove_logo_button.setObjectName("DangerButton")
        self._remove_logo_button.clicked.connect(self._on_remove_logo_clicked)

        actions_row.addWidget(self._upload_logo_button, 1)
        actions_row.addWidget(self._remove_logo_button, 1)
        card_layout.addLayout(actions_row)
        card_layout.addStretch(1)
        return card

    def reload(self) -> None:
        """Load school profile and logo preview state from the application service."""
        try:
            view = self._service.load_profile()
        except DatabaseError as exc:
            logger.exception("Failed to load school profile")
            self._set_form_status(f"Unable to load school profile: {exc}", is_error=True)
            return

        profile = view.profile
        if profile is None:
            self._school_name_input.clear()
            self._school_code_input.clear()
            self._set_week_group(DEFAULT_SCHOOL_WEEK_GROUP)
            self._address_input.clear()
            self._phone_input.clear()
            self._email_input.clear()
            self._current_logo_path = None
        else:
            self._school_name_input.setText(profile.school_name)
            self._school_code_input.setText(profile.school_code)
            self._set_week_group(profile.school_week_group)
            self._address_input.setPlainText(profile.address or "")
            self._phone_input.setText(profile.phone or "")
            self._email_input.setText(profile.email or "")
            self._current_logo_path = profile.logo_path

        self._apply_logo_view(view)

    def _set_week_group(self, group: str) -> None:
        idx = self._week_group_combo.findData(group)
        if idx >= 0:
            self._week_group_combo.setCurrentIndex(idx)

    def _apply_logo_view(self, view: SchoolProfileView) -> None:
        if view.logo_exists and view.logo_file_path is not None:
            self._show_logo_pixmap(view.logo_file_path)
            self._upload_logo_button.setText("Replace Logo")
            self._remove_logo_button.setEnabled(True)
            rel_path = view.profile.logo_path if view.profile else self._current_logo_path
            self._logo_path_label.setText(f"Saved file: {rel_path or 'assets/school_logo.png'}")
        elif view.logo_missing_on_disk:
            self._logo_preview_label.setPixmap(QPixmap())
            self._logo_preview_label.setText("Logo file missing on disk")
            self._upload_logo_button.setText("Replace Logo")
            self._remove_logo_button.setEnabled(True)
            self._logo_path_label.setText(
                "Logo path is configured, but the image file was not found."
            )
            self._set_logo_status(
                "School logo file is missing on disk. Upload a new logo or remove it.",
                is_error=True,
            )
        else:
            self._logo_preview_label.setPixmap(QPixmap())
            self._logo_preview_label.setText("No school logo uploaded")
            self._upload_logo_button.setText("Upload Logo")
            self._remove_logo_button.setEnabled(False)
            self._logo_path_label.setText("Logo status: Not configured")

    def _show_logo_pixmap(self, image_path: Path) -> None:
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            self._logo_preview_label.setPixmap(QPixmap())
            self._logo_preview_label.setText("Unable to preview logo image")
            return

        max_dim = _LOGO_PREVIEW_BOX_SIZE - _LOGO_PIXMAP_PADDING
        scaled = pixmap.scaled(
            max_dim,
            max_dim,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._logo_preview_label.setText("")
        self._logo_preview_label.setPixmap(scaled)

    def _set_form_status(self, message: str, *, is_error: bool) -> None:
        self._form_status_label.setObjectName(
            "StatusBannerError" if is_error else "StatusBannerSuccess"
        )
        self._form_status_label.style().unpolish(self._form_status_label)
        self._form_status_label.style().polish(self._form_status_label)
        self._form_status_label.setText(message)
        self._form_status_label.setVisible(True)

    def _set_logo_status(self, message: str, *, is_error: bool) -> None:
        self._logo_status_label.setObjectName(
            "StatusBannerError" if is_error else "StatusBannerSuccess"
        )
        self._logo_status_label.style().unpolish(self._logo_status_label)
        self._logo_status_label.style().polish(self._logo_status_label)
        self._logo_status_label.setText(message)
        self._logo_status_label.setVisible(True)

    def _on_save_clicked(self) -> None:
        week_group = str(self._week_group_combo.currentData() or DEFAULT_SCHOOL_WEEK_GROUP)
        raw_input = SchoolProfileInput(
            school_name=self._school_name_input.text(),
            school_code=self._school_code_input.text(),
            school_week_group=week_group,
            address=self._address_input.toPlainText(),
            phone=self._phone_input.text(),
            email=self._email_input.text(),
            logo_path=self._current_logo_path,
        )
        try:
            saved = self._service.save_profile(raw_input)
        except SchoolProfileValidationError as exc:
            self._set_form_status(str(exc), is_error=True)
            return
        except DatabaseError as exc:
            logger.exception("Failed to save school profile")
            self._set_form_status(f"Failed to save school profile: {exc}", is_error=True)
            QMessageBox.critical(self, "Save Error", f"Failed to save school profile:\n\n{exc}")
            return

        self._school_name_input.setText(saved.school_name)
        self._school_code_input.setText(saved.school_code)
        self._set_week_group(saved.school_week_group)
        self._current_logo_path = saved.logo_path
        self._set_form_status("School profile saved successfully.", is_error=False)

    def _on_upload_logo_clicked(self) -> None:
        selected_file, _selected_filter = QFileDialog.getOpenFileName(
            self,
            "Select School Logo",
            "",
            "Image Files (*.png *.jpg *.jpeg);;All Files (*)",
        )
        if not selected_file:
            return

        try:
            updated_profile, info, relative_path = self._service.upload_logo(Path(selected_file))
        except (SchoolLogoError, DatabaseError) as exc:
            logger.warning("School logo upload failed: %s", exc)
            self._set_logo_status(str(exc), is_error=True)
            QMessageBox.warning(self, "School Logo Upload Failed", str(exc))
            return

        self._current_logo_path = relative_path
        self._show_logo_pixmap(info.output_path)
        self._upload_logo_button.setText("Replace Logo")
        self._remove_logo_button.setEnabled(True)
        self._logo_path_label.setText(f"Saved file: {relative_path}")

        w, h = info.final_size
        if updated_profile is None:
            self._set_logo_status(
                f"Logo processed ({w}×{h} PNG). Click Save School Profile to save school details.",
                is_error=False,
            )
        elif info.was_resized:
            self._set_logo_status(
                f"Logo saved as PNG ({w}×{h} px, proportionally resized).",
                is_error=False,
            )
        else:
            self._set_logo_status(f"Logo saved as PNG ({w}×{h} px).", is_error=False)

    def _on_remove_logo_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "Remove School Logo",
            "Remove the current school logo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self._service.remove_logo()
        except (SchoolLogoError, DatabaseError) as exc:
            logger.exception("Failed to remove school logo")
            self._set_logo_status(f"Failed to remove logo: {exc}", is_error=True)
            QMessageBox.critical(self, "Remove Logo Error", str(exc))
            return

        self._current_logo_path = None
        self._logo_preview_label.setPixmap(QPixmap())
        self._logo_preview_label.setText("No school logo uploaded")
        self._upload_logo_button.setText("Upload Logo")
        self._remove_logo_button.setEnabled(False)
        self._logo_path_label.setText("Logo status: Not configured")
        self._set_logo_status("School logo removed.", is_error=False)
