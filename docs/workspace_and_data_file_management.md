# Workspace and Data File Management Decisions

**Project:** TAVIO — Timetable Administration & Validation Intelligent Organizer  
**Repository:** `zmd94/TAVIO`  
**Status:** Design decisions recorded; implementation not authorized by this document  
**Scope:** Workspace lifecycle, `.tavio` data packages, saving, backup, recovery, validation, and database migration.

## 1. Purpose and scope

This document records the agreed product and safety decisions for managing TAVIO workspaces and their data files. It supplements the existing project specifications.

This is a decision record only. It does not authorize implementation, database schema changes, migrations, or changes to existing application code. Technical design and implementation details must be reviewed separately before development.

## 2. Terminology

- **Workspace:** The school data currently loaded and being used by TAVIO.
- **`.tavio` file:** A single portable data package containing the data for a school workspace.
- **NEW TIMETABLE:** The user-facing command for creating a new workspace. In this project, **NEW TIMETABLE and NEW WORKSPACE mean the same operation**. Use **NEW TIMETABLE** in the application interface.
- **Current workspace:** The workspace currently open in the application.
- **Unsaved changes:** Changes made in the current workspace that have not yet been saved to its data file.

## 3. Workspace and data-package model

1. TAVIO stores a school workspace in one `.tavio` package file, rather than asking users to manage separate files for individual database tables.
2. The package is intended to include the school profile and settings, academic years and sessions, master data, teacher and class-teacher assignments, timetables and their versions, report settings, school assets such as the logo, and related workspace information.
3. Users can use SAVE AS to create a portable package and transfer it to another computer, for example by USB drive or network storage.
4. OPEN AS loads a `.tavio` package as a separate workspace.
5. Users may keep multiple `.tavio` files and switch between them. Workspace data must remain isolated; data from different packages must never be mixed.
6. TAVIO must validate compatibility and data integrity before accepting a package as a workspace.
7. Opening a package must not silently modify the source file. Changes are saved only through an explicit SAVE or SAVE AS action.

## 4. Main workspace commands

TAVIO's main workspace commands are:

| Command | Agreed purpose |
|---|---|
| NEW TIMETABLE | Create a new workspace, following the data-retention rules in Section 5 |
| OPEN AS | Open a selected `.tavio` package as a separate workspace |
| SAVE | Save changes to the current workspace file |
| SAVE AS | Save the current workspace as a new `.tavio` file |
| EXIT | Close the TAVIO application |

A separate user-facing **CLOSE WORKSPACE** command will not be provided. The existing NEW TIMETABLE, OPEN AS, and EXIT commands are sufficient for the agreed user workflow. TAVIO may still use an internal no-workspace state where technically necessary.

## 5. NEW TIMETABLE — create a new workspace

NEW TIMETABLE is the same operation as NEW WORKSPACE. It creates a new workspace; it does not edit or clear the source workspace's `.tavio` file.

### 5.1 Data copied into the new workspace

TAVIO automatically copies these three sections from the current workspace:

1. SCHOOL PROFILE
2. SCHOOL ADMINISTRATORS
3. SCHEDULE SIGNATORIES

This avoids requiring users to re-enter school identity, administrator, and signatory information for every new timetable workspace.

### 5.2 Data that starts empty in the new workspace

The new workspace starts without the previous workspace's timetable-production data, including:

- Teachers
- Classes
- Subjects
- Special Rooms
- Teacher Assignments
- Class Teacher Assignments
- Timetable data and all timetable versions
- Other master data, assignments, and settings specific to timetable preparation

The user will enter the MASTER DATA again for the new workspace.

### 5.3 Unsaved changes before NEW TIMETABLE

If the current workspace has unsaved changes, TAVIO must ask the user to choose:

- **SAVE** — save the current workspace first, then create the new workspace.
- **DON'T SAVE** — discard the unsaved changes, then create the new workspace.
- **CANCEL** — cancel the operation and keep the current workspace open.

If SAVE fails, TAVIO must not proceed with NEW TIMETABLE. The current workspace must remain available.

### 5.4 Source-workspace protection

Copying the three retained sections must not modify or delete data in the source workspace. The old `.tavio` file remains intact.

## 6. First launch and reopening the last workspace

1. If TAVIO is launched for the first time and no `.tavio` workspace has yet been created, it automatically provides an empty workspace so the user can begin entering SCHOOL PROFILE and other information.
2. TAVIO remembers the last workspace used.
3. On the next application launch, TAVIO automatically attempts to reopen that last workspace.
4. If the last file has been moved, renamed, deleted, or cannot be opened, TAVIO asks the user to select another `.tavio` file.
5. TAVIO must not silently create a different workspace or overwrite a data file when reopening fails.

## 7. Unsaved changes before OPEN AS

When the user tries to open a different `.tavio` file while the current workspace has unsaved changes, TAVIO must offer:

- **SAVE** — save the current workspace first, then open the selected file.
- **DON'T SAVE** — discard current unsaved changes, then open the selected file.
- **CANCEL** — cancel OPEN AS and keep the current workspace.

