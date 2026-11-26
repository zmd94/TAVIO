# TAVIO — Timetable Administration & Validation Intelligent Organizer

**Smart School Scheduling System** · **Windows Desktop** · **Source-Available Software**

## Overview

TAVIO is an offline-first, source-available Windows desktop application being developed for Malaysian schools. It aims to support school timetable administration, validation and optimization, including multiple school sessions, operating-day schedules, specialist-room constraints, teacher assignments, and teacher absence/relief workflows.

The authoritative application codebase is the Python/PySide6 project in [tavio/](tavio/README.md).

## Project Status

**Overall: Active development — foundational infrastructure is in place; core school workflows are still being developed.**

TAVIO has progressed beyond the original Phase 0 skeleton. The SQLite database layer and versioned migrations are implemented, and several school-configuration screens are functional. The full Master Data workflows, timetable generation and editing, relief management, and final reporting workflows are not yet complete.

### Implemented

- Modular Python package structure for the Windows desktop application.
- PySide6 application shell, navigation, startup diagnostics, and single-instance protection.
- Local application configuration, resource resolution, and rotating UTF-8 logging.
- SQLite database infrastructure, schema management, and versioned migrations through migration version 3.
- Database migration for Class Teacher linkage: nullable classes.class_teacher_id references teachers(id) with ON DELETE RESTRICT.
- Functional school-configuration pages: School Profile, School Administrators, and Schedule Signatories.
- Startup dependency checks and an OR-Tools CP-SAT smoke test.
- Automated test and lint configuration, plus a PyInstaller Windows packaging specification and build script.

### Partially implemented / in progress

- **Phase 1 — Application and school configuration foundation:** database infrastructure and initial configuration screens exist; the complete configuration workflow and approved portable workspace-file design are not yet implemented.
- **Phase 2 — Master Data foundation:** database groundwork exists, but complete Teachers, Classes, Subjects, Special Rooms, teaching assignments, and Class Teacher management workflows are not yet available in the application.

### Not yet implemented as complete application workflows

- Timetable generation and full constraint validation.
- Manual timetable editing, locking, and version-management workflows.
- Teacher absence management and automated relief allocation.
- Final PDF and Excel reporting workflows.

> A database table or migration does not mean its corresponding user-facing feature is complete. This status describes usable application workflows, not merely the presence of schema objects.

## Development Roadmap

| Phase | Scope | Current assessment |
| :--- | :--- | :--- |
| **Phase 0** | Project skeleton, Windows paths, logging, single-instance protection, dependency checks, CP-SAT smoke test, packaging foundation | **Substantially complete** |
| **Phase 1** | SQLite persistence and migrations; school configuration; remaining configuration and workspace foundation | **In progress** |
| **Phase 2** | Master Data, teaching assignments, Class Teacher assignments, and validation | **In progress — database groundwork exists; application workflows remain** |
| **Phase 3** | Timetable generation, constraint validation, solver diagnostics, and optimization using OR-Tools CP-SAT | **Not started as a complete workflow** |
| **Phase 4** | Manual timetable editor, slot locking, timetable versioning, and related validation | **Not started** |
| **Phase 5** | Teacher absences, relief allocation, workload balancing, overrides, and audit history | **Not started** |
| **Phase 6** | PDF/Excel reports, final packaging and release readiness | **Not started** |

Phase labels are planning milestones. Work may overlap where database foundations are needed ahead of their user-facing phase.

## Important Architecture Note: Database and Workspace Design

The current application has a local SQLite database implementation managed under the Windows local application-data area.

Separately, the approved product direction describes a portable single .tavio workspace file per school, with NEW TIMETABLE, OPEN AS, SAVE, SAVE AS, background recovery/autosave, and recovery handling.

**The portable .tavio workspace-file workflow is a documented design, not an implemented feature.** The current SQLite database architecture and migrations must be technically reconciled with that workspace design before implementation. Existing database schema and migrations must not be discarded or replaced casually.

See [docs/data_file_management.md](docs/data_file_management.md) for the approved workspace decisions.

## Technology Stack

- **Language:** Python 3.11 or 3.12 (64-bit Windows)
- **Desktop GUI:** PySide6 (Qt 6)
- **Database:** SQLite with versioned migrations
- **Optimization Engine:** Google OR-Tools (CP-SAT)
- **PDF Reporting:** ReportLab (planned workflow)
- **Excel Operations:** OpenPyXL (planned workflow)
- **Testing & Code Quality:** pytest, Ruff
- **Windows Packaging:** PyInstaller (--onedir); Inno Setup is part of the planned installer workflow

## Repository Structure

- LICENSE
- README.md — Main project overview, status and roadmap
- docs/ — Approved product and reporting specifications
- tavio/ — Authoritative Python/PySide6 desktop application
  - pyproject.toml
  - README.md — Technical setup, implementation status and build guide
  - packaging/
  - resources/
  - src/tavio/
  - tests/
- Root React/Vite scaffold files (package.json, index.html, src/, vite.config.ts, tsconfig.json, metadata.json, .env.example) are inherited workspace template/prototype files. They are not part of, or dependencies of, the official TAVIO desktop application; their future disposition has not yet been finalized.

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Normal operation:** Designed for offline local use
- **Development/build environment:** Python 3.11 or 3.12 (64-bit), Windows PowerShell 5.1+ or PowerShell 7+

## Installation & Development Documentation

For setup, dependency installation, running the application, tests, Ruff, and Windows build instructions, see:

- [TAVIO Technical Documentation (tavio/README.md)](tavio/README.md)
- [Python Package Configuration (tavio/pyproject.toml)](tavio/pyproject.toml)

## License & Usage Policy

TAVIO is distributed as **Source-Available Software** under the **[PolyForm Noncommercial License 1.0.0](LICENSE)** (SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0).

> TAVIO is **not** OSI-approved Open Source Software because the license restricts commercial use.

Full terms are available in [LICENSE](LICENSE) and at https://polyformproject.org/licenses/noncommercial/1.0.0.

### Permitted Uses

Educational institutions are permitted to use TAVIO under the PolyForm Noncommercial License 1.0.0, regardless of funding sources, subject to the license terms. Permitted uses include educational institutions, noncommercial purposes, personal study/research/testing without anticipated commercial application, and modification/distribution for license-permitted purposes with the required license terms and Required Notice.

### Commercial Use

Commercial use is not automatically granted. Any individual or organization wishing to use, sell, host, or distribute TAVIO for commercial purposes must obtain a separate commercial license or explicit written permission from the TAVIO owner.

### Third-Party Dependencies

The PolyForm Noncommercial License 1.0.0 applies solely to original TAVIO code and materials. It does not replace or modify the respective licenses of third-party dependencies, including PySide6, Google OR-Tools, ReportLab, OpenPyXL, PyInstaller, pytest, and Ruff.
