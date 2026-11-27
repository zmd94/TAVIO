# Workspace Architecture Reconciliation — Technical Review

**Project:** TAVIO — Timetable Administration & Validation Intelligent Organizer  
**Repository:** `zmd94/TAVIO`  
**Branch:** `main`  
**Status:** Agreed architecture direction; detailed design and implementation still require review and explicit authorization  
**Related specification:** [Workspace and Data File Management Decisions](data_file_management.md)

## 1. Purpose

This document records the technical review that reconciles TAVIO's existing SQLite application with the agreed portable `.tavio` workspace-file workflow.

It separates:
- user-facing product decisions already agreed;
- findings observed in the current repository;
- the agreed technical direction; and
- technical details that still need design and testing.

This document is not authorization to change application code, database schema, migrations, or stable modules.

## 2. Agreed architecture direction

The agreed direction is:

1. A `.tavio` workspace will be a **single native SQLite database file** with the `.tavio` extension. It will not use a ZIP layer or another packaging format and should remain inspectable with standard SQLite software.
2. The `.tavio` file is portable: it can be moved and opened on another Windows computer with TAVIO installed, without depending on the original computer or an internet connection.
3. The school logo and other workspace-owned assets must be stored inside that workspace database, so moving or opening a workspace on another computer does not depend on a shared machine-local asset path.
4. Each workspace has a unique, persistent internal workspace ID stored in the database. The ID remains unchanged when the file is moved or renamed. A newly created workspace receives a new ID, even when selected school information is copied from another workspace.
5. TAVIO will introduce a `WorkspaceManager` and active `WorkspaceContext` lifecycle/context layer. The manager owns workspace creation, opening, switching, and safe activation; the context binds the active database manager, repositories, services, file path, and workspace-owned assets together. Repositories and services are rebuilt for the new context when switching. If opening a candidate workspace fails, the current context remains active and intact.
6. TAVIO follows an **offline-first, independent-computer model**. It does not detect whether the same workspace or another copy is open on another computer, does not use cross-computer file locks, and does not provide cross-computer synchronization, conflict detection, or merge. Users manage file transfer and decide which workspace copy is authoritative/latest.
7. Recovery data is computer-local and separate from the portable workspace file. Each computer maintains its own recovery state for a workspace, matched using the persistent workspace ID. A missing local recovery file must never prevent opening a valid `.tavio` file.
8. Existing SQLite repositories and services should be retained where practical. The project should evolve from its current SQLite foundation; a wholesale database or application rewrite is not the goal.
9. Workspace data must remain isolated. A failed OPEN AS or workspace switch must leave the currently active workspace usable and unchanged.
10. These decisions define the architecture direction only. They do not approve a specific migration, new table definition, code change, or implementation task.

## 3. Findings in the current repository

The technical review inspected the current database manager, connection setup, application startup, main window/service wiring, schema and migrations, school-profile service, configuration paths, and the workspace data-file decision record.

### 3.1 SQLite uses WAL mode

The current database connection configures SQLite with WAL journal mode and `synchronous=NORMAL`.

WAL mode can create companion `-wal` and `-shm` files. That behavior needs explicit lifecycle handling if the user-facing workspace is intended to be one portable file. A simple file copy of an active WAL database is not a safe packaging or backup strategy.

**Design implication:** the workspace implementation must define a safe SQLite checkpoint/close/backup lifecycle. A rollback-journal configuration such as `journal_mode=DELETE` may be more suitable for a single-file workspace, but the final journal-mode choice must be tested and approved as part of detailed design. Do not change the current connection mode casually or as an isolated patch.

### 3.2 Database path is currently application-managed

The current `DatabaseManager` obtains its database path from application paths. It is not currently designed around an injected, user-selected active `.tavio` file.

The main window constructs repositories and services around that manager at startup. The current arrangement does not provide a complete, safe mechanism for switching the database underneath all existing repositories and services.

**Design implication:** introduce a workspace context/lifecycle boundary that owns the active database manager and the services/repositories bound to it. Avoid scattered path changes or partial rebinding.

### 3.3 Startup currently initializes a local database

Application startup currently initializes the local SQLite database and applies migrations before the user-facing workspace-selection/reopen workflow.

**Design implication:** startup must be redesigned so it can resolve the last-used workspace, create the initial empty workspace when appropriate, validate a selected workspace, and only then establish the active workspace context. It must not silently create an unrelated blank workspace when reopening the last one fails.

### 3.4 School logo is currently outside the database

The school logo is currently stored under the application-local assets directory (for example, `%LOCALAPPDATA%\\TAVIO\\assets\\school_logo.png`). The school profile stores a path, and the school-profile service resolves and writes the image through application paths.

This creates a workspace-isolation problem: separate workspaces can point to or overwrite the same machine-local logo file.

**Design implication:** move workspace-owned logo bytes into the corresponding `.tavio` database. The application may extract an image to a temporary location when a UI or PDF library requires a filesystem path, but that temporary copy must not become the authoritative asset. Any cache must be workspace-scoped and safely cleaned up.

### 3.5 Existing migrations and schema version

