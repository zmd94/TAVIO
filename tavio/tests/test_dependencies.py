"""Tests for Phase 0 dependency verification."""

from __future__ import annotations

import importlib

import pytest

from tavio.services.startup_service import (
    REQUIRED_DEPENDENCIES,
    DependencyVerificationError,
    StartupService,
)


def test_required_dependencies_import_and_report_versions() -> None:
    service = StartupService()
    statuses = service.verify_dependencies(raise_on_error=True)

    assert len(statuses) == len(REQUIRED_DEPENDENCIES)
    assert all(status.available for status in statuses)
    assert all(status.version != "" for status in statuses)


def test_missing_dependency_raises_explicit_error(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str, package: str | None = None):
        if name == "reportlab":
            raise ImportError("Simulated missing reportlab")
        return real_import(name, package)

    monkeypatch.setattr(importlib, "import_module", fake_import)

    service = StartupService()
    with pytest.raises(DependencyVerificationError, match="ReportLab"):
        service.verify_dependencies(raise_on_error=True)


def test_startup_service_run_diagnostics() -> None:
    report = StartupService().run_diagnostics()

    assert len(report.dependencies) == len(REQUIRED_DEPENDENCIES)
    assert all(dep.available for dep in report.dependencies)
    assert report.solver_result.status_name == "OPTIMAL"
    assert report.solver_result.objective_value == 15
