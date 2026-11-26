"""Application services package for TAVIO."""

from tavio.services.school_administrator_service import (
    SchoolAdministratorService,
    SchoolAdministratorValidationError,
)
from tavio.services.school_logo_service import (
    MAX_LOGO_DIMENSION,
    MAX_LOGO_FILE_SIZE_BYTES,
    MIN_LOGO_DIMENSION,
    ProcessedLogoInfo,
    SchoolLogoError,
    SchoolLogoService,
)
from tavio.services.school_profile_service import (
    SchoolProfileService,
    SchoolProfileValidationError,
    SchoolProfileView,
)
from tavio.services.startup_service import (
    DependencyStatus,
    DependencyVerificationError,
    StartupDiagnosticReport,
    StartupService,
)

__all__ = [
    "DependencyStatus",
    "DependencyVerificationError",
    "MAX_LOGO_DIMENSION",
    "MAX_LOGO_FILE_SIZE_BYTES",
    "MIN_LOGO_DIMENSION",
    "ProcessedLogoInfo",
    "SchoolAdministratorService",
    "SchoolAdministratorValidationError",
    "SchoolLogoError",
    "SchoolLogoService",
    "SchoolProfileService",
    "SchoolProfileValidationError",
    "SchoolProfileView",
    "StartupDiagnosticReport",
    "StartupService",
]
