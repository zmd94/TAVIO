# TAVIO — Technical Documentation (tavio/)

TAVIO (Timetable Administration & Validation Intelligent Organizer) is an offline-first, source-available Windows desktop application for Malaysian schools. This folder contains the authoritative Python and PySide6 desktop codebase.

This document describes the implementation status and Windows development/build workflow. It distinguishes implemented infrastructure from planned application features.

## Current Implementation Status

**Overall: Active development. The project has progressed beyond the initial Phase 0 skeleton.**

### Implemented foundation

- Modular Python package structure under src/tavio/.
- PySide6 main window, navigation, and implemented school-configuration pages: School Profile, School Administrators, and Schedule Signatories.
- Windows application-data path and resource resolution.
- Rotating UTF-8 application logging.
- Single-instance protection using Qt QLockFile.
- SQLite database manager, schema initialization, and versioned migration system.
- Database migrations currently reach PRAGMA user_version = 4.
- Migration v3 adds nullable classes.class_teacher_id, with a foreign key to teachers(id) and ON DELETE RESTRICT.
- Migration v4 removes unused legacy timetable autosave schema objects and the obsolete 10-minute autosave setting; it does not implement workspace recovery.
- Startup dependency diagnostics for PySide6, OR-Tools, ReportLab, and OpenPyXL.
- OR-Tools CP-SAT smoke test.
- pytest and Ruff configuration.
- PyInstaller --onedir specification and PowerShell build script.

### In progress / not yet complete

- Remaining school configuration workflows.
- Master Data user workflows for Teachers, Classes, Subjects, and Special Rooms.
- Teaching assignment and Class Teacher assignment workflows, including eligibility validation.
- Integration of Master Data and assignments with timetable workflows.

### Planned application workflows

- Timetable generation and full constraint validation.
- Manual timetable editing, slot locking, and timetable version management.
- Teacher absence management and automated relief allocation.
- PDF and Excel reporting, including the approved timetable report layouts.

**Important:** Database schema objects, migrations, placeholder navigation pages, and smoke tests do not by themselves constitute completed user-facing features.

## Roadmap

| Phase | Scope | Status |
| :--- | :--- | :--- |
| **Phase 0** | Project skeleton, local paths, logging, single-instance guard, startup checks, CP-SAT smoke test, packaging foundation | **Substantially complete** |
| **Phase 1** | SQLite persistence/migrations and school configuration | **In progress** |
| **Phase 2** | Master Data, teaching assignments, Class Teacher assignments, and validation | **In progress — database groundwork exists; application workflows remain** |
| **Phase 3** | OR-Tools CP-SAT timetable generation and diagnostics | **Not started as a complete workflow** |
| **Phase 4** | Manual timetable editor, locking, and version management | **Not started** |
| **Phase 5** | Absence management, relief allocation, and audit history | **Not started** |
| **Phase 6** | PDF/Excel reports and release packaging | **Not started** |

## Workspace Architecture Status

The current implementation uses a local SQLite database managed by the application under its Windows application-data location.

The approved product specification separately defines a portable single-file .tavio workspace per school, including NEW TIMETABLE, OPEN AS, SAVE, SAVE AS, five-minute background recovery autosave to a .bak file, and startup recovery choices.

**That portable workspace-file workflow has not yet been implemented.** The existing SQLite database manager, repositories, migrations, and data lifecycle need a deliberate technical design to support the approved workspace model. Do not assume that the current local database already behaves as a portable .tavio file.

See [../docs/data_management.md](../docs/data_file_management.md) for the approved product decisions. These are specifications, not evidence that the corresponding code exists.

## Prerequisites

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.11 or 3.12 (64-bit)
- **Shell:** Windows PowerShell 5.1+ or PowerShell 7+

## Setup & Installation (Windows PowerShell)

Run these commands from the repository's tavio/ folder:

    cd tavio
    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -e ".[dev]"

For Python 3.11, replace py -3.12 with py -3.11.

## Running the Application

With the virtual environment activated inside tavio/:

    python -m tavio.main

Alternatively, run the installed GUI script tavio.

## Running Tests & Linter

Run pytest:

    python -m pytest

Run Ruff:

    python -m ruff check src tests

## Building the Windows Executable (PyInstaller --onedir)

Run the PowerShell build script inside tavio/ (by default, it runs pytest and Ruff before invoking PyInstaller):

    .\packaging\build_windows.ps1

Or invoke PyInstaller directly:

    python -m PyInstaller --noconfirm --clean packaging\tavio.spec

The --onedir output is generated at dist\TAVIO\. Launch the packaged executable manually on Windows to verify GUI rendering, single-instance locking, bundled stylesheets, and CP-SAT execution:

    .\dist\TAVIO\TAVIO.exe

**Note:** Packaging and executable runtime behavior must be verified directly on Windows 10/11.

## Local Application Data

At runtime, TAVIO resolves the Windows local application-data location for its application files (or TAVIO_DATA_DIR when explicitly overridden for testing). The current implementation initializes application directories for database storage, logs, and the single-instance lock.

The current database is initialized at `%LOCALAPPDATA%\\TAVIO\\data\\tavio.db` by default (or under `TAVIO_DATA_DIR` when overridden). This local database arrangement is not the approved portable `.tavio` workspace workflow; see Workspace Architecture Status above.

## Project Structure

    tavio/
    ├── pyproject.toml
    ├── README.md
    ├── packaging/
    │   ├── build_windows.ps1
    │   └── tavio.spec
    ├── resources/
    │   ├── fonts/
    │   ├── icons/
    │   └── styles/
    │       └── main.qss
    ├── src/
    │   └── tavio/
    │       ├── config.py
    │       ├── logging_setup.py
    │       ├── main.py
    │       ├── database/
    │       ├── domain/
    │       ├── excel/
    │       ├── reports/
    │       ├── services/
    │       ├── solver/
    │       └── ui/
    └── tests/

Directory names may evolve as implementation progresses. The presence of a package or directory does not imply that all planned features are complete.

## License

TAVIO is **Source-Available Software** licensed under the **PolyForm Noncommercial License 1.0.0** (SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0). See [../LICENSE](../LICENSE) for the full license text and Required Notice, and [../README.md](../README.md) for the project usage policy.

This license covers only original TAVIO code and materials; third-party dependencies (PySide6, ortools, reportlab, openpyxl, PyInstaller, pytest, and Ruff) remain governed by their respective licenses.
