"""Tests for the Phase 0 OR-Tools CP-SAT smoke solver."""

from __future__ import annotations

from tavio.solver.smoke_test import run_cp_sat_smoke_test


def test_cp_sat_smoke_test_finds_optimal_schedule() -> None:
    result = run_cp_sat_smoke_test()

    assert result.status_name == "OPTIMAL"
    # Optimal assignment: T1->Slot 2 (5), T2->Slot 1 (4), T3->Slot 3 (6) => 15
    assert result.objective_value == 15
    assert result.assignments == {"T1": 2, "T2": 1, "T3": 3}
    assert result.assignments["T1"] != 1
    assert len(set(result.assignments.values())) == 3
    assert result.wall_time_ms >= 0.0
    assert "CP-SAT Status: OPTIMAL" in result.format_summary()
