# Workspace and Data File Management Decisions

**Project:** TAVIO — Timetable Administration & Validation Intelligent Organizer  
**Repository:** `zmd94/TAVIO`  
**Status:** Design decisions recorded; implementation not authorized by this document  
**Scope:** Workspace lifecycle, `.tavio` data packages, autosave, saving, backup, recovery, validation, and database migration.

## 1. Purpose and scope

This document records the agreed product and safety decisions for managing TAVIO workspaces and their data files. It supplements the existing project specifications.

This is a decision record only. It does not authorize implementation, database schema changes, migrations, or changes to existing application code. Technical design and implementation details must be reviewed separately before development.

## 2. Terminology

- **Workspace:** The school data currently loaded and being used by TAVIO.
- **`.tavio` file:** A single portable data package containing the data for a school workspace.
- **NEW TIMETABLE:** The user-facing command for creating a new workspace. In this project, **NEW TIMETABLE and NEW WORKSPACE mean the same operation**. Use **NEW TIMETABLE** in the application interface.
- **Current workspace:** The workspace currently open in the application.
- **Unsaved changes:** Changes made in the current workspace that have not yet been committed to the main `.tavio` file by a successful SAVE.
- **Autosave recovery file:** The single associated `.bak` file that stores the latest successfully autosaved workspace state. It is not a historical backup of the previous main file.

## 3. Workspace and data-package model

1. TAVIO stores a school workspace in one **native SQLite database file** with the `.tavio` extension. No ZIP layer or additional packaging format is used. The file should remain inspectable using standard SQLite software.
2. The single `.tavio` file contains the school profile and settings, academic years and sessions, master data, teacher and class-teacher assignments, timetables and their versions, report settings, school assets such as the logo, a persistent unique workspace ID, and related workspace information.
3. The `.tavio` file is portable. It can be moved by USB, network storage, or another user-managed transfer method and opened on another Windows computer with TAVIO installed. It does not depend on the original computer, its local logo path, a recovery file from that computer, or an internet connection.
4. OPEN AS loads a `.tavio` file as a separate workspace.
5. Users may keep multiple `.tavio` files and switch between them. Workspace data must remain isolated; data from different packages must never be mixed.
6. TAVIO must validate compatibility and data integrity before accepting a package as a workspace.
7. Opening a package must not silently modify the source file. Changes are saved to the main package only through an explicit SAVE or SAVE AS action. Periodic autosave writes to computer-local recovery data, not to the main `.tavio` file.
8. Every workspace has a unique internal ID stored in its SQLite database. The ID is generated when the workspace is created and remains unchanged when the file is saved, copied, moved, or renamed. A newly created workspace receives a new ID, including NEW TIMETABLE workspaces that copy the agreed school information from the current workspace. The ID is not displayed in the normal user interface.

## 4. Main workspace commands

TAVIO's main workspace commands are:

| Command | Agreed purpose |
|---|---|
| NEW TIMETABLE | Create a new workspace, following the data-retention rules in Section 5 |
| OPEN AS | Open a selected `.tavio` package as a separate workspace |
| SAVE | Commit the current workspace to the main `.tavio` file |
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

If SAVE fails, TAVIO must not proceed with NEW TIMETABLE. The current workspace must remain available. The user must be informed if recoverable autosaved changes remain in the recovery file.

### 5.4 Source-workspace protection

Copying the three retained sections must not modify or delete data in the source workspace. The old `.tavio` file remains intact.

## 6. First launch and reopening the last workspace

1. If TAVIO is launched for the first time and no `.tavio` workspace has yet been created, it automatically provides an empty workspace so the user can begin entering SCHOOL PROFILE and other information.
2. TAVIO remembers the last workspace used.
3. On the next application launch, TAVIO automatically attempts to reopen that last workspace.
4. If the last file has been moved, renamed, deleted, or cannot be opened, TAVIO asks the user to select another `.tavio` file.
5. TAVIO must not silently create a different workspace or overwrite a data file when reopening fails.
6. TAVIO checks for computer-local recovery data associated with the workspace ID and follows the recovery procedure in Section 11 if valid recovery data exists. If this computer has no recovery data for that workspace ID, TAVIO establishes a new local recovery context after the workspace is successfully opened.

## 7. Unsaved changes before OPEN AS

When the user tries to open a different `.tavio` file while the current workspace has unsaved changes, TAVIO must offer:

- **SAVE** — save the current workspace first, then open the selected file.
- **DON'T SAVE** — discard current unsaved changes, then open the selected file.
- **CANCEL** — cancel OPEN AS and keep the current workspace.