The current migration chain contains schema migrations v1, v2, and v3. Migration v3 adds the nullable `classes.class_teacher_id` foreign key to `teachers(id)` with `ON DELETE RESTRICT`.

The current migration system uses SQLite `PRAGMA user_version` to track the database schema version.

**Design implication:** keep schema versioning distinct from the TAVIO application/package compatibility version. A newer TAVIO application version and a newer SQLite schema are related but are not interchangeable concepts. Validate package/application compatibility before attempting migration.

### 3.6 Existing timetable autosave setting needs separate treatment

The current schema includes `timetable_workspace_autosaves` and an `app_settings` autosave interval setting seeded as 10 minutes in the reviewed code.

The agreed workspace-file specification separately requires whole-workspace recovery autosave every 5 minutes to the associated `.bak` file.

**Design implication:** do not assume these are the same feature. Inspect all reads/writes and user-facing behavior of `timetable_workspace_autosaves` and the 10-minute setting before making changes. Preserve timetable-draft autosave behavior unless a separate reviewed decision explicitly changes it. The whole-workspace `.bak` recovery process must have its own clearly defined responsibility and interval.

## 4. Proposed logical architecture

The following is the recommended separation of responsibilities. Exact class names and module boundaries remain subject to detailed design.

```text
TAVIO Application
|
+-- Application Services
|   +-- Main Window / UI
|   +-- Application-local settings and logging
|   +-- Recent / last-opened workspace reference
|
+-- Workspace Lifecycle Layer
|   +-- WorkspaceManager
|   +-- Active WorkspaceContext
|   +-- NEW TIMETABLE / OPEN AS / SAVE / SAVE AS
|   +-- Compatibility and integrity validation
|   +-- Autosave / backup / recovery coordination
|
+-- Active WorkspaceContext
|   +-- Workspace file path (.tavio)
|   +-- SQLite DatabaseManager / connection
|   +-- Repositories and services for this workspace
|   +-- Workspace-owned assets (including school logo)
|
+-- Native SQLite .tavio file
    +-- Existing TAVIO relational data
    +-- Workspace settings and report settings
    +-- Timetable data and versions
    +-- Embedded workspace assets
```

### 4.1 Application-local data versus workspace data

Keep application-local operational data separate from school workspace data.

Potential application-local items include logs, application preferences, last-opened workspace reference, lock/coordination files, and temporary staging files. These must not contain authoritative school data that should travel with the `.tavio` package.

School profile, master data, assignments, timetables, report configuration, and school-owned assets belong to the active workspace.

The exact list of application-local settings versus workspace settings must be checked against current `app_settings` usage before implementation.

### 4.2 Workspace context and switching

The workspace lifecycle layer should own creation and activation of the workspace context.

For OPEN AS, the recommended sequence is:
1. Resolve unsaved-change and recovery decisions for the current workspace using the already agreed user workflow.
2. Validate the candidate `.tavio` file without changing the active context.
3. Open and initialize a candidate database manager and its dependent services/repositories.
4. Complete required integrity and compatibility checks.
5. Activate the new context only after all prior steps succeed.
6. Release the previous context safely after successful activation.

If any candidate step fails, retain the existing active workspace and its services. Never mix repositories or services from two workspaces.

### 4.3 Database manager injection

The current fixed-path database manager should be adapted through a deliberate design so it can receive the active workspace database path (or a workspace-owned connection provider).

Repositories and services must be constructed against the correct active context. Avoid mutating a global path while existing repositories still hold connections to the previous database.

## 5. Embedded workspace assets

The approved direction is that the logo is stored within the `.tavio` workspace database.

A possible implementation is a dedicated table such as `workspace_assets` containing an asset key, media type, binary content, and any required metadata. This is an example of a design option, **not an approved schema definition**.

Before adding a table or migration, decide:
- supported asset types and size limits;
- whether there can be multiple logos or historical assets;
- how asset replacement and deletion work;
- how UI and PDF code access asset bytes;
- whether temporary extracted files are needed and how they are scoped/cleaned;
- how existing school-logo files are imported during migration;
- how failed migration or SAVE preserves the original asset and workspace.

Do not leave the authoritative logo in a shared application-local folder after workspace embedding is implemented.

## 5.1 Portable workspace identity and computer-local recovery

Every workspace must contain a unique internal workspace ID. The ID is generated when the workspace is created and remains stable through SAVE, SAVE AS, file movement, and file renaming. A genuinely new workspace receives a new ID.

The recovery mechanism is local to each computer:
- The portable `.tavio` file contains the authoritative workspace data and workspace ID.
- Each computer keeps its own recovery data in an application-local recovery area, keyed by workspace ID. Recovery data is not required to travel with the `.tavio` file.
- The local recovery record also carries the workspace ID. TAVIO must verify the ID before offering or applying recovery; a mismatch blocks recovery.
- When a `.tavio` file is opened on a computer that has no local recovery record for that workspace ID, TAVIO creates a new local recovery context after successfully validating/opening the workspace. The source `.tavio` is not modified merely by opening it.
- The absence of a local recovery file must not block OPEN AS.

