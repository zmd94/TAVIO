"""OR-Tools CP-SAT smoke test for Phase 0 dependency and solver verification.

This module intentionally has zero dependency on PySide6 or SQLite.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from ortools.sat.python import cp_model


@dataclass(frozen=True, slots=True)
class SolverSmokeResult:
    """Structured outcome from the Phase 0 OR-Tools CP-SAT verification problem."""

    status_name: str
    objective_value: int
    assignments: dict[str, int]
    wall_time_ms: float

    def format_summary(self) -> str:
        """Return a human-readable summary of the solved schedule."""
        ordered = ", ".join(f"{teacher}->Slot {slot}" for teacher, slot in self.assignments.items())
        return (
            f"CP-SAT Status: {self.status_name} | "
            f"Objective: {self.objective_value} | "
            f"Assignments: [{ordered}] | "
            f"Time: {self.wall_time_ms:.2f} ms"
        )


def run_cp_sat_smoke_test() -> SolverSmokeResult:
    """Solve a minimal 3-teacher, 3-slot assignment optimization problem.

    Problem definition:
    - Teachers T1, T2, T3 must each be assigned to exactly one distinct slot in {1, 2, 3}.
    - T1 is unavailable for Slot 1.
    - Maximize total slot preference score:
      T1: {Slot 2: 5, Slot 3: 3}
      T2: {Slot 1: 4, Slot 2: 6, Slot 3: 2}
      T3: {Slot 1: 5, Slot 2: 1, Slot 3: 6}
    """
    started = time.perf_counter()
    model = cp_model.CpModel()

    teachers = ("T1", "T2", "T3")
    slots = (1, 2, 3)

    x: dict[tuple[str, int], cp_model.IntVar] = {}
    for teacher in teachers:
        for slot in slots:
            x[(teacher, slot)] = model.NewBoolVar(f"x_{teacher}_{slot}")

    # Hard constraint 1: Each teacher gets exactly one slot.
    for teacher in teachers:
        model.AddExactlyOne(x[(teacher, slot)] for slot in slots)

    # Hard constraint 2: Each slot hosts at most/exactly one teacher.
    for slot in slots:
        model.AddExactlyOne(x[(teacher, slot)] for teacher in teachers)

    # Hard constraint 3: T1 is unavailable in Slot 1.
    model.Add(x[("T1", 1)] == 0)

    # Soft objective: Maximize preference weights.
    preferences: dict[tuple[str, int], int] = {
        ("T1", 1): 0,
        ("T1", 2): 5,
        ("T1", 3): 3,
        ("T2", 1): 4,
        ("T2", 2): 6,
        ("T2", 3): 2,
        ("T3", 1): 5,
        ("T3", 2): 1,
        ("T3", 3): 6,
    }
    model.Maximize(
        sum(preferences[(t, s)] * x[(t, s)] for t in teachers for s in slots)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 5.0
    status = solver.Solve(model)
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    status_name = solver.StatusName(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(
            f"Phase 0 CP-SAT smoke test failed with unexpected status: {status_name}"
        )

    assignments: dict[str, int] = {}
    for teacher in teachers:
        for slot in slots:
            if solver.BooleanValue(x[(teacher, slot)]):
                assignments[teacher] = slot
                break

    if len(assignments) != len(teachers):
        raise RuntimeError("CP-SAT smoke test did not produce complete assignments.")

    return SolverSmokeResult(
        status_name=status_name,
        objective_value=round(solver.ObjectiveValue()),
        assignments=assignments,
        wall_time_ms=elapsed_ms,
    )
