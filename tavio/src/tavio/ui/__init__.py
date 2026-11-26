"""PySide6 UI package for TAVIO."""

from tavio.ui.main_window import MainWindow
from tavio.ui.schedule_signatories_page import ScheduleSignatoriesPage
from tavio.ui.school_administrators_page import SchoolAdministratorsPage
from tavio.ui.school_profile_page import SchoolProfilePage

__all__ = [
    "MainWindow",
    "ScheduleSignatoriesPage",
    "SchoolAdministratorsPage",
    "SchoolProfilePage",
]
