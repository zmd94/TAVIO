"""Startup dependency verification and Phase 0 diagnostics service."""

from __future__ import annotations

import importlib
import importlib.metadata
import logging
from dataclasses import dataclass

from tavio.solver.smoke_test import SolverSmokeResult, run_cp_sat_smoke_test

logger = logging.getLogger(__name__)

REQUIRED_DEPENDENCIES: tuple[tuple[str, str, str], ...] = (
    ("PySide6", "PySide6", "PySide6"),
    ("OR-Tools", "ortools.sat.python.cp_model", "ortools"),
    ("ReportLab", "reportlab", "reportlab"),
    ("OpenPyXL", "openpyxl", "openpyxl"),
)


class DependencyVerificationError(RuntimeError):
    """Raised when one or more required runtime packages cannot be imported."""


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    """Verification outcome for a single third-party package."""

    display_name: str
    import_name: str
    distribution_name: str
    available: bool
    version: str
    error: str = ""


@dataclass(frozen=True, slots=True)
class StartupDiagnosticReport:
    """Aggregated Phase 0 startup check results."""

    dependencies: tuple[DependencyStatus, ...]
    solver_result: SolverSmokeResult


class StartupService:
    """Coordinates Phase 0 dependency checks and solver smoke verification."""

    def verify_dependencies(
        self,
        *,
        raise_on_error: bool = True,
    ) -> tuple[DependencyStatus, ...]:
        """Verify all required runtime dependencies can be imported."""
        statuses: list[DependencyStatus] = []
        failures: list[str] = []

        for display_name, import_name, dist_name in REQUIRED_DEPENDENCIES:
            try:
                importlib.import_module(import_name)
                try:
                    pkg_version = importlib.metadata.version(dist_name)
                except importlib.metadata.PackageNotFoundError:
                    pkg_version = "unknown"
                status = DependencyStatus(
                    display_name=display_name,
                    import_name=import_name,
                    distribution_name=dist_name,
                    available=True,
                    version=pkg_version,
                )
                logger.info("Verified dependency %-10s (%s)", display_name, pkg_version)
            except Exception as exc:  # noqa: BLE001 - report exact import/DLL failure
                error_msg = f"{type(exc).__name__}: {exc}"
                status = DependencyStatus(
                    display_name=display_name,
                    import_name=import_name,
                    distribution_name=dist_name,
                    available=False,
                    version="-",
                    error=error_msg,
                )
                failures.append(f"{display_name} ({import_name}): {error_msg}")
                logger.error("Dependency check failed for %s: %s", display_name, error_msg)

            statuses.append(status)

        if failures and raise_on_error:
            joined = "; ".join(failures)
            raise DependencyVerificationError(
                f"Required dependencies failed verification: {joined}"
            )

        return tuple(statuses)

    def run_diagnostics(self) -> StartupDiagnosticReport:
        """Verify dependencies and execute the Phase 0 OR-Tools CP-SAT smoke test."""
        dependencies = self.verify_dependencies(raise_on_error=True)
        solver_result = run_cp_sat_smoke_test()
        logger.info(solver_result.format_summary())
        return StartupDiagnosticReport(
            dependencies=dependencies,
            solver_result=solver_result,
        )
