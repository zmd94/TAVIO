# TAVIO — Timetable Administration & Validation Intelligent Organizer

**Smart School Scheduling System** · **Windows Desktop** · **Source-Available Software**

> **[TAVIO Logo Placeholder]**  
> *Brand banner and application icon assets will be added to `tavio/resources/icons/` in a later release.*

---

## Overview & Problem Statement

**TAVIO** (*Timetable Administration & Validation Intelligent Organizer*) is an offline-first, source-available Windows desktop application designed for Malaysian schools.

Schools regularly face complex scheduling challenges: managing multiple school sessions, varying bell schedules across operating days, team-taught and split-group lessons, specialist room constraints, and daily teacher absences (*Guru Ganti* / relief coordination). Many schools rely on manual spreadsheets or disconnected tools that require constant internet access or recurring cloud subscriptions.

TAVIO aims to solve these challenges locally on a school's Windows PC—operating **100% offline** with deterministic validation, constraint optimization, and printable administrative outputs.

---

## Project Status

**Current Status:** **Phase 0 — Project Skeleton & Windows Packaging Spike** (Active Development)

TAVIO is in early foundational development. Core scheduling, database persistence, and relief modules are scheduled for upcoming phases and are **not yet implemented**.

### Implemented in Phase 0
- Modular Python package structure inside `tavio/src/tavio/`
- Windows `%LOCALAPPDATA%\TAVIO\` directory initialization (`data\`, `backups\`, `logs\`)
- Rotating UTF-8 application logging (`%LOCALAPPDATA%\TAVIO\logs\tavio.log`)
- Long-lived single-instance protection using `QLockFile` (`tavio.lock`)
- Minimal PySide6 desktop shell window with Phase 1–6 navigation placeholders
- Startup dependency verification (`PySide6`, `ortools`, `reportlab`, `openpyxl`) and an OR-Tools CP-SAT smoke test
- PyInstaller `--onedir` Windows packaging specification (`tavio/packaging/tavio.spec`) and PowerShell build script

### Planned Features (Phases 1–6)
- **School timetable generation** (OR-Tools CP-SAT optimization with cross-session conflict validation, team teaching, parallel student groups, and synchronized multi-class scheduling) — *Phase 3*
- **Manual timetable management** (interactive Class, Teacher, and Room editor with real-time conflict checking, slot locking, and version management) — *Phase 4*
- **Teacher absence management** (full-day, multi-day, session/period, and custom `HH:MM` partial-day absences with overlap protection) — *Phase 5*
- **Automated teacher relief allocation** (CP-SAT daily and date-range relief batches, workload balancing, manual overrides, and append-only audit logs) — *Phase 5*
- **PDF and Excel reporting** (ReportLab timetable PDFs, *Slip Guru Ganti*, and OpenPyXL import/export workbooks) — *Phases 2 & 6*
- **Offline-first local operation** (local SQLite storage in `tavio.db` and atomic backup/restore) — *Phases 1 & 6*

---

## Development Roadmap

| Phase | Scope | Status |
| :--- | :--- | :--- |
| **Phase 0** | Project skeleton, `LocalAppData` setup, logging, `QLockFile`, dependency & CP-SAT smoke checks, PyInstaller `--onedir` config | **Current Phase** |
| **Phase 1** | Local SQLite schema & migrations (`tavio.db`), school configuration, flexible operating days, multi-session bell schedules | Planned |
| **Phase 2** | Master data (teachers, classes, education levels, subjects, rooms), teaching assignments, Excel import templates | Planned |
| **Phase 3** | Cross-session OR-Tools CP-SAT timetable generation engine & pre-solve diagnostics | Planned |
| **Phase 4** | Manual timetable editor, slot locking, timetable versioning & future-relief impact checks | Planned |
| **Phase 5** | Granular teacher absences, automated batch relief allocation & append-only audit history | Planned |
| **Phase 6** | ReportLab PDFs (*Slip Guru Ganti* & timetables), Excel analytics, SQLite backup/restore & Windows release packaging | Planned |

---

## Technology Stack

- **Language:** Python 3.11 or 3.12 (64-bit Windows)
- **Desktop GUI:** PySide6 (Qt 6)
- **Local Database:** SQLite (planned for Phase 1+, stored locally as `tavio.db`)
- **Optimization Engine:** Google OR-Tools (CP-SAT)
- **PDF Reporting:** ReportLab
- **Excel Operations:** OpenPyXL
- **Testing & Code Quality:** pytest, Ruff
- **Windows Packaging:** PyInstaller (`--onedir`)

---

## Repository Structure

```text
.
├── LICENSE                  # PolyForm Noncommercial License 1.0.0 + Required Notice
├── README.md                # Main project overview and usage policy
└── tavio/                   # Authoritative Python desktop application
    ├── pyproject.toml       # Python metadata, dependencies, pytest & Ruff config
    ├── README.md            # Technical setup, test, and Windows build documentation
    ├── packaging/           # PyInstaller .spec and PowerShell build script
    ├── resources/           # Stylesheets, icons, and fonts
    ├── src/tavio/           # Modular application source code
    └── tests/               # Automated pytest suite
```

---

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Network:** Fully offline during normal operation (no mandatory internet connection, no cloud database)
- **Development / Build Environment:**
  - Python 3.11 or 3.12 (64-bit)
  - Windows PowerShell 5.1+ or PowerShell 7+

---

## Installation & Development Documentation

For step-by-step instructions on setting up the Python virtual environment, installing dependencies, running the application, running `pytest` and `Ruff`, and building the Windows executable, see:

- **[TAVIO Technical Documentation (`tavio/README.md`)](tavio/README.md)**
- **[Python Package Configuration (`tavio/pyproject.toml`)](tavio/pyproject.toml)**

---

## License & Usage Policy

TAVIO is distributed as **Source-Available Software** under the **[PolyForm Noncommercial License 1.0.0](LICENSE)** (`SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0`).

> **Note:** TAVIO is **not** OSI-approved Open Source Software because the license restricts commercial use.

Full license terms are available in **[LICENSE](LICENSE)** and at <https://polyformproject.org/licenses/noncommercial/1.0.0>.

### Permitted Uses
Under the PolyForm Noncommercial License 1.0.0, TAVIO may be used without separate fee or commercial agreement for:
- **Educational institutions**, including government/public and private schools, regardless of funding source (`Noncommercial Organizations` section).
- **Noncommercial purposes** (`Noncommercial Purposes` section).
- **Personal study, learning, research, experimentation, and testing** without anticipated commercial application (`Personal Uses` section).
- **Modification and distribution of copies** for purposes permitted by the license, provided all distributed copies include the license terms (or official URL) and the `Required Notice:` line from `LICENSE`.

### Commercial Use
- Commercial use is **not** automatically granted by this license.
- Any individual or organization wishing to use, sell, host, or distribute TAVIO for commercial purposes must obtain a separate commercial license or explicit written permission from the TAVIO owner.
- The TAVIO owner reserves the right to offer separate commercial licensing terms.
- Permission granted to educational institutions under the license applies to use by those institutions and does **not** grant third-party vendors or commercial service providers general permission to sell or commercially exploit TAVIO.

### Third-Party Dependencies
The PolyForm Noncommercial License 1.0.0 applies solely to the original code and materials owned or licensed by the TAVIO contributors. It does **not** replace, override, or modify the respective licenses of third-party dependencies used by TAVIO (including PySide6, Google OR-Tools, ReportLab, OpenPyXL, PyInstaller, pytest, and Ruff).