If saving the current workspace fails, TAVIO must not proceed to open the other file. The user must be informed if recoverable autosaved changes remain. If the selected file fails validation or cannot be opened, the current workspace must remain intact and active. Workspaces must never be mixed.

## 8. SAVE and SAVE AS

### 8.1 SAVE

SAVE commits the current workspace to the current workspace's main `.tavio` file. The autosave recovery file must be preserved until the new main file has been completely written, validated, replaced, and verified. The detailed sequence is in Section 10.

### 8.2 SAVE AS

SAVE AS saves the current workspace as a new `.tavio` file at a location selected by the user.

- SAVE AS must not alter the source file from which the workspace was opened.
- If the destination already exists, TAVIO must ask the user to confirm before replacing it.
- SAVE AS is distinct from SAVE and must not silently overwrite another workspace file.
- The destination's associated recovery file must be handled safely; an existing recovery file must not be silently treated as belonging to the newly saved workspace.

## 9. Autosave and recovery-file policy

### 9.1 Autosave interval and behavior

1. TAVIO automatically autosaves the current workspace every **5 minutes**.
2. Autosave runs in the background and must not interrupt the user's work with a dialog for each autosave.
3. Autosave writes the latest workspace state to the associated `.bak` recovery file, **not to the main `.tavio` file**.
4. The main `.tavio` file therefore remains at the last successfully completed explicit SAVE or SAVE AS.
5. The autosave recovery file represents the latest successfully written recovery state, not a permanent history of every autosave.
6. If an autosave attempt fails, TAVIO must not replace a valid earlier recovery file with an incomplete or invalid one. The failure must be recorded internally for safe handling, but it must not trigger an immediate notification.
7. Autosave must use a temporary write-and-validate process before replacing the previous recovery file, so interruption during autosave does not destroy the last valid recovery state.

### 9.1.1 Autosave notifications and failure warnings

The user decided that autosave must operate without routine user-facing notifications:

- Do not show a notification when autosave succeeds.
- Do not show an immediate notification when autosave fails.
- Do not show a permanent autosave status in the main-window status bar.
- Autosave continues silently in the background at the agreed 5-minute interval.
- An autosave failure must still be recorded internally so TAVIO can handle the risk safely.

**Show a user-facing warning about an autosave failure only in these circumstances:**

1. When the user chooses **EXIT**.
2. When the user chooses **NEW TIMETABLE**, provided the user has not first used **SAVE** or **SAVE AS**.

The warning must explain that the recovery file could not be updated and that the latest changes may therefore not be protected against an unexpected shutdown. It must not imply that the workspace has been saved successfully.

Do not show this autosave-failure warning during ordinary work or merely because an autosave attempt has failed. This rule does not remove the separate SAVE / DON'T SAVE / CANCEL confirmation behavior already agreed for EXIT and NEW TIMETABLE.

### 9.2 Recovery-file name, identity, and computer-local location

- Recovery data is stored locally on the current computer in an application-local recovery area, not beside the portable `.tavio` file.
- Recovery data is associated with the workspace using its persistent unique workspace ID, not only the workspace filename or folder path. Renaming or moving the `.tavio` file therefore does not change the workspace identity.
- The local recovery record must contain the same workspace ID. Before offering or applying recovery, TAVIO must compare the recovery ID with the ID read from the target workspace. If the IDs do not match, recovery is blocked and the mismatched recovery data must not overwrite the workspace.
- Each computer maintains its own recovery state for the same workspace ID. A recovery file from one computer is not required or expected to be present on another computer.
- When a workspace is opened on a computer that has no local recovery record for its ID, TAVIO creates a fresh local recovery context after successful validation/opening. This must not modify the source `.tavio` file.
- The exact local directory and filename convention are implementation details. A workspace that has not yet been saved also uses its workspace ID to keep its temporary recovery state separate from other workspaces.
- The `.bak` recovery state represents the latest successfully autosaved state. It is **not** a copy of the old main file.
- Keep one current recovery state per workspace per computer; do not maintain multiple dated autosave files or a rolling autosave history.
- The absence of a local `.bak` file must never prevent a valid `.tavio` file from being opened.

### 9.3 No password protection

The user decided that `.tavio` files do not need password protection for SAVE, SAVE AS, or OPEN AS. Do not add a password prompt or password-based file protection to these workflows as part of this specification.

## 10. SAVE sequence and safe replacement