The exact local recovery file layout and naming remain implementation details, but the design must not put the only recovery copy beside a portable file on removable or shared storage in a way that makes recovery depend on that location.

## 5.2 Offline-first and multiple computers

TAVIO does not coordinate workspace access between computers. It does not check whether a file or another copy is open elsewhere, does not create cross-computer locks, and does not synchronize or merge data.

Users may independently open a `.tavio` file on different computers. Each computer works with its own local state and recovery data. When users transfer workspace files by USB, network storage, or cloud storage, they are responsible for choosing and managing the latest authoritative copy. TAVIO does not resolve differences between copies.

This is not a collaborative editing or cloud-sync model. Avoid introducing network services, mandatory internet access, or cross-computer coordination into the workspace lifecycle.

## 6. Safe SQLite persistence and recovery

The existing workspace data-file decisions remain authoritative for user-facing behavior:
- one `.tavio` file per workspace;
- SAVE and SAVE AS are explicit operations;
- autosave every 5 minutes writes the associated `.bak`, not the main file;
- a failed autosave must not replace the last valid `.bak`;
- SAVE must not delete the recovery file until the new main file has been fully written and validated;
- recovery choices are RESTORE, KEEP CURRENT, and CANCEL;
- newer-version workspace files are rejected without modifying the source;
- older supported files are migrated only after preserving the original and validating the result.

### 6.1 Do not copy a live WAL database as a normal file

If WAL remains enabled, a valid database state may depend on the WAL file. Do not use a raw filesystem copy of only the main database file as the backup or SAVE candidate.

The detailed design must choose and test a safe mechanism, such as SQLite's Backup API or a properly coordinated checkpoint and connection shutdown. A candidate file should be validated before it replaces the destination.

### 6.2 Candidate validation

At minimum, the design should evaluate:
- SQLite `PRAGMA integrity_check`;
- SQLite `PRAGMA foreign_key_check`;
- required TAVIO schema objects and migration state;
- TAVIO application/package compatibility metadata;
- required workspace contents and asset integrity.

Validation must happen before replacing a valid main or recovery file. Exact validation rules and performance impact need testing with realistic school workspaces.

### 6.3 Journal mode decision

A single-file portable workspace may be easier to manage with SQLite rollback-journal mode (`DELETE`) than WAL, provided the application's local database access and performance requirements are satisfied. Cross-computer simultaneous editing and coordination are not product requirements.

This is a candidate decision for detailed design, not an instruction to change the current database connection immediately. Compare:
- sidecar-file behavior;
- local read/write needs;
- checkpoint and shutdown behavior;
- save/backup reliability;
- performance on typical and large school workspaces;
- behavior on USB and network-backed storage, while keeping the offline-first/no-sync product boundary clear.

## 7. Migration and compatibility boundaries

1. Validate that a candidate file is a TAVIO workspace before treating it as one.
2. Read both TAVIO application/package compatibility metadata and SQLite schema version.
3. Reject files from a newer TAVIO application version without modifying them.
4. For an older supported schema, preserve the original package before migration.
5. Migrate a safe candidate rather than risking the only original file.
6. Validate the migrated candidate before activation.
7. On failure, retain the original package and recovery material, and keep the currently active workspace unchanged.

Do not conflate `PRAGMA user_version` with the application version. The exact metadata location and compatibility policy need a separate technical specification.

## 8. Required follow-up technical design

Before implementation, prepare and review designs for:

1. Workspace file format metadata and application/schema compatibility.
2. WorkspaceManager and WorkspaceContext lifecycle and ownership.
3. DatabaseManager path/connection injection and repository/service construction.
4. SQLite journal mode, checkpoint, connection close, and backup strategy.
5. Embedded asset schema and logo import/access lifecycle.
6. Startup and last-opened workspace behavior.
7. NEW TIMETABLE creation and copying only SCHOOL PROFILE, SCHOOL ADMINISTRATORS, and SCHEDULE SIGNATORIES.
8. Computer-local recovery for a workspace that has not yet been saved to a user-selected path, and creation of a fresh local recovery context when a portable workspace is opened on another computer.
9. Separation of whole-workspace recovery autosave from existing timetable draft autosave.
10. SAVE, SAVE AS, computer-local recovery, migration, and interrupted replacement failure handling.
11. Test plan for crash, power loss, disk full, permission errors, USB/network/removable storage, invalid files, local recovery identity checks, and multiple workspace switching. Do not add cross-computer locking or synchronization tests as product requirements.

## 9. Explicit implementation boundaries

- No code, database schema, or migration changes are authorized by this document.
- Do not begin implementation solely because the architecture direction is agreed.
- Do not repurpose existing timetable autosave tables/settings without tracing their usage and reviewing the impact.
- Do not change unrelated stable modules or perform a broad refactor.
- Preserve the existing SQLite foundation and existing data wherever possible.
- Bring unresolved technical choices back for review before implementation.

---

**Summary:** TAVIO will move toward a native SQLite `.tavio` workspace with workspace-owned assets embedded in the database and a dedicated workspace lifecycle/context layer. This is the agreed direction; detailed technical design and implementation approval remain separate steps.