If saving the current workspace fails, TAVIO must not proceed to open the other file. If the selected file fails validation or cannot be opened, the current workspace must remain intact and active. Workspaces must never be mixed.

## 8. SAVE and SAVE AS

### 8.1 SAVE

SAVE writes changes to the current workspace's existing `.tavio` file. Before replacing an existing file, TAVIO uses the temporary backup and safe-save procedure in Section 9.

### 8.2 SAVE AS

SAVE AS saves the current workspace as a new `.tavio` file at a location selected by the user.

- SAVE AS must not alter the source file from which the workspace was opened.
- If the destination already exists, TAVIO must ask the user to confirm before replacing it.
- SAVE AS is distinct from SAVE and must not silently overwrite another workspace file.

## 9. Temporary backup and safe-save procedure

The agreed policy is **one temporary backup per file**, not a rolling history of backups.

### 9.1 Backup location and name

- Create the backup in the same folder as the main `.tavio` file.
- Use a corresponding `.bak` file, for example `Data_Sekolah_2026.tavio.bak`.
- Maintain only one backup for that main file. A new backup may replace an older backup only after the new backup has been safely created.

### 9.2 SAVE sequence

The intended safe-save sequence is:

1. Create a backup of the existing main file.
2. Write the updated workspace to a temporary file in the same folder.
3. Validate the temporary file and its database integrity.
4. Replace the main file using an appropriate atomic replacement operation supported by the operating system and file system.
5. Verify that the resulting main file is valid and can be opened.
6. Only after successful verification, delete the temporary `.bak` backup.

If backup creation fails, cancel SAVE and preserve the existing main file. If any later save or verification step fails, do not report success; preserve the available recovery files and restore the original from backup when safe and necessary. Do not delete the backup until successful completion has been established.

The implementation must handle interrupted operations carefully. Atomic replacement and recovery behavior must be tested on supported Windows file systems; do not assume that a rename or replacement is atomic in every possible storage environment.

### 9.3 Backup purpose

The backup is a temporary safety copy used during SAVE. Under the agreed normal-success behavior, it is automatically deleted after the saved main file has been verified. It is not intended to be a permanent archive of previous versions.

## 10. Recovery after an unexpected shutdown

When TAVIO starts, it checks for temporary save files or a leftover `.bak` file that may indicate an interrupted SAVE.

If recovery files are found:

1. TAVIO informs the user that a previous save may have been interrupted.
2. TAVIO checks which files are structurally valid before offering recovery.
3. The user is offered:
   - **RESTORE** — restore from a valid backup.
   - **KEEP CURRENT** — keep the current main file.
   - **CANCEL** — defer the decision without deleting recovery files.
4. TAVIO must not automatically delete recovery files before the user has made a decision.
5. An invalid backup or temporary file must not be used to overwrite the main file.

The recovery process must preserve the best available valid copy and must not claim recovery succeeded until validation is complete.

## 11. OPEN AS — package validation

Before opening a selected `.tavio` file, TAVIO checks:

1. **File format:** The file is a valid TAVIO package.
2. **SQLite structure:** The database structure is readable and contains the required schema objects.
3. **Schema version:** The database schema version is supported by the installed TAVIO application.
4. **Database integrity:** SQLite integrity and foreign-key relationships are checked.

If validation fails:

- OPEN AS is cancelled.
- The currently active workspace remains open and unchanged.
- The selected source file is not modified.
- TAVIO explains the validation problem to the user.

## 12. AUTO MIGRATION for older workspace files

If a selected `.tavio` package uses an older schema version supported for migration:

1. TAVIO identifies the source schema version.
2. TAVIO informs the user that migration is required.
3. TAVIO creates a backup of the original file before migration.
4. TAVIO runs the defined migrations in the required order.
5. TAVIO validates the migrated database structure and integrity.
6. If migration succeeds, TAVIO opens the migrated workspace using the current supported schema.
7. If migration fails, TAVIO restores or retains the original file and backup, cancels the open, and keeps the current workspace unchanged.

Migration must not silently lose data. Migration steps and compatibility must be explicitly defined and tested for each supported schema version.

## 13. Compatibility with files from newer TAVIO versions — pending decision

A proposal was raised to reject a `.tavio` file created by a newer TAVIO application version and show a message asking the user to update TAVIO first.

**This proposal has not yet been confirmed by the user.** It remains an open decision and must not be treated as an agreed requirement until reviewed.

## 14. Implementation boundaries and safeguards

- This document does not authorize changes to the existing database schema, migrations, or application code.
- Do not implement workspace packaging, save/recovery, or migration by making unrelated changes to stable modules.
- Preserve existing data and enforce database referential integrity.
- Keep workspaces isolated and protect source files during OPEN AS, NEW TIMETABLE, SAVE, SAVE AS, and migration.
- Define and test failure handling, including process termination, power loss, insufficient disk space, permission errors, and interrupted file replacement.
- Any implementation proposal that changes these agreed user-facing behaviors must be brought back for review before development.

---

**Document status:** Design decisions recorded. One compatibility proposal (newer-version files) remains pending user confirmation.