The autosave recovery file and the old main file have distinct roles. The `.bak` file contains the latest recoverable workspace state; the existing main `.tavio` file remains the last successfully saved version until replacement succeeds.

The intended SAVE sequence is:

1. Ensure the latest in-memory workspace state is safely written to the recovery file, using the validated temporary-write procedure in Section 9.
2. Write the new main-package candidate to a temporary file in the same folder as the main `.tavio` file.
3. Validate the candidate package, schema compatibility, database integrity, and required contents.
4. Replace the main `.tavio` file using an appropriate safe replacement operation.
5. Verify that the resulting main file is valid and can be opened.
6. Only after successful verification, delete the associated `.bak` recovery file.

Failure handling:

- If writing or validating the candidate fails before replacement, leave the old main file untouched and retain the valid `.bak` recovery file.
- If replacement or post-replacement verification fails, do not report SAVE success. Preserve all available valid recovery material and restore the old main file only when it can be done safely.
- If the application or computer stops unexpectedly after the main file is replaced but before the `.bak` file is deleted, startup recovery must validate both files and let the user choose whether to keep the main file or restore the recoverable autosaved state.
- Never delete the only valid recovery copy before the main file has been successfully verified.
- Do not assume that rename or replacement is atomic on every supported Windows file system or storage device. Test the actual replacement and recovery behavior on supported environments.

## 11. Recovery after an unexpected shutdown

When TAVIO starts or reopens a workspace, it checks for an associated `.bak` recovery file and any relevant incomplete temporary files.

If recovery material is found:

1. TAVIO informs the user that recoverable autosaved changes or an interrupted save may be available.
2. TAVIO validates the main file, recovery file, and any candidate temporary file before offering an action.
3. If the recovery file is valid and contains a recoverable workspace state, offer:
   - **RESTORE** — recover the workspace from the valid autosave recovery file.
   - **KEEP CURRENT** — continue with the main `.tavio` file and discard the recovery state only after the user's choice is confirmed.
   - **CANCEL** — defer the decision and retain recovery material.
4. If the main file is missing or invalid but the recovery file is valid, explain the situation and offer recovery; never silently overwrite or discard the only valid copy.
5. If the recovery file is invalid, do not use it to overwrite the main file. Explain the problem and preserve other valid data.
6. TAVIO must not automatically delete recovery files before the user has made a decision.
7. Do not claim recovery succeeded until the restored workspace has been validated.

The recovery flow must distinguish ordinary autosaved changes from an interrupted SAVE. It must not assume that the main file is always older or newer without validating the available files and their saved-state metadata.

## 12. OPEN AS — package validation

Before opening a selected `.tavio` file, TAVIO checks:

1. **File format:** The file is a valid TAVIO workspace stored as a native SQLite database.
2. **SQLite structure:** The database structure is readable and contains the required schema objects.
3. **Workspace identity:** The database contains a valid unique workspace ID. This ID is used to locate and verify computer-local recovery data.
4. **Schema version:** The database schema version is supported by the installed TAVIO application.
5. **Database integrity:** SQLite integrity and foreign-key relationships are checked.

The local recovery file is not a prerequisite for OPEN AS. If no local recovery exists for the validated workspace ID, TAVIO opens the workspace and establishes a new computer-local recovery context.

If validation fails:

- OPEN AS is cancelled.
- The currently active workspace remains open and unchanged.
- The selected source file is not modified.
- TAVIO explains the validation problem to the user.

If a selected workspace has an associated valid recovery file, TAVIO must detect it and use the recovery procedure in Section 11 without mixing it with the currently active workspace.

## 13. AUTO MIGRATION for older workspace files

If a selected `.tavio` package uses an older schema version supported for migration:

1. TAVIO identifies the source schema version.
2. TAVIO informs the user that migration is required.
3. TAVIO preserves the original package before migration. The exact preservation mechanism must not overwrite or destroy a valid autosave recovery file.
4. TAVIO runs the defined migrations in the required order.
5. TAVIO validates the migrated database structure and integrity.
6. If migration succeeds, TAVIO opens the migrated workspace using the current supported schema.
7. If migration fails, TAVIO restores or retains the original file and any recovery material, cancels the open, and keeps the current workspace unchanged.

Migration must not silently lose data. Migration steps and compatibility must be explicitly defined and tested for each supported schema version.

## 14. Offline-first operation and multiple computers

TAVIO is an **offline-first desktop application**. Each computer operates independently and does not need internet access or communication with another computer to open, edit, save, or recover a local workspace.

