# TAVIO — Technical Documentation (`tavio/`)

**TAVIO** (*Timetable Administration & Validation Intelligent Organizer*) is an offline-first, **source-available** Windows desktop application for Malaysian schools. This folder (`tavio/`) contains the authoritative Python and PySide6 desktop codebase.

---

## Phase 0 Scope & Current Status

TAVIO is currently in **Phase 0 (Project Skeleton & Windows Packaging Spike)**. Database schemas, school configuration, timetable generation, manual editing, absence tracking, relief allocation, and reporting modules are planned for **Phases 1–6** and are **not yet implemented**.

Phase 0 currently provides:
- Modular `src/tavio/` package layout (`ui`, `services`, `solver`, `database`, `reports`, `excel`, `domain`)
- Windows local storage resolution under `%LOCALAPPDATA%\TAVIO\`
- Rotating UTF-8 application logging (`%LOCALAPPDATA%\TAVIO\logs\tavio.log`)
- Long-lived single-instance protection via `QLockFile` (`tavio.lock`, `setStaleLockTime(0)`)
- Minimal PySide6 main window with navigation placeholders for Phases 1–6
- Explicit startup dependency checks (`PySide6`, `ortools`, `reportlab`, `openpyxl`)
- Headless OR-Tools CP-SAT smoke test (`tavio.solver.smoke_test`)
- PyInstaller `--onedir` Windows build specification (`packaging/tavio.spec`) and PowerShell script (`packaging/build_windows.ps1`)

---

## Prerequisites

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python **3.11** or **3.12** (64-bit)
- **Shell:** Windows PowerShell 5.1+ or PowerShell 7+

---

## Setup & Installation (Windows PowerShell)

All commands below assume your working directory is the `tavio/` folder inside the repository:

```powershell
cd tavio

# 1. Create and activate a virtual environment
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Upgrade pip and install TAVIO with development/build dependencies
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

*(If you use Python 3.11 instead of 3.12, replace `py -3.12` with `py -3.11`.)*

---

## Running the Application

With the virtual environment activated inside `tavio/`:

```powershell
python -m tavio.main
```

*(Alternatively, run the installed GUI script `tavio`.)*

---

## Running Tests & Linter

### Run `pytest`
```powershell
python -m pytest
```

### Run `Ruff`
```powershell
python -m ruff check src tests
```

---

## Building the Windows Executable (PyInstaller `--onedir`)

Run the PowerShell build script inside `tavio/` (by default this runs `pytest` and `ruff check` before invoking PyInstaller):

```powershell
.\packaging\build_windows.ps1
```

Or invoke PyInstaller directly using the spec file:

```powershell
python -m PyInstaller --noconfirm --clean packaging\tavio.spec
```

The `--onedir` output is generated at `dist\TAVIO\`. Launch the packaged executable manually on Windows to verify GUI rendering, single-instance locking, bundled stylesheets, and CP-SAT execution:

```powershell
.\dist\TAVIO\TAVIO.exe
```

*(Note: Packaging and `.exe` runtime behavior must be verified directly on Windows 10/11.)*

---

## Local Data Storage (`%LOCALAPPDATA%\TAVIO\`)

At runtime, TAVIO resolves `%LOCALAPPDATA%\TAVIO\` (or `TAVIO_DATA_DIR` if explicitly overridden for testing) and initializes:

- **Database directory:** `%LOCALAPPDATA%\TAVIO\data\` (reserved for `tavio.db` starting in Phase 1)
- **Backup directory:** `%LOCALAPPDATA%\TAVIO\backups\` (reserved for atomic backups in Phase 6)
- **Log file:** `%LOCALAPPDATA%\TAVIO\logs\tavio.log` (UTF-8 rotating log, up to 5 backups of 2 MB)
- **Single-instance lock:** `%LOCALAPPDATA%\TAVIO\tavio.lock`

---

## Folder Structure

```text
tavio/
├── .gitignore
├── pyproject.toml                # Package metadata, dependencies, pytest & Ruff config
├── README.md                     # Technical documentation (this file)
├── packaging/
│   ├── build_windows.ps1         # Automated Windows test, lint, and PyInstaller build script
│   └── tavio.spec                # PyInstaller --onedir build specification
├── resources/
│   ├── fonts/                    # Reserved for bundled PDF fonts (Phase 6)
│   ├── icons/                    # Reserved for tavio.ico application icon
│   └── styles/
│       └── main.qss              # Phase 0 desktop Qt stylesheet
├── src/
│   └── tavio/
│       ├── __init__.py
│       ├── config.py             # %LOCALAPPDATA%\TAVIO path & resource resolution
│       ├── logging_setup.py      # Rotating UTF-8 file + console logger
│       ├── main.py               # Entry point, QLockFile guard, startup checks, GUI launch
│       ├── database/             # Reserved for SQLite persistence (Phase 1+)
│       ├── domain/               # Reserved for domain models & rules (Phase 1+)
│       ├── excel/                # Reserved for OpenPyXL import/export (Phase 2+)
│       ├── reports/              # Reserved for ReportLab PDF generation (Phase 6)
│       ├── services/
│       │   └── startup_service.py # Dependency verification & CP-SAT smoke runner
│       ├── solver/
│       │   └── smoke_test.py     # Headless OR-Tools CP-SAT Phase 0 smoke problem
│       └── ui/
│           └── main_window.py    # Minimal PySide6 shell window & Phase 0 diagnostics
└── tests/
    ├── conftest.py
    ├── test_config.py            # Path, resource, ConfigurationError, and logging tests
    ├── test_dependencies.py      # Import verification and diagnostics tests
    ├── test_single_instance.py   # Long-lived QLockFile behavior tests
    └── test_solver_smoke.py      # OR-Tools CP-SAT smoke test
```

---

## License

TAVIO is **Source-Available Software** licensed under the **PolyForm Noncommercial License 1.0.0** (`SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0`). See [`../LICENSE`](../LICENSE) for the full license text and `Required Notice`, and [`../README.md`](../README.md) for the project usage policy.

This license covers only original TAVIO code and materials; third-party dependencies (`PySide6`, `ortools`, `reportlab`, `openpyxl`, `PyInstaller`, `pytest`, `Ruff`) remain governed by their respective licenses.
