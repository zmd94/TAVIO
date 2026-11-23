# TAVIO — Timetable Administration & Validation Intelligent Organizer

TAVIO is an offline-first, open-source Windows desktop application for Malaysian schools covering timetable generation, manual timetable management, teacher absence tracking, and automated teacher relief allocation.

## Phase 0 Scope

Phase 0 establishes the verified project skeleton and Windows packaging spike:

- Modular `src/tavio/` package architecture (`ui`, `services`, `solver`, `database`, `reports`, `excel`, `domain`)
- Windows local storage resolution under `%LOCALAPPDATA%\TAVIO\`
- Rotating application logging (`%LOCALAPPDATA%\TAVIO\logs\tavio.log`)
- Single-instance enforcement via `QLockFile`
- Minimal PySide6 shell window with navigation placeholders
- Explicit dependency verification (`PySide6`, `ortools`, `reportlab`, `openpyxl`)
- Headless OR-Tools CP-SAT smoke test
- PyInstaller `--onedir` Windows packaging configuration

## Prerequisites (Windows 10 / 11, 64-bit)

- Python **3.11** or **3.12** (64-bit)
- PowerShell 5.1+ or PowerShell 7+

## Setup & Installation (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Run the Application

```powershell
python -m tavio.main
```

## Run Automated Tests & Linter

```powershell
pytest
ruff check src tests
```

## Build Windows Executable (`--onedir`)

```powershell
.\packaging\build_windows.ps1
```

Launch the packaged application:

```powershell
.\dist\TAVIO\TAVIO.exe
```

## Local Data Directory

At runtime, TAVIO stores local data in:

- `%LOCALAPPDATA%\TAVIO\data\` (reserved for `tavio.db` in Phase 1+)
- `%LOCALAPPDATA%\TAVIO\backups\`
- `%LOCALAPPDATA%\TAVIO\logs\tavio.log`
- `%LOCALAPPDATA%\TAVIO\tavio.lock`