The user explicitly decided:

1. TAVIO does not need to know whether the same `.tavio` file or another copy of the workspace is open on another computer.
2. TAVIO does not implement cross-computer file locking or opening-session detection.
3. TAVIO does not provide automatic synchronization, conflict detection, or merging of changes between computers.
4. Each computer works with its own opened workspace state and its own computer-local recovery data.
5. Users are responsible for transferring `.tavio` files between computers and deciding which copy is the latest/authoritative one.
6. The product does not promise collaborative editing or safe simultaneous synchronization of one shared workspace across computers.

When users transfer files using USB, network storage, or cloud storage, TAVIO treats the file selected by the user as the workspace to open. It does not compare or reconcile other copies. The application must not introduce cross-computer coordination contrary to this offline-first decision.

## 15. Compatibility with files from newer TAVIO versions

**Agreed decision:** TAVIO must reject a `.tavio` file created by a newer TAVIO application version than the installed application.

- OPEN AS is cancelled.
- TAVIO tells the user to update TAVIO before opening the file.
- The selected source file must not be modified or migrated.
- The currently active workspace remains intact and unchanged.

## 16. Implementation boundaries and safeguards

- This document does not authorize changes to the existing database schema, migrations, or application code.
- Do not implement workspace packaging, autosave, save/recovery, or migration by making unrelated changes to stable modules.
- Preserve existing data and enforce database referential integrity.
- Keep workspaces isolated and protect source files during OPEN AS, NEW TIMETABLE, SAVE, SAVE AS, autosave, and migration.
- Define and test failure handling, including process termination, power loss, insufficient disk space, permission errors, interrupted file replacement, recovery on a second computer, and independent local recovery states.
- The design must specifically test that autosave never modifies the main `.tavio` file, that an incomplete autosave cannot replace the last valid computer-local recovery state, that recovery identity must match the workspace ID, and that SAVE does not delete recovery data before the main file is verified.
- Any implementation proposal that changes these agreed user-facing behaviors must be brought back for review before development.

---

**Document status:** Workspace, portable native-SQLite file, offline-first multi-computer behavior, workspace identity, computer-local autosave/recovery, password-protection, and version-compatibility decisions recorded. Implementation remains unauthorized pending separate technical review.

## 17. Existing timetable autosave schema cleanup — planned migration v4

The user reviewed the existing database schema and agreed that the legacy timetable-draft autosave mechanism is not needed as a separate autosave system. TAVIO has not yet implemented the timetable-construction workflow that would use this table, and no active timetable-draft autosave workflow or data needs to be preserved.

The current schema findings are:
- `timetable_workspace_autosaves` is created by the original v1 schema.
- The table has two associated scope-validation triggers: `trg_twa_base_version_ins` and `trg_twa_base_version_upd`.
- `app_settings` is seeded with `autosave_interval_minutes = 10`, describing the old timetable-workspace autosave interval.
- The reviewed application runtime does not currently read or write this table or setting.

**Agreed migration v4 scope (design decision only; not implemented):**

1. Add a new forward-only SQLite schema migration, version 4. Do not edit historical migrations v1, v2, or v3.
2. Drop `trg_twa_base_version_ins` and `trg_twa_base_version_upd`.
3. Drop `timetable_workspace_autosaves`.
4. Delete the legacy `app_settings` row whose key is `autosave_interval_minutes`.
5. Preserve all unrelated tables, rows, indexes, triggers, and foreign-key relationships.
6. Set `PRAGMA user_version` to 4 only as part of the successful atomic migration.
7. A fresh database initialized using the complete migration chain must finish at schema version 4. Existing v3 databases must upgrade to v4.
8. The migration test suite must verify preservation of unrelated data, removal of the legacy table/triggers/setting, foreign-key and SQLite integrity, idempotent initialization, and complete rollback if migration fails.

**One whole-workspace recovery mechanism replaces the legacy timetable autosave mechanism.** The agreed whole-workspace recovery runs every 5 minutes and writes to computer-local recovery data associated with the workspace ID. It does not write to the main portable `.tavio` file. There is no separate timetable autosave table or second autosave interval.

The 5-minute recovery interval is an application-local configuration value, not a workspace setting. It must not be stored in `app_settings` or in the portable `.tavio` database. This keeps computer-local recovery policy separate from portable school workspace data.

Migration v4 only removes obsolete schema objects and the old setting. It does not implement the new recovery engine, local recovery file format, or workspace lifecycle. Those require separate technical design and explicit implementation authorization.

